from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    EvidenceLink,
    ObservationEmbedding,
    OpportunityProblemLink,
    ProblemCluster,
    ProblemObservation,
    SourceComment,
    SourcePost,
    StartupOpportunity,
)
from app.scoring.engine import compute_scores


def tombstone_source_post(db: Session, post: SourcePost, reason: str) -> None:
    now = datetime.now(timezone.utc)
    post.deleted_at = now
    post.deletion_reason = reason
    post.title = None
    post.body = None
    post.author_fingerprint = None
    post.raw = {}
    db.flush()

    for comment in post.comments:
        comment.deleted_at = now
        comment.deletion_reason = reason
        comment.body = None
        comment.author_fingerprint = None

    for ev in db.scalars(select(EvidenceLink).where(EvidenceLink.source_post_id == post.id)):
        ev.invalidated = True

    for obs in list(post.observations):
        other_live = False
        if not other_live:
            obs.deleted_at = now
            emb = db.scalar(select(ObservationEmbedding).where(ObservationEmbedding.observation_id == obs.id))
            if emb:
                db.delete(emb)
            for ev in db.scalars(select(EvidenceLink).where(EvidenceLink.observation_id == obs.id)):
                ev.invalidated = True

    _recompute_clusters_and_opportunities(db)
    db.flush()


def _recompute_clusters_and_opportunities(db: Session) -> None:
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))).all()
    for cluster in clusters:
        live_obs = [
            m.observation
            for m in cluster.memberships
            if m.active and m.observation.deleted_at is None and not m.observation.is_duplicate
        ]
        fingerprints = {o.author_fingerprint for o in live_obs if o.author_fingerprint}
        cluster.independent_observation_count = len(fingerprints)
        if cluster.independent_observation_count == 0:
            cluster.deleted_at = datetime.now(timezone.utc)

        links = db.scalars(select(OpportunityProblemLink).where(OpportunityProblemLink.cluster_id == cluster.id)).all()
        for link in links:
            opp = db.get(StartupOpportunity, link.opportunity_id)
            if not opp:
                continue
            if cluster.independent_observation_count == 0:
                opp.evaluation_stale = True
                opp.research_status = "archived"
                opp.quality_status = "needs_more_research"
            elif cluster.independent_observation_count < 3:
                opp.evaluation_stale = True
                opp.is_provisional = True
                opp.research_status = "provisional"
                if opp.evaluations:
                    latest = max(opp.evaluations, key=lambda e: e.version)
                    latest.stale = True
                    factors = [
                        {
                            "criterion": f.criterion,
                            "weight": f.weight,
                            "score": f.score,
                            "confidence": f.confidence,
                        }
                        for f in latest.factors
                    ]
                    metrics = compute_scores(factors)
                    opp.observed_quality_score = metrics["observed_quality_score"]
                    opp.research_completeness = metrics["research_completeness"]
                    opp.conservative_score = metrics["conservative_score"]
