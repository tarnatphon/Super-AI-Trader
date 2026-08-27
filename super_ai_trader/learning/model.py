"""A tiny, dependency-free machine-learning model.

Logistic regression with standardization and L2 regularization, trained with
gradient descent. It predicts P(next move is up). Deliberately simple and fully
auditable — the point is a *learned* directional signal you can validate
out-of-sample, not a black box. Swap in any sklearn/torch model later via the same
`predict_proba(features) -> float` interface.
"""
from __future__ import annotations

import json
import math
import random


def sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _standardize_fit(X: list[list[float]]):
    n = len(X)
    d = len(X[0])
    means = [sum(row[j] for row in X) / n for j in range(d)]
    stds = []
    for j in range(d):
        var = sum((row[j] - means[j]) ** 2 for row in X) / n
        stds.append(math.sqrt(var) if var > 1e-12 else 1.0)
    return means, stds


def standardize(X, means, stds):
    return [[(row[j] - means[j]) / stds[j] for j in range(len(means))] for row in X]


def train_logistic(
    X: list[list[float]],
    y: list[int],
    *,
    epochs: int = 400,
    lr: float = 0.1,
    l2: float = 1e-4,
    seed: int = 7,
):
    """Return a trained model dict: {w, b, means, stds, feature_count}."""
    rng = random.Random(seed)
    means, stds = _standardize_fit(X)
    Xs = standardize(X, means, stds)
    d = len(Xs[0])
    w = [rng.uniform(-0.01, 0.01) for _ in range(d)]
    b = 0.0
    n = len(Xs)
    for _ in range(epochs):
        gw = [0.0] * d
        gb = 0.0
        for xi, yi in zip(Xs, y):
            z = b + sum(w[j] * xi[j] for j in range(d))
            err = sigmoid(z) - yi
            for j in range(d):
                gw[j] += err * xi[j]
            gb += err
        for j in range(d):
            gw[j] = gw[j] / n + l2 * w[j]
            w[j] -= lr * gw[j]
        b -= lr * (gb / n)
    return {"w": w, "b": b, "means": means, "stds": stds, "features": d}


def predict_proba(model: dict, x: list[float]) -> float:
    """P(up) for a single raw feature vector (standardized internally)."""
    xs = [(x[j] - model["means"][j]) / model["stds"][j] for j in range(model["features"])]
    z = model["b"] + sum(model["w"][j] * xs[j] for j in range(model["features"]))
    return sigmoid(z)


def evaluate(model: dict, X: list[list[float]], y: list[int], threshold: float = 0.5) -> dict:
    """Out-of-sample metrics: accuracy, precision/recall for the up-class, and a
    simple directional edge (up-day hit rate vs base rate)."""
    tp = fp = tn = fn = 0
    probs = []
    for xi, yi in zip(X, y):
        p = predict_proba(model, xi)
        probs.append(p)
        pred = 1 if p >= threshold else 0
        if pred == 1 and yi == 1:
            tp += 1
        elif pred == 1 and yi == 0:
            fp += 1
        elif pred == 0 and yi == 0:
            tn += 1
        else:
            fn += 1
    n = len(y) or 1
    acc = (tp + tn) / n
    base_up = sum(y) / n
    # Edge when confident: hit rate on bars where model prob >= 0.6
    conf = [(p, yi) for p, yi in zip(probs, y) if p >= 0.6]
    conf_up = sum(1 for p, yi in conf if yi == 1) / len(conf) if conf else None
    conf_down = [(p, yi) for p, yi in zip(probs, y) if p <= 0.4]
    conf_dn = sum(1 for p, yi in conf_down if yi == 0) / len(conf_down) if conf_down else None
    return {
        "accuracy": round(acc, 3),
        "base_up_rate": round(base_up, 3),
        "samples": n,
        "confident_buy_hit_rate": round(conf_up, 3) if conf_up is not None else None,
        "confident_sell_hit_rate": round(conf_dn, 3) if conf_dn is not None else None,
        "confident_buy_n": len(conf),
        "confident_sell_n": len(conf_down),
    }


def save_model(model: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(model, f)


def load_model(path: str) -> dict:
    with open(path) as f:
        return json.load(f)
