"""MCP Server — arXiv Search Tool (Project 12)

Project 12 replaces the direct arxiv-library calls inside ResearchDigestService
with this MCP stdio server.  The server exposes one tool:

    search_arxiv(query, max_results, start) -> {"papers": [...]}

Field contract (matches ResearchDigestService._search_arxiv expectations):
  id          – full arXiv URL  (e.g. https://arxiv.org/abs/2301.12345)
  title       – paper title (stripped)
  authors     – list[str], up to 4 names
  summary     – abstract text, up to 700 chars
  published   – "YYYY-MM-DD"
  categories  – list[str], up to 3 categories

What did NOT change (Project 12 guarantee)
------------------------------------------
* stream_digest() logic and all SSE event shapes  → byte-for-byte identical
* /agents/research-digest/stream API router       → byte-for-byte identical
* All frontend code                               → byte-for-byte identical
* The LLM synthesis system prompt                 → byte-for-byte identical

Only _search_arxiv() in research_digest_service.py changed: it now calls this
MCP server over stdio instead of importing arxiv directly.
"""

from __future__ import annotations

import arxiv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arxiv-search")


@mcp.tool()
def search_arxiv(query: str, max_results: int = 6, start: int = 0) -> dict:
    """Search arXiv for papers matching *query*.

    Returns {"papers": [...]} where each paper has:
      id (full arXiv URL), title, authors (up to 4), summary (≤700 chars),
      published (YYYY-MM-DD), categories (up to 3).

    query:       arXiv search string (same syntax as arxiv.org search).
    max_results: number of papers to return after skipping *start* results.
    start:       zero-based offset — skip this many results before collecting.
    """
    fetch_total = start + max_results
    client = arxiv.Client(page_size=min(fetch_total, 25), num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=fetch_total,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending,
    )
    all_papers: list[dict] = []
    for r in client.results(search):
        all_papers.append({
            "id": r.entry_id,                      # full URL — matches service field
            "title": r.title.strip(),
            "authors": [a.name for a in r.authors[:4]],
            "summary": r.summary.strip()[:700],    # "summary" not "abstract"
            "published": r.published.strftime("%Y-%m-%d"),
            "categories": list(r.categories[:3]),
        })
    return {"papers": all_papers[start:]}          # apply start-offset slice


if __name__ == "__main__":
    # Invoked as a subprocess by research_digest_service.py over stdio.
    mcp.run()
