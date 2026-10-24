# VentureRadar Database Schema

PostgreSQL 16 + pgvector. UUID primary keys, timestamptz, foreign keys, indexes. Alembic is the migration source of truth.

## Origin and tombstones

Every research artifact has `data_origin` (`synthetic` | `live`) and `is_synthetic`. Sources support `deleted_at`, `deletion_reason`, and wiped title/body/author fields after compliance deletion.

Unique `(platform, external_id)` on `source_posts` and `source_comments`.

## Core tables

| Table | Purpose |
|---|---|
| `source_posts` | Normalized Reddit/X posts |
| `source_comments` | Comments tied to posts |
| `search_queries` | Configurable queries and communities |
| `research_runs` | Pipeline run metadata |
| `problem_observations` | Extracted problems |
| `problem_clusters` | Canonical problems |
| `cluster_memberships` | Observation↔cluster (versioned) |
| `startup_opportunities` | Concepts + separate score columns |
| `opportunity_problem_links` | Opportunity↔cluster |
| `competitor_research` | Source-backed alternatives only |
| `evidence_links` | Claim → source provenance |
| `evaluations` | Versioned evaluation headers |
| `evaluation_factors` | Per-criterion drafts including nulls |
| `score_history` | Score changes with reasons |
| `quality_audits` | Agent 5 outcomes |
| `agent_runs` | Per-agent execution log |
| `research_jobs` | Queue, retries, `dedupe_key` |
| `founder_profiles` | Configurable founder fit input |
| `model_usage` | LLM token/cost estimates |
| `api_usage` | Connector usage |
| `user_feedback` | Bookmarks, notes, rejects, validation |
| `settings` | Pause, weights, budgets, credentials (server-side) |

## Additions

| Table | Purpose |
|---|---|
| `platform_retention_policies` | Per-platform rules; not a universal TTL |
| `collection_stats` | Volume, query hash, scheduled vs succeeded, pagination, truncations, rate-limits, outages, window coverage |
| `cluster_period_stats` | Normalized trend inputs |
| `embeddings` | Observation vectors |
| `author_fingerprints` | Opaque hashes only |
| `threshold_decisions` | qualified / provisional / skip |
| `budget_accounts` | Limits plus reserved/actual/provider_billed |
| `budget_reservations` | Per-call estimated/reserved/actual/provider_billed |
| `collection_attempts` | Per-search attempt outcomes |

## Provenance graph

```
source_posts → source_comments
source_* → problem_observations → embeddings
problem_observations → cluster_memberships → problem_clusters
problem_clusters → opportunity_problem_links → startup_opportunities
startup_opportunities → competitor_research, evaluations, evaluation_factors,
                         quality_audits, score_history, user_feedback
evidence_links → source_*
```

Deletion cascade: tombstone source → wipe required fields → drop orphan observations/embeddings → recompute cluster counts → invalidate evidence_links → stale or demote opportunities → deterministic rescore only.

## Opportunity score columns

`observed_quality_score`, `research_completeness`, `conservative_score`, `conservative_score_kind` (always `heuristic`), `evidence_confidence`, `founder_fit_score`, `research_status`, `is_provisional`, `quality_status`. Founder fit is never written into the three market scores.
