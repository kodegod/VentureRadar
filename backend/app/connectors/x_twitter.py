from __future__ import annotations

from app.config import settings
from app.connectors.base import NormalizedPost


class XConnector:
    """Official X API v2 recent search. Disabled until approval + live smoke test."""

    platform = "x"

    def is_enabled(self) -> bool:
        return False

    def search(self, query: str, community: str | None = None) -> list[NormalizedPost]:
        if not settings.x_bearer_token:
            return []
        return []
