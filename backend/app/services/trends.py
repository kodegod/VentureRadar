from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClusterPeriodStat, CollectionStat, ProblemCluster


INCOMPARABLE = "insufficient_comparable_data"


def periods_comparable(a: ClusterPeriodStat | CollectionStat, b: ClusterPeriodStat | CollectionStat) -> bool:
    if a.query_set_hash != b.query_set_hash:
        return False
    if getattr(a, "window_coverage", 1) < 0.8 or getattr(b, "window_coverage", 1) < 0.8:
        return False
    if getattr(a, "pagination_complete", True) != getattr(b, "pagination_complete", True):
        return False
    if getattr(a, "rate_limit_failures", 0) > 0 or getattr(b, "rate_limit_failures", 0) > 0:
        return False
    if getattr(a, "source_outages", 0) > 0 or getattr(b, "source_outages", 0) > 0:
        return False
    return True


def compute_cluster_trend(current: ClusterPeriodStat | None, previous: ClusterPeriodStat | None) -> str:
    if current is None or previous is None:
        return INCOMPARABLE
    if not periods_comparable(current, previous):
        return INCOMPARABLE
    if previous.observation_rate <= 0:
        return INCOMPARABLE
    delta = (current.observation_rate - previous.observation_rate) / previous.observation_rate
    if delta > 0.15:
        return "up"
    if delta < -0.15:
        return "down"
    return "flat"


def refresh_cluster_trends(db: Session, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    period_end = now
    period_start = now - timedelta(days=7)
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))).all()
    for cluster in clusters:
        stats = (
            db.scalars(
                select(ClusterPeriodStat)
                .where(ClusterPeriodStat.cluster_id == cluster.id)
                .order_by(ClusterPeriodStat.period_start.desc())
            )
            .all()
        )
        current = next((s for s in stats if s.period_end <= period_end and s.period_start >= period_start - timedelta(days=1)), stats[0] if stats else None)
        previous = stats[1] if len(stats) > 1 else None
        cluster.trend = compute_cluster_trend(current, previous)
    db.flush()
