"""End-to-end simulation orchestration used by CLI and API."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any
from alerts.alert_manager import AlertManager
from collector.collector import TelemetryCollector
from database.db import Database
from detection.anomaly_detector import AnomalyDetector
from features.extractor import persist_window
from simulation.generator import PROFILES, generate_window


def simulate_window(database: Database, device_id: str, sequence: int = 0,
                    anomalous: bool = False, detector: str = "statistical") -> dict[str, Any]:
    start = datetime.now(timezone.utc) + timedelta(minutes=sequence)
    events = generate_window(device_id, sequence, anomalous, start)
    collector = TelemetryCollector(database)
    for event in events: collector.collect(event)
    features = persist_window(database, device_id, [event.model_dump(mode="json") for event in events],
                              start.isoformat(), (start + timedelta(minutes=1)).isoformat())
    if database.baselines(device_id):
        score, status, indicators = AnomalyDetector(database).detect(device_id, features, detector)
        database.execute("UPDATE features SET anomaly_score=?,detector=? WHERE device_id=? AND window_start=?",
                         [score, detector, device_id, features["window_start"]])
        database.update_device_state(device_id, status, score)
        AlertManager(database).create_if_needed(device_id, score, detector, indicators)
        features.update(anomaly_score=score, detector=detector, status=status, indicators=indicators)
    return features


def simulate_all(database: Database, windows: int = 10) -> None:
    for sequence in range(windows):
        for device_id in PROFILES: simulate_window(database, device_id, sequence)

