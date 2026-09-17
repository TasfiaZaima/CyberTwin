"""Explainable alert creation from detector results."""
from __future__ import annotations
import json
from typing import Any
from database.db import Database, utc_now
from detection.scoring import severity


class AlertManager:
    def __init__(self, database: Database) -> None: self.database = database

    def create_if_needed(self, device_id: str, score: float, detector: str,
                         indicators: dict[str, Any]) -> int | None:
        level = severity(score)
        if level is None: return None
        reason = "Potential compromise / abnormal behavior detected. Investigate recent device activity."
        return self.database.execute("""INSERT INTO alerts
          (timestamp,device_id,severity,anomaly_score,detector,reason,indicators,status)
          VALUES (?,?,?,?,?,?,?,'ACTIVE')""",
          [utc_now(), device_id, level, score, detector, reason, json.dumps(indicators)])

