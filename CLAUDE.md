# fuzzy-spaghetti

Full-text search tooling over a personal research paper library (quant finance PDFs).

## Quick Start

```bash
pip install -e ".[mcp]"

# Ingest all papers (metadata DB + BM25/TF-IDF)
fz-ingest

# Also build vector index (requires Ollama running with nomic-embed-text)
fz-ingest --vectors

# Search
fz-search "OIS discounting" -m hybrid -k 5
fz-search "Henrard" -m metadata
fz-search "how does convexity affect pricing" -m semantic
```

## Architecture

```
Papers/                          # PDF library (iCloud/local)
├── Interest_Rates/              # Topic folders with PDFs + .bib files
├── Vol_Surface_and_SABR/
└── .search_index/               # Generated indices
    ├── library.sqlite           # Metadata DB (papers + authors + FTS)
    ├── bm25.pkl                 # BM25 sparse index
    ├── tfidf.pkl + .npy         # TF-IDF vectorizer + matrix
    ├── chunks.json              # Chunk metadata + full texts
    └── vectors/                 # LanceDB dense vector index
```

## Search Modes

| Mode | Best for | Backing |
|------|----------|---------|
| `hybrid` | General queries (default) | BM25 + TF-IDF reciprocal rank fusion |
| `bm25` | Exact quant terms ("SOFR futures") | BM25Okapi |
| `tfidf` | Conceptual/thematic queries | TF-IDF cosine similarity |
| `metadata` | Author/title/institution lookup | SQLite FTS5 |
| `semantic` | Meaning-based ("how does X work") | LanceDB + Ollama nomic-embed-text |

## MCP Server

Exposes `search_papers`, `lookup_paper`, `semantic_search`, `library_stats` tools.
Configure in `.mcp.json`:

```json
{
  "mcpServers": {
    "papers": {
      "command": "python3",
      "args": ["-m", "fuzzy_spaghetti.mcp_server"],
      "env": { "FUZZY_PAPERS_ROOT": "/path/to/Papers" }
    }
  }
}
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `FUZZY_PAPERS_ROOT` | `~/PycharmProjects/Papers` | Root of the PDF library |
| `FUZZY_INDEX_DIR` | `$PAPERS_ROOT/.search_index` | Where indices are stored |
| `FUZZY_OLLAMA_URL` | `http://localhost:11434/api/embed` | Ollama embedding endpoint |
| `FUZZY_EMBED_MODEL` | `nomic-embed-text` | Embedding model name |

## Code Conventions

- Config via env vars (see `config.py`), no hardcoded paths
- Search modes are independent: metadata/BM25/TF-IDF work without Ollama
- Vector search requires Ollama running locally
- All search functions return JSON-serializable dicts
