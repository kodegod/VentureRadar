import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SourcePost(Base, TimestampMixin):
    __tablename__ = "source_posts"
    __table_args__ = (UniqueConstraint("platform", "external_id", name="uq_source_posts_platform_ext"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str] = mapped_column(String(128), index=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    community: Mapped[str | None] = mapped_column(String(128), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    engagement: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    data_origin: Mapped[str] = mapped_column(String(16), default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deletion_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)

    comments: Mapped[list["SourceComment"]] = relationship(back_populates="post")
    observations: Mapped[list["ProblemObservation"]] = relationship(back_populates="source_post")


class SourceComment(Base, TimestampMixin):
    __tablename__ = "source_comments"
    __table_args__ = (UniqueConstraint("platform", "external_id", name="uq_source_comments_platform_ext"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("source_posts.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(32))
    external_id: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_origin: Mapped[str] = mapped_column(String(16), default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deletion_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)

    post: Mapped[SourcePost] = relationship(back_populates="comments")


class SearchQuery(Base, TimestampMixin):
    __tablename__ = "search_queries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    platform: Mapped[str] = mapped_column(String(32))
    query: Mapped[str] = mapped_column(Text)
    community: Mapped[str | None] = mapped_column(String(128), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_cursor: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ResearchRun(Base, TimestampMixin):
    __tablename__ = "research_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    status: Mapped[str] = mapped_column(String(32), default="running")
    trigger: Mapped[str] = mapped_column(String(32), default="manual")
    data_origin: Mapped[str] = mapped_column(String(16), default="synthetic")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProblemObservation(Base, TimestampMixin):
    __tablename__ = "problem_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    source_post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_posts.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    target_customer: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    workflow: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_class: Mapped[str] = mapped_column(String(32))
    severity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    workaround: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools_mentioned: Mapped[list[str]] = mapped_column(JSONType, default=list)
    time_or_money: Mapped[str | None] = mapped_column(Text, nullable=True)
    buying_intent: Mapped[str] = mapped_column(String(16), default="none")
    source_span: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    unknowns: Mapped[list[str]] = mapped_column(JSONType, default=list)
    author_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problem_observations.id"), nullable=True
    )
    data_origin: Mapped[str] = mapped_column(String(16), default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_post: Mapped[SourcePost | None] = relationship(back_populates="observations")
    memberships: Mapped[list["ClusterMembership"]] = relationship(back_populates="observation")


class ProblemCluster(Base, TimestampMixin):
    __tablename__ = "problem_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    canonical_title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    customer_segment: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    independent_observation_count: Mapped[int] = mapped_column(Integer, default=0)
    reddit_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    x_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    workarounds: Mapped[list[str]] = mapped_column(JSONType, default=list)
    first_observed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_observed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trend: Mapped[str] = mapped_column(String(32), default="insufficient_comparable_data")
    data_origin: Mapped[str] = mapped_column(String(16), default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[list["ClusterMembership"]] = relationship(back_populates="cluster")


class ClusterMembership(Base, TimestampMixin):
    __tablename__ = "cluster_memberships"
    __table_args__ = (UniqueConstraint("cluster_id", "observation_id", "version", name="uq_membership"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    cluster_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("problem_clusters.id", ondelete="CASCADE"))
    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problem_observations.id", ondelete="CASCADE")
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    cluster: Mapped[ProblemCluster] = relationship(back_populates="memberships")
    observation: Mapped[ProblemObservation] = relationship(back_populates="memberships")


class StartupOpportunity(Base, TimestampMixin):
    __tablename__ = "startup_opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    working_name: Mapped[str] = mapped_column(String(128))
    one_line_pitch: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    target_customer: Mapped[str] = mapped_column(Text)
    customer_problem: Mapped[str] = mapped_column(Text)
    proposed_solution: Mapped[str] = mapped_column(Text)
    unique_value_proposition: Mapped[str] = mapped_column(Text)
    why_now: Mapped[str] = mapped_column(Text)
    business_model: Mapped[str] = mapped_column(Text)
    pricing_approach: Mapped[str] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mvp: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    critical_assumptions: Mapped[list[str]] = mapped_column(JSONType, default=list)
    unknowns: Mapped[list[str]] = mapped_column(JSONType, default=list)
    observed_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    research_completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    conservative_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conservative_score_kind: Mapped[str] = mapped_column(String(32), default="heuristic")
    evidence_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    founder_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    research_status: Mapped[str] = mapped_column(String(32), default="draft")
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evaluation_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
    rejected_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    data_origin: Mapped[str] = mapped_column(String(16), default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    scoring_version: Mapped[str] = mapped_column(String(16), default="2")

    links: Mapped[list["OpportunityProblemLink"]] = relationship(back_populates="opportunity")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="opportunity")
    audits: Mapped[list["QualityAudit"]] = relationship(back_populates="opportunity")


class OpportunityProblemLink(Base, TimestampMixin):
    __tablename__ = "opportunity_problem_links"
    __table_args__ = (UniqueConstraint("opportunity_id", "cluster_id", name="uq_opp_cluster"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("startup_opportunities.id", ondelete="CASCADE")
    )
    cluster_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("problem_clusters.id", ondelete="CASCADE"))

    opportunity: Mapped[StartupOpportunity] = relationship(back_populates="links")
    cluster: Mapped[ProblemCluster] = relationship()


class CompetitorResearch(Base, TimestampMixin):
    __tablename__ = "competitor_research"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("startup_opportunities.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(256))
    kind: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="unresearched")
    data_origin: Mapped[str] = mapped_column(String(16), default="synthetic")


class EvidenceLink(Base, TimestampMixin):
    __tablename__ = "evidence_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    subject_type: Mapped[str] = mapped_column(String(64), index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    source_post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_posts.id", ondelete="SET NULL"), nullable=True
    )
    observation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problem_observations.id", ondelete="SET NULL"), nullable=True
    )
    claim: Mapped[str] = mapped_column(Text)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text)
    evidence_level: Mapped[str] = mapped_column(String(32), default="opinion")
    polarity: Mapped[str] = mapped_column(String(16), default="supports")
    invalidated: Mapped[bool] = mapped_column(Boolean, default=False)


class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("startup_opportunities.id", ondelete="CASCADE")
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    scoring_version: Mapped[str] = mapped_column(String(16), default="2")
    observed_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    research_completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    conservative_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conservative_score_kind: Mapped[str] = mapped_column(String(32), default="heuristic")
    evidence_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    founder_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stale: Mapped[bool] = mapped_column(Boolean, default=False)

    opportunity: Mapped[StartupOpportunity] = relationship(back_populates="evaluations")
    factors: Mapped[list["EvaluationFactor"]] = relationship(back_populates="evaluation")


class EvaluationFactor(Base, TimestampMixin):
    __tablename__ = "evaluation_factors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"))
    criterion: Mapped[str] = mapped_column(String(64))
    weight: Mapped[float] = mapped_column(Float)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[list[str]] = mapped_column(JSONType, default=list)
    contradictions: Mapped[list[str]] = mapped_column(JSONType, default=list)
    missing: Mapped[list[str]] = mapped_column(JSONType, default=list)

    evaluation: Mapped[Evaluation] = relationship(back_populates="factors")


class ScoreHistory(Base, TimestampMixin):
    __tablename__ = "score_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("startup_opportunities.id", ondelete="CASCADE")
    )
    scoring_version: Mapped[str] = mapped_column(String(16), default="2")
    observed_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    research_completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    conservative_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    founder_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(Text)


class QualityAudit(Base, TimestampMixin):
    __tablename__ = "quality_audits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("startup_opportunities.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(32))
    risks: Mapped[list[str]] = mapped_column(JSONType, default=list)
    arguments_against: Mapped[list[str]] = mapped_column(JSONType, default=list)
    missing_evidence: Mapped[list[str]] = mapped_column(JSONType, default=list)
    unsupported_claims: Mapped[list[str]] = mapped_column(JSONType, default=list)
    validation_experiments: Mapped[list[str]] = mapped_column(JSONType, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")

    opportunity: Mapped[StartupOpportunity] = relationship(back_populates="audits")


class AgentRun(Base, TimestampMixin):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    research_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_runs.id"), nullable=True
    )
    agent_name: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    current_task: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResearchJob(Base, TimestampMixin):
    __tablename__ = "research_jobs"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_research_jobs_dedupe"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class FounderProfile(Base, TimestampMixin):
    __tablename__ = "founder_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(128), default="default")
    background: Mapped[str] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSONType, default=list)
    interests: Mapped[list[str]] = mapped_column(JSONType, default=list)
    location: Mapped[str] = mapped_column(String(128), default="India")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ModelUsage(Base, TimestampMixin):
    __tablename__ = "model_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    purpose: Mapped[str] = mapped_column(String(64), default="inference")


