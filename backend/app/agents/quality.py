from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AgentRun,
    EvidenceLink,
    OpportunityProblemLink,
    ProblemCluster,
    QualityAudit,
    SourcePost,
    StartupOpportunity,
)
from app.scoring.ranking import is_verified


def run_quality(db: Session, run_id: uuid.UUID) -> dict:
    agent = AgentRun(research_run_id=run_id, agent_name="quality", status="running", current_task="audit")
    db.add(agent)
    db.flush()
    audited = 0
    opportunities = db.scalars(select(StartupOpportunity)).all()
    for opp in opportunities:
        if opp.audits:
            continue
        audit = _audit(db, opp)
        db.add(audit)
        opp.quality_status = audit.status
        if audit.status == "rejected":
            opp.research_status = "rejected"
            opp.is_provisional = True
        elif audit.status == "needs_more_research":
            opp.research_status = "needs_more_research"
            opp.is_provisional = True
        elif opp.is_provisional:
            opp.research_status = "provisional"
        else:
            opp.research_status = "evaluated"
        # Agent 5 cannot promote provisional to verified.
        payload = {
            "research_completeness": opp.research_completeness,
            "evidence_confidence": opp.evidence_confidence,
            "quality_status": opp.quality_status,
            "rejected_by_user": opp.rejected_by_user,
        }
        if opp.is_provisional and is_verified(payload):
            opp.is_provisional = True
        audited += 1

    agent.status = "completed"
    agent.completed_tasks = audited
    agent.finished_at = datetime.now(timezone.utc)
    agent.current_task = None
    db.flush()
    return {"audits": audited}


def _audit(db: Session, opp: StartupOpportunity) -> QualityAudit:
    links = db.scalars(select(OpportunityProblemLink).where(OpportunityProblemLink.opportunity_id == opp.id)).all()
    clusters = [db.get(ProblemCluster, link.cluster_id) for link in links]
    observations = []
    for cluster in clusters:
        if not cluster:
            continue
        observations.extend([m.observation for m in cluster.memberships if m.active and m.observation.deleted_at is None])

    independents = [o for o in observations if not o.is_duplicate]
    evidence = db.scalars(
        select(EvidenceLink).where(EvidenceLink.subject_id == opp.id, EvidenceLink.invalidated.is_(False))
    ).all()
    fabricated = [e for e in evidence if e.source_url and "synthetic.ventureradar.test" not in e.source_url and not e.source_post_id]
    # Attribution rule: every supporting URL must belong to a stored source or be a Tavily URL stored on competitor_research.

    risks = []
    against = []
    missing = []
    unsupported = []
    experiments = [
        "Interview 5 people who posted the workflow complaint and confirm they buy tools",
        "Sell a concierge version before writing product code",
        "Check whether the incumbent last-mile feature is already on a roadmap",
    ]

    if opp.is_synthetic or opp.data_origin == "synthetic":
        risks.append("Evidence is synthetic_labeled, not live customer research.")
        against.append("Do not treat this as real-world demand.")
    if len({o.author_fingerprint for o in independents}) < 3:
        risks.append("Fewer than three independent accounts after duplicate collapse.")
        against.append("A small number of voices can create false demand.")
    if opp.research_completeness is not None and opp.research_completeness < 0.70:
        missing.append("Factor coverage below the verified completeness gate.")
    if any((o.buying_intent in (None, "none")) for o in independents) and not any(
        o.buying_intent in {"moderate", "strong", "committed"} for o in independents
    ):
        against.append("No stated purchasing language.")

    # Conflicting posts on the same cluster theme
    cluster_ids = [c.id for c in clusters if c]
    related_posts = []
    if cluster_ids:
        related_posts = db.scalars(select(SourcePost).where(SourcePost.deleted_at.is_(None))).all()
    negatives = [
        p
        for p in related_posts
        if p.body
        and any(word in p.body.lower() for word in ("work fine", "no budget", "would not pay", "already solve"))
        and any(word in (p.body + (p.title or "")).lower() for word in (opp.customer_problem.lower().split()[:2]))
    ]
    if negatives:
        against.append("Negative evidence exists: some users say current tools work or they will not pay.")
        risks.append("Contradictory demand signals.")

    if fabricated:
        unsupported.append("Evidence URL did not resolve to a stored source.")

    if len(independents) == 0:
        status = "rejected"
        against.append("No remaining independent observations.")
    elif opp.is_synthetic:
        status = "passed_with_limitations"
    elif len({o.author_fingerprint for o in independents}) < 3:
        status = "needs_more_research"
    else:
        status = "passed_with_limitations" if missing or against else "passed"

    if opp.is_provisional and status == "passed":
        status = "passed_with_limitations"

    return QualityAudit(
        opportunity_id=opp.id,
        status=status,
        risks=risks,
        arguments_against=against,
        missing_evidence=missing,
        unsupported_claims=unsupported,
        validation_experiments=experiments,
        notes="Independent skeptic pass. Does not write scores.",
    )
