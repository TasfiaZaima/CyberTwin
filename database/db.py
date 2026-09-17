"""SQLite persistence primitives for CyberTwin.

The module owns schema creation and small, explicit database operations.  Each
operation opens its own connection, which makes the class safe to share among
FastAPI and simulator threads without sharing a SQLite connection.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp suitable for persistent records."""

    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class DeviceRecord:
    """A configured device registered with CyberTwin."""

    device_id: str
    name: str
    device_type: str
    source_ip: str
    expected_destinations: Sequence[str]
    expected_protocols: Sequence[str]
    status: str = "NORMAL"


class Database:
    """Initialize and access the durable CyberTwin SQLite database."""

    def __init__(self, path: str | Path = "data/cybertwin.db") -> None:
        self.path = Path(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a transactional connection with named-column row access."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create all required tables and indexes idempotently."""

        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def register_devices(self, devices: Sequence[DeviceRecord]) -> None:
        """Insert configured devices, updating mutable metadata on re-run."""

        now = utc_now()
        rows = []
        for device in devices:
            data = asdict(device)
            rows.append(
                (
                    data["device_id"], data["name"], data["device_type"],
                    data["source_ip"], json.dumps(data["expected_destinations"]),
                    json.dumps(data["expected_protocols"]), data["status"], now,
                )
            )
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO devices (
                    device_id, name, device_type, source_ip,
                    expected_destinations, expected_protocols, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    name = excluded.name,
                    device_type = excluded.device_type,
                    source_ip = excluded.source_ip,
                    expected_destinations = excluded.expected_destinations,
                    expected_protocols = excluded.expected_protocols
                """,
                rows,
            )

    def list_devices(self) -> list[dict[str, Any]]:
        """Return every device with JSON fields decoded."""

        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM devices ORDER BY device_id"
            ).fetchall()
        return [self._device_dict(row) for row in rows]

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        """Return one device, or ``None`` when it is not registered."""

        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM devices WHERE device_id = ?", (device_id,)
            ).fetchone()
        return self._device_dict(row) if row else None

    def table_names(self) -> set[str]:
        """Return application table names; useful for health checks."""

        with self.connect() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        return {str(row["name"]) for row in rows if row["name"] != "sqlite_sequence"}

    @staticmethod
    def _device_dict(row: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(row)
        item["expected_destinations"] = json.loads(item["expected_destinations"])
        item["expected_protocols"] = json.loads(item["expected_protocols"])
        return item


SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    source_ip TEXT NOT NULL UNIQUE,
    expected_destinations TEXT NOT NULL,
    expected_protocols TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'NORMAL'
        CHECK(status IN ('NORMAL', 'DEGRADED', 'ANOMALOUS')),
    anomaly_score REAL NOT NULL DEFAULT 0.0 CHECK(anomaly_score BETWEEN 0 AND 1),
    last_update TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    source_ip TEXT NOT NULL,
    destination TEXT NOT NULL,
    destination_port INTEGER NOT NULL CHECK(destination_port BETWEEN 1 AND 65535),
    protocol TEXT NOT NULL,
    packets INTEGER NOT NULL CHECK(packets >= 0),
    bytes INTEGER NOT NULL CHECK(bytes >= 0),
    direction TEXT NOT NULL DEFAULT 'outbound'
        CHECK(direction IN ('outbound', 'inbound'))
);

CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    packets_per_second REAL NOT NULL,
    bytes_per_second REAL NOT NULL,
    connections_per_minute REAL NOT NULL,
    unique_destinations INTEGER NOT NULL,
    unique_ports INTEGER NOT NULL,
    dns_requests INTEGER NOT NULL,
    tcp_connections INTEGER NOT NULL,
    udp_connections INTEGER NOT NULL,
    avg_packet_size REAL NOT NULL,
    outbound_ratio REAL NOT NULL,
    anomaly_score REAL,
    detector TEXT,
    UNIQUE(device_id, window_start, window_end)
);

CREATE TABLE IF NOT EXISTS baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    mean REAL NOT NULL,
    std_dev REAL NOT NULL,
    min_value REAL NOT NULL,
    max_value REAL NOT NULL,
    percentile_05 REAL NOT NULL,
    percentile_95 REAL NOT NULL,
    sample_count INTEGER NOT NULL CHECK(sample_count > 0),
    trained_at TEXT NOT NULL,
    UNIQUE(device_id, feature_name)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    severity TEXT NOT NULL CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH')),
    anomaly_score REAL NOT NULL CHECK(anomaly_score BETWEEN 0 AND 1),
    detector TEXT NOT NULL,
    reason TEXT NOT NULL,
    indicators TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'))
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
    ON telemetry(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_features_device_time
    ON features(device_id, window_start);
CREATE INDEX IF NOT EXISTS idx_alerts_device_time
    ON alerts(device_id, timestamp);
"""

