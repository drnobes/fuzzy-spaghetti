"""
Search engine: BM25, TF-IDF, hybrid (RRF), metadata (SQL), and semantic (LanceDB).

Usage:
    from fuzzy_spaghetti.search import search
    results = search("OIS discounting", mode="hybrid", top_k=5)
"""

import json
import pickle
import re
import sqlite3
import tempfile
import shutil
from pathlib import Path

import numpy as np

from . import config


# ── index loading (cached at module level) ───────────────────────────────────

_cache: dict = {}


def _load_fulltext():
    if "bm25" in _cache:
        return _cache["bm25"], _cache["tfidf"], _cache["matrix"], _cache["chunks"], _cache["texts"]

    with open(config.BM25_PATH, "rb") as f:
        _cache["bm25"] = pickle.load(f)
    with open(config.TFIDF_PATH, "rb") as f:
        _cache["tfidf"] = pickle.load(f)
    _cache["matrix"] = np.load(str(config.TFIDF_MATRIX_PATH))
    with open(config.CHUNKS_PATH) as f:
        data = json.load(f)
    _cache["chunks"] = data["chunks"]
    _cache["texts"] = data["texts"]
    return _cache["bm25"], _cache["tfidf"], _cache["matrix"], _cache["chunks"], _cache["texts"]


def _load_lancedb():
    if "lance_tbl" in _cache:
        return _cache["lance_tbl"]
    try:
        import lancedb
        db = lancedb.connect(str(config.VECTORS_DIR))
        tbl = db.open_table("papers")
        _cache["lance_tbl"] = tbl
        return tbl
    except Exception:
        return None


def invalidate_cache():
    """Clear cached indices (call after re-indexing)."""
    _cache.clear()


# ── helpers ──────────────────────────────────────────────────────────────────

