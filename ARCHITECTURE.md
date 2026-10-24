# VentureRadar Architecture

Five-agent autonomous startup research system. Discovers customer problems from Reddit and X, clusters them, evaluates startup opportunities, and ranks them with deterministic scores.

**Live social-media collection is not operational** until authorized Reddit/X access is configured and a recorded live smoke test passes. The default mode is **synthetic research** using labeled fixtures.

## Services

Docker Compose runs exactly six containers:

| Service | Role |
|---|---|
| `db` | PostgreSQL 16 + pgvector |
| `redis` | Broker, cache, locks |
| `api` | FastAPI |
| `worker` | Celery worker (same five agents) |
| `beat` | Celery Beat scheduler |
| `web` | Next.js dashboard |

No extra microservices. Scoring, trends, ranking, budget, and deletion cascade are deterministic library code.

## Pipeline

```
Reddit/X connectors (disabled until live smoke test)
        ↓
Agent 1 Discovery → source_posts / source_comments
        ↓
Agent 2 Extraction → problem_observations
        ↓
Agent 3 Clustering → problem_clusters
        ↓
Threshold service → qualified | provisional | skip
        ↓
Agent 4 Opportunity (+ Tavily if configured, else unresearched)
        ↓
Deterministic scorer (observed quality, completeness, conservative heuristic)
        ↓
Agent 5 Quality audit
        ↓
Ranking engine → dashboard
```

Agents communicate only through persisted records. Jobs are idempotent (`research_jobs.dedupe_key`).

## Connectors

- `SourceConnector` protocol: `search`, `fetch_comments`, `is_enabled`.
- `MockRedditConnector` / `MockXConnector` load synthetic fixtures (`data_origin=synthetic`).
- `RedditConnector` / `XConnector` implement official OAuth/Bearer APIs and stay `enabled=False` until credentials **and** a passing live smoke test.
- `TavilyConnector` is used only by Agent 4. Missing key → competitor/market factors `unresearched`, score `null`. Never invent prices or market sizes.

## Operational controls

- Pause/resume in `settings`.
- Atomic budget reservations: `estimated`, `reserved`, `actual`, `provider_billed`. Conservative ceilings; reconcile after the call. **Not an exact-spend guarantee** when provider billing lags.
- Retention/deletion follows `platform_retention_policies` plus the provenance graph. No hardcoded universal TTL.
- Trends require comparable collection windows; otherwise **Insufficient comparable data**.

## Security

Secrets stay on the server. Social text is untrusted (prompt-injection isolation). LLM JSON is validated with Pydantic. No posting or DMs. No deanonymization. No model training on Reddit/X content.

## Blockers (operator action)

1. Reddit Data API approval (not self-serve).
2. X developer account + pay-per-use credits.
3. Optional LLM key for live inference (tests run without it).
4. Optional Tavily key for competitor research.
5. Confirmed access agreements for retention overrides.
