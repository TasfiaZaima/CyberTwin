"""Digital-twin state types."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TwinState:
    observed: dict[str, Any] = field(default_factory=dict)
    differences: dict[str, Any] = field(default_factory=dict)
    anomaly_score: float = 0.0
    status: str = "NORMAL"
    last_update: str | None = None

