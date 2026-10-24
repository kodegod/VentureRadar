from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.tavily import TavilyConnector
from app.models import (
    AgentRun,
    CompetitorResearch,
    Evaluation,
    EvaluationFactor,
    EvidenceLink,
    FounderProfile,
    OpportunityProblemLink,
    ProblemCluster,
    QualityAudit,
    ScoreHistory,
    StartupOpportunity,
    ThresholdDecision,
)
from app.scoring.engine import DEFAULT_WEIGHTS, compute_scores
from app.scoring.founder_fit import score_founder_fit
from app.scoring.thresholds import decide_threshold
from app.services.budget import BudgetRejected, reconcile, release, reserve


def run_opportunity(db: Session, run_id: uuid.UUID) -> dict:
    agent = AgentRun(research_run_id=run_id, agent_name="opportunity", status="running", current_task="evaluate")
    db.add(agent)
    db.flush()
    created = 0
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))).all()
    for cluster in clusters:
        existing_link = db.scalar(select(OpportunityProblemLink).where(OpportunityProblemLink.cluster_id == cluster.id))
        if existing_link:
            continue
        live = [m.observation for m in cluster.memberships if m.active and m.observation.deleted_at is None]
        independents = [o for o in live if not o.is_duplicate]
        decision = decide_threshold(
            independent_observation_count=cluster.independent_observation_count,
            severity_score=cluster.severity_score,
            max_observation_severity=max((o.severity_score or 0) for o in independents) if independents else None,
            has_workaround=any(o.workaround for o in independents),
            has_named_tool=any(o.tools_mentioned for o in independents),
            has_time_or_money=any(o.time_or_money for o in independents),
            buying_intents=[o.buying_intent for o in independents],
        )
        db.add(
            ThresholdDecision(
                cluster_id=cluster.id,
                decision=decision["decision"],
                reasons=decision["reasons"],
            )
        )
        if decision["decision"] == "skip":
            continue
        _create_opportunity(db, cluster, independents, decision["decision"] == "provisional")
        created += 1

    agent.status = "completed"
    agent.completed_tasks = created
    agent.finished_at = datetime.now(timezone.utc)
    agent.current_task = None
    db.flush()
    return {"opportunities_created": created}


