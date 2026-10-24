from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.base import NormalizedPost
from app.models import AgentRun, EvidenceLink, ProblemObservation, SourcePost
from app.nlp import classify, extract_problems, is_near_duplicate


def run_extraction(db: Session, run_id: uuid.UUID) -> dict:
    agent = AgentRun(research_run_id=run_id, agent_name="extraction", status="running", current_task="extract")
    db.add(agent)
    db.flush()

    posts = db.scalars(
        select(SourcePost).where(SourcePost.processed.is_(False), SourcePost.deleted_at.is_(None))
    ).all()
    created = 0
    for post in posts:
        normalized = NormalizedPost(
            platform=post.platform,
            external_id=post.external_id,
            url=post.url,
            title=post.title or "",
            body=post.body or "",
            author_fingerprint=post.author_fingerprint or "",
            community=post.community,
            posted_at=post.posted_at,
            data_origin=post.data_origin,
            is_synthetic=post.is_synthetic,
        )
        relevance = classify(normalized)
        problems = extract_problems(normalized)
        if not problems and relevance != "genuine_problem":
            post.processed = True
            continue
        for problem in problems:
            obs = ProblemObservation(
                source_post_id=post.id,
                title=problem["title"],
                description=problem["description"],
                target_customer=problem["target_customer"],
                industry=problem["industry"],
                workflow=problem["workflow"],
                relevance_class=relevance,
                severity_score=problem["severity_score"],
                frequency=problem["frequency"],
                workaround=problem["workaround"],
                tools_mentioned=problem["tools_mentioned"],
                time_or_money=problem["time_or_money"],
                buying_intent=problem["buying_intent"],
                source_span=problem["source_span"],
                source_url=problem["source_url"],
                confidence=problem["confidence"],
                unknowns=problem["unknowns"],
                author_fingerprint=post.author_fingerprint,
                data_origin=post.data_origin,
                is_synthetic=post.is_synthetic,
            )
            _mark_duplicate(db, obs, f"{post.title} {post.body}")
            db.add(obs)
            db.flush()
            db.add(
                EvidenceLink(
                    subject_type="problem_observation",
                    subject_id=obs.id,
                    source_post_id=post.id,
                    observation_id=obs.id,
                    claim=obs.title,
                    quote=obs.source_span,
                    source_url=obs.source_url,
                    evidence_level="opinion",
                    polarity="supports",
                )
            )
            created += 1
        post.processed = True

    agent.status = "completed"
    agent.completed_tasks = created
    agent.finished_at = datetime.now(timezone.utc)
    agent.current_task = None
    db.flush()
    return {"observations_created": created}


def _mark_duplicate(db: Session, obs: ProblemObservation, text: str) -> None:
    existing = db.scalars(
        select(ProblemObservation).where(
            ProblemObservation.deleted_at.is_(None),
            ProblemObservation.id != obs.id,
        )
    ).all()
    for other in existing:
        other_text = f"{other.title} {other.description}"
        if is_near_duplicate(text, other_text):
            obs.is_duplicate = True
            obs.duplicate_of_id = other.duplicate_of_id or other.id
            return
