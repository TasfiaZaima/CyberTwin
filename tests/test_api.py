from fastapi.testclient import TestClient
import api.main as api_module
from database.setup import initialize_from_config
from tests.test_database import output_path

def test_major_api_workflow():
    api_module.database = initialize_from_config(database_path=output_path("api.db"))
    client = TestClient(api_module.app)
    assert client.get("/health").status_code == 200
    assert len(client.get("/devices").json()) == 4
    assert client.post("/simulation/start", json={"windows": 3}).status_code == 200
    assert client.post("/baseline/train").status_code == 200
    response = client.post("/simulation/anomaly/camera-01")
    assert response.status_code == 200
    assert response.json()["status"] == "ANOMALOUS"
    assert client.get("/devices/camera-01/telemetry").json()
    assert client.get("/devices/camera-01/features").json()
    assert client.get("/alerts").json()
