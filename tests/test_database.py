from pathlib import Path
from uuid import uuid4

import pytest

from database.db import Database, DeviceRecord
from database.setup import initialize_from_config, load_config


EXPECTED_TABLES = {"devices", "telemetry", "features", "baselines", "alerts"}


def output_path(filename: str) -> Path:
    """Return a unique ignored path without pytest's Windows temp ACL changes."""

    directory = Path("data/test-output") / uuid4().hex
    directory.mkdir(parents=True)
    return directory / filename


def test_initialize_creates_complete_schema() -> None:
    database = Database(output_path("cybertwin.db"))
    database.initialize()
    assert database.table_names() == EXPECTED_TABLES


def test_register_devices_is_idempotent() -> None:
    database = Database(output_path("cybertwin.db"))
    database.initialize()
    device = DeviceRecord(
        device_id="camera-01",
        name="Smart Camera",
        device_type="smart_camera",
        source_ip="10.20.0.10",
        expected_destinations=["camera-cloud.local"],
        expected_protocols=["HTTPS"],
    )
    database.register_devices([device])
    database.register_devices([device])
    assert len(database.list_devices()) == 1
    assert database.get_device("camera-01")["expected_protocols"] == ["HTTPS"]


def test_initialize_from_config_registers_devices() -> None:
    database = initialize_from_config(database_path=output_path("configured.db"))
    assert {item["device_id"] for item in database.list_devices()} == {
        "camera-01", "smart-plug-01", "temperature-sensor-01", "edge-gateway-01"
    }


def test_invalid_config_is_rejected() -> None:
    config = output_path("invalid.yaml")
    config.write_text("database: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="devices"):
        load_config(config)
