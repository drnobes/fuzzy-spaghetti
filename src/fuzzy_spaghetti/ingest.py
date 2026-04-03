"""
Ingest pipeline: .bib files → SQLite metadata DB, PDFs → BM25/TF-IDF indices.

Usage as library:
    from fuzzy_spaghetti.ingest import build_metadata_db, build_search_index
    build_metadata_db()          # reads all .bib files under PAPERS_ROOT
    build_search_index()         # extracts text from PDFs, builds BM25 + TF-IDF
"""

import json
import os
import pickle
import re
import sqlite3
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from . import config

# Threshold: if average chars/page is below this, trigger OCR
_OCR_CHARS_PER_PAGE_THRESHOLD = 100


# ── .bib parsing ─────────────────────────────────────────────────────────────

def parse_bib_file(bib_path: Path) -> dict | None:
    """Parse a single .bib file into a metadata dict."""
    text = bib_path.read_text(encoding="utf-8", errors="replace")

    # Extract entry type and cite key
    m = re.search(r"@(\w+)\{([^,]+),", text)
    if not m:
        return None
    entry_type, cite_key = m.group(1).lower(), m.group(2).strip()

    def field(name: str) -> str:
        # Match field = {value} or field = value
        pat = rf"{name}\s*=\s*\{{(.*?)\}}"
        fm = re.search(pat, text, re.DOTALL)
        if fm:
            return re.sub(r"\s+", " ", fm.group(1)).strip()
        return ""

    # Parse authors: "Last1, First1 and Last2, First2" → list of [last, first]
    raw_authors = field("author")
    authors = []
    if raw_authors:
        for part in raw_authors.split(" and "):
            part = part.strip()
            if "," in part:
                pieces = [p.strip() for p in part.split(",", 1)]
                # Unescape BibTeX
                pieces = [p.replace(r"\_", "_").replace(r"\&", "&") for p in pieces]
                authors.append(pieces)  # [last, first]
            elif part:
                authors.append([part, ""])

    # Parse CSL-JSON from comments for richer data
    csl = {}
    csl_match = re.search(r"% CSL-JSON.*?\n((?:%.*\n)+)", text)
    if csl_match:
        csl_text = "\n".join(
            line.lstrip("% ") for line in csl_match.group(1).strip().split("\n")
        )
        try:
            csl = json.loads(csl_text)
        except json.JSONDecodeError:
            pass

    # Find companion PDF: check bib 'file' field first, then stem match
    bib_file_field = field("file")
    pdf_path = None
    if bib_file_field:
        candidate = bib_path.parent / bib_file_field
        if candidate.exists():
            pdf_path = candidate
    if not pdf_path:
        candidate = bib_path.with_suffix(".pdf")
        if candidate.exists():
            pdf_path = candidate

    return {
        "entry_type": entry_type,
        "cite_key": cite_key,
        "title": field("title"),
        "authors": authors,
        "year": field("year"),
        "date": field("date"),
        "institution": field("institution"),
        "publisher": csl.get("publisher", ""),
        "abstract": field("abstract"),
        "keywords": field("keywords"),
        "doc_type": field("type") or entry_type,
        "identifier": field("number"),
        "pages": field("pages"),
        "language": field("language") or "en",
        "pdf_filename": pdf_path.name if pdf_path else "",
        "pdf_path": str(pdf_path) if pdf_path else "",
        "topic": bib_path.parent.name,
    }


# ── SQLite metadata DB ──────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cite_key    TEXT UNIQUE NOT NULL,
    entry_type  TEXT,
    title       TEXT,
    year        TEXT,
    date        TEXT,
    institution TEXT,
    publisher   TEXT,
    abstract    TEXT,
    keywords    TEXT,
    doc_type    TEXT,
    identifier  TEXT,
    pages       TEXT,
    language    TEXT,
    pdf_filename TEXT,
    pdf_path    TEXT,
    topic       TEXT
);

