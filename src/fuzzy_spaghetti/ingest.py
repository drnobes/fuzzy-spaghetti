"""
Ingest pipeline: .bib files → SQLite metadata DB, PDFs → BM25/TF-IDF indices.

Usage as library:
    from fuzzy_spaghetti.ingest import build_metadata_db, build_search_index
    build_metadata_db()          # reads all .bib files under PAPERS_ROOT
    build_search_index()         # extracts text from PDFs, builds BM25 + TF-IDF
"""

import json
import pickle
import re
import sqlite3
from pathlib import Path

import numpy as np

from . import config


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

    # Find companion PDF
    bib_stem = bib_path.stem
    pdf_candidates = list(bib_path.parent.glob(f"{bib_stem}.pdf"))
    if not pdf_candidates:
        # Try matching by cite_key prefix in filenames
        pdf_candidates = list(bib_path.parent.glob("*.pdf"))
    pdf_path = pdf_candidates[0] if pdf_candidates else None

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

def _extract_pdf_text(pdf_path: Path) -> list[str]:
    """Extract text page-by-page from a PDF. Returns list of page texts."""
    import pdfplumber

    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text)
    except Exception as e:
        print(f"  WARNING: failed to extract {pdf_path.name}: {e}")
    return pages


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

    for row in rows:
        pdf_path = Path(row["pdf_path"]) if row["pdf_path"] else None
        if not pdf_path or not pdf_path.exists():
            # Try to find it relative to papers_root
            if row["pdf_filename"]:
                candidates = list(papers_root.rglob(row["pdf_filename"]))
                pdf_path = candidates[0] if candidates else None
            if not pdf_path or not pdf_path.exists():
                print(f"  SKIP (no PDF): {row['cite_key']}")
                continue

        print(f"  Extracting: {pdf_path.name}")
        pages = _extract_pdf_text(pdf_path)

        for page_num, page_text in enumerate(pages, 1):
            chunks.append({
                "pdf_name": row["pdf_filename"] or pdf_path.name,
                "pdf_path": str(pdf_path),
                "page_num": page_num,
                "chunk_idx": 0,
                "cite_key": row["cite_key"],
                "title": row["title"],
                "authors": row["author_list"] or "",
                "year": row["year"] or "",
                "topic": row["topic"] or "",
            })
            texts.append(page_text)

    if not texts:
        print("No text extracted — nothing to index.")
        return {"chunks": 0}

    print(f"Building BM25 over {len(texts)} chunks...")
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)
    with open(index_dir / "bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)

    print(f"Building TF-IDF over {len(texts)} chunks...")
    tfidf = TfidfVectorizer(max_features=50000, stop_words="english")
    matrix = tfidf.fit_transform(texts).toarray()
    with open(index_dir / "tfidf.pkl", "wb") as f:
        pickle.dump(tfidf, f)
    np.save(str(index_dir / "tfidf_matrix.npy"), matrix)

    # Save chunks + texts for later use (vector index, search)
    with open(index_dir / "chunks.json", "w") as f:
        json.dump({"chunks": chunks, "texts": texts}, f)

    print(f"Search index: {len(chunks)} chunks from {len(set(c['cite_key'] for c in chunks))} papers")
    print(f"Saved to: {index_dir}")
    return {"chunks": len(chunks), "papers": len(set(c["cite_key"] for c in chunks))}
