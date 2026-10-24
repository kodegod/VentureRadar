from __future__ import annotations

from contextlib import asynccontextmanager

from uuid import UUID

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.serializers import cluster_out, observation_out, opportunity_out
from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app import models  # noqa: F401
from app.models import (
    AgentRun,
    AppSetting,
    BudgetAccount,
    BudgetReservation,
    CompetitorResearch,
    Evaluation,
    EvaluationFactor,
    EvidenceLink,
    FounderProfile,
    ModelUsage,
    OpportunityProblemLink,
    PlatformRetentionPolicy,
    ProblemCluster,
    ProblemObservation,
    QualityAudit,
    ResearchJob,
    ResearchRun,
    ScoreHistory,
    SearchQuery,
    SourcePost,
    StartupOpportunity,
    UserFeedback,
)
from app.scoring.ranking import rank_opportunities
from app.services.bootstrap import bootstrap, is_paused, live_operational, set_paused
from app.services.pipeline import run_full_pipeline


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap(db)
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="VentureRadar", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ready"}


@app.get("/api/status")
def status(db: Session = Depends(get_db)):
    last = db.scalars(select(ResearchRun).order_by(ResearchRun.created_at.desc())).first()
    return {
        "mode": "synthetic",
        "live_collection_operational": live_operational(db),
        "research_paused": is_paused(db),
        "banner": "Synthetic research mode. Live social-media collection is not operational.",
        "dataset": "synthetic_labeled",
        "last_run": {
            "id": str(last.id) if last else None,
            "status": last.status if last else None,
            "finished_at": last.finished_at.isoformat() if last and last.finished_at else None,
        },
    }


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    problems = db.scalar(select(func.count()).select_from(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))) or 0
    opps = db.scalars(select(StartupOpportunity)).all()
    serialized = [opportunity_out(o) for o in opps]
    high = [o for o in serialized if o.get("verified")]
    reddit = db.scalar(select(func.count()).select_from(SourcePost).where(SourcePost.platform == "reddit")) or 0
    x_count = db.scalar(select(func.count()).select_from(SourcePost).where(SourcePost.platform == "x")) or 0
    last = db.scalars(select(ResearchRun).order_by(ResearchRun.created_at.desc())).first()
    cost = db.scalar(select(func.coalesce(func.sum(BudgetAccount.actual), 0))) or 0
    return {
        "banner": "Synthetic research mode. Live social-media collection is not operational.",
        "dataset": "synthetic_labeled",
        "totals": {
            "problems": problems,
            "opportunities": len(opps),
            "high_priority": len(high),
            "new_this_week": len(opps),
            "reddit_posts": reddit,
            "x_posts": x_count,
            "estimated_cost": float(cost),
        },
        "last_run": last.status if last else None,
        "research_paused": is_paused(db),
        "top_opportunities": rank_opportunities(serialized, "highest_opportunity")[:15],
    }


@app.get("/api/opportunities")
def list_opportunities(
    q: str | None = None,
    industry: str | None = None,
    ranking: str = "highest_opportunity",
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(StartupOpportunity)).all()
    items = [opportunity_out(o) for o in rows]
    if q:
        ql = q.lower()
        items = [i for i in items if ql in (i["working_name"] + i["customer_problem"] + (i["industry"] or "")).lower()]
    if industry:
        items = [i for i in items if i.get("industry") == industry]
    return {"dataset": "synthetic_labeled", "items": rank_opportunities(items, ranking)}


