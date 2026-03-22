# fuzzy-spaghetti usage guide

## How the MCP server works

The `.mcp.json` file tells Claude Code: "when this conversation starts, launch `python3 -m fuzzy_spaghetti.mcp_server` and keep it running as a subprocess." That subprocess speaks MCP (Model Context Protocol) over stdio — Claude sends JSON-RPC requests in, the server sends results back out.

It registers 4 **tools** that Claude can call, just like it calls `Read` or `Bash`:
- `search_papers` — keyword search (BM25/TF-IDF)
- `lookup_paper` — author/title/metadata SQL search
- `semantic_search` — vector similarity via Ollama embeddings
- `library_stats` — what's indexed

When Claude decides it needs to find a paper, it calls one of these tools instead of grepping through PDFs manually. The tool runs the search locally and returns JSON results.

The MCP server is **not a daemon** — it doesn't run persistently. Claude Code spawns it as a child process when a conversation starts and kills it when the conversation ends. Nothing to manage, nothing to restart after a reboot.

## Claude Code / Cowork integration

**Claude Code (terminal)**: Reads `.mcp.json` from the working directory. If you `cd ~/PycharmProjects/redesigned-train` and run `claude`, it picks up the papers server automatically. You'll see it listed when you do `/mcp`.

**Cowork**: Same — if the cowork session is rooted in a directory with `.mcp.json`, it picks it up.

**Any project**: Drop a `.mcp.json` in that project's root directory with:

```json
{
  "mcpServers": {
    "papers": {
      "command": "python3",
      "args": ["-m", "fuzzy_spaghetti.mcp_server"],
      "env": {
        "FUZZY_PAPERS_ROOT": "/Users/mnobes/PycharmProjects/Papers"
      }
    }
  }
}
```

**Regular Claude (claude.ai web)**: No MCP support — Claude Code feature only.

## Full example

Start an Opus session in redesigned-train and say:

> "Find the paper that implements walk vol, read it and implement the walk vol algorithm"

Claude will:
1. See the `papers` MCP server is available
2. Call `search_papers(query="walk volatility", mode="hybrid")` — gets back results showing "Measuring Interest Rate Volatility" by Rod Knowles, page numbers, snippets
3. Call `lookup_paper(query="Knowles walk volatility")` for full metadata
4. Use the `pdf_path` from the result to `Read` the actual PDF
5. Implement the algorithm from what it reads

You don't need to do anything special — just ask naturally. Claude sees the MCP tools in its tool list and uses them when relevant.

## Syncing the database to cloud storage

The indices live at `~/PycharmProjects/Papers/.search_index/` (~50MB total: SQLite + pickles + LanceDB). To sync across devices:

**Simplest**: Point `FUZZY_PAPERS_ROOT` at the iCloud Papers directory. Then the indices build inside iCloud and sync automatically. Change `config.py`'s default or set the env var, then re-run `fz-ingest --vectors`.

LanceDB is file-based specifically for this reason — no server process, just files on disk. iCloud/Google Drive handle the ~50MB index fine.

From a phone, you wouldn't run searches directly, but you could build a Shortcuts workflow or simple web interface that hits the MCP server on the Mac via Tailscale/SSH tunnel.

## Local LLM options

The structured SQLite DB with FTS5 is the key — you don't even need an LLM for most retrieval.

**Direct SQL**: The cheapest option. `granite4:3b` or `ministral-3:3b` (both already pulled locally) can generate SQL queries against `library.sqlite`. The schema is simple — `papers` table with FTS5 on title/abstract/keywords.

**Function calling**: Both 3B models support tool use. You could write a tiny Ollama-based agent that calls the same `search()` function the MCP server uses. No embedding needed — just BM25/hybrid mode.

**For semantic search specifically**: That's where the vector index helps, but the 3B models are too small to be the query planner *and* the embedder. The embedding is handled separately by `nomic-embed-text` (see below).

Bottom line: a 3B model + the SQLite FTS5 index is genuinely good enough for retrieval. The hybrid BM25/TF-IDF search doesn't need any LLM at all — it's pure algorithm.

## What nomic-embed-text does

`nomic-embed-text` is **not a chat model** — it's an **embedding model**. It converts text into 768-dimensional vectors (arrays of floats). It doesn't generate text, it doesn't answer questions.

What it does: takes a passage like "The convexity adjustment for CMS swaps under SABR..." and produces a vector `[0.023, -0.187, 0.041, ...]`. Similar concepts produce similar vectors. So when you search "how does convexity affect swap pricing", it embeds your query into the same vector space and finds the closest passages by cosine distance.

This is the **semantic search** mode — it catches conceptual matches that keyword search misses. "How does the term structure evolve?" would find passages about "yield curve dynamics" even though the words don't overlap.

The `ministral-3:3b` and `granite4:3b` models on this machine are **chat models** — different purpose. `nomic-embed-text` (274MB) is tiny and fast because embedding is a much simpler task than generation.
