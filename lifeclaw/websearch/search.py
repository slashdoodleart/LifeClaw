"""Multi-provider web search — Brave, DuckDuckGo, Jina, Tavily, SearXNG."""

import json
import os
from dataclasses import dataclass

import httpx
from loguru import logger


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class WebSearchProvider:
    """Multi-backend web search with automatic fallback."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.provider = self.config.get("provider", "duckduckgo")
        self.max_results = self.config.get("maxResults", 5)
        self.proxy = self.config.get("proxy")

    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        """Search using configured provider, fall back to DuckDuckGo."""
        n = max_results or self.max_results
        try:
            if self.provider == "brave":
                return await self._brave(query, n)
            elif self.provider == "tavily":
                return await self._tavily(query, n)
            elif self.provider == "jina":
                return await self._jina(query, n)
            elif self.provider == "searxng":
                return await self._searxng(query, n)
            else:
                return await self._duckduckgo(query, n)
        except Exception as e:
            logger.warning(f"Search ({self.provider}) failed: {e}, falling back to DuckDuckGo")
            if self.provider != "duckduckgo":
                return await self._duckduckgo(query, n)
            return []

    async def fetch_page(self, url: str) -> str:
        """Fetch a web page and return text content."""
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # Try Jina reader API first for clean markdown
            jina_key = self.config.get("jinaApiKey") or os.getenv("JINA_API_KEY")
            if jina_key:
                try:
                    resp = await client.get(
                        f"https://r.jina.ai/{url}",
                        headers={"Authorization": f"Bearer {jina_key}", "Accept": "text/markdown"},
                    )
                    if resp.status_code == 200:
                        return resp.text[:10000]
                except Exception:
                    pass
            # Fallback: raw fetch
            resp = await client.get(url)
            return resp.text[:10000]

    async def _brave(self, query: str, n: int) -> list[SearchResult]:
        api_key = self.config.get("apiKey") or os.getenv("BRAVE_API_KEY")
        if not api_key:
            raise ValueError("Brave API key not set")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": n},
                headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            )
            data = resp.json()
            return [
                SearchResult(r["title"], r["url"], r.get("description", ""))
                for r in data.get("web", {}).get("results", [])[:n]
            ]

    async def _tavily(self, query: str, n: int) -> list[SearchResult]:
        api_key = self.config.get("apiKey") or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("Tavily API key not set")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={"query": query, "max_results": n, "api_key": api_key},
            )
            data = resp.json()
            return [
                SearchResult(r.get("title", ""), r["url"], r.get("content", ""))
                for r in data.get("results", [])[:n]
            ]

    async def _jina(self, query: str, n: int) -> list[SearchResult]:
        api_key = self.config.get("apiKey") or os.getenv("JINA_API_KEY")
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://s.jina.ai/{query}",
                headers=headers,
            )
            data = resp.json()
            return [
                SearchResult(r.get("title", ""), r.get("url", ""), r.get("description", ""))
                for r in data.get("data", [])[:n]
            ]

    async def _searxng(self, query: str, n: int) -> list[SearchResult]:
        base_url = self.config.get("baseUrl") or os.getenv("SEARXNG_BASE_URL")
        if not base_url:
            raise ValueError("SearXNG base URL not set")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{base_url}/search",
                params={"q": query, "format": "json", "pageno": 1},
            )
            data = resp.json()
            return [
                SearchResult(r.get("title", ""), r.get("url", ""), r.get("content", ""))
                for r in data.get("results", [])[:n]
            ]

    async def _duckduckgo(self, query: str, n: int) -> list[SearchResult]:
        """DuckDuckGo instant answer API — zero config, free."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            data = resp.json()
            results = []
            # Abstract
            if data.get("Abstract"):
                results.append(SearchResult(
                    data.get("Heading", query),
                    data.get("AbstractURL", ""),
                    data["Abstract"][:300],
                ))
            # Related topics
            for topic in data.get("RelatedTopics", [])[:n]:
                if isinstance(topic, dict) and "FirstURL" in topic:
                    results.append(SearchResult(
                        topic.get("Text", "")[:80],
                        topic["FirstURL"],
                        topic.get("Text", "")[:200],
                    ))
            return results[:n]
