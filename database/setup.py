"""Initialize CyberTwin storage from the device configuration."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from database.db import Database, DeviceRecord


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate the YAML application configuration."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict) or not isinstance(config.get("devices"), list):
        raise ValueError("Configuration must contain a 'devices' list")
    if not config["devices"]:
        raise ValueError("Configuration must define at least one device")
    return config


def initialize_from_config(
    config_path: str | Path = "config/devices.yaml",
    database_path: str | Path | None = None,
) -> Database:
    """Create the schema and register every configured device."""

    config = load_config(config_path)
    db_path = database_path or config.get("database", {}).get("path", "data/cybertwin.db")
    database = Database(db_path)
    database.initialize()
    records = [
        DeviceRecord(
            device_id=item["device_id"],
            name=item["name"],
            device_type=item["device_type"],
            source_ip=item["source_ip"],
            expected_destinations=item["expected_destinations"],
            expected_protocols=item["expected_protocols"],
        )
        for item in config["devices"]
    ]
    database.register_devices(records)
    return database


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the CyberTwin database")
    parser.add_argument("--config", default="config/devices.yaml")
    parser.add_argument("--database", default=None)
    args = parser.parse_args()
    database = initialize_from_config(args.config, args.database)
    print(f"Initialized {database.path} with {len(database.list_devices())} devices")


if __name__ == "__main__":
    main()

