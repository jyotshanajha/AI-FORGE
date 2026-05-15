from collections.abc import AsyncGenerator
from xml.etree import ElementTree

import httpx
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.llm import llm


ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


class ResearchDigestService:
    @staticmethod
    async def _search_arxiv(query: str, max_results: int) -> list[dict[str, object]]:
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": "0",
            "max_results": str(max_results),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except httpx.ConnectError as e:
                print(f"[ResearchDigestService] arXiv connection error: {e}")
                return []
            except httpx.TimeoutException as e:
                print(f"[ResearchDigestService] arXiv timeout: {e}")
                return []
            except Exception as e:
                print(f"[ResearchDigestService] arXiv error: {e}")
                return []

        try:
            root = ElementTree.fromstring(response.text)
            entries = root.findall("atom:entry", ATOM_NAMESPACE)
        except Exception as e:
            print(f"[ResearchDigestService] XML parse error: {e}")
            return []

        papers: list[dict[str, object]] = []
        for entry in entries:
            paper_id = (entry.findtext("atom:id", default="", namespaces=ATOM_NAMESPACE) or "").strip()
            title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NAMESPACE) or "").split())
            summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ATOM_NAMESPACE) or "").split())
            published = (entry.findtext("atom:published", default="", namespaces=ATOM_NAMESPACE) or "")[:10]

            author_nodes = entry.findall("atom:author", ATOM_NAMESPACE)
            authors = [
                (author.findtext("atom:name", default="", namespaces=ATOM_NAMESPACE) or "").strip()
                for author in author_nodes
            ]
            authors = [author for author in authors if author]

            if paper_id and title:
                papers.append(
                    {
                        "id": paper_id,
                        "title": title,
                        "summary": summary,
                        "published": published,
                        "authors": authors,
                    }
                )

        return papers

    @staticmethod
    def _has_enough_evidence(papers: list[dict[str, object]], target: int) -> bool:
        # Stop searching once we have enough unique papers for a useful digest.
        return len(papers) >= target

    @staticmethod
    async def _collect_evidence(query: str, max_papers: int) -> list[dict[str, object]]:
        variants = [query, f"{query} survey", f"{query} recent advances"]
        seen: set[str] = set()
        collected: list[dict[str, object]] = []

        for variant in variants:
            found = await ResearchDigestService._search_arxiv(variant, max_results=max_papers)
            for paper in found:
                paper_id = str(paper.get("id", ""))
                if not paper_id or paper_id in seen:
                    continue
                seen.add(paper_id)
                collected.append(paper)

            if ResearchDigestService._has_enough_evidence(collected, max_papers):
                break

        return collected[:max_papers]

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
            lines.append(f"{idx}. {paper['title']} ({paper['published']})")

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
    async def stream_digest(query: str, max_papers: int, user_email: str) -> AsyncGenerator[str, None]:
        try:
            papers = await ResearchDigestService._collect_evidence(query, max_papers=max_papers)
        except Exception as e:
            print(f"[ResearchDigestService] collect_evidence error: {e}")
            yield f"Error collecting evidence: {str(e)}"
            return

        if not papers:
            yield "No relevant arXiv papers were found for this query."
            return

        if llm is None:
            fallback = ResearchDigestService._fallback_digest(query, papers)
            for token in fallback:
                yield token
            return

        paper_context_lines: list[str] = []
        for idx, paper in enumerate(papers, start=1):
            authors = ", ".join(list(paper["authors"])[:4]) or "Unknown authors"
            summary = str(paper["summary"])[:800]
            paper_context_lines.append(
                (
                    f"[{idx}] Title: {paper['title']}\n"
                    f"Published: {paper['published']}\n"
                    f"Authors: {authors}\n"
                    f"Abstract: {summary}\n"
                    f"Link: {paper['id']}"
                )
            )

        system_prompt = (
            "You are a research digest agent. You must produce a structured digest in markdown "
            "with these sections: Overview, Key Findings, Paper-by-Paper Notes, Consensus, "
            "Open Questions, and Practical Next Steps. Be concise and evidence-based."
        )
        user_prompt = (
            f"Research topic: {query}\n"
            f"Evidence papers analyzed: {len(papers)}\n\n"
            "Paper evidence:\n"
            + "\n\n".join(paper_context_lines)
        )

        try:
            async for chunk in llm.astream(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
                config={"metadata": {"user_email": user_email}},
            ):
                content = chunk.content if hasattr(chunk, "content") else ""
                if isinstance(content, str) and content:
                    yield content
        except Exception as e:
            print(f"[ResearchDigestService] LLM stream error: {e}")
            fallback = ResearchDigestService._fallback_digest(query, papers)
            for token in fallback:
                yield token
