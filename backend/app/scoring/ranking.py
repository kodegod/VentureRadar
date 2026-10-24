from __future__ import annotations

from typing import Any

VERIFIED_MIN_COMPLETENESS = 0.70
VERIFIED_MIN_CONFIDENCE = 0.60
PASSING_AUDITS = {"passed", "passed_with_limitations"}


def is_verified(item: dict[str, Any]) -> bool:
    completeness = item.get("research_completeness") or 0
    confidence = item.get("evidence_confidence") or 0
    status = item.get("quality_status")
    return (
        completeness >= VERIFIED_MIN_COMPLETENESS
        and confidence >= VERIFIED_MIN_CONFIDENCE
        and status in PASSING_AUDITS
        and not item.get("rejected_by_user")
        and not item.get("is_provisional")
        and status != "rejected"
    )


def rank_opportunities(items: list[dict[str, Any]], mode: str = "highest_opportunity") -> list[dict[str, Any]]:
    def key_observed(o: dict[str, Any]) -> float:
        return o.get("observed_quality_score") or -1

    if mode == "verified":
        return sorted([o for o in items if is_verified(o)], key=key_observed, reverse=True)
    if mode == "highest_opportunity":
        verified = sorted([o for o in items if is_verified(o)], key=key_observed, reverse=True)
        rest = sorted([o for o in items if not is_verified(o)], key=key_observed, reverse=True)
        return verified + rest
    if mode == "highest_confidence":
        return sorted(items, key=lambda o: o.get("evidence_confidence") or 0, reverse=True)
    if mode == "best_founder_fit":
        return sorted(items, key=lambda o: o.get("founder_fit_score") or 0, reverse=True)
    if mode == "fastest_growing":
        growing = [o for o in items if o.get("trend") == "up"]
        return sorted(growing, key=key_observed, reverse=True)
    if mode == "recently_discovered":
        return sorted(items, key=lambda o: o.get("created_at") or "", reverse=True)
    if mode == "strongest_commercial_evidence":
        return sorted(items, key=lambda o: o.get("commercial_signal") or 0, reverse=True)
    if mode == "provisional":
        return [o for o in items if o.get("is_provisional") or not is_verified(o)]
    return items
