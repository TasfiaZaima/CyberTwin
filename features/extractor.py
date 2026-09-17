"""Windowed feature extraction from structured flow events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from database.db import Database


FEATURE_NAMES = ("packets_per_second", "bytes_per_second", "connections_per_minute",
                 "unique_destinations", "unique_ports", "dns_requests", "tcp_connections",
                 "udp_connections", "avg_packet_size", "outbound_ratio")


def extract_features(events: Sequence[dict[str, Any]], window_seconds: float = 60.0) -> dict[str, float]:
    """Calculate behavioral features for a non-empty telemetry window."""
    if not events:
        raise ValueError("At least one telemetry event is required")
    duration = max(float(window_seconds), 1.0)
    packets = sum(int(event["packets"]) for event in events)
    byte_count = sum(int(event["bytes"]) for event in events)
    outbound = sum(1 for event in events if event.get("direction", "outbound") == "outbound")
    protocols = [str(event["protocol"]).upper() for event in events]
    return {
        "packets_per_second": packets / duration,
        "bytes_per_second": byte_count / duration,
        "connections_per_minute": len(events) * 60.0 / duration,
        "unique_destinations": float(len({event["destination"] for event in events})),
        "unique_ports": float(len({int(event["destination_port"]) for event in events})),
        "dns_requests": float(protocols.count("DNS")),
        "tcp_connections": float(sum(p in {"TCP", "HTTPS", "MQTT"} for p in protocols)),
        "udp_connections": float(sum(p in {"UDP", "DNS", "NTP"} for p in protocols)),
        "avg_packet_size": byte_count / packets if packets else 0.0,
        "outbound_ratio": outbound / len(events),
    }


def persist_window(database: Database, device_id: str, events: Sequence[dict[str, Any]],
                   window_start: str, window_end: str, window_seconds: float = 60.0) -> dict[str, Any]:
    values: dict[str, Any] = {"device_id": device_id, "window_start": window_start,
                              "window_end": window_end, **extract_features(events, window_seconds),
                              "anomaly_score": None, "detector": None}
    database.add_features(values)
    return values

