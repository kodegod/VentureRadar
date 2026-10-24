from __future__ import annotations

DEFAULT_PROFILE = {
    "background": "Software engineering",
    "skills": ["python", "javascript", "typescript", "ai", "llm"],
    "interests": ["saas", "ai agents", "automation", "b2b"],
    "location": "India",
}


def score_founder_fit(
    *,
    industry: str | None,
    target_customer: str | None,
    proposed_solution: str | None,
    mvp_difficulty: str | None = None,
    profile: dict | None = None,
) -> float:
    """Separate 0-100 score. Never blended into market attractiveness."""
    profile = profile or DEFAULT_PROFILE
    text = " ".join(filter(None, [industry, target_customer, proposed_solution, mvp_difficulty])).lower()
    score = 40.0
    skills = [s.lower() for s in profile.get("skills", [])]
    interests = [s.lower() for s in profile.get("interests", [])]
    hits = sum(1 for token in skills + interests if token in text)
    score += min(40.0, hits * 8.0)
    if any(word in text for word in ("saas", "b2b", "automat", "agent", "workflow")):
        score += 12.0
    if any(word in text for word in ("hardware", "biotech", "clinic", "regulated pharma")):
        score -= 20.0
    return max(0.0, min(100.0, round(score, 2)))
