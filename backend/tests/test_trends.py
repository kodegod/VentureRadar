from datetime import datetime, timedelta, timezone

from app.models import ClusterPeriodStat
from app.services.trends import INCOMPARABLE, compute_cluster_trend


def _stat(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = dict(
        cluster_id=None,
        period_start=now - timedelta(days=7),
        period_end=now,
        independent_observations=5,
        collection_volume=50,
        observation_rate=0.1,
        query_set_hash="abc",
        window_coverage=1.0,
        pagination_complete=True,
        rate_limit_failures=0,
        source_outages=0,
    )
    defaults.update(kwargs)
    return ClusterPeriodStat(**{k: v for k, v in defaults.items() if k != "cluster_id" or v is not None}, cluster_id=defaults["cluster_id"] or __import__("uuid").uuid4())


def test_incomparable_when_query_hash_changes():
    a = _stat(query_set_hash="one", observation_rate=0.1)
    b = _stat(query_set_hash="two", observation_rate=0.5)
    assert compute_cluster_trend(b, a) == INCOMPARABLE


def test_incomparable_when_rate_limited():
    a = _stat(rate_limit_failures=2, observation_rate=0.1)
    b = _stat(rate_limit_failures=0, observation_rate=0.5)
    assert compute_cluster_trend(b, a) == INCOMPARABLE


def test_up_only_when_comparable():
    a = _stat(observation_rate=0.10, collection_volume=100)
    b = _stat(observation_rate=0.20, collection_volume=100)
    assert compute_cluster_trend(b, a) == "up"
