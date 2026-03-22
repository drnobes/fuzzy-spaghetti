"""Paths and configuration — all overridable via environment variables."""

import os
from pathlib import Path

# Root of the papers library
PAPERS_ROOT = Path(os.environ.get(
    "FUZZY_PAPERS_ROOT",
    os.path.expanduser("~/PycharmProjects/Papers"),
))

# Where indices live (inside the papers tree by default)
INDEX_DIR = Path(os.environ.get(
    "FUZZY_INDEX_DIR",
    str(PAPERS_ROOT / ".search_index"),
))

# Ollama endpoint for embeddings
OLLAMA_URL = os.environ.get("FUZZY_OLLAMA_URL", "http://localhost:11434/api/embed")
EMBED_MODEL = os.environ.get("FUZZY_EMBED_MODEL", "nomic-embed-text")
EMBED_DIM = int(os.environ.get("FUZZY_EMBED_DIM", "768"))

# Derived paths
DB_PATH = INDEX_DIR / "library.sqlite"
BM25_PATH = INDEX_DIR / "bm25.pkl"
TFIDF_PATH = INDEX_DIR / "tfidf.pkl"
TFIDF_MATRIX_PATH = INDEX_DIR / "tfidf_matrix.npy"
CHUNKS_PATH = INDEX_DIR / "chunks.json"
VECTORS_DIR = INDEX_DIR / "vectors"
