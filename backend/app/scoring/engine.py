from __future__ import annotations

from typing import Any

DEFAULT_WEIGHTS: dict[str, float] = {
    "problem_severity": 0.20,
    "willingness_to_pay": 0.20,
    "market_potential": 0.15,
    "existing_solution_dissatisfaction": 0.10,
    "competitive_opportunity": 0.10,
    "customer_accessibility": 0.10,
    "growing_demand": 0.10,
    "mvp_feasibility": 0.05,
}

SCORING_VERSION = "2"


def compute_scores(factors: list[dict[str, Any]], weights: dict[str, float] | None = None) -> dict[str, Any]:
    """Deterministic three-metric scoring. Unknowns stay null; never impute 3."""
    weights = weights or DEFAULT_WEIGHTS
    known_weight = 0.0
    weighted_sum = 0.0
    confidences: list[float] = []

    for factor in factors:
        criterion = factor["criterion"]
        weight = float(factor.get("weight", weights.get(criterion, 0.0)))
        score = factor.get("score")
        if score is None:
            continue
        known_weight += weight
        weighted_sum += (float(score) / 5.0) * weight
        if factor.get("confidence") is not None:
            confidences.append(float(factor["confidence"]))

    completeness = known_weight / 1.00
    if known_weight == 0:
        observed = None
        conservative = None
    else:
        observed = round((weighted_sum / known_weight) * 100, 2)
        conservative = round(weighted_sum * 100, 2)

    evidence_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

    return {
        "observed_quality_score": observed,
        "research_completeness": round(completeness, 4),
        "conservative_score": conservative,
        "conservative_score_kind": "heuristic",
        "evidence_confidence": evidence_confidence,
        "known_weight": round(known_weight, 4),
        "scoring_version": SCORING_VERSION,
    }