def _rrf(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _snippet(text: str, query: str, window: int = 300) -> str:
    terms = query.lower().split()
    best_start, best_score = 0, -1
    for i in range(0, max(len(text) - window, 1), 50):
        seg = text[i:i + window].lower()
        score = sum(seg.count(t) for t in terms)
        if score > best_score:
            best_score = score
            best_start = i
    snip = text[best_start:best_start + window].strip()
    if best_start > 0:
        snip = re.sub(r"^\S+\s", "", snip)
    return snip + ("\u2026" if best_start + window < len(text) else "")


def _dedup(ranked, chunks, texts, query, top_k, max_per_pdf=2):
    seen: dict[str, int] = {}
    results = []
    for idx, score in ranked:
        chunk = chunks[idx]
        pdf = chunk["pdf_name"]
        if seen.get(pdf, 0) < max_per_pdf:
            seen[pdf] = seen.get(pdf, 0) + 1
            results.append({
                "rank": len(results) + 1,
                "score": round(score, 4),
                "title": chunk["title"],
                "authors": chunk["authors"],
                "year": chunk["year"],
                "pdf_name": chunk["pdf_name"],
                "page": chunk["page_num"],
                "cite_key": chunk["cite_key"],
                "snippet": _snippet(texts[idx], query),
            })
        if len(results) >= top_k:
            break
    return results


# ── search modes ─────────────────────────────────────────────────────────────

def search_fulltext(query: str, mode: str = "hybrid", top_k: int = 5) -> list[dict]:
    bm25, tfidf_vec, matrix, chunks, texts = _load_fulltext()

    bm25_ranking = tfidf_ranking = None
    bm25_scores = cosine_scores = None

    if mode in ("bm25", "hybrid"):
        tokens = query.lower().split()
        bm25_scores = bm25.get_scores(tokens)
        bm25_ranking = list(np.argsort(bm25_scores)[::-1])

    if mode in ("tfidf", "hybrid"):
        qvec = tfidf_vec.transform([query]).toarray()[0]
        qnorm = np.linalg.norm(qvec)
        if qnorm > 0:
            qvec = qvec / qnorm
        row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        row_norms[row_norms == 0] = 1.0
        cosine_scores = (matrix / row_norms) @ qvec
        tfidf_ranking = list(np.argsort(cosine_scores)[::-1])

    if mode == "bm25":
        ranked = [(i, float(bm25_scores[i])) for i in bm25_ranking[:top_k * 3]]
    elif mode == "tfidf":
        ranked = [(i, float(cosine_scores[i])) for i in tfidf_ranking[:top_k * 3]]
    else:
        ranked = _rrf([bm25_ranking, tfidf_ranking])

    return _dedup(ranked, chunks, texts, query, top_k)


def search_metadata(query: str, top_k: int = 5) -> list[dict]:
    if not config.DB_PATH.exists():
        return [{"error": f"metadata DB not found at {config.DB_PATH}"}]

    # Copy to temp to avoid locking issues
    tmp = Path(tempfile.mktemp(suffix=".sqlite"))
    shutil.copy2(config.DB_PATH, tmp)
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row

    rows = []
    # 1. FTS
    try:
        rows = conn.execute("""
            SELECT p.*, GROUP_CONCAT(a.given || ' ' || a.family, '; ') AS author_list
            FROM papers p LEFT JOIN authors a ON a.paper_id = p.id
            WHERE p.id IN (SELECT rowid FROM papers_fts WHERE papers_fts MATCH ?)
            GROUP BY p.id ORDER BY p.year DESC LIMIT ?
        """, (query, top_k)).fetchall()
    except Exception:
        pass

    # 2. Author name
    author_rows = conn.execute("""
        SELECT DISTINCT p.*, GROUP_CONCAT(a2.given || ' ' || a2.family, '; ') AS author_list
        FROM papers p JOIN authors a ON a.paper_id = p.id
        LEFT JOIN authors a2 ON a2.paper_id = p.id
        WHERE a.family LIKE ? OR a.given LIKE ?
        GROUP BY p.id ORDER BY p.year DESC LIMIT ?
    """, (f"%{query}%", f"%{query}%", top_k)).fetchall()

    seen_keys: set = set()
    merged = []
    for row in list(author_rows) + list(rows):
        key = row["cite_key"]
        if key not in seen_keys:
            seen_keys.add(key)
            merged.append(row)

    # 3. Broad LIKE fallback
    if not merged:
        merged = conn.execute("""
            SELECT p.*, GROUP_CONCAT(a.given || ' ' || a.family, '; ') AS author_list
            FROM papers p LEFT JOIN authors a ON a.paper_id = p.id
            WHERE p.title LIKE ? OR p.abstract LIKE ? OR p.keywords LIKE ?
               OR p.institution LIKE ? OR p.publisher LIKE ?
            GROUP BY p.id ORDER BY p.year DESC LIMIT ?
        """, (f"%{query}%",) * 5 + (top_k,)).fetchall()

    conn.close()
    try:
        tmp.unlink()
    except Exception:
        pass

    results = []
    for i, row in enumerate(merged[:top_k]):
        results.append({
            "rank": i + 1,
            "title": row["title"],
            "authors": row["author_list"] or "",
            "year": row["year"],
            "institution": row["institution"] or row["publisher"] or "",
            "doc_type": row["doc_type"] or row["entry_type"] or "",
            "keywords": row["keywords"] or "",
            "abstract": (row["abstract"] or "")[:400],
            "cite_key": row["cite_key"],
            "pdf_name": row["pdf_filename"],
            "pdf_path": row["pdf_path"],
        })
    return results


def search_semantic(query: str, top_k: int = 5) -> list[dict]:
    """Vector similarity search via LanceDB + Ollama embeddings."""
    import requests

    tbl = _load_lancedb()
    if tbl is None:
        return [{"error": "LanceDB vector index not built yet. Run fz-ingest --vectors"}]

    # Embed the query
    resp = requests.post(
        config.OLLAMA_URL,
        json={"model": config.EMBED_MODEL, "input": [query]},
        timeout=30,
    )
    resp.raise_for_status()
    qvec = resp.json()["embeddings"][0]

    rows = tbl.search(qvec).limit(top_k * 2).to_list()

    seen: dict[str, int] = {}
    results = []
    for row in rows:
        pdf = row["pdf_name"]
        if seen.get(pdf, 0) < 2:
            seen[pdf] = seen.get(pdf, 0) + 1
            results.append({
                "rank": len(results) + 1,
                "score": round(float(row.get("_distance", 0)), 4),
                "title": row["title"],
                "authors": row["authors"],
                "year": row["year"],
                "pdf_name": row["pdf_name"],
                "page": row["page_num"],
                "cite_key": row["cite_key"],
                "snippet": row["text"][:300],
            })
        if len(results) >= top_k:
            break
    return results


# ── unified entry point ──────────────────────────────────────────────────────

def search(query: str, mode: str = "hybrid", top_k: int = 5) -> dict:
    """
    Search the paper library.

    Modes: bm25, tfidf, hybrid, metadata, semantic
    """
    if mode == "metadata":
        results = search_metadata(query, top_k)
    elif mode == "semantic":
        results = search_semantic(query, top_k)
    else:
        results = search_fulltext(query, mode, top_k)

    return {"query": query, "mode": mode, "n": len(results), "results": results}
