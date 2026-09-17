"""Deterministic, safe generation of local structured IoT flow events."""
from __future__ import annotations
import random
from datetime import datetime, timedelta, timezone
from collector.collector import FlowEvent

PROFILES = {
 "camera-01": ("10.20.0.10", [("camera-cloud.local",443,"HTTPS"),("dns.local",53,"DNS"),("ntp.local",123,"NTP")], 8, 3500),
 "smart-plug-01": ("10.20.0.11", [("mqtt.local",1883,"MQTT"),("dns.local",53,"DNS")], 3, 550),
 "temperature-sensor-01": ("10.20.0.12", [("mqtt.local",1883,"MQTT"),("ntp.local",123,"NTP")], 2, 240),
 "edge-gateway-01": ("10.20.0.2", [("mqtt.local",1883,"MQTT"),("dns.local",53,"DNS"),("ntp.local",123,"NTP")], 10, 1800),
}


def generate_window(device_id: str, sequence: int = 0, anomalous: bool = False,
                    timestamp: datetime | None = None) -> list[FlowEvent]:
    """Generate a reproducible one-minute window; never performs network attacks."""
    source, normal_targets, count, average_bytes = PROFILES[device_id]
    rng = random.Random(f"{device_id}:{sequence}:{anomalous}")
    total = count + rng.randint(-1, 1)
    targets = list(normal_targets)
    if anomalous:
        total = count * 12
        targets += [(f"unexpected-{i}.local", 40000 + i, "TCP") for i in range(20)]
        average_bytes *= 25
    start = timestamp or datetime.now(timezone.utc)
    events = []
    for index in range(max(1, total)):
        destination, port, protocol = targets[index % len(targets)]
        packets = max(1, int(rng.gauss(8 if device_id == "camera-01" else 3, 1)))
        byte_count = max(packets, int(rng.gauss(average_bytes, average_bytes * 0.08)))
        events.append(FlowEvent(timestamp=start + timedelta(seconds=index * 60 / total), device_id=device_id,
          source_ip=source, destination=destination, destination_port=port, protocol=protocol,
          packets=packets, bytes=byte_count))
    return events

