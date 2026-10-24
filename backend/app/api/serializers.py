from __future__ import annotations

from app.models import ProblemCluster, ProblemObservation, StartupOpportunity
from app.scoring.ranking import is_verified


def opportunity_out(o: StartupOpportunity) -> dict:
    payload = {
        "id": str(o.id),
        "working_name": o.working_name,
        "one_line_pitch": o.one_line_pitch,
        "description": o.description,
        "target_customer": o.target_customer,
        "customer_problem": o.customer_problem,
        "proposed_solution": o.proposed_solution,
        "unique_value_proposition": o.unique_value_proposition,
        "why_now": o.why_now,
        "business_model": o.business_model,
        "pricing_approach": o.pricing_approach,
        "industry": o.industry,
        "mvp": o.mvp,
        "critical_assumptions": o.critical_assumptions,
        "unknowns": o.unknowns,
        "observed_quality_score": o.observed_quality_score,
        "research_completeness": o.research_completeness,
        "conservative_score": o.conservative_score,
        "conservative_score_kind": o.conservative_score_kind,
        "evidence_confidence": o.evidence_confidence,
        "founder_fit_score": o.founder_fit_score,
        "research_status": o.research_status,
        "is_provisional": o.is_provisional,
        "quality_status": o.quality_status,
        "evaluation_stale": o.evaluation_stale,
        "bookmarked": o.bookmarked,
        "data_origin": o.data_origin,
        "is_synthetic": o.is_synthetic,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
        "trend": o.links[0].cluster.trend if o.links else "insufficient_comparable_data",
        "observation_count": o.links[0].cluster.independent_observation_count if o.links else 0,
    }
    payload["verified"] = is_verified(payload)
    return payload


def cluster_out(c: ProblemCluster) -> dict:
    return {
        "id": str(c.id),
        "canonical_title": c.canonical_title,
        "description": c.description,
        "customer_segment": c.customer_segment,
        "industry": c.industry,
        "severity_score": c.severity_score,
        "frequency": c.frequency,
        "independent_observation_count": c.independent_observation_count,
        "reddit_evidence_count": c.reddit_evidence_count,
        "x_evidence_count": c.x_evidence_count,
        "workarounds": c.workarounds,
        "first_observed": c.first_observed.isoformat() if c.first_observed else None,
        "last_observed": c.last_observed.isoformat() if c.last_observed else None,
        "trend": c.trend,
        "data_origin": c.data_origin,
        "is_synthetic": c.is_synthetic,
        "linked_opportunities": [str(link.opportunity_id) for link in c.memberships[:0]],
    }


def observation_out(o: ProblemObservation) -> dict:
    return {
        "id": str(o.id),
        "title": o.title,
        "description": o.description,
        "relevance_class": o.relevance_class,
        "severity_score": o.severity_score,
        "buying_intent": o.buying_intent,
        "workaround": o.workaround,
        "tools_mentioned": o.tools_mentioned,
        "time_or_money": o.time_or_money,
        "source_span": o.source_span,
        "source_url": o.source_url,
        "is_duplicate": o.is_duplicate,
        "data_origin": o.data_origin,
        "is_synthetic": o.is_synthetic,
    }
