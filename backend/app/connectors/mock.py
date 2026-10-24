from __future__ import annotations

import hashlib

from app.connectors.base import NormalizedPost
from app.fixtures.synthetic import generate_synthetic_posts


def _fingerprint(platform: str, author: str) -> str:
    return hashlib.sha256(f"{platform}:{author}".encode()).hexdigest()[:16]


class MockRedditConnector:
    platform = "reddit"

    def is_enabled(self) -> bool:
        return True

    def search(self, query: str, community: str | None = None) -> list[NormalizedPost]:
        return _from_fixtures("reddit")


class MockXConnector:
    platform = "x"

    def is_enabled(self) -> bool:
        return True

    def search(self, query: str, community: str | None = None) -> list[NormalizedPost]:
        return _from_fixtures("x")


def _from_fixtures(platform: str) -> list[NormalizedPost]:
    out: list[NormalizedPost] = []
    for raw in generate_synthetic_posts():
        if raw["platform"] != platform:
            continue
        out.append(
            NormalizedPost(
                platform=raw["platform"],
                external_id=raw["external_id"],
                url=raw["url"],
                title=raw["title"],
                body=raw["body"],
                author_fingerprint=_fingerprint(raw["platform"], raw["author"]),
                community=raw.get("community"),
                posted_at=raw.get("posted_at"),
                engagement=raw.get("engagement") or {},
                data_origin="synthetic",
                is_synthetic=True,
                labels=raw.get("labels") or {},
            )
        )
    return out