CREATE TABLE IF NOT EXISTS authors (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    family   TEXT,
    given    TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
    title, abstract, keywords, institution, publisher,
    content='papers', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
    INSERT INTO papers_fts(rowid, title, abstract, keywords, institution, publisher)
    VALUES (new.id, new.title, new.abstract, new.keywords, new.institution, new.publisher);
END;

CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
    INSERT INTO papers_fts(papers_fts, rowid, title, abstract, keywords, institution, publisher)
    VALUES ('delete', old.id, old.title, old.abstract, old.keywords, old.institution, old.publisher);
END;
"""


def build_metadata_db(papers_root: Path | None = None, index_dir: Path | None = None) -> Path:
    """Scan all .bib files under papers_root, build/update library.sqlite."""
    papers_root = papers_root or config.PAPERS_ROOT
    index_dir = index_dir or config.INDEX_DIR
    db_path = index_dir / "library.sqlite"
    index_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    bib_files = sorted(papers_root.rglob("*.bib"))
    inserted, skipped = 0, 0

    for bib_path in bib_files:
        # Skip anything in processed/ subdirectories
        if "processed" in str(bib_path).lower():
            continue
        meta = parse_bib_file(bib_path)
        if not meta:
            skipped += 1
            continue

        # Upsert: skip if cite_key already exists
        existing = conn.execute(
            "SELECT id FROM papers WHERE cite_key = ?", (meta["cite_key"],)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        cur = conn.execute(
            """INSERT INTO papers
               (cite_key, entry_type, title, year, date, institution, publisher,
                abstract, keywords, doc_type, identifier, pages, language,
                pdf_filename, pdf_path, topic)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (meta["cite_key"], meta["entry_type"], meta["title"], meta["year"],
             meta["date"], meta["institution"], meta["publisher"],
             meta["abstract"], meta["keywords"], meta["doc_type"],
             meta["identifier"], meta["pages"], meta["language"],
             meta["pdf_filename"], meta["pdf_path"], meta["topic"]),
        )
        paper_id = cur.lastrowid
        for author in meta["authors"]:
            family = author[0] if len(author) > 0 else ""
            given = author[1] if len(author) > 1 else ""
            conn.execute(
                "INSERT INTO authors (paper_id, family, given) VALUES (?, ?, ?)",
                (paper_id, family, given),
            )
        inserted += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    conn.close()

    print(f"Metadata DB: {inserted} new, {skipped} skipped, {total} total papers → {db_path}")
    return db_path


# ── Full-text index (BM25 + TF-IDF) ────────────────────────────────────────

def _pdfplumber_extract(pdf_path: Path) -> tuple[list[str], int]:
    """Extract text page-by-page with pdfplumber. Returns (page_texts, total_page_count)."""
    import pdfplumber

    pages = []
    total_pages = 0
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
    return pages, total_pages


# ── Scan diagnostics ──────────────────────────────────────────────────────

# Quality thresholds — tuned from empirical runs across the library.
_QUALITY_REAL_WORD_PCT = 0.35      # below this → likely garbled OCR
_QUALITY_CHARS_PER_PAGE_LOW = 200  # below this after OCR → suspect

