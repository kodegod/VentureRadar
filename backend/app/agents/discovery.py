from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.mock import MockRedditConnector, MockXConnector
from app.connectors.reddit import RedditConnector
from app.connectors.x_twitter import XConnector
from app.models import (
    AgentRun,
    AuthorFingerprint,
    CollectionAttempt,
    CollectionStat,
    ResearchJob,
    SearchQuery,
    SourcePost,
)
from app.services.bootstrap import live_operational


def run_discovery(db: Session, run_id: uuid.UUID) -> dict:
    agent = AgentRun(research_run_id=run_id, agent_name="discovery", status="running", current_task="search")
    db.add(agent)
    db.flush()

    live = live_operational(db)
    reddit = RedditConnector() if live else MockRedditConnector()
    x = XConnector() if live else MockXConnector()
    # Live connectors are never used unless a smoke test passed.
    if isinstance(reddit, RedditConnector) and not reddit.is_enabled():
        reddit = MockRedditConnector()
    if isinstance(x, XConnector) and not x.is_enabled():
        x = MockXConnector()

    queries = db.scalars(select(SearchQuery).where(SearchQuery.enabled.is_(True))).all()
    if not queries:
        queries = [
            SearchQuery(platform="reddit", query="I do this manually", community="smallbusiness", enabled=True),
            SearchQuery(platform="x", query="takes me hours", community=None, enabled=True),
        ]

    created = 0
    scheduled = 0
    succeeded = 0
    query_blob = []
    seen: set[tuple[str, str]] = set()
    for q in queries:
        scheduled += 1
        connector = reddit if q.platform == "reddit" else x
        posts = connector.search(q.query, q.community)
        succeeded += 1
        query_blob.append(f"{q.platform}:{q.query}:{q.community}")
        db.add(
            CollectionAttempt(
                research_run_id=run_id,
                platform=q.platform,
                query=q.query,
                scheduled=True,
                succeeded=True,
                pagination_complete=True,
                results_truncated=False,
                result_count=len(posts),
            )
        )
        for post in posts:
            key = (post.platform, post.external_id)
            if key in seen:
                continue
            exists = db.scalar(
                select(SourcePost).where(SourcePost.platform == post.platform, SourcePost.external_id == post.external_id)
            )
            seen.add(key)
            if exists:
                continue
            row = SourcePost(
                platform=post.platform,
                external_id=post.external_id,
                url=post.url,
                title=post.title,
                body=post.body,
                author_fingerprint=post.author_fingerprint,
                community=post.community,
                posted_at=post.posted_at,
                engagement=post.engagement,
                raw={"labels": post.labels},
                data_origin=post.data_origin,
                is_synthetic=post.is_synthetic,
            )
            db.add(row)
            created += 1
            if post.author_fingerprint:
                fp = db.scalar(
                    select(AuthorFingerprint).where(
                        AuthorFingerprint.platform == post.platform,
                        AuthorFingerprint.fingerprint == post.author_fingerprint,
                    )
                )
                if fp:
                    fp.post_count += 1
                else:
                    db.add(
                        AuthorFingerprint(
                            platform=post.platform, fingerprint=post.author_fingerprint, post_count=1
                        )
                    )
        db.add(
            ResearchJob(
                job_type="extract_batch",
                dedupe_key=f"discover:{run_id}:{q.platform}:{q.query}:{q.community}",
                status="done",
                payload={"count": len(posts)},
            )
        )
        q.last_cursor = datetime.now(timezone.utc).isoformat()

    now = datetime.now(timezone.utc)
    db.add(
        CollectionStat(
            research_run_id=run_id,
            platform="all",
            period_start=now - timedelta(days=7),
            period_end=now,
            collection_volume=created,
            query_set_hash=hashlib.sha256("|".join(sorted(query_blob)).encode()).hexdigest()[:16],
            active_query_count=len(query_blob),
            searches_scheduled=scheduled,
            searches_succeeded=succeeded,
            pagination_complete=True,
            results_truncated=False,
            rate_limit_failures=0,
            source_outages=0,
            window_coverage=1.0,
        )
    )
    agent.status = "completed"
    agent.completed_tasks = created
    agent.finished_at = datetime.now(timezone.utc)
    agent.current_task = None
    db.flush()
    return {"posts_created": created, "searches_scheduled": scheduled, "searches_succeeded": succeeded}
