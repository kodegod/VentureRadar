from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class TavilyConnector:
    """Authorized Tavily Search. Returns source URLs or empty if unconfigured."""

    def is_enabled(self) -> bool:
        return bool(settings.tavily_api_key)

    def search(self, query: str) -> list[dict[str, Any]]:
        if not self.is_enabled():
            return []
        response = httpx.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
            json={"query": query, "search_depth": "basic", "max_results": 5},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        results = []
        for item in payload.get("results") or []:
            url = item.get("url")
            if not url:
                continue
            results.append(
                {
                    "title": item.get("title") or "",
                    "url": url,
                    "content": item.get("content") or "",
                }
            )
        return results