class ApiUsage(Base, TimestampMixin):
    __tablename__ = "api_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(64))
    endpoint: Mapped[str] = mapped_column(String(128))
    units: Mapped[int] = mapped_column(Integer, default=1)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)


class UserFeedback(Base, TimestampMixin):
    __tablename__ = "user_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("startup_opportunities.id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(Text)


class AppSetting(Base, TimestampMixin):
    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)


class PlatformRetentionPolicy(Base, TimestampMixin):
    __tablename__ = "platform_retention_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    platform: Mapped[str] = mapped_column(String(32))
    rule_type: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(Text)
    source_of_rule: Mapped[str] = mapped_column(Text)
    confirmed_by_operator: Mapped[bool] = mapped_column(Boolean, default=False)


class CollectionStat(Base, TimestampMixin):
    __tablename__ = "collection_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    research_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_runs.id"), nullable=True
    )
    platform: Mapped[str] = mapped_column(String(32))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collection_volume: Mapped[int] = mapped_column(Integer, default=0)
    query_set_hash: Mapped[str] = mapped_column(String(64))
    active_query_count: Mapped[int] = mapped_column(Integer, default=0)
    searches_scheduled: Mapped[int] = mapped_column(Integer, default=0)
    searches_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    pagination_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    results_truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    rate_limit_failures: Mapped[int] = mapped_column(Integer, default=0)
    source_outages: Mapped[int] = mapped_column(Integer, default=0)
    window_coverage: Mapped[float] = mapped_column(Float, default=1.0)