@app.get("/api/opportunities/{opp_id}")
def opportunity_detail(opp_id: str, db: Session = Depends(get_db)):
    opp = db.get(StartupOpportunity, UUID(opp_id))
    if not opp:
        raise HTTPException(404, "not found")
    evaluations = db.scalars(
        select(Evaluation).where(Evaluation.opportunity_id == opp.id).order_by(Evaluation.version.desc())
    ).all()
    latest = evaluations[0] if evaluations else None
    factors = latest.factors if latest else []
    audit = db.scalars(select(QualityAudit).where(QualityAudit.opportunity_id == opp.id).order_by(QualityAudit.created_at.desc())).first()
    competitors = db.scalars(select(CompetitorResearch).where(CompetitorResearch.opportunity_id == opp.id)).all()
    evidence = db.scalars(
        select(EvidenceLink).where(EvidenceLink.subject_id == opp.id, EvidenceLink.invalidated.is_(False))
    ).all()
    history = db.scalars(select(ScoreHistory).where(ScoreHistory.opportunity_id == opp.id)).all()
    clusters = []
    for link in opp.links:
        cluster = db.get(ProblemCluster, link.cluster_id)
        if cluster:
            clusters.append(cluster_out(cluster))
    return {
        "dataset": "synthetic_labeled",
        "opportunity": opportunity_out(opp),
        "clusters": clusters,
        "factors": [
            {
                "criterion": f.criterion,
                "weight": f.weight,
                "score": f.score,
                "status": f.status,
                "confidence": f.confidence,
                "explanation": f.explanation,
                "evidence": f.evidence,
                "contradictions": f.contradictions,
                "missing": f.missing,
            }
            for f in factors
        ],
        "audit": {
            "status": audit.status if audit else None,
            "risks": audit.risks if audit else [],
            "arguments_against": audit.arguments_against if audit else [],
            "missing_evidence": audit.missing_evidence if audit else [],
            "unsupported_claims": audit.unsupported_claims if audit else [],
            "validation_experiments": audit.validation_experiments if audit else [],
        },
        "competitors": [
            {
                "name": c.name,
                "kind": c.kind,
                "notes": c.notes,
                "source_url": c.source_url,
                "status": c.status,
            }
            for c in competitors
        ],
        "evidence": [
            {
                "claim": e.claim,
                "quote": e.quote,
                "source_url": e.source_url,
                "evidence_level": e.evidence_level,
                "polarity": e.polarity,
            }
            for e in evidence
        ],
        "score_history": [
            {
                "observed_quality_score": h.observed_quality_score,
                "research_completeness": h.research_completeness,
                "conservative_score": h.conservative_score,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "reason": h.reason,
            }
            for h in history
        ],
    }


@app.post("/api/opportunities/{opp_id}/bookmark")
def bookmark(opp_id: str, db: Session = Depends(get_db)):
    opp = db.get(StartupOpportunity, UUID(opp_id))
    if not opp:
        raise HTTPException(404, "not found")
    opp.bookmarked = not opp.bookmarked
    return {"bookmarked": opp.bookmarked}


@app.post("/api/opportunities/{opp_id}/reject")
def reject(opp_id: str, db: Session = Depends(get_db)):
    opp = db.get(StartupOpportunity, UUID(opp_id))
    if not opp:
        raise HTTPException(404, "not found")
    opp.rejected_by_user = True
    opp.research_status = "rejected"
    db.add(UserFeedback(opportunity_id=opp.id, kind="reject", body="user rejected"))
    return {"rejected": True}


@app.post("/api/opportunities/{opp_id}/notes")
def notes(opp_id: str, body: dict, db: Session = Depends(get_db)):
    opp = db.get(StartupOpportunity, UUID(opp_id))
    if not opp:
        raise HTTPException(404, "not found")
    db.add(UserFeedback(opportunity_id=opp.id, kind=body.get("kind", "note"), body=body.get("body", "")))
    return {"ok": True}


@app.get("/api/problems")
def list_problems(q: str | None = None, db: Session = Depends(get_db)):
    rows = db.scalars(select(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))).all()
    items = []
    for c in rows:
        item = cluster_out(c)
        links = db.scalars(select(OpportunityProblemLink).where(OpportunityProblemLink.cluster_id == c.id)).all()
        item["linked_opportunities"] = [str(link.opportunity_id) for link in links]
        if q:
            blob = f"{c.canonical_title} {c.description} {c.industry}".lower()
            if q.lower() not in blob:
                continue
        items.append(item)
    return {"dataset": "synthetic_labeled", "items": items}


@app.get("/api/problems/{cluster_id}")
def problem_detail(cluster_id: str, db: Session = Depends(get_db)):
    cluster = db.get(ProblemCluster, UUID(cluster_id))
    if not cluster:
        raise HTTPException(404, "not found")
    observations = [
        observation_out(m.observation)
        for m in cluster.memberships
        if m.active and m.observation.deleted_at is None
    ]
    links = db.scalars(select(OpportunityProblemLink).where(OpportunityProblemLink.cluster_id == cluster.id)).all()
    item = cluster_out(cluster)
    item["linked_opportunities"] = [str(link.opportunity_id) for link in links]
    return {"dataset": "synthetic_labeled", "problem": item, "observations": observations}


