"""
MCP server exposing paper search tools.

Run standalone:
    python -m fuzzy_spaghetti.mcp_server

Or via Claude Code settings (stdio transport):
    "mcpServers": {
        "papers": {
            "command": "python",
            "args": ["-m", "fuzzy_spaghetti.mcp_server"],
            "env": {
                "FUZZY_PAPERS_ROOT": "~/PycharmProjects/Papers"
            }
        }
    }
"""

import json
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "papers",
    instructions=(
        "Search a personal research paper library. "
        "Use 'search_papers' for keyword/conceptual queries, "
        "'lookup_paper' for author/title/metadata lookups, "
        "and 'semantic_search' for meaning-based queries via embeddings."
    ),
)


@mcp.tool()
def search_papers(
    query: str,
    mode: str = "hybrid",
    top_k: int = 5,
) -> str:
    """Search the paper library using keyword-based methods.

    Args:
        query: Search query (e.g. "OIS discounting", "walk volatility swaption")
        mode: Search mode — "hybrid" (BM25+TF-IDF, default), "bm25" (exact terms), "tfidf" (conceptual)
        top_k: Number of results to return (default 5)

    Returns:
        JSON with ranked results including title, authors, year, page, snippet.
    """
    from .search import search
    result = search(query, mode=mode, top_k=top_k)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def lookup_paper(query: str, top_k: int = 5) -> str:
    """Look up papers by author name, title fragment, year, or institution.

    Best for: "papers by Mercurio", "SABR calibration", "2005 Merrill Lynch".

    Args:
        query: Author name, title fragment, year, institution, or keyword.
        top_k: Number of results (default 5).

    Returns:
        JSON with paper metadata: title, authors, year, abstract, keywords, cite_key.
    """
    from .search import search
    result = search(query, mode="metadata", top_k=top_k)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def semantic_search(query: str, top_k: int = 5) -> str:
    """Semantic similarity search using vector embeddings (requires Ollama running).

    Best for conceptual queries like "how does convexity affect swap pricing"
    where exact keyword matching may miss relevant passages.

    Args:
        query: Natural language question or concept description.
        top_k: Number of results (default 5).

    Returns:
        JSON with ranked results including title, authors, page, and text snippet.
    """
    from .search import search
    result = search(query, mode="semantic", top_k=top_k)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def library_stats() -> str:
    """Get summary statistics about the indexed paper library.

    Returns:
        JSON with paper count, chunk count, topic breakdown, index status.
    """
    import sqlite3
    from pathlib import Path
    from . import config

    stats = {
        "papers_root": str(config.PAPERS_ROOT),
        "index_dir": str(config.INDEX_DIR),
        "indices": {
            "metadata_db": config.DB_PATH.exists(),
            "bm25": config.BM25_PATH.exists(),
            "tfidf": config.TFIDF_PATH.exists(),
            "chunks": config.CHUNKS_PATH.exists(),
            "vectors": config.VECTORS_DIR.exists(),
        },
    }

    if config.DB_PATH.exists():
        conn = sqlite3.connect(config.DB_PATH)
        stats["total_papers"] = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        stats["total_authors"] = conn.execute("SELECT COUNT(DISTINCT family || given) FROM authors").fetchone()[0]
        topics = conn.execute(
            "SELECT topic, COUNT(*) as n FROM papers GROUP BY topic ORDER BY n DESC"
        ).fetchall()
        stats["topics"] = {t[0]: t[1] for t in topics}
        conn.close()

    if config.CHUNKS_PATH.exists():
        with open(config.CHUNKS_PATH) as f:
            data = json.load(f)
        stats["total_chunks"] = len(data["chunks"])

    return json.dumps(stats, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