def _create_opportunity(db: Session, cluster: ProblemCluster, observations: list, provisional: bool) -> StartupOpportunity:
    name = {
        "weekly_reports": "FridayPack",
        "recruiting_inbox": "InboxRank",
        "invoice_chasing": "ChaseLite",
        "saas_seat_waste": "SeatReclaim",
        "password_reset": "ResetDesk",
        "crm_data_entry": "CallToCRM",
        "month_end_close": "CloseLane",
    }.get(observations[0].workflow if observations else "", cluster.canonical_title[:40].replace(" ", ""))

    opp = StartupOpportunity(
        working_name=name,
        one_line_pitch=f"Help {cluster.customer_segment or 'teams'} with {cluster.canonical_title.lower()}",
        description=cluster.description,
        target_customer=cluster.customer_segment or "unknown",
        customer_problem=cluster.canonical_title,
        proposed_solution="A focused workflow product that automates the painful steps customers already describe.",
        unique_value_proposition="Built around stated workarounds rather than a generic suite.",
        why_now="Recurring public complaints describe hours lost and existing tools that do not cover the last mile.",
        business_model="B2B SaaS subscription",
        pricing_approach="Assumption: seat or workspace pricing — not observed",
        industry=cluster.industry,
        mvp={
            "smallest_useful_product": "One happy-path automation for the stated weekly workflow",
            "capabilities": ["ingest existing exports", "apply saved mapping", "deliver a pack", "show exceptions"],
            "implementation_difficulty": "moderate",
            "technical_dependencies": ["Python", "TypeScript", "connectors"],
            "fastest_validation": "Paid concierge on 5 teams using their real Friday/inbox/AR workflow",
        },
        critical_assumptions=[
            "The people posting are buyers or can reach buyers",
            "Existing suites will not ship this last-mile workflow soon",
        ],
        unknowns=["market size", "true willingness to pay"],
        is_provisional=provisional,
        research_status="provisional" if provisional else "evaluated",
        data_origin=cluster.data_origin,
        is_synthetic=cluster.is_synthetic,
    )
    db.add(opp)
    db.flush()
    db.add(OpportunityProblemLink(opportunity_id=opp.id, cluster_id=cluster.id))

    for obs in observations:
        db.add(
            EvidenceLink(
                subject_type="startup_opportunity",
                subject_id=opp.id,
                source_post_id=obs.source_post_id,
                observation_id=obs.id,
                claim=obs.title,
                quote=obs.source_span,
                source_url=obs.source_url,
                evidence_level="opinion" if not obs.time_or_money else "workaround",
                polarity="supports",
            )
        )

    tavily_hits: list[dict] = []
    tavily = TavilyConnector()
    if tavily.is_enabled():
        try:
            reservation = reserve(
                db,
                name="tavily",
                period="daily",
                estimated=0.008,
                ceiling=0.02,
                purpose="competitor_search",
                idempotency_key=f"tavily:{opp.id}",
            )
            tavily_hits = tavily.search(f"{cluster.canonical_title} software alternatives")
            reconcile(db, reservation, actual=0.008 if tavily_hits else 0.0)
        except BudgetRejected:
            tavily_hits = []
        except Exception:
            try:
                release(db, reservation)
            except Exception:
                pass
            tavily_hits = []

    if tavily_hits:
        for hit in tavily_hits[:5]:
            db.add(
                CompetitorResearch(
                    opportunity_id=opp.id,
                    name=hit["title"][:120],
                    kind="web",
                    notes=hit.get("content") or "",
                    source_url=hit["url"],
                    status="researched",
                    data_origin="live",
                )
            )
    else:
        mentioned = sorted({tool for obs in observations for tool in (obs.tools_mentioned or [])})
        if mentioned:
            for tool in mentioned:
                db.add(
                    CompetitorResearch(
                        opportunity_id=opp.id,
                        name=tool,
                        kind="mentioned_workaround",
                        notes="Named in social posts as an existing tool or workaround. Not independently verified.",
                        source_url=observations[0].source_url,
                        status="mentioned_only",
                        data_origin=cluster.data_origin,
                    )
                )
        else:
            db.add(
                CompetitorResearch(
                    opportunity_id=opp.id,
                    name="unresearched",
                    kind="market",
                    notes="Tavily not configured. Market and competitor factors left unresearched.",
                    source_url=None,
                    status="unresearched",
                    data_origin=cluster.data_origin,
                )
            )

    factors = _draft_factors(cluster, observations, tavily_hits)
    metrics = compute_scores(factors)
    profile = db.scalar(select(FounderProfile).where(FounderProfile.active.is_(True)))
    founder = score_founder_fit(
        industry=cluster.industry,
        target_customer=cluster.customer_segment,
        proposed_solution=opp.proposed_solution,
        mvp_difficulty="saas automation",
        profile={
            "skills": profile.skills if profile else None,
            "interests": profile.interests if profile else None,
        }
        if profile
        else None,
    )
    opp.observed_quality_score = metrics["observed_quality_score"]
    opp.research_completeness = metrics["research_completeness"]
    opp.conservative_score = metrics["conservative_score"]
    opp.conservative_score_kind = "heuristic"
    opp.evidence_confidence = metrics["evidence_confidence"]
    opp.founder_fit_score = founder

    evaluation = Evaluation(
        opportunity_id=opp.id,
        version=1,
        scoring_version=metrics["scoring_version"],
        observed_quality_score=metrics["observed_quality_score"],
        research_completeness=metrics["research_completeness"],
        conservative_score=metrics["conservative_score"],
        conservative_score_kind="heuristic",
        evidence_confidence=metrics["evidence_confidence"],
        founder_fit_score=founder,
    )
    db.add(evaluation)
    db.flush()
    for factor in factors:
        db.add(
            EvaluationFactor(
                evaluation_id=evaluation.id,
                criterion=factor["criterion"],
                weight=factor["weight"],
                score=factor["score"],
                status=factor["status"],
                confidence=factor.get("confidence"),
                explanation=factor.get("explanation") or "",
                evidence=factor.get("evidence") or [],
                contradictions=factor.get("contradictions") or [],
                missing=factor.get("missing") or [],
            )
        )
    db.add(
        ScoreHistory(
            opportunity_id=opp.id,
            scoring_version=metrics["scoring_version"],
            observed_quality_score=metrics["observed_quality_score"],
            research_completeness=metrics["research_completeness"],
            conservative_score=metrics["conservative_score"],
            evidence_confidence=metrics["evidence_confidence"],
            founder_fit_score=founder,
            reason="initial_evaluation",
        )
    )
    db.flush()
    return opp


