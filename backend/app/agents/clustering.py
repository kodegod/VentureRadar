from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AgentRun,
    ClusterMembership,
    ClusterPeriodStat,
    CollectionStat,
    ObservationEmbedding,
    ProblemCluster,
    ProblemObservation,
)
from app.nlp import jaccard, lexical_vector, tokens
from app.services.trends import compute_cluster_trend


def run_clustering(db: Session, run_id: uuid.UUID) -> dict:
    agent = AgentRun(research_run_id=run_id, agent_name="clustering", status="running", current_task="cluster")
    db.add(agent)
    db.flush()

    observations = db.scalars(
        select(ProblemObservation).where(
            ProblemObservation.deleted_at.is_(None),
            ProblemObservation.relevance_class == "genuine_problem",
        )
    ).all()

    created = 0
    for obs in observations:
        if any(m.active for m in obs.memberships):
            continue
        cluster = _find_cluster(db, obs)
        if cluster is None:
            cluster = ProblemCluster(
                canonical_title=obs.title,
                description=obs.description,
                customer_segment=obs.target_customer,
                industry=obs.industry,
                severity_score=obs.severity_score,
                frequency=obs.frequency,
                data_origin=obs.data_origin,
                is_synthetic=obs.is_synthetic,
                first_observed=obs.created_at,
                last_observed=obs.created_at,
            )
            db.add(cluster)
            db.flush()
            created += 1
        db.add(ClusterMembership(cluster_id=cluster.id, observation_id=obs.id, version=1, active=True))
        db.add(ObservationEmbedding(observation_id=obs.id, model="lexical", vector=lexical_vector(obs.description)))
        db.flush()

    for cluster in db.scalars(select(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))).all():
        _roll_up(db, cluster, run_id)

    agent.status = "completed"
    agent.completed_tasks = created
    agent.finished_at = datetime.now(timezone.utc)
    agent.current_task = None
    db.flush()
    return {"clusters_touched": created}


def _find_cluster(db: Session, obs: ProblemObservation) -> ProblemCluster | None:
    hint = obs.workflow if obs.workflow and obs.workflow != "unknown" else None
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))).all()
    obs_tokens = tokens(f"{obs.title} {obs.description} {obs.industry} {obs.target_customer}")
    best = None
    best_score = 0.0
    for cluster in clusters:
        # Do not merge unrelated customer segments
        if (
            cluster.customer_segment
            and obs.target_customer
            and cluster.customer_segment != obs.target_customer
            and cluster.industry != obs.industry
        ):
            continue
        if hint and cluster.memberships:
            member_workflows = {m.observation.workflow for m in cluster.memberships if m.active}
            if hint not in member_workflows and cluster.industry != obs.industry:
                continue
        score = jaccard(obs_tokens, tokens(f"{cluster.canonical_title} {cluster.description} {cluster.industry}"))
        if hint and hint in (cluster.canonical_title + cluster.description + (cluster.industry or "")).lower():
            score += 0.2
        if obs.industry and obs.industry == cluster.industry:
            score += 0.15
        if score > best_score:
            best = cluster
            best_score = score
    if best_score >= 0.22:
        return best
    # Prefer matching workflow title
    for cluster in clusters:
        if obs.title == cluster.canonical_title:
            return cluster
    return None


def _roll_up(db: Session, cluster: ProblemCluster, run_id: uuid.UUID) -> None:
    live = [m.observation for m in cluster.memberships if m.active and m.observation.deleted_at is None]
    independents = [o for o in live if not o.is_duplicate]
    fps = {o.author_fingerprint for o in independents if o.author_fingerprint}
    cluster.independent_observation_count = len(fps)
    cluster.reddit_evidence_count = sum(1 for o in independents if o.source_post and o.source_post.platform == "reddit")
    cluster.x_evidence_count = sum(1 for o in independents if o.source_post and o.source_post.platform == "x")
    cluster.workarounds = sorted({o.workaround for o in independents if o.workaround})
    sevs = [o.severity_score for o in independents if o.severity_score is not None]
    cluster.severity_score = max(sevs) if sevs else None
    times = [o.created_at for o in live if o.created_at]
    if times:
        cluster.first_observed = min(times)
        cluster.last_observed = max(times)

    stat = db.scalar(select(CollectionStat).where(CollectionStat.research_run_id == run_id))
    now = datetime.now(timezone.utc)
    volume = stat.collection_volume if stat else max(len(live), 1)
    period = ClusterPeriodStat(
        cluster_id=cluster.id,
        period_start=now - timedelta(days=7),
        period_end=now,
        independent_observations=cluster.independent_observation_count,
        collection_volume=volume,
        observation_rate=cluster.independent_observation_count / max(volume, 1),
        query_set_hash=stat.query_set_hash if stat else "unknown",
        distinct_communities=len({o.source_post.community for o in independents if o.source_post and o.source_post.community}),
        reddit_evidence_count=cluster.reddit_evidence_count,
        x_evidence_count=cluster.x_evidence_count,
        window_coverage=stat.window_coverage if stat else 1.0,
        pagination_complete=stat.pagination_complete if stat else True,
        rate_limit_failures=stat.rate_limit_failures if stat else 0,
        source_outages=stat.source_outages if stat else 0,
        coverage_comparable=False,
    )
    db.add(period)
    db.flush()
    previous = db.scalars(
        select(ClusterPeriodStat)
        .where(ClusterPeriodStat.cluster_id == cluster.id, ClusterPeriodStat.id != period.id)
        .order_by(ClusterPeriodStat.period_start.desc())
    ).first()
    cluster.trend = compute_cluster_trend(period, previous)
