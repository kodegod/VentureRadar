"""100-post synthetic path: collection → ranked dashboard API. dataset=synthetic_labeled."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import get_db
from app.fixtures.synthetic import generate_synthetic_posts
from app.main import app
from app.models import ProblemCluster, ProblemObservation, SourcePost, StartupOpportunity
from app.scoring.ranking import is_verified
from app.services.pipeline import run_full_pipeline


def test_hundred_posts_to_ranked_dashboard(db):
    assert len(generate_synthetic_posts()) == 100
    run = run_full_pipeline(db, trigger="e2e")
    assert run.status == "completed"
    assert run.stats["dataset"] == "synthetic_labeled"

    posts = db.scalars(select(SourcePost)).all()
    assert len(posts) == 100
    assert all(p.is_synthetic for p in posts)

    observations = db.scalars(select(ProblemObservation)).all()
    assert observations
    assert all(o.source_url.startswith("https://synthetic.ventureradar.test/") for o in observations)

    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.deleted_at.is_(None))).all()
    assert clusters
    titles = {c.canonical_title for c in clusters}
    assert any("report" in t.lower() or "Weekly" in t for t in titles)

    opps = db.scalars(select(StartupOpportunity)).all()
    assert opps
    assert all(o.is_synthetic for o in opps)
    assert all(o.conservative_score_kind == "heuristic" for o in opps)
    assert all(o.founder_fit_score is None or o.observed_quality_score != o.founder_fit_score for o in opps)

    provisional = [o for o in opps if o.is_provisional]
    assert provisional  # remain discoverable

    def override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override
    client = TestClient(app)
    dash = client.get("/api/dashboard").json()
    assert dash["dataset"] == "synthetic_labeled"
    assert "Synthetic research mode" in dash["banner"]
    assert dash["totals"]["opportunities"] >= 1
    assert dash["totals"]["problems"] >= 1
    names = {row["working_name"] for row in dash["top_opportunities"]}
    assert names

    listing = client.get("/api/opportunities", params={"ranking": "highest_opportunity"}).json()
    assert listing["dataset"] == "synthetic_labeled"
    verified = [i for i in listing["items"] if i["verified"]]
    for item in verified:
        assert is_verified(item)
        assert item["quality_status"] in {"passed", "passed_with_limitations"}
        assert (item["research_completeness"] or 0) >= 0.70

    problems = client.get("/api/problems").json()
    assert problems["items"]
    detail = client.get(f"/api/opportunities/{listing['items'][0]['id']}").json()
    assert detail["evidence"]
    assert all(e["source_url"].startswith("https://synthetic.ventureradar.test/") for e in detail["evidence"])
    statuses = {f["status"] for f in detail["factors"]}
    assert "unresearched" in statuses or "unknown" in statuses or "scored" in statuses
    app.dependency_overrides.clear()


def test_pause_blocks_pipeline(db):
    from app.services.bootstrap import set_paused

    set_paused(db, True)
    run = run_full_pipeline(db, trigger="paused")
    assert run.status == "paused"
    set_paused(db, False)