def _diagnose_scan(pdf_path: Path, sample_pages: int = 5) -> dict:
    """Quick diagnostics on a scanned PDF before OCR.

    Checks:
    - Image-only pages (no embedded text)
    - Effective DPI (from image dimensions vs page dimensions)
    - Landscape/rotation (width > height)

    Returns a dict of diagnostic info and a list of warnings.
    """
    import pdfplumber

    warnings = []
    diag = {"warnings": warnings, "image_only": False, "needs_rotation": False,
            "estimated_dpi": 0, "pages_checked": 0}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            n_check = min(sample_pages, len(pdf.pages))
            # Sample from content pages (skip first 10 which are often front matter)
            start = min(10, len(pdf.pages) - 1)
            indices = range(start, min(start + n_check, len(pdf.pages)))
            diag["pages_checked"] = len(indices)

            text_pages = 0
            image_pages = 0
            landscape_pages = 0
            dpis = []

            for i in indices:
                pg = pdf.pages[i]
                text = pg.extract_text() or ""
                has_text = len(text.strip()) > 50
                has_images = len(pg.images) > 0

                if has_text:
                    text_pages += 1
                if has_images and not has_text:
                    image_pages += 1

                # Check orientation: if page is portrait but image is wider
                # than tall relative to the page, the content is rotated
                if pg.width > pg.height:
                    landscape_pages += 1

                # Estimate DPI from image dimensions vs page size
                if pg.images:
                    img = pg.images[0]
                    img_w = img.get("width", 0)
                    if img_w > 0 and pg.width > 0:
                        # Page dimensions are in points (72pt = 1in)
                        page_inches = pg.width / 72
                        dpi = img_w / page_inches
                        dpis.append(dpi)

            diag["image_only"] = image_pages > 0 and text_pages == 0
            diag["needs_rotation"] = landscape_pages > n_check / 2

            if dpis:
                avg_dpi = sum(dpis) / len(dpis)
                diag["estimated_dpi"] = round(avg_dpi)
                if avg_dpi < 150:
                    warnings.append(f"Low DPI (~{avg_dpi:.0f}), OCR quality may suffer")

            if diag["image_only"]:
                warnings.append("Image-only PDF (scanned), will require OCR")
            if diag["needs_rotation"]:
                warnings.append("Landscape orientation detected — pages likely rotated")

    except Exception as e:
        warnings.append(f"Diagnostic failed: {e}")

    return diag


def _check_ocr_quality(pages: list[str], pdf_name: str) -> list[str]:
    """Post-OCR quality checks. Returns a list of warnings (empty = OK)."""
    warnings = []
    if not pages:
        warnings.append("OCR produced zero text pages")
        return warnings

    total_chars = sum(len(p) for p in pages)
    avg_chars = total_chars / len(pages)

    # Check character density — too low means OCR mostly failed
    if avg_chars < _QUALITY_CHARS_PER_PAGE_LOW:
        warnings.append(
            f"Low text density after OCR ({avg_chars:.0f} chars/pg avg, "
            f"expected >{_QUALITY_CHARS_PER_PAGE_LOW})"
        )

    # Check word quality — sample middle pages (skip front/back matter)
    mid = len(pages) // 2
    sample = " ".join(pages[max(0, mid - 2):mid + 3])
    words = sample.split()
    if words:
        real_words = sum(1 for w in words if len(w) >= 3 and w.isalpha())
        pct = real_words / len(words)
        if pct < _QUALITY_REAL_WORD_PCT:
            warnings.append(
                f"Low OCR quality ({pct:.0%} recognizable words, "
                f"expected >{_QUALITY_REAL_WORD_PCT:.0%}) — "
                f"check scan rotation/DPI"
            )

    return warnings


# ── Extraction pipeline ───────────────────────────────────────────────────

def _ocr_extract(pdf_path: Path) -> tuple[list[str], list[str]]:
    """Run OCR on a scanned PDF via ocrmypdf, then re-extract text.

    ocrmypdf adds a text layer to the PDF; we then extract with pdfplumber.
    The OCR'd PDF is saved alongside the original as <name>.ocr.pdf.

    Returns (page_texts, warnings).

    Key parameters tuned empirically:
    - rotate_pages: auto-detect and fix rotated scans (critical for book scans)
    - oversample=300: upsample low-DPI images before OCR (significant quality gain)
    - force_ocr: treat as image-only (faster than skip_text for fully scanned docs)
    """
    import ocrmypdf

    ocr_output = pdf_path.with_suffix(".ocr.pdf")

    n_jobs = max(1, int(os.cpu_count() ** 0.5))
    result = ocrmypdf.ocr(
        str(pdf_path),
        str(ocr_output),
        language=["eng"],
        force_ocr=True,
        rotate_pages=True,
        oversample=300,
        optimize=0,
        jobs=n_jobs,
        progress_bar=False,
    )
    warnings = []
    if result != ocrmypdf.ExitCode.ok:
        warnings.append(f"ocrmypdf exit code: {result.name}")

    pages, _ = _pdfplumber_extract(ocr_output)

    # Post-OCR quality gate
    quality_warnings = _check_ocr_quality(pages, pdf_path.name)
    warnings.extend(quality_warnings)

    return pages, warnings


