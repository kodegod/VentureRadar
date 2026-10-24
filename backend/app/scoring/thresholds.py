from __future__ import annotations

from typing import Any

DEMAND_INTENTS = {"moderate", "strong", "committed"}


def decide_threshold(
    *,
    independent_observation_count: int,
    severity_score: int | None,
    max_observation_severity: int | None,
    has_workaround: bool,
    has_named_tool: bool,
    has_time_or_money: bool,
    buying_intents: list[str],
    min_independent: int = 3,
    min_severity: int = 3,
    high_severity: int = 4,
) -> dict[str, Any]:
    intents = set(buying_intents)
    demand_hits = sum(
        [
            has_workaround,
            has_named_tool,
            has_time_or_money,
            bool(intents & DEMAND_INTENTS),
        ]
    )
    severity_ok = (severity_score is not None and severity_score >= min_severity) or (
        max_observation_severity is not None and max_observation_severity >= high_severity
    )
    reasons: list[str] = []

    if independent_observation_count >= min_independent and severity_ok and demand_hits >= 2:
        return {"decision": "qualified", "reasons": ["independent>=3", "severity_ok", f"demand_indicators={demand_hits}"]}

    high_intent = bool(intents & {"strong", "committed"})
    high_sev = (severity_score is not None and severity_score >= high_severity) or (
        max_observation_severity is not None and max_observation_severity >= high_severity
    )
    if independent_observation_count >= 1 and (high_sev or high_intent):
        if not severity_ok:
            reasons.append("severity_below_qualified")
        if independent_observation_count < min_independent:
            reasons.append("independent<3")
        if demand_hits < 2:
            reasons.append("demand_indicators<2")
        return {"decision": "provisional", "reasons": reasons or ["exceptional_weak_support"]}

    reasons.append("below_threshold")
    return {"decision": "skip", "reasons": reasons}
