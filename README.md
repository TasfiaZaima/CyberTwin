# CyberTwin

CyberTwin is a local digital twin for learning normal IoT/edge network behavior
and identifying significant behavioral deviations. It uses structured flow
telemetry, explainable statistical scoring, and entirely local simulation. No
physical IoT devices or external attack targets are required.

## Current implementation: Phase 1

Phase 1 provides the repository structure, YAML device inventory, durable SQLite
schema, idempotent device registration, Docker foundation, and automated storage
tests. Later phases will add real telemetry generation, feature extraction,
behavioral twins, detection, API, and dashboard in that order.

## Setup

Python 3.11 or newer is required.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m database.setup
pytest
```

The initializer creates `data/cybertwin.db`, all five application tables, and
registers the four configured devices. It is safe to run repeatedly.

## Run and inspect Phase 1

Phase 1 is a database foundation and does not yet include a browser dashboard or
running API. After completing setup, initialize the project from PowerShell:

```powershell
cd D:\CyberTwin
.\.venv\Scripts\Activate.ps1
python -m database.setup
python -m pytest
```

Successful output will look similar to:

```text
Initialized data\cybertwin.db with 4 devices
4 passed
```

Print the configured devices and their expected behavior:

```powershell
python -c "from database.db import Database; import pprint; pprint.pp(Database().list_devices())"
```

The persistent database is stored at `data/cybertwin.db`. You can inspect it
with any SQLite browser, or use Python to list its application tables:

```powershell
python -c "from database.db import Database; print(sorted(Database().table_names()))"
```

Expected tables:

```text
alerts, baselines, devices, features, telemetry
```

On WSL/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m database.setup
pytest
```

To inspect devices on WSL/Linux:

```bash
python -c "from database.db import Database; import pprint; pprint.pp(Database().list_devices())"
```

## Docker

The Phase 1 container validates configuration and initializes persistent storage:

```bash
docker compose up --build
docker compose down
```

For Phase 1, `docker compose up --build` initializes the database volume and the
container then exits successfully. This is expected behavior. Once the API and
dashboard phases are implemented, their planned local addresses will be:

```text
API documentation: http://localhost:8000/docs
Dashboard:         http://localhost:8501
```

The private Docker network is deliberately internal. Device, gateway, API, and
dashboard services will be added as their working implementations are completed.

## Data model

- `devices`: configured identity, expectations, and current twin status
- `telemetry`: structured local flow events
- `features`: windowed behavioral measurements and scores
- `baselines`: reusable per-device feature statistics
- `alerts`: explainable anomaly findings and lifecycle state

Configuration is held in `config/devices.yaml`; runtime database files are not
committed.

## Research direction

The guiding research question is: *Can a digital twin-based behavioral model
improve the detection of anomalous activity in resource-constrained IoT and edge
environments?* No experimental result is claimed at this stage.