def _extract_pdf_text(pdf_path: Path) -> tuple[list[str], dict]:
    """Extract text page-by-page from a PDF, with OCR fallback for scanned docs.

    Strategy:
    1. Try pdfplumber (fast).
    2. If avg chars/page < threshold → diagnose the scan, then OCR.
    3. After OCR, run quality checks and surface warnings in telemetry.

    Returns (page_texts, telemetry) where telemetry contains timing and size info.
    """
    file_mb = pdf_path.stat().st_size / (1024 * 1024)
    t0 = time.perf_counter()
    pages = []
    total_pages = 0
    total_chars = 0
    ocr_used = False
    all_warnings = []

    try:
        pages, total_pages = _pdfplumber_extract(pdf_path)
        total_chars = sum(len(p) for p in pages)

        # Check if extraction was too thin — likely a scanned PDF
        avg_chars = total_chars / total_pages if total_pages > 0 else 0
        if total_pages > 0 and avg_chars < _OCR_CHARS_PER_PAGE_THRESHOLD:
            # Diagnose before OCR
            diag = _diagnose_scan(pdf_path)
            for w in diag["warnings"]:
                print(f"    DIAG: {w}")
                all_warnings.append(w)

            print(f"    Low text ({avg_chars:.0f} chars/pg avg) — running OCR...")
            ocr_used = True
            t_ocr_start = time.perf_counter()
            pages, ocr_warnings = _ocr_extract(pdf_path)
            total_chars = sum(len(p) for p in pages)
            t_ocr = time.perf_counter() - t_ocr_start

            for w in ocr_warnings:
                print(f"    WARN: {w}")
                all_warnings.append(w)

            print(f"    OCR done: {len(pages)} pages, {total_chars} chars "
                  f"in {t_ocr:.1f}s")
    except Exception as e:
        msg = f"Extraction failed: {e}"
        print(f"  WARNING: {msg}")
        all_warnings.append(msg)

    elapsed = time.perf_counter() - t0

    telemetry = {
        "file": pdf_path.name,
        "file_mb": round(file_mb, 2),
        "total_pages": total_pages,
        "extracted_pages": len(pages),
        "total_chars": total_chars,
        "extract_sec": round(elapsed, 2),
        "pages_per_sec": round(total_pages / elapsed, 1) if elapsed > 0 else 0,
        "mb_per_sec": round(file_mb / elapsed, 2) if elapsed > 0 else 0,
        "ocr_used": ocr_used,
        "warnings": all_warnings,
    }
    return pages, telemetry


def _extract_one(args: tuple) -> tuple[str, list[str], dict]:
    """Worker function for parallel extraction. Takes (cite_key, pdf_path_str).

    Returns (cite_key, page_texts, telemetry). Must be a top-level function
    for ProcessPoolExecutor pickling.
    """
    cite_key, pdf_path_str = args
    pdf_path = Path(pdf_path_str)
    pages, telemetry = _extract_pdf_text(pdf_path)
    return cite_key, pages, telemetry