@app.get("/api/research/ops")
def research_ops(db: Session = Depends(get_db)):
    agents = {}
    for name in ("discovery", "extraction", "clustering", "opportunity", "quality"):
        last = db.scalars(select(AgentRun).where(AgentRun.agent_name == name).order_by(AgentRun.created_at.desc())).first()
        agents[name] = {
            "status": last.status if last else "idle",
            "last_run": last.created_at.isoformat() if last and last.created_at else None,
            "current_task": last.current_task if last else None,
            "completed_tasks": last.completed_tasks if last else 0,
            "errors": last.errors if last else 0,
            "tokens_used": last.tokens_used if last else 0,
            "estimated_cost": last.estimated_cost if last else 0,
        }
    jobs = db.scalars(select(ResearchJob).order_by(ResearchJob.created_at.desc()).limit(20)).all()
    runs = db.scalars(select(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(10)).all()
    return {
        "banner": "Synthetic research mode. Live social-media collection is not operational.",
        "paused": is_paused(db),
        "live_operational": live_operational(db),
        "agents": agents,
        "jobs": [{"id": str(j.id), "job_type": j.job_type, "status": j.status, "dedupe_key": j.dedupe_key} for j in jobs],
        "history": [
            {"id": str(r.id), "status": r.status, "trigger": r.trigger, "finished_at": r.finished_at.isoformat() if r.finished_at else None}
            for r in runs
        ],
        "source_api": {
            "reddit": "disabled",
            "x": "disabled",
            "tavily": "optional",
        },
    }


@app.post("/api/research/run")
def trigger_run(db: Session = Depends(get_db)):
    run = run_full_pipeline(db, trigger="manual")
    return {"id": str(run.id), "status": run.status, "stats": run.stats, "dataset": "synthetic_labeled"}


@app.post("/api/research/pause")
def pause(db: Session = Depends(get_db)):
    set_paused(db, True)
    return {"paused": True}


@app.post("/api/research/resume")
def resume(db: Session = Depends(get_db)):
    set_paused(db, False)
    return {"paused": False}


@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    queries = db.scalars(select(SearchQuery)).all()
    profile = db.scalar(select(FounderProfile).where(FounderProfile.active.is_(True)))
    policies = db.scalars(select(PlatformRetentionPolicy)).all()
    budgets = db.scalars(select(BudgetAccount)).all()
    return {
        "research_paused": is_paused(db),
        "live_collection_operational": live_operational(db),
        "credentials_configured": {
            "reddit": bool(settings.reddit_client_id),
            "x": bool(settings.x_bearer_token),
            "llm": bool(settings.llm_api_key),
            "tavily": bool(settings.tavily_api_key),
        },
        "search_queries": [
            {"id": str(q.id), "platform": q.platform, "query": q.query, "community": q.community, "enabled": q.enabled}
            for q in queries
        ],
        "founder_profile": {
            "background": profile.background if profile else None,
            "skills": profile.skills if profile else [],
            "interests": profile.interests if profile else [],
            "location": profile.location if profile else None,
        },
        "budgets": [
            {
                "name": b.name,
                "period": b.period,
                "limit_amount": b.limit_amount,
                "reserved": b.reserved,
                "actual": b.actual,
                "provider_billed": b.provider_billed,
                "paused": b.paused,
            }
            for b in budgets
        ],
        "retention_policies": [
            {
                "platform": p.platform,
                "rule_type": p.rule_type,
                "value": p.value,
                "source_of_rule": p.source_of_rule,
                "confirmed_by_operator": p.confirmed_by_operator,
            }
            for p in policies
        ],
        "note": "Secrets are never returned. Budget actuals are estimates, not provider invoices.",
    }


@app.post("/api/settings/queries")
def add_query(body: dict, db: Session = Depends(get_db)):
    q = SearchQuery(
        platform=body.get("platform", "reddit"),
        query=body.get("query", ""),
        community=body.get("community"),
        enabled=True,
    )
    db.add(q)
    db.flush()
    return {"id": str(q.id)}


@app.get("/api/export/opportunities")
def export_opportunities(db: Session = Depends(get_db)):
    rows = db.scalars(select(StartupOpportunity)).all()
    return {"dataset": "synthetic_labeled", "items": [opportunity_out(o) for o in rows]}
