from app.scoring.engine import compute_scores
from app.scoring.founder_fit import score_founder_fit
from app.scoring.ranking import is_verified, rank_opportunities
from app.scoring.thresholds import decide_threshold


def test_unknowns_stay_null_and_three_metrics():
    factors = [
        {"criterion": "problem_severity", "weight": 0.20, "score": 5, "confidence": 0.8},
        {"criterion": "willingness_to_pay", "weight": 0.20, "score": None, "confidence": None},
        {"criterion": "mvp_feasibility", "weight": 0.05, "score": 4, "confidence": 0.7},
    ]
    metrics = compute_scores(factors)
    assert metrics["research_completeness"] == 0.25
    assert metrics["observed_quality_score"] == round(((1.0 * 0.20) + (0.8 * 0.05)) / 0.25 * 100, 2)
    assert metrics["conservative_score"] == round((1.0 * 0.20 + 0.8 * 0.05) * 100, 2)
    assert metrics["conservative_score_kind"] == "heuristic"
    assert metrics["observed_quality_score"] != metrics["conservative_score"]


def test_all_unknown_is_null():
    metrics = compute_scores([{"criterion": "market_potential", "weight": 0.15, "score": None}])
    assert metrics["observed_quality_score"] is None
    assert metrics["conservative_score"] is None


def test_founder_fit_not_in_market_scores():
    fit = score_founder_fit(industry="saas", target_customer="b2b ops", proposed_solution="automation agent")
    metrics = compute_scores([{"criterion": "problem_severity", "weight": 0.20, "score": 4, "confidence": 0.6}])
    assert "founder" not in metrics
    assert fit > 40


def test_verified_ranking_requires_gates():
    weak = {
        "observed_quality_score": 90,
        "research_completeness": 0.4,
        "evidence_confidence": 0.9,
        "quality_status": "passed",
        "is_provisional": True,
    }
    strong = {
        "observed_quality_score": 70,
        "research_completeness": 0.8,
        "evidence_confidence": 0.7,
        "quality_status": "passed_with_limitations",
        "is_provisional": False,
    }
    rejected = {
        "observed_quality_score": 99,
        "research_completeness": 0.9,
        "evidence_confidence": 0.9,
        "quality_status": "rejected",
    }
    assert not is_verified(weak)
    assert is_verified(strong)
    assert not is_verified(rejected)
    assert not is_verified({**strong, "is_provisional": True})
    ranked = rank_opportunities([weak, strong, rejected], "highest_opportunity")
    assert ranked[0] is strong
    provisional = rank_opportunities([weak, strong], "provisional")
    assert weak in provisional


def test_threshold_qualified_and_provisional():
    qualified = decide_threshold(
        independent_observation_count=4,
        severity_score=3,
        max_observation_severity=3,
        has_workaround=True,
        has_named_tool=True,
        has_time_or_money=False,
        buying_intents=["none"],
    )
    assert qualified["decision"] == "qualified"
    provisional = decide_threshold(
        independent_observation_count=1,
        severity_score=4,
        max_observation_severity=4,
        has_workaround=False,
        has_named_tool=False,
        has_time_or_money=False,
        buying_intents=["strong"],
    )
    assert provisional["decision"] == "provisional"
    skip = decide_threshold(
        independent_observation_count=1,
        severity_score=2,
        max_observation_severity=2,
        has_workaround=False,
        has_named_tool=False,
        has_time_or_money=False,
        buying_intents=["none"],
    )
    assert skip["decision"] == "skip"
