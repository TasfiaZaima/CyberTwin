"""FastAPI control plane for CyberTwin."""
from __future__ import annotations
import os
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from collector.collector import FlowEvent, TelemetryCollector
from database.setup import initialize_from_config
from simulation.generator import PROFILES
from simulation.service import simulate_all, simulate_window
from twin.baseline import train_baseline

DB_PATH = os.getenv("CYBERTWIN_DB", "data/cybertwin.db")
database = initialize_from_config(database_path=DB_PATH)
app = FastAPI(title="CyberTwin API", version="1.0.0",
              description="Behavioral digital twin for a local simulated IoT network")


class SimulationRequest(BaseModel):
    windows: int = Field(default=10, ge=1, le=100)


@app.get("/health")
def health() -> dict[str, Any]: return {"status": "ok", "database": str(database.path)}

@app.get("/devices")
def devices() -> list[dict[str, Any]]: return database.list_devices()

@app.get("/devices/{device_id}")
def device(device_id: str) -> dict[str, Any]:
    value = database.get_device(device_id)
    if value is None: raise HTTPException(404, "Device not found")
    return value

@app.get("/devices/{device_id}/state")
def state(device_id: str) -> dict[str, Any]:
    value = device(device_id); rows = database.feature_rows(device_id, 1)
    return {"device": value, "observed": rows[0] if rows else None,
            "baseline": database.baselines(device_id)}

@app.get("/devices/{device_id}/telemetry")
def telemetry(device_id: str, limit: int = Query(200, ge=1, le=5000)): return database.telemetry(device_id, limit)

@app.get("/devices/{device_id}/features")
def features(device_id: str, limit: int = Query(200, ge=1, le=1000)): return database.feature_rows(device_id, limit)

@app.get("/devices/{device_id}/alerts")
def device_alerts(device_id: str): return database.alerts(device_id)

@app.get("/alerts")
def alerts(): return database.alerts()

@app.post("/telemetry", status_code=201)
def collect(event: FlowEvent): return {"id": TelemetryCollector(database).collect(event)}

@app.post("/simulation/start")
def start(request: SimulationRequest):
    simulate_all(database, request.windows); return {"status": "completed", "windows": request.windows}

@app.post("/simulation/stop")
def stop(): return {"status": "idle", "detail": "Batch simulation has no background process to stop"}

@app.post("/simulation/anomaly/{device_id}")
def anomaly(device_id: str, detector: str = "statistical"):
    if device_id not in PROFILES: raise HTTPException(404, "Device not found")
    try: return simulate_window(database, device_id, 9999, True, detector)
    except ValueError as error: raise HTTPException(409, str(error)) from error

@app.post("/baseline/train")
def baseline_train():
    trained = {}
    for device_id in PROFILES:
        try: trained[device_id] = train_baseline(database, device_id)
        except ValueError as error: raise HTTPException(409, str(error)) from error
    return {"trained": list(trained), "feature_count": sum(len(v) for v in trained.values())}

