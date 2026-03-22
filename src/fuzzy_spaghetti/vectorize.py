"""
Build LanceDB dense vector index using Ollama embeddings.

Usage:
    from fuzzy_spaghetti.vectorize import build_vector_index
    build_vector_index()
"""

import json
import time

import requests

from . import config


def build_vector_index(
    index_dir=None,
    ollama_url=None,
    model=None,
    batch_size: int = 64,
):
    """Embed all chunks via Ollama and store in LanceDB."""
    import lancedb
    import pyarrow as pa

    index_dir = index_dir or config.INDEX_DIR
    ollama_url = ollama_url or config.OLLAMA_URL
    model = model or config.EMBED_MODEL
    dim = config.EMBED_DIM
    vectors_dir = index_dir / "vectors"
    chunks_path = index_dir / "chunks.json"

    print(f"Loading chunks from {chunks_path}")
    with open(chunks_path) as f:
        data = json.load(f)
    chunks = data["chunks"]
    texts = data["texts"]
    assert len(chunks) == len(texts), "chunk/text mismatch"
    print(f"  {len(chunks)} chunks loaded")

    # Clean texts: Ollama rejects empty strings; truncate very long ones
    MAX_CHARS = 8000
    texts = [t[:MAX_CHARS] if t.strip() else "(empty page)" for t in texts]

    # Embed
    def embed_batch(batch_texts):
        r = requests.post(
            ollama_url,
            json={"model": model, "input": batch_texts},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["embeddings"]

    print(f"Embedding {len(texts)} chunks with {model} (batch={batch_size})...")
    all_embeddings = []
    start = time.time()
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            embs = embed_batch(batch)
        except requests.HTTPError:
            # Fall back to one-at-a-time for this batch
            embs = []
            for t in batch:
                try:
                    embs.extend(embed_batch([t]))
                except requests.HTTPError:
                    embs.append([0.0] * dim)  # zero vector for bad chunks
        all_embeddings.extend(embs)
        done = len(all_embeddings)
        elapsed = time.time() - start
        eta = (elapsed / done) * (len(texts) - done) if done else 0
        print(f"  {done}/{len(texts)}  elapsed={elapsed:.0f}s  ETA={eta:.0f}s")

    assert len(all_embeddings) == len(chunks), "embedding count mismatch"

    # Build LanceDB
    vectors_dir.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(vectors_dir))

    schema = pa.schema([
        pa.field("vector", pa.list_(pa.float32(), dim)),
        pa.field("text", pa.string()),
        pa.field("pdf_name", pa.string()),
        pa.field("pdf_path", pa.string()),
        pa.field("page_num", pa.int32()),
        pa.field("chunk_idx", pa.int32()),
        pa.field("cite_key", pa.string()),
        pa.field("title", pa.string()),
        pa.field("authors", pa.string()),
        pa.field("year", pa.int32()),
        pa.field("topic", pa.string()),
    ])

    TABLE = "papers"
    if TABLE in db.table_names():
        db.drop_table(TABLE)

    rows = []
    for chunk, emb, text in zip(chunks, all_embeddings, texts):
        rows.append({
            "vector": [float(x) for x in emb],
            "text": text,
            "pdf_name": chunk["pdf_name"],
            "pdf_path": chunk["pdf_path"],
            "page_num": int(chunk["page_num"]),
            "chunk_idx": int(chunk.get("chunk_idx", 0)),
            "cite_key": chunk["cite_key"],
            "title": chunk["title"],
            "authors": chunk["authors"],
            "year": int(chunk["year"]) if chunk["year"] else 0,
            "topic": chunk["topic"],
        })

    print(f"Writing {len(rows)} rows to LanceDB...")
    tbl = db.create_table(TABLE, data=rows, schema=schema)
    try:
        tbl.create_fts_index("text", replace=True)
    except Exception as e:
        print(f"  FTS index creation skipped: {e}")
    print(f"LanceDB table '{TABLE}': {tbl.count_rows()} rows")
    print(f"Saved to: {vectors_dir}")
    return {"rows": tbl.count_rows(), "path": str(vectors_dir)}
