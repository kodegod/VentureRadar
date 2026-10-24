from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AppSetting, BudgetAccount, FounderProfile, PlatformRetentionPolicy, SearchQuery

DEFAULT_QUERIES = [
    ("reddit", "I wish there was", "smallbusiness"),
    ("reddit", "I do this manually", "SaaS"),
    ("reddit", "Takes me hours", "sysadmin"),
    ("reddit", "Looking for software", "recruiting"),
    ("reddit", "Frustrated with", "sales"),
    ("reddit", "Too expensive", "Accounting"),
    ("reddit", "There must be a better way", "Entrepreneur"),
    ("x", '"I wish there was" lang:en -is:retweet', None),
    ("x", '"I do this manually" lang:en -is:retweet', None),
]


def bootstrap(db: Session) -> None:
    if db.scalar(select(FounderProfile).where(FounderProfile.active.is_(True))) is None:
        db.add(
            FounderProfile(
                name="default",
                background="Software engineering; Python and TypeScript; AI/LLM applications",
                skills=["python", "javascript", "typescript", "ai", "llm"],
                interests=["saas", "ai agents", "automation", "b2b"],
                location="India",
                active=True,
            )
        )

    if db.scalar(select(SearchQuery.id)) is None:
        for platform, query, community in DEFAULT_QUERIES:
            db.add(SearchQuery(platform=platform, query=query, community=community, enabled=True))

    accounts = [
        ("llm", "daily", settings.budget_llm_daily),
        ("llm", "monthly", settings.budget_llm_monthly),
        ("tavily", "daily", settings.budget_tavily_daily),
        ("tavily", "monthly", settings.budget_tavily_monthly),
        ("x", "daily", settings.budget_x_daily),
        ("x", "monthly", settings.budget_x_monthly),
        ("reddit", "daily", 0.0),
        ("reddit", "monthly", 0.0),
    ]
    for name, period, limit in accounts:
        existing = db.scalar(select(BudgetAccount).where(BudgetAccount.name == name, BudgetAccount.period == period))
        if existing is None:
            db.add(
                BudgetAccount(
                    name=name,
                    period=period,
                    limit_amount=limit,
                    period_start=datetime.now(timezone.utc),
                )
            )

    policies = [
        (
            "reddit",
            "delete_on_source_deletion",
            "required",
            "Reddit Data API Wiki: remove stored content and author IDs when Reddit deletes the post/comment/account. Anonymized retention of deleted content is a violation.",
        ),
        (
            "reddit",
            "routine_wipe_recommendation",
            "48h_recommendation_only",
            "Reddit recommends routine deletion of stored user data within 48 hours. This is a recommendation, not a hardcoded obligation. Override from the approved Data API agreement.",
        ),
        (
            "x",
            "sync_with_live_state",
            "required",
            "X Developer Policy: stored content must track live state (deleted, protected, suspended, withheld). Act as soon as reasonably possible, or within 24 hours of a request from X or the account owner.",
        ),
        (
            "synthetic",
            "no_platform_deletion_duty",
            "n/a",
            "Synthetic fixtures have no platform deletion obligation.",
        ),
    ]
    for platform, rule_type, value, source in policies:
        exists = db.scalar(
            select(PlatformRetentionPolicy).where(
                PlatformRetentionPolicy.platform == platform,
                PlatformRetentionPolicy.rule_type == rule_type,
            )
        )
        if exists is None:
            db.add(
                PlatformRetentionPolicy(
                    platform=platform,
                    rule_type=rule_type,
                    value=value,
                    source_of_rule=source,
                    confirmed_by_operator=False,
                )
            )

    defaults = {
        "research_paused": settings.research_paused,
        "live_collection_enabled": False,
        "live_smoke_test_passed": False,
        "dataset_disclaimer": "dataset=synthetic_labeled",
    }
    for key, value in defaults.items():
        if db.scalar(select(AppSetting).where(AppSetting.key == key)) is None:
            db.add(AppSetting(key=key, value={"value": value}))

    db.flush()


def is_paused(db: Session) -> bool:
    row = db.scalar(select(AppSetting).where(AppSetting.key == "research_paused"))
    if row is None:
        return settings.research_paused
    return bool(row.value.get("value"))


def set_paused(db: Session, paused: bool) -> None:
    row = db.scalar(select(AppSetting).where(AppSetting.key == "research_paused"))
    if row is None:
        db.add(AppSetting(key="research_paused", value={"value": paused}))
    else:
        row.value = {"value": paused}
    db.flush()


def live_operational(db: Session) -> bool:
    enabled = db.scalar(select(AppSetting).where(AppSetting.key == "live_collection_enabled"))
    smoke = db.scalar(select(AppSetting).where(AppSetting.key == "live_smoke_test_passed"))
    return bool(enabled and enabled.value.get("value") and smoke and smoke.value.get("value"))
