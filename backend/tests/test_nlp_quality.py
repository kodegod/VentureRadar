"""Synthetic-labeled quality tests. Not real-world model performance."""

from itertools import combinations

from app.connectors.base import NormalizedPost
from app.fixtures.synthetic import SYNTHETIC_DATASET_LABEL, generate_synthetic_posts
from app.nlp import buying_intent, classify, extract_problems, infer_cluster_key, is_near_duplicate
from tests.metrics import prf


def _as_post(raw: dict) -> NormalizedPost:
    return NormalizedPost(
        platform=raw["platform"],
        external_id=raw["external_id"],
        url=raw["url"],
        title=raw["title"],
        body=raw["body"],
        author_fingerprint=raw["author"],
        community=raw.get("community"),
        posted_at=raw.get("posted_at"),
        data_origin="synthetic",
        is_synthetic=True,
        labels=raw["labels"],
    )


def test_dataset_is_synthetic_and_size():
    posts = generate_synthetic_posts()
    assert len(posts) == 100
    assert all(p["labels"]["dataset"] == SYNTHETIC_DATASET_LABEL for p in posts)


def test_extraction_and_class_prf():
    posts = [_as_post(p) for p in generate_synthetic_posts()]
    pred_pos = 0
    actual_pos = 0
    tp = 0
    class_tp = class_pred = class_actual = 0
    for post in posts:
        labels = post.labels
        actual_problems = labels["problems"]
        predicted = extract_problems(post)
        pred_pos += 1 if predicted else 0
        actual_pos += 1 if actual_problems else 0
        if predicted and actual_problems:
            tp += 1
        pred_class = classify(post)
        if labels["relevance_class"] == pred_class:
            class_tp += 1
        class_pred += 1
        class_actual += 1
    scores = prf(tp, pred_pos, actual_pos)
    print("extraction", scores)
    assert scores["dataset"] == "synthetic_labeled"
    assert scores["f1"] >= 0.70
    assert class_tp / class_actual >= 0.70


def test_duplicate_prf():
    raw = generate_synthetic_posts()
    by_id = {p["external_id"]: p for p in raw}
    canonical = {
        p["external_id"]: p["labels"]["is_duplicate_of"] or p["external_id"] for p in raw
    }
    actual_pairs = set()
    ids = list(canonical)
    for a, b in combinations(ids, 2):
        if canonical[a] == canonical[b] and (canonical[a] != a or canonical[b] != b):
            actual_pairs.add(tuple(sorted((a, b))))
    pred_pairs = set()
    for a, b in combinations(raw, 2):
        if is_near_duplicate(f"{a['title']} {a['body']}", f"{b['title']} {b['body']}"):
            pred_pairs.add(tuple(sorted((a["external_id"], b["external_id"]))))
    tp = len(actual_pairs & pred_pairs)
    scores = prf(tp, len(pred_pairs), len(actual_pairs))
    print("duplicates", scores)
    assert scores["precision"] >= 0.80
    assert scores["recall"] >= 0.80


def test_clustering_pair_f1():
    posts = [_as_post(p) for p in generate_synthetic_posts() if p["labels"]["relevance_class"] == "genuine_problem"]
    labeled = [(p.external_id, p.labels["cluster_id"]) for p in posts if p.labels["cluster_id"]]
    pred = [(p.external_id, infer_cluster_key(p)) for p in posts]
    actual_pairs = {
        tuple(sorted((a[0], b[0])))
        for a, b in combinations(labeled, 2)
        if a[1] and a[1] == b[1]
    }
    pred_pairs = {
        tuple(sorted((a[0], b[0])))
        for a, b in combinations(pred, 2)
        if a[1] and a[1] == b[1]
    }
    tp = len(actual_pairs & pred_pairs)
    scores = prf(tp, len(pred_pairs), len(actual_pairs))
    print("clustering", scores)
    assert scores["f1"] >= 0.65


def test_buying_intent_macro_f1():
    posts = [_as_post(p) for p in generate_synthetic_posts()]
    classes = ["none", "weak", "moderate", "strong", "committed"]
    f1s = []
    for cls in classes:
        tp = pred = actual = 0
        for post in posts:
            y = post.labels["buying_intent"]
            yhat = buying_intent(post)
            if y == cls:
                actual += 1
            if yhat == cls:
                pred += 1
            if y == cls and yhat == cls:
                tp += 1
        if actual == 0 and pred == 0:
            continue
        f1s.append(prf(tp, pred, actual)["f1"])
    macro = sum(f1s) / len(f1s)
    print("intent_macro_f1", macro, "dataset=synthetic_labeled")
    assert macro >= 0.60


def test_attribution_never_fabricates_url():
    posts = [_as_post(p) for p in generate_synthetic_posts()]
    fabricated = 0
    predicted = 0
    for post in posts:
        for problem in extract_problems(post):
            predicted += 1
            if problem["source_url"] != post.url:
                fabricated += 1
            if problem["source_span"] and problem["source_span"] not in post.body and problem["source_span"] not in post.title:
                fabricated += 1
    assert predicted > 0
    assert fabricated == 0
