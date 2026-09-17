# CyberTwin

CyberTwin is a runnable, local digital twin of a small IoT/edge network. It learns
normal flow behavior per device, compares new observations with those baselines,
and produces explainable anomaly alerts. It does not contact external systems or
claim that an anomaly proves compromise.

> Research question: Can a digital twin-based behavioral model improve detection
> of anomalous activity in resource-constrained IoT and edge environments?

## Architecture

```text
Camera ───────┐
Smart Plug ───┼─> Edge/API collector -> SQLite telemetry -> Feature windows
Sensor ───────┤                                      |             |
Gateway ──────┘                                      v             v
                                              Behavioral baseline -> Detector
                                                                      |
                                                        Alerts <──────┘
                                                          |
                                                   Streamlit dashboard
```

The simulator produces structured flow telemetry, not raw packets. All named
destinations such as `mqtt.local` and `camera-cloud.local` are synthetic.

## Technology

Python 3.11+, SQLite, FastAPI, Streamlit, Pandas, NumPy, scikit-learn,
Pydantic, Plotly, pytest, Docker, and Docker Compose.

## Quick start with Docker

Install Docker Desktop, open PowerShell in the repository, and run:

```powershell
docker compose up --build
```

Open:

- Dashboard: http://localhost:8501
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

In the dashboard, follow the numbered demonstration:

1. Select **Generate normal data**.
2. Select **Train baselines**.
3. Choose a device and select **Simulate anomaly**.
4. Inspect its score, charts, expected-versus-observed values, and alert.

The camera, smart plug, temperature sensor, and edge gateway containers also
send normal structured telemetry to the API. Stop the stack with:

```powershell
docker compose down
```

The database persists in the `cybertwin-data` volume. To deliberately erase it:

```powershell
docker compose down -v
```

## Local Windows setup

```powershell
cd D:\CyberTwin
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m database.setup
```

If activation is blocked, first run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

WSL/Linux uses the equivalent commands:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m database.setup
```

## Run locally

### Complete terminal walkthrough

From a fresh copy of the project, open a VS Code PowerShell terminal and run
each command separately:

```powershell
cd D:\CyberTwin
python --version
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow it for the current terminal session and
try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies, initialize storage, and verify the installation:

```powershell
python -m pip install -r requirements.txt
python -m database.setup
python -m pytest
```

Expected initialization output includes:

```text
Initialized data\cybertwin.db with 4 devices
```

If a virtual environment is not wanted, omit its creation and activation and
run the remaining `python -m ...` commands with the installed Python directly.

After setup, use the two-terminal instructions below to start the application.

The API and dashboard are separate processes, so they must run at the same time
in two VS Code terminals.

1. Open the CyberTwin folder in VS Code.
2. Select **Terminal → New Terminal**. This is Terminal 1.
3. Start the API using the commands below and leave this terminal running.
4. Click the **+** button in the Terminal panel to create Terminal 2. You can
   alternatively click **Split Terminal** to display both terminals side by side.
5. Start the dashboard in Terminal 2 and leave it running.

### Terminal 1 — API

With a virtual environment:

```powershell
cd D:\CyberTwin
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload
```

Without a virtual environment:

```powershell
cd D:\CyberTwin
python -m uvicorn api.main:app --reload
```

Wait until Terminal 1 reports that Uvicorn is running at
`http://127.0.0.1:8000`. Do not close this terminal.

### Terminal 2 — Dashboard

With a virtual environment:

```powershell
cd D:\CyberTwin
.\.venv\Scripts\Activate.ps1
python -m streamlit run dashboard/app.py
```

Without a virtual environment:

```powershell
cd D:\CyberTwin
python -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
```

Wait until Terminal 2 displays the Streamlit URL. Then open:

- Dashboard: http://127.0.0.1:8501
- API documentation: http://127.0.0.1:8000/docs

Both terminals must remain running while CyberTwin is in use:

```text
VS Code Terminal 1                         VS Code Terminal 2
API on http://127.0.0.1:8000               Dashboard on http://127.0.0.1:8501
python -m uvicorn api.main:app --reload     python -m streamlit run dashboard/app.py
```

To stop the project, select each terminal and press `Ctrl+C`.

### Verify that both services are running

From a third terminal, these commands should return data rather than an error:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/devices
```

If the API works but the dashboard does not, check that Terminal 2 is still
running and restart it with:

```powershell
python -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
```

### Terminal-only demonstration

The API and dashboard are optional for a quick command-line demonstration. Run:

```powershell
python -m cybertwin start
python -m cybertwin train
python -m cybertwin status
python -m cybertwin attack camera-01
python -m cybertwin status
```

The final status should identify `camera-01` as anomalous while the other
devices remain normal.

## CLI workflow

The same end-to-end demonstration can run without a browser:

```powershell
python -m cybertwin start
python -m cybertwin train
python -m cybertwin status
python -m cybertwin attack camera-01
python -m cybertwin status
```

Individual simulation commands are also available:

```powershell
python -m simulation.normal
python -m simulation.anomaly --device camera-01
python -m twin.baseline --device camera-01
```

## Behavioral model

Each one-minute window includes packets/sec, bytes/sec, connections/minute,
unique destinations and ports, DNS requests, TCP and UDP connections, average
packet size, and outbound ratio. Baseline training stores the mean, standard
deviation, range, and 5th/95th percentiles for each feature.

The default detector combines multiple normalized statistical deviations into a
score. An optional Isolation Forest is available after at least ten windows.

```text
0.00–0.29  NORMAL
0.30–0.59  LOW / DEGRADED
0.60–0.79  MEDIUM / ANOMALOUS
0.80–1.00  HIGH / ANOMALOUS
```

Alerts record detector, baseline values, observations, feature contributions,
and the assessment “Potential compromise / abnormal behavior detected.”

## REST API

Key endpoints:

```text
GET  /health
GET  /devices
GET  /devices/{device_id}/state
GET  /devices/{device_id}/telemetry
GET  /devices/{device_id}/features
GET  /devices/{device_id}/alerts
GET  /alerts
POST /telemetry
POST /simulation/start
POST /simulation/stop
POST /simulation/anomaly/{device_id}
POST /baseline/train
```

FastAPI provides interactive request documentation at `/docs`.

## Database

Local execution stores data in `data/cybertwin.db`. Tables are `devices`,
`telemetry`, `features`, `baselines`, and `alerts`. Inspect the file with a VS
Code SQLite viewer, or run:

```powershell
python -c "from database.db import Database; import pprint; pprint.pp(Database().list_devices())"
```

## Testing

```powershell
python -m pytest
```

The suite checks storage, deterministic simulations, exact feature calculations,
baseline persistence, anomaly score separation, alert creation, and major API
workflow endpoints.

## Project structure

```text
alerts/       explainable alert persistence
api/          FastAPI application
collector/    validated flow ingestion
config/       device inventory and thresholds
cybertwin/    unified CLI
dashboard/    Streamlit UI
database/     SQLite schema and access
detection/    statistical and Isolation Forest detectors
devices/      containerized device producers
features/     flow-window aggregation
simulation/   deterministic normal and anomaly generation
tests/        automated verification
twin/         digital-twin state and baseline learning
```

## Research and future work

Evaluation should measure detection rate, false-positive rate, latency, CPU,
memory, network overhead, and inference time. No research result is claimed
without experiments. Future work includes packet capture, public IoT datasets,
federated and lightweight learning, concept drift, adversarial ML,
privacy-preserving telemetry, evidence hash chains, Raspberry Pi deployment,
and distributed edge gateways.
