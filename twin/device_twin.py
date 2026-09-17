"""Virtual behavioral representation of an IoT or edge device."""
from dataclasses import dataclass, field
from typing import Any
from database.db import utc_now
from twin.state import TwinState


@dataclass(slots=True)
class DeviceTwin:
    device_id: str
    device_type: str
    expected_destinations: list[str] = field(default_factory=list)
    expected_protocols: list[str] = field(default_factory=list)
    state: TwinState = field(default_factory=TwinState)

    def update(self, observed: dict[str, Any], score: float, status: str,
               differences: dict[str, Any]) -> TwinState:
        self.state = TwinState(observed, differences, score, status, utc_now())
        return self.state