def build_search_index(
    papers_root: Path | None = None,
    index_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict:
    """Extract text from all indexed PDFs, build BM25 + TF-IDF indices."""
    from rank_bm25 import BM25Okapi
    from sklearn.feature_extraction.text import TfidfVectorizer

    papers_root = papers_root or config.PAPERS_ROOT
    index_dir = index_dir or config.INDEX_DIR
    db_path = db_path or config.DB_PATH
    index_dir.mkdir(parents=True, exist_ok=True)

    # Load paper metadata from DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT p.*, GROUP_CONCAT(a.given || ' ' || a.family, '; ') AS author_list
        FROM papers p
        LEFT JOIN authors a ON a.paper_id = p.id
        GROUP BY p.id
    """).fetchall()
    conn.close()

    chunks = []   # metadata per chunk
    texts = []    # raw text per chunk
    pdf_telemetry = []

    # Resolve PDF paths and build work items
    work_items = []  # (cite_key, pdf_path_str)
    row_by_key = {}  # cite_key → row
    for row in rows:
        pdf_path = Path(row["pdf_path"]) if row["pdf_path"] else None
        if not pdf_path or not pdf_path.exists():
            if row["pdf_filename"]:
                candidates = list(papers_root.rglob(row["pdf_filename"]))
                pdf_path = candidates[0] if candidates else None
            if not pdf_path or not pdf_path.exists():
                print(f"  SKIP (no PDF): {row['cite_key']}")
                continue

        work_items.append((row["cite_key"], str(pdf_path)))
        row_by_key[row["cite_key"]] = row

    # Parallel extraction — use processes (not threads) because pdfplumber
    # and ocrmypdf both benefit from true parallelism.
    # Cap workers: too many causes memory pressure on large PDFs.
    n_workers = min(os.cpu_count() or 1, len(work_items), 4)
    results_by_key = {}

    t_extract_start = time.perf_counter()
    if n_workers > 1 and len(work_items) > 1:
        print(f"Extracting {len(work_items)} PDFs with {n_workers} workers...")
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            futures = {pool.submit(_extract_one, item): item for item in work_items}
            for future in as_completed(futures):
                cite_key, pages, telemetry = future.result()
                results_by_key[cite_key] = (pages, telemetry)
                ocr_tag = " [OCR]" if telemetry.get("ocr_used") else ""
                print(f"  {telemetry['file']}: {telemetry['total_pages']}pg, "
                      f"{telemetry['file_mb']}MB → {telemetry['extract_sec']}s "
                      f"({telemetry['pages_per_sec']} pg/s){ocr_tag}")
    else:
        print(f"Extracting {len(work_items)} PDFs (single worker)...")
        for item in work_items:
            cite_key, pages, telemetry = _extract_one(item)
            results_by_key[cite_key] = (pages, telemetry)
            ocr_tag = " [OCR]" if telemetry.get("ocr_used") else ""
            print(f"  {telemetry['file']}: {telemetry['total_pages']}pg, "
                  f"{telemetry['file_mb']}MB → {telemetry['extract_sec']}s "
                  f"({telemetry['pages_per_sec']} pg/s){ocr_tag}")

    # Assemble chunks in original row order (deterministic)
    for cite_key, pdf_path_str in work_items:
        if cite_key not in results_by_key:
            continue
        pages, telemetry = results_by_key[cite_key]
        pdf_telemetry.append(telemetry)
        row = row_by_key[cite_key]

        for page_num, page_text in enumerate(pages, 1):
            chunks.append({
                "pdf_name": row["pdf_filename"] or Path(pdf_path_str).name,
                "pdf_path": pdf_path_str,
                "page_num": page_num,
                "chunk_idx": 0,
                "cite_key": row["cite_key"],
                "title": row["title"],
                "authors": row["author_list"] or "",
                "year": row["year"] or "",
                "topic": row["topic"] or "",
            })
            texts.append(page_text)
    t_extract_total = time.perf_counter() - t_extract_start

    if not texts:
        print("No text extracted — nothing to index.")
        return {"chunks": 0}

    t_bm25_start = time.perf_counter()
    print(f"Building BM25 over {len(texts)} chunks...")
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)
    with open(index_dir / "bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)
    t_bm25 = time.perf_counter() - t_bm25_start

    t_tfidf_start = time.perf_counter()
    print(f"Building TF-IDF over {len(texts)} chunks...")
    tfidf = TfidfVectorizer(max_features=50000, stop_words="english")
    matrix = tfidf.fit_transform(texts).toarray()
    with open(index_dir / "tfidf.pkl", "wb") as f:
        pickle.dump(tfidf, f)
    np.save(str(index_dir / "tfidf_matrix.npy"), matrix)
    t_tfidf = time.perf_counter() - t_tfidf_start

    # Save chunks + texts for later use (vector index, search)
    with open(index_dir / "chunks.json", "w") as f:
        json.dump({"chunks": chunks, "texts": texts}, f)

    # ── Telemetry summary ─────────────────────────────────────────────────
    total_mb = sum(t["file_mb"] for t in pdf_telemetry)
    total_pages = sum(t["total_pages"] for t in pdf_telemetry)
    ocr_count = sum(1 for t in pdf_telemetry if t.get("ocr_used"))
    slowest = max(pdf_telemetry, key=lambda t: t["extract_sec"]) if pdf_telemetry else None

    print(f"\n{'='*60}")
    print(f"TELEMETRY SUMMARY")
    print(f"{'='*60}")
    print(f"PDF extraction:  {t_extract_total:.1f}s wall-clock  ({len(pdf_telemetry)} files, "
          f"{total_mb:.1f}MB, {total_pages} pages, {n_workers} workers)")
    if ocr_count:
        print(f"  OCR fallback:  {ocr_count} file(s)")
    if total_pages > 0:
        sum_extract = sum(t["extract_sec"] for t in pdf_telemetry)
        print(f"  Sum-of-parts:  {sum_extract:.1f}s  "
              f"(speedup: {sum_extract/t_extract_total:.1f}x from parallelism)")
        print(f"  Avg throughput: {total_pages/t_extract_total:.1f} pages/s, "
              f"{total_mb/t_extract_total:.2f} MB/s")
    if slowest:
        print(f"  Slowest file:  {slowest['file']} "
              f"({slowest['total_pages']}pg, {slowest['file_mb']}MB, {slowest['extract_sec']}s)")
    print(f"BM25 build:      {t_bm25:.1f}s")
    print(f"TF-IDF build:    {t_tfidf:.1f}s")
    print(f"Total pipeline:  {t_extract_total + t_bm25 + t_tfidf:.1f}s")
    print(f"{'='*60}")

    # Per-PDF detail table
    print(f"\n{'File':<50} {'MB':>5} {'Pages':>5} {'Sec':>6} {'Pg/s':>6} {'OCR':>4}")
    print("-" * 80)
    for t in sorted(pdf_telemetry, key=lambda x: -x["extract_sec"]):
        name = t["file"][:49]
        ocr_flag = "YES" if t.get("ocr_used") else ""
        print(f"{name:<50} {t['file_mb']:>5} {t['total_pages']:>5} "
              f"{t['extract_sec']:>6} {t['pages_per_sec']:>6} {ocr_flag:>4}")

    # ── Warnings summary ─────────────────────────────────────────────────
    files_with_warnings = [t for t in pdf_telemetry if t.get("warnings")]
    if files_with_warnings:
        print(f"\n{'!'*60}")
        print(f"QUALITY WARNINGS ({len(files_with_warnings)} file(s))")
        print(f"{'!'*60}")
        for t in files_with_warnings:
            print(f"\n  {t['file']}:")
            for w in t["warnings"]:
                print(f"    - {w}")
        print()

    n_papers = len(set(c["cite_key"] for c in chunks))
    print(f"\nSearch index: {len(chunks)} chunks from {n_papers} papers")
    print(f"Saved to: {index_dir}")

    result = {
        "chunks": len(chunks),
        "papers": n_papers,
        "telemetry": {
            "pdf_extraction_sec": round(t_extract_total, 2),
            "bm25_build_sec": round(t_bm25, 2),
            "tfidf_build_sec": round(t_tfidf, 2),
            "total_mb": round(total_mb, 2),
            "total_pages": total_pages,
            "per_pdf": pdf_telemetry,
        },
    }
    return result