class ClusterPeriodStat(Base, TimestampMixin):
    __tablename__ = "cluster_period_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    cluster_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("problem_clusters.id", ondelete="CASCADE"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    independent_observations: Mapped[int] = mapped_column(Integer, default=0)
    collection_volume: Mapped[int] = mapped_column(Integer, default=0)
    observation_rate: Mapped[float] = mapped_column(Float, default=0.0)
    query_set_hash: Mapped[str] = mapped_column(String(64))
    distinct_communities: Mapped[int] = mapped_column(Integer, default=0)
    reddit_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    x_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    window_coverage: Mapped[float] = mapped_column(Float, default=1.0)
    pagination_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_failures: Mapped[int] = mapped_column(Integer, default=0)
    source_outages: Mapped[int] = mapped_column(Integer, default=0)
    coverage_comparable: Mapped[bool] = mapped_column(Boolean, default=False)


class ObservationEmbedding(Base, TimestampMixin):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("problem_observations.id", ondelete="CASCADE"), unique=True
    )
    model: Mapped[str] = mapped_column(String(128), default="lexical")
    vector: Mapped[list[float]] = mapped_column(JSONType, default=list)


class AuthorFingerprint(Base, TimestampMixin):
    __tablename__ = "author_fingerprints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    platform: Mapped[str] = mapped_column(String(32))
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    post_count: Mapped[int] = mapped_column(Integer, default=0)


class ThresholdDecision(Base, TimestampMixin):
    __tablename__ = "threshold_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    cluster_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("problem_clusters.id", ondelete="CASCADE"))
    decision: Mapped[str] = mapped_column(String(32))
    reasons: Mapped[list[str]] = mapped_column(JSONType, default=list)
    threshold_version: Mapped[str] = mapped_column(String(16), default="1")


class BudgetAccount(Base, TimestampMixin):
    __tablename__ = "budget_accounts"
    __table_args__ = (UniqueConstraint("name", "period", name="uq_budget_name_period"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(32))
    period: Mapped[str] = mapped_column(String(16))
    limit_amount: Mapped[float] = mapped_column(Float)
    reserved: Mapped[float] = mapped_column(Float, default=0.0)
    actual: Mapped[float] = mapped_column(Float, default=0.0)
    provider_billed: Mapped[float | None] = mapped_column(Float, nullable=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paused: Mapped[bool] = mapped_column(Boolean, default=False)


class BudgetReservation(Base, TimestampMixin):
    __tablename__ = "budget_reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("budget_accounts.id"))
    idempotency_key: Mapped[str] = mapped_column(String(256), unique=True)
    estimated: Mapped[float] = mapped_column(Float)
    reserved: Mapped[float] = mapped_column(Float)
    actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_billed: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="reserved")
    purpose: Mapped[str] = mapped_column(String(64), default="call")


class CollectionAttempt(Base, TimestampMixin):
    __tablename__ = "collection_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    research_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_runs.id"), nullable=True
    )
    platform: Mapped[str] = mapped_column(String(32))
    query: Mapped[str] = mapped_column(Text)
    scheduled: Mapped[bool] = mapped_column(Boolean, default=True)
    succeeded: Mapped[bool] = mapped_column(Boolean, default=False)
    pagination_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    results_truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    rate_limited: Mapped[bool] = mapped_column(Boolean, default=False)
    outage: Mapped[bool] = mapped_column(Boolean, default=False)
    result_count: Mapped[int] = mapped_column(Integer, default=0)


Index("ix_observations_class", ProblemObservation.relevance_class)
Index("ix_opportunities_status", StartupOpportunity.research_status)
