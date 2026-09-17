"""Explainable statistical anomaly scoring."""
from __future__ import annotations
import math
from typing import Any


def statistical_score(observed: dict[str, Any], baselines: list[dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    contributions: dict[str, Any] = {}
    signals = []
    for baseline in baselines:
        name = baseline["feature_name"]
        value, mean, std = float(observed[name]), float(baseline["mean"]), float(baseline["std_dev"])
        scale = std if std > 1e-9 else max(abs(mean) * 0.10, 0.5)
        z_score = abs(value - mean) / scale
        contribution = 1.0 - math.exp(-max(0.0, z_score - 1.0) / 2.0)
        signals.append(contribution)
        if contribution >= 0.10:
            contributions[name] = {"baseline": round(mean, 3), "observed": round(value, 3),
                                   "z_score": round(z_score, 3), "contribution": round(contribution, 3)}
    if not signals:
        raise ValueError("No matching baseline features")
    top = sorted(signals, reverse=True)[:4]
    return round(sum(top) / len(top), 4), contributions


def classify(score: float, thresholds: dict[str, float] | None = None) -> str:
    limits = thresholds or {"low": 0.30, "medium": 0.60, "high": 0.80}
    if score >= limits["high"]: return "ANOMALOUS"
    if score >= limits["medium"]: return "ANOMALOUS"
    if score >= limits["low"]: return "DEGRADED"
    return "NORMAL"


def severity(score: float, thresholds: dict[str, float] | None = None) -> str | None:
    limits = thresholds or {"low": 0.30, "medium": 0.60, "high": 0.80}
    if score >= limits["high"]: return "HIGH"
    if score >= limits["medium"]: return "MEDIUM"
    if score >= limits["low"]: return "LOW"
    return None

