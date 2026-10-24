from __future__ import annotations


def prf(true_pos: int, pred_pos: int, actual_pos: int) -> dict[str, float]:
    precision = true_pos / pred_pos if pred_pos else 0.0
    recall = true_pos / actual_pos if actual_pos else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "dataset": "synthetic_labeled"}
