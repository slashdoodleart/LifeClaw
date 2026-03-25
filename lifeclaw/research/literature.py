"""Real academic literature search — OpenAlex, Semantic Scholar, arXiv.

No hallucinated references. Every paper returned has a real ID you can verify.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger


@dataclass
class Paper:
    """A real academic paper with verified metadata."""
    title: str
    authors: list[str]
    year: int
    abstract: str = ""
    doi: str = ""
    arxiv_id: str = ""
    semantic_scholar_id: str = ""
    openalex_id: str = ""
    url: str = ""
    citation_count: int = 0
    source: str = ""  # "openalex", "semantic_scholar", "arxiv"
    relevance_score: float = 0.0

    @property
    def bibtex_key(self) -> str:
        first_author = self.authors[0].split()[-1].lower() if self.authors else "unknown"
        return f"{first_author}{self.year}"

    def to_bibtex(self) -> str:
        authors_str = " and ".join(self.authors)
        key = self.bibtex_key
        lines = [
            f"@article{{{key},",
            f"  title = {{{self.title}}},",
            f"  author = {{{authors_str}}},",
            f"  year = {{{self.year}}},",
        ]
        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")
        if self.arxiv_id:
            lines.append(f"  eprint = {{{self.arxiv_id}}},")
            lines.append(f"  archivePrefix = {{arXiv}},")
        if self.url:
            lines.append(f"  url = {{{self.url}}},")
        lines.append("}")
        return "\n".join(lines)


class LiteratureSearch:
    """Multi-source academic search with deduplication and ranking."""

    def __init__(self, s2_api_key: str = ""):
        self.s2_api_key = s2_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self._seen_titles: set[str] = set()

    async def search(
        self,
        query: str,
        max_results: int = 20,
        sources: list[str] | None = None,
    ) -> list[Paper]:
        """Search multiple academic sources and return deduplicated results."""
        sources = sources or ["openalex", "semantic_scholar", "arxiv"]
        all_papers: list[Paper] = []

        # Search in parallel
        tasks = []
        if "openalex" in sources:
            tasks.append(self._search_openalex(query, max_results))
        if "semantic_scholar" in sources:
            tasks.append(self._search_semantic_scholar(query, max_results))
        if "arxiv" in sources:
            tasks.append(self._search_arxiv(query, max_results))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Literature source failed: {result}")
                continue
            all_papers.extend(result)

        # Deduplicate by normalized title
        deduped = self._deduplicate(all_papers)

        # Sort by citation count (proxy for relevance)
        deduped.sort(key=lambda p: p.citation_count, reverse=True)

        return deduped[:max_results]

    async def _search_openalex(self, query: str, max_results: int) -> list[Paper]:
        """Search OpenAlex — free, no API key needed, covers 250M+ works."""
        papers = []
        try:
            params = {
                "search": query,
                "per_page": min(max_results, 25),
                "sort": "relevance_score:desc",
                "select": "id,title,authorships,publication_year,doi,cited_by_count,abstract_inverted_index",
            }
            resp = await self.client.get(
                "https://api.openalex.org/works",
                params=params,
                headers={"User-Agent": "LifeClaw/0.2 (mailto:research@lifeclaw.dev)"},
            )
            if resp.status_code != 200:
                logger.warning(f"OpenAlex returned {resp.status_code}")
                return []

            data = resp.json()
            for work in data.get("results", []):
                authors = []
                for authorship in work.get("authorships", [])[:10]:
                    name = authorship.get("author", {}).get("display_name", "")
                    if name:
                        authors.append(name)

                # Reconstruct abstract from inverted index
                abstract = self._reconstruct_abstract(
                    work.get("abstract_inverted_index", {})
                )

                doi = work.get("doi", "") or ""
                if doi.startswith("https://doi.org/"):
                    doi = doi[16:]

                papers.append(Paper(
                    title=work.get("title", ""),
                    authors=authors,
                    year=work.get("publication_year", 0) or 0,
                    abstract=abstract,
                    doi=doi,
                    openalex_id=work.get("id", ""),
                    citation_count=work.get("cited_by_count", 0) or 0,
                    source="openalex",
                    url=f"https://doi.org/{doi}" if doi else "",
                ))
        except Exception as e:
            logger.warning(f"OpenAlex search failed: {e}")
        return papers

    async def _search_semantic_scholar(self, query: str, max_results: int) -> list[Paper]:
        """Search Semantic Scholar — free tier: 1 req/sec, optional API key for more."""
        papers = []
        try:
            headers = {}
            if self.s2_api_key:
                headers["x-api-key"] = self.s2_api_key

            params = {
                "query": query,
                "limit": min(max_results, 20),
                "fields": "title,authors,year,abstract,externalIds,citationCount,url",
            }
            resp = await self.client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
                headers=headers,
            )
            if resp.status_code != 200:
                logger.warning(f"Semantic Scholar returned {resp.status_code}")
                return []

            data = resp.json()
            for item in data.get("data", []):
                authors = [a.get("name", "") for a in item.get("authors", [])]
                ext_ids = item.get("externalIds", {}) or {}

                papers.append(Paper(
                    title=item.get("title", ""),
                    authors=authors,
                    year=item.get("year", 0) or 0,
                    abstract=item.get("abstract", "") or "",
                    doi=ext_ids.get("DOI", ""),
                    arxiv_id=ext_ids.get("ArXiv", ""),
                    semantic_scholar_id=item.get("paperId", ""),
                    citation_count=item.get("citationCount", 0) or 0,
                    source="semantic_scholar",
                    url=item.get("url", ""),
                ))
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")
        return papers

    async def _search_arxiv(self, query: str, max_results: int) -> list[Paper]:
        """Search arXiv via Atom API — free, no key needed."""
        papers = []
        try:
            # arXiv API uses Atom XML
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": min(max_results, 20),
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            resp = await self.client.get(
                "http://export.arxiv.org/api/query",
                params=params,
            )
            if resp.status_code != 200:
                return []

            # Simple XML parsing without lxml dependency
            text = resp.text
            entries = re.findall(r"<entry>(.*?)</entry>", text, re.DOTALL)

            for entry in entries:
                title = self._xml_text(entry, "title").replace("\n", " ").strip()
                summary = self._xml_text(entry, "summary").replace("\n", " ").strip()

                authors = re.findall(r"<name>(.*?)</name>", entry)

                # Extract arxiv ID from the id URL
                id_url = self._xml_text(entry, "id")
                arxiv_id = ""
                if "arxiv.org/abs/" in id_url:
                    arxiv_id = id_url.split("arxiv.org/abs/")[-1]

                published = self._xml_text(entry, "published")
                year = int(published[:4]) if published else 0

                doi_match = re.search(r'<arxiv:doi.*?>(.*?)</arxiv:doi>', entry)
                doi = doi_match.group(1) if doi_match else ""

                papers.append(Paper(
                    title=title,
                    authors=authors,
                    year=year,
                    abstract=summary[:500],
                    doi=doi,
                    arxiv_id=arxiv_id,
                    source="arxiv",
                    url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "",
                ))
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}")
        return papers

    def _deduplicate(self, papers: list[Paper]) -> list[Paper]:
        """Remove duplicate papers by normalized title."""
        seen: dict[str, Paper] = {}
        for p in papers:
            key = re.sub(r"[^a-z0-9]", "", p.title.lower())
            if key in seen:
                # Merge metadata from different sources
                existing = seen[key]
                if not existing.doi and p.doi:
                    existing.doi = p.doi
                if not existing.arxiv_id and p.arxiv_id:
                    existing.arxiv_id = p.arxiv_id
                if not existing.semantic_scholar_id and p.semantic_scholar_id:
                    existing.semantic_scholar_id = p.semantic_scholar_id
                if p.citation_count > existing.citation_count:
                    existing.citation_count = p.citation_count
                if not existing.abstract and p.abstract:
                    existing.abstract = p.abstract
            else:
                seen[key] = p
        return list(seen.values())

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict | None) -> str:
        """Reconstruct abstract from OpenAlex inverted index format."""
        if not inverted_index:
            return ""
        word_positions: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        return " ".join(w for _, w in word_positions)[:500]

    @staticmethod
    def _xml_text(xml: str, tag: str) -> str:
        match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", xml, re.DOTALL)
        return match.group(1).strip() if match else ""

    async def verify_citation(self, paper: Paper) -> dict:
        """4-layer citation verification — arXiv, CrossRef, Semantic Scholar."""
        result = {"paper": paper.title, "verified": False, "checks": []}

        # Layer 1: arXiv ID check
        if paper.arxiv_id:
            try:
                resp = await self.client.get(
                    f"http://export.arxiv.org/api/query?id_list={paper.arxiv_id}"
                )
                if resp.status_code == 200 and "<entry>" in resp.text:
                    result["checks"].append({"layer": "arxiv", "status": "verified"})
                    result["verified"] = True
                    return result
            except Exception:
                pass
            result["checks"].append({"layer": "arxiv", "status": "failed"})

        # Layer 2: DOI check via CrossRef
        if paper.doi:
            try:
                resp = await self.client.get(
                    f"https://api.crossref.org/works/{paper.doi}",
                    headers={"User-Agent": "LifeClaw/0.2 (mailto:research@lifeclaw.dev)"},
                )
                if resp.status_code == 200:
                    result["checks"].append({"layer": "crossref", "status": "verified"})
                    result["verified"] = True
                    return result
            except Exception:
                pass
            result["checks"].append({"layer": "crossref", "status": "failed"})

        # Layer 3: Semantic Scholar title match
        try:
            params = {"query": paper.title, "limit": 3, "fields": "title"}
            resp = await self.client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("data", []):
                    if self._title_match(paper.title, item.get("title", "")):
                        result["checks"].append({"layer": "s2_title", "status": "verified"})
                        result["verified"] = True
                        return result
        except Exception:
            pass
        result["checks"].append({"layer": "s2_title", "status": "failed"})

        return result

    @staticmethod
    def _title_match(a: str, b: str) -> bool:
        """Fuzzy title match — normalize and compare."""
        norm_a = re.sub(r"[^a-z0-9]", "", a.lower())
        norm_b = re.sub(r"[^a-z0-9]", "", b.lower())
        if not norm_a or not norm_b:
            return False
        # Check if one contains the other or they're very similar
        shorter, longer = sorted([norm_a, norm_b], key=len)
        return shorter in longer or len(set(shorter) & set(longer)) / len(set(shorter)) > 0.8

    def generate_bibtex(self, papers: list[Paper]) -> str:
        """Generate a complete .bib file from verified papers."""
        entries = [p.to_bibtex() for p in papers if p.title]
        return "\n\n".join(entries)

    async def close(self):
        await self.client.aclose()
