# VentureRadar Implementation Plan

## Status

Phases 0–4 are the working MVP on **synthetic fixtures**. Live Reddit/X stay disabled until authorized access, policy confirmation, and a recorded live smoke test.

Synthetic benchmark numbers are `dataset=synthetic_labeled`. They are **not** real-world model performance.

## Phases

| Phase | Deliverable |
|---|---|
| 0 | This docs set |
| 1 | Docker, schema, health, Celery, atomic budget, retention worker |
| 2 | Mock connectors, Agents 1–3, synthetic 100-post set, P/R tests |
| 3 | Thresholds, Agent 4, three-metric scorer, founder fit, Agent 5, ranking |
| 4 | Six-page dashboard on real APIs |
| 5 | Gated live connectors |
| 6 | Auth and production hardening |

## Synthetic quality gates (not real-world claims)

- Extraction F1 ≥ 0.70
- Duplicate precision/recall ≥ 0.80
- Clustering pair-F1 ≥ 0.65
- Buying-intent macro-F1 ≥ 0.60
- Attribution precision = 1.00 (no fabricated URLs)
- E2E: 100 synthetic posts → ranked dashboard API

## Local run

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000  Dashboard: http://localhost:3000

`POST /api/research/run` executes the full synthetic pipeline. Beat continues after the browser closes.

## Tests

```bash
docker compose exec api pytest -q
```

Covers normalization, extraction, duplicates, clustering, scoring, quality gates, ranking, budget reservations, retention cascade, scheduling hooks, and the 100-post E2E path.

## Cost defaults

LLM $5/day $30/month; Tavily $1/day $8/month; X $2/day $20/month; Reddit 60 QPM. Hard-stop on failed reservation. Provider invoices may differ from `actual`.
