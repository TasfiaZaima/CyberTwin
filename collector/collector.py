"""Validated collection of structured, local network-flow telemetry."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from database.db import Database


class FlowEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str
    source_ip: str
    destination: str
    destination_port: int = Field(ge=1, le=65535)
    protocol: str
    packets: int = Field(ge=0)
    bytes: int = Field(ge=0)
    direction: Literal["outbound", "inbound"] = "outbound"


class TelemetryCollector:
    def __init__(self, database: Database) -> None:
        self.database = database

    def collect(self, event: FlowEvent) -> int:
        if self.database.get_device(event.device_id) is None:
            raise ValueError(f"Unknown device: {event.device_id}")
        values = event.model_dump(mode="json")
        values["timestamp"] = event.timestamp.isoformat()
        return self.database.add_telemetry(values)

