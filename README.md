# VentureRadar

Autonomous startup research platform. Five agents discover customer problems from social discussions, cluster them, and rank evidence-backed opportunities.

**Synthetic research mode is the default.** Live Reddit/X collection is not operational until authorized API access is configured and a live smoke test passes.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Next.js dashboard: http://localhost:3000
- API + fallback dashboard: http://localhost:8000
- Health: http://localhost:8000/health

Without Docker (SQLite, no Redis/Beat):

```bash
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt
set DATABASE_URL=sqlite+pysqlite:///backend/ventureradar.db
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000 and `POST /api/research/run`.

Trigger a synthetic research cycle from Research Operations or:

```bash
curl -X POST http://localhost:8000/api/research/run
```

**Live Reddit/X collection is not operational.** Connectors exist but stay disabled until authorized access and a recorded smoke test.

## Tests

```bash
docker compose exec api pytest -q
```

Synthetic benchmark output is labeled `dataset=synthetic_labeled` and is not real-world model performance.

## Docs

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [AGENTS.md](AGENTS.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [SCORING.md](SCORING.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
