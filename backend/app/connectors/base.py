from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass
class NormalizedPost:
    platform: str
    external_id: str
    url: str
    title: str
    body: str
    author_fingerprint: str
    community: str | None
    posted_at: datetime | None
    engagement: dict[str, Any] = field(default_factory=dict)
    data_origin: str = "synthetic"
    is_synthetic: bool = True
    labels: dict[str, Any] = field(default_factory=dict)


class SourceConnector(Protocol):
    platform: str

    def is_enabled(self) -> bool: ...

    def search(self, query: str, community: str | None = None) -> list[NormalizedPost]: ...
