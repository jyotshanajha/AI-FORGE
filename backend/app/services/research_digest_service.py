from collections.abc import AsyncGenerator
import json
import logging
import sys
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.ai.llm import llm

# Path to the MCP server script — resolved once at import time
_MCP_SERVER_SCRIPT = str(
    Path(__file__).resolve().parent.parent.parent / "mcp_server" / "arxiv_tools.py"
)


MAX_AUTONOMOUS_ROUNDS = 6
MAX_QUERY_VARIANTS = 6
MAX_EVIDENCE_SAMPLE = 12
DEFAULT_QUERY_VARIANTS = 4

logger = logging.getLogger(__name__)


class ResearchDigestService:
    @staticmethod
    def _clamp_confidence(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric))

    @staticmethod
    def _fallback_confidence(current: int, target: int) -> float:
        if target <= 0:
            return 0.0
        return max(0.15, min(0.98, current / target))

    @staticmethod
    async def _search_arxiv(
        query: str,
        max_results: int,
        start: int = 0,
        *,
        mcp_session: ClientSession,
    ) -> list[dict[str, object]]:
        """
        Search arXiv by calling the MCP server tool `search_arxiv` over stdio.
        The arxiv library is no longer imported directly here — all paper
        retrieval goes through the MCP protocol (Project 12).
        """
        try:
            result = await mcp_session.call_tool(
                "search_arxiv",
                {"query": query, "max_results": max_results, "start": start},
            )
            # MCP returns a list of Content objects; the tool returns JSON
            # embedded as text in the first TextContent item.
            raw_text = ""
            for item in result.content:
                if hasattr(item, "text"):
                    raw_text = item.text
                    break
            if not raw_text:
                logger.warning("MCP search_arxiv returned empty content for '%s'", query)
                return []
            data = json.loads(raw_text)
            return list(data.get("papers", []))
        except Exception as exc:
            logger.warning("MCP arXiv search failed for '%s': %s", query, exc)
            return []

    @staticmethod
    def _default_variants(query: str) -> list[str]:
        return [
            query,
            f"{query} survey",
            f"{query} recent advances",
            f"{query} benchmark evaluation",
        ]

    @staticmethod
    async def _build_query_variants(query: str, user_email: str) -> list[str]:
        defaults = ResearchDigestService._default_variants(query)
        if llm is None:
            return defaults[:MAX_QUERY_VARIANTS]

        system_prompt = (
            "You are a research planner. Generate diverse arXiv search queries that maximize recall and relevance. "
            "Return strict JSON only with key 'queries' as a list of short strings."
        )
        user_prompt = (
            f"Topic: {query}\n"
            f"Return 4 to {MAX_QUERY_VARIANTS} compact arXiv queries with varied framing "
            f"(survey, methods, applications, evaluation)."
        )

        try:
            response = await llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
                config={"metadata": {"user_email": user_email}},
            )
            content = response.content if hasattr(response, "content") else str(response)
            parsed = ResearchDigestService._parse_json_payload(str(content))
            raw_queries = parsed.get("queries", [])
            variants: list[str] = []
            if isinstance(raw_queries, list):
                for item in raw_queries:
                    candidate = str(item).strip()
                    if len(candidate) >= 3 and candidate not in variants:
                        variants.append(candidate)

            if query not in variants:
                variants.insert(0, query)
            return variants[:MAX_QUERY_VARIANTS] if variants else defaults[:MAX_QUERY_VARIANTS]
        except Exception as exc:
            logger.warning("Query variant planning failed, using defaults: %s", exc)
            return defaults[:MAX_QUERY_VARIANTS]

    @staticmethod
    async def _has_enough_evidence(
        query: str,
        papers: list[dict[str, object]],
        target: int,
        user_email: str,
    ) -> tuple[bool, str, float]:
        # If the LLM is unavailable, use a simple deterministic fallback threshold.
        if llm is None:
            enough = len(papers) >= target
            reason = (
                f"Collected {len(papers)} papers which meets target {target}."
                if enough
                else f"Collected {len(papers)} papers; continuing until target {target}."
            )
            return enough, reason, ResearchDigestService._fallback_confidence(len(papers), target)

        compact_evidence: list[dict[str, str]] = []
        for paper in papers[:MAX_EVIDENCE_SAMPLE]:
            compact_evidence.append(
                {
                    "title": str(paper.get("title", "")),
                    "published": str(paper.get("published", "")),
                    "summary": str(paper.get("summary", ""))[:280],
                }
            )

        system_prompt = (
            "You decide whether enough evidence has been gathered to write a useful research digest. "
            "Return strict JSON only with keys: enough_evidence (boolean), reason (string), confidence (0-1 number)."
        )
        user_prompt = (
            f"Topic: {query}\n"
            f"Target papers: {target}\n"
            f"Current unique papers: {len(papers)}\n"
            f"Evidence sample: {json.dumps(compact_evidence, ensure_ascii=True)}"
        )

        try:
            response = await llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
                config={"metadata": {"user_email": user_email}},
            )
            content = response.content if hasattr(response, "content") else str(response)
            parsed = ResearchDigestService._parse_json_payload(str(content))
            enough = bool(parsed.get("enough_evidence", False))
            reason = str(parsed.get("reason", "No reason provided")).strip() or "No reason provided"
            confidence = ResearchDigestService._clamp_confidence(parsed.get("confidence", 0.0))
            return enough, reason, confidence
        except Exception as exc:
            logger.warning("Evidence decision fallback due to model output issue: %s", exc)
            # Fall back gracefully when model output is malformed.
            enough = len(papers) >= target
            reason = (
                f"Fallback threshold met with {len(papers)} papers."
                if enough
                else f"Fallback threshold not met ({len(papers)}/{target})."
            )
            return enough, reason, ResearchDigestService._fallback_confidence(len(papers), target)

    @staticmethod
    def _parse_json_payload(content: str) -> dict[str, object]:
        candidate = content.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            candidate = candidate.replace("json", "", 1).strip()

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return {}
            try:
                parsed = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                return {}

        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _source_preview(papers: list[dict[str, object]]) -> list[dict[str, object]]:
        preview: list[dict[str, object]] = []
        for paper in papers[:10]:
            preview.append(
                {
                    "title": str(paper.get("title", "")),
                    "id": str(paper.get("id", "")),
                    "published": str(paper.get("published", "")),
                    "authors": list(paper.get("authors", []))[:4],
                }
            )
        return preview

    @staticmethod
    def _fallback_digest(query: str, papers: list[dict[str, object]]) -> str:
        lines = [
            f"# Research Digest: {query}",
            "",
            "## Evidence Coverage",
            f"- Papers analyzed: {len(papers)}",
            "",
            "## Key Papers",
        ]
        for idx, paper in enumerate(papers[:8], start=1):
            url = str(paper.get("id", ""))
            title = str(paper.get("title", ""))
            published = str(paper.get("published", ""))
            if url:
                lines.append(f"{idx}. [{title}]({url}) ({published})")
            else:
                lines.append(f"{idx}. {title} ({published})")

        lines.extend(
            [
                "",
                "## Takeaways",
                "- This digest is generated without advanced synthesis because the LLM is unavailable.",
                "- The paper list above can still be used as a curated starting point.",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    async def stream_digest(
        query: str,
        max_papers: int,
        user_email: str,
        max_rounds: int = MAX_AUTONOMOUS_ROUNDS,
        papers_per_round: int = 5,
    ) -> AsyncGenerator[dict[str, object], None]:
        """
        Fully real-time streaming agent:
        - Immediately yields each planning/search/decision step as it happens.
        - Never buffers and batch-releases events.
        - Streams the LLM synthesis token-by-token.

        Project 12 change: arXiv searches are now routed through the MCP
        stdio server (mcp_server/arxiv_tools.py).  A single MCP session is
        opened for the lifetime of this request and reused across all rounds.
        The agent logic, SSE event shapes, API router, and all frontend code
        are byte-for-byte identical to Project 10.
        """
        yield {"type": "status", "message": "Starting autonomous arXiv search..."}

        # ── Open MCP session — one subprocess per stream_digest invocation ──
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[_MCP_SERVER_SCRIPT],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()
                async for event in ResearchDigestService._run_digest(
                    query=query,
                    max_papers=max_papers,
                    user_email=user_email,
                    max_rounds=max_rounds,
                    papers_per_round=papers_per_round,
                    mcp_session=mcp_session,
                ):
                    yield event

    @staticmethod
    async def _run_digest(
        query: str,
        max_papers: int,
        user_email: str,
        max_rounds: int,
        papers_per_round: int,
        mcp_session: ClientSession,
    ) -> AsyncGenerator[dict[str, object], None]:
        """Inner generator — identical to the Project 10 agent loop.
        Extracted so that stream_digest can own the MCP session context."""
        # ── Step 1: Plan query variants (stream status immediately, then do LLM call) ──
        yield {"type": "status", "message": "Planning query variants with AI..."}
        try:
            variants = await ResearchDigestService._build_query_variants(query, user_email)
        except Exception as exc:
            logger.exception("Failed to plan query variants: %s", exc)
            variants = ResearchDigestService._default_variants(query)

        yield {
            "type": "status",
            "message": f"Using {len(variants)} search variants: {' | '.join(variants)}",
        }

        # ── Step 2: Iterative evidence collection — yield each event immediately ──
        seen: set[str] = set()
        collected: list[dict[str, object]] = []
        page_size = max(2, min(15, papers_per_round))
        rounds_executed = 0
        stop_early = False

        for round_idx in range(max_rounds):
            rounds_executed = round_idx + 1
            variant = variants[round_idx % len(variants)]
            page = round_idx // len(variants)
            start_offset = page * page_size

            yield {
                "type": "status",
                "message": f"[Round {round_idx + 1}/{max_rounds}] Searching arXiv via MCP for: '{variant}'...",
            }

            try:
                found = await ResearchDigestService._search_arxiv(
                    variant,
                    max_results=page_size,
                    start=start_offset,
                    mcp_session=mcp_session,
                )
            except Exception as exc:
                logger.warning("arXiv search failed for variant '%s': %s", variant, exc)
                yield {"type": "status", "message": f"  Search failed for '{variant}', skipping."}
                continue

            new_count = 0
            for paper in found:
                paper_id = str(paper.get("id", ""))
                if not paper_id or paper_id in seen:
                    continue
                seen.add(paper_id)
                collected.append(paper)
                new_count += 1

            yield {
                "type": "status",
                "message": (
                    f"  Fetched {len(found)} results, added {new_count} new papers "
                    f"(total: {len(collected)})"
                ),
            }

            # ── Evidence decision — stream result immediately ──
            yield {"type": "status", "message": "  Evaluating evidence sufficiency..."}
            try:
                enough, reason, confidence = await ResearchDigestService._has_enough_evidence(
                    query=query,
                    papers=collected,
                    target=max_papers,
                    user_email=user_email,
                )
            except Exception as exc:
                logger.warning("Evidence decision failed: %s", exc)
                enough = len(collected) >= max_papers
                reason = f"Fallback: {len(collected)}/{max_papers} papers collected."
                confidence = ResearchDigestService._fallback_confidence(len(collected), max_papers)

            yield {
                "type": "evidence_decision",
                "enough_evidence": enough,
                "confidence": confidence,
                "reason": reason,
                "papers_considered": len(collected),
            }

            if enough and len(collected) >= 3:
                stop_early = True
                break

        final_papers = collected[:max_papers]

        if not final_papers:
            yield {"type": "error", "message": "No relevant arXiv papers were found for this query."}
            return

        stop_msg = "Sufficient evidence collected." if stop_early else f"Completed {rounds_executed} search rounds."
        yield {"type": "status", "message": stop_msg}

        # ── Step 3: Emit metadata and source list ──
        yield {
            "type": "meta",
            "papers_found": len(final_papers),
            "query": query,
            "rounds_executed": rounds_executed,
            "query_variants": variants,
        }
        yield {"type": "sources", "papers": ResearchDigestService._source_preview(final_papers)}

        # ── Step 4: LLM synthesis (stream tokens as they arrive) ──
        if llm is None:
            yield {"type": "status", "message": "LLM unavailable — producing fallback digest."}
            fallback = ResearchDigestService._fallback_digest(query, final_papers)
            for token in fallback.splitlines(keepends=True):
                yield {"type": "token", "token": token}
            return

        paper_context_lines: list[str] = []
        for idx, paper in enumerate(final_papers, start=1):
            authors = ", ".join(list(paper["authors"])[:4]) or "Unknown authors"
            summary = str(paper["summary"])[:800]
            url = str(paper.get("id", ""))
            # Do NOT include [N] numbering in context to prevent citation-style output.
            paper_context_lines.append(
                f"Title: {paper['title']}\n"
                f"arXiv URL: {url}\n"
                f"Published: {paper['published']}\n"
                f"Authors: {authors}\n"
                f"Abstract: {summary}"
            )

        system_prompt = (
            "You are a research digest agent. Produce a structured digest in markdown with these sections: "
            "Overview, Key Findings, Paper-by-Paper Notes, Consensus, Open Questions, and Practical Next Steps. "
            "Be concise and evidence-based. Use proper markdown headings (##), bullet points, and bold text. \n\n"
            "**CRITICAL INSTRUCTION - MANDATORY HYPERLINKS:** \n"
            "Every single time you reference, mention, or cite a paper in the digest, you MUST create a clickable markdown hyperlink using the exact arXiv URL. \n"
            "Format: [Paper Title](arXiv_URL) \n"
            "NEVER use citation numbers like [1], [2], etc. NEVER use plain text paper titles without hyperlinks. \n"
            "Examples of CORRECT formatting: \n"
            "  - In Key Findings: 'Dynamic pricing models are discussed in [Title of First Paper](https://arxiv.org/abs/2023.xxxxx).' \n"
            "  - In Paper-by-Paper Notes: '[Title of Paper](https://arxiv.org/abs/2023.xxxxx) by Smith et al. (2023) addresses...' \n"
            "  - Always make the paper title itself into a hyperlink. \n\n"
            "At the end, include a ## References section listing all papers as full markdown hyperlinks: \n"
            "## References\n"
            "1. [Full Paper Title](https://arxiv.org/abs/URL)\n"
            "2. [Full Paper Title](https://arxiv.org/abs/URL)\n"
            "etc."
        )
        user_prompt = (
            f"Research topic: {query}\n"
            f"Total papers analyzed: {len(final_papers)}\n\n"
            "PAPER EVIDENCE:\n"
            "---\n"
            + "\n---\n".join(paper_context_lines)
            + "\n---\n\n"
            "Reminder: Use markdown hyperlinks [Paper Title](URL) every time you mention a paper. Do NOT use [1], [2] citations."
        )

        yield {"type": "status", "message": f"Synthesizing digest from {len(final_papers)} papers..."}

        try:
            async for chunk in llm.astream(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
                config={"metadata": {"user_email": user_email}},
            ):
                content = chunk.content if hasattr(chunk, "content") else ""
                if isinstance(content, str) and content:
                    yield {"type": "token", "token": content}
        except Exception as exc:
            logger.exception("LLM stream error for research digest: %s", exc)
            yield {"type": "status", "message": "LLM synthesis failed — producing fallback digest."}
            fallback = ResearchDigestService._fallback_digest(query, final_papers)
            for token in fallback.splitlines(keepends=True):
                yield {"type": "token", "token": token}