def _draft_factors(cluster: ProblemCluster, observations: list, tavily_hits: list[dict]) -> list[dict]:
    weights = DEFAULT_WEIGHTS
    intents = {o.buying_intent for o in observations}
    contradictions = []
    if cluster.canonical_title.lower().find("report") >= 0:
        pass
    negative_quotes = [
        o.description
        for o in observations
        if "work fine" in (o.description or "").lower() or "would not pay" in (o.description or "").lower()
    ]
    # Negative evidence lives on general_complaint posts, not genuine observations.
    # Attach cluster-level contradictions from related non-genuine posts via description keywords in cluster desc — handled in quality agent.

    wtp_score = None
    wtp_status = "unknown"
    if "committed" in intents:
        wtp_score, wtp_status = 5, "scored"
    elif "strong" in intents:
        wtp_score, wtp_status = 4, "scored"
    elif "moderate" in intents:
        wtp_score, wtp_status = 3, "scored"
    elif observations:
        wtp_score, wtp_status = 2, "scored"

    tools = {t for o in observations for t in (o.tools_mentioned or [])}
    dissatisfaction = 3 if any(o.workaround for o in observations) else None
    dissatisfaction_status = "scored" if dissatisfaction else "unknown"
    if any("hate" in (o.description or "").lower() for o in observations):
        dissatisfaction = 4
        dissatisfaction_status = "scored"

    competitive_score = None
    competitive_status = "unresearched"
    competitive_missing = ["independent competitor research"]
    if tavily_hits:
        competitive_score = 3
        competitive_status = "scored"
        competitive_missing = []
    elif tools:
        competitive_score = 3
        competitive_status = "scored"
        competitive_missing = ["Tavily not configured; scored only from named tools in posts"]

    market_score = 3 if tavily_hits else None
    market_status = "scored" if tavily_hits else "unresearched"

    demand_score = None
    demand_status = "unknown"
    demand_missing = ["comparable collection windows"]
    if cluster.trend in {"up", "flat", "down"}:
        demand_score = {"up": 4, "flat": 3, "down": 2}[cluster.trend]
        demand_status = "scored"
        demand_missing = []

    return [
        {
            "criterion": "problem_severity",
            "weight": weights["problem_severity"],
            "score": cluster.severity_score if cluster.severity_score else None,
            "status": "scored" if cluster.severity_score else "unknown",
            "confidence": 0.7,
            "explanation": "Rolled up from independent observations; hours/money raise severity.",
            "evidence": [o.source_url for o in observations if o.severity_score],
            "contradictions": contradictions,
            "missing": [],
        },
        {
            "criterion": "willingness_to_pay",
            "weight": weights["willingness_to_pay"],
            "score": wtp_score,
            "status": wtp_status,
            "confidence": 0.62,
            "explanation": "From stated buying-intent language only. Upvotes are ignored.",
            "evidence": [o.source_url for o in observations if o.buying_intent not in (None, "none")],
            "contradictions": negative_quotes[:3],
            "missing": ["actual payments"],
        },
        {
            "criterion": "market_potential",
            "weight": weights["market_potential"],
            "score": market_score,
            "status": market_status,
            "confidence": 0.55 if tavily_hits else None,
            "explanation": "Source-backed web research only. Unresearched without Tavily.",
            "evidence": [h["url"] for h in tavily_hits],
            "contradictions": [],
            "missing": [] if tavily_hits else ["authorized web research"],
        },
        {
            "criterion": "existing_solution_dissatisfaction",
            "weight": weights["existing_solution_dissatisfaction"],
            "score": dissatisfaction,
            "status": dissatisfaction_status,
            "confidence": 0.65 if dissatisfaction else None,
            "explanation": "Workarounds and explicit dislike of current tools.",
            "evidence": [o.source_url for o in observations if o.workaround],
            "contradictions": [],
            "missing": [] if dissatisfaction else ["workaround evidence"],
        },
        {
            "criterion": "competitive_opportunity",
            "weight": weights["competitive_opportunity"],
            "score": competitive_score,
            "status": competitive_status,
            "confidence": 0.5 if competitive_score else None,
            "explanation": "Named tools in posts or Tavily results. No invented prices.",
            "evidence": [o.source_url for o in observations if o.tools_mentioned],
            "contradictions": [],
            "missing": competitive_missing,
        },
        {
            "criterion": "customer_accessibility",
            "weight": weights["customer_accessibility"],
            "score": 4 if observations else None,
            "status": "scored" if observations else "unknown",
            "confidence": 0.6,
            "explanation": "Customers are posting in public professional communities. That is reachability, not a distribution plan.",
            "evidence": [o.source_url for o in observations[:3]],
            "contradictions": [],
            "missing": ["outbound experiment"],
        },
        {
            "criterion": "growing_demand",
            "weight": weights["growing_demand"],
            "score": demand_score,
            "status": demand_status,
            "confidence": 0.45 if demand_score else None,
            "explanation": "Uses normalized observation rate on comparable windows only.",
            "evidence": [],
            "contradictions": [],
            "missing": demand_missing,
        },
        {
            "criterion": "mvp_feasibility",
            "weight": weights["mvp_feasibility"],
            "score": 4,
            "status": "scored",
            "confidence": 0.7,
            "explanation": "Workflow automation fits a Python/TypeScript SaaS MVP. This is not founder-fit.",
            "evidence": [],
            "contradictions": [],
            "missing": [],
        },
    ]
