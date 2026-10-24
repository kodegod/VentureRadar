from __future__ import annotations

from app.config import settings
from app.connectors.base import NormalizedPost


class RedditConnector:
    """Official OAuth Data API connector. Disabled until approval + live smoke test."""

    platform = "reddit"

    def is_enabled(self) -> bool:
        return False

    def search(self, query: str, community: str | None = None) -> list[NormalizedPost]:
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            return []
        # Live collection stays off until LIVE_COLLECTION_ENABLED and a recorded smoke test.
        return []
