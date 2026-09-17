"""Statistical and optional Isolation Forest detectors."""
from __future__ import annotations
from typing import Any
import numpy as np
from sklearn.ensemble import IsolationForest
from database.db import Database
from detection.scoring import classify, statistical_score
from features.extractor import FEATURE_NAMES


class AnomalyDetector:
    def __init__(self, database: Database) -> None: self.database = database

    def detect(self, device_id: str, observed: dict[str, Any], detector: str = "statistical") -> tuple[float, str, dict[str, Any]]:
        if detector == "isolation_forest":
            history = self.database.feature_rows(device_id, 500)
            if len(history) < 10: raise ValueError("Isolation Forest requires at least 10 windows")
            data = np.asarray([[float(row[n]) for n in FEATURE_NAMES] for row in history])
            model = IsolationForest(random_state=42, contamination="auto").fit(data)
            raw = float(-model.decision_function([[float(observed[n]) for n in FEATURE_NAMES]])[0])
            score = float(np.clip((raw + 0.25) / 0.75, 0, 1))
            details = {"model_score": round(raw, 4)}
        else:
            score, details = statistical_score(observed, self.database.baselines(device_id))
        return score, classify(score), details

