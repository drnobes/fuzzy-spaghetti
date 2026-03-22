"""CLI entry points for fuzzy-spaghetti."""

import argparse
import json
import sys


def ingest_main():
    parser = argparse.ArgumentParser(description="Ingest papers into search indices")
    parser.add_argument("--papers-root", default=None, help="Override PAPERS_ROOT")
    parser.add_argument("--index-dir", default=None, help="Override INDEX_DIR")
    parser.add_argument("--metadata-only", action="store_true", help="Only build metadata DB")
    parser.add_argument("--search-only", action="store_true", help="Only build BM25/TF-IDF")
    parser.add_argument("--vectors", action="store_true", help="Also build LanceDB vector index")
    args = parser.parse_args()

    from pathlib import Path
    from . import config
    from .ingest import build_metadata_db, build_search_index

    papers_root = Path(args.papers_root) if args.papers_root else config.PAPERS_ROOT
    index_dir = Path(args.index_dir) if args.index_dir else config.INDEX_DIR

    if not args.search_only:
        print("=== Building metadata DB ===")
        db_path = build_metadata_db(papers_root, index_dir)

    if not args.metadata_only:
        print("\n=== Building search index ===")
        build_search_index(papers_root, index_dir, index_dir / "library.sqlite")

    if args.vectors:
        print("\n=== Building vector index ===")
        from .vectorize import build_vector_index
        build_vector_index(index_dir)

    print("\nDone.")


def search_main():
    parser = argparse.ArgumentParser(description="Search the paper library")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--query", "-q", dest="query_flag", help="Search query (alt)")
    parser.add_argument("--mode", "-m", default="hybrid",
                        choices=["bm25", "tfidf", "hybrid", "metadata", "semantic"])
    parser.add_argument("--top-k", "-k", type=int, default=5)
    args = parser.parse_args()

    query = args.query or args.query_flag
    if not query:
        parser.error("query is required")

    from .search import search
    result = search(query, mode=args.mode, top_k=args.top_k)
    print(json.dumps(result, indent=2, ensure_ascii=False))
