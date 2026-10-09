# Air-Gapped AI Copilot for Predictive MPLS Network Operations

## Stage 1: MPLS Network Simulator Module

This repository contains the independent **MPLS Network Simulator** module for the college Software Engineering project *“Air-Gapped AI Copilot for Predictive MPLS Network Operations”*.

---

### System Architecture Boundary

```
+--------------------------------------------------------------+
|                    MPLS Network Simulator                    |
|   (Virtual Routers • Stochastic Physics • Fault Injection)   |
+--------------------------------------------------------------+
                                |
                                v
               Generated Telemetry Stream (JSON Lines)
                                |
                                v
+--------------------------------------------------------------+
|            Local Structured Log Storage                      |
|                  logs/telemetry.jsonl                        |
+--------------------------------------------------------------+
                                |
                                v  (Future Stages - Separate)
+--------------------------------------------------------------+
|   Log Collection & Processing -> Database -> AI Analytics   |
+--------------------------------------------------------------+
```

> **Important Boundary Rule**: The simulator's sole responsibility is creating configurable virtual MPLS routers, simulating network behavior, and producing machine-readable structured telemetry logs. The simulator **does not** perform anomaly detection, failure prediction, ML models, or dashboard analytics.

---

### Features & Capabilities

1. **Dynamic Virtual Routers**:
   - Create as many virtual routers as needed (`R1`, `R2`, `R3`, `R4`, `R5`, `R6`, ...).
   - Each card displays Router ID, descriptive name, and status (`ACTIVE`, `FAULTED`, `OFFLINE`).
   - Clean, uncluttered interface preserving the tactile 3D clay aesthetic.

2. **Real-Time Telemetry Hover Popover**:
   - Hovering over any router card reveals live dynamic metrics:
     - **Latency** (ms)
     - **Packet Loss** (%)
     - **Jitter** (ms)
     - **Bandwidth Usage** (%) with visual gauge
     - **CPU Usage** (%) with visual gauge
     - **Memory Usage** (%) with visual gauge

3. **Stochastic Physics Engine**:
   - Realistic baselines with natural mean-reversion drift and sensible cross-metric correlations (e.g. queue buildup when bandwidth > 70% or CPU > 70% introduces queuing latency and packet jitter).

4. **Controlled Fault Injection**:
   - Target Router selection across all provisioned nodes.
   - Fault Types:
     - `Latency Spike`
     - `Packet Loss Spike`
     - `High Jitter`
     - `Bandwidth Congestion`
     - `CPU Overload`
     - `Memory Overload`
     - `Link Failure`
   - Configurable **Duration** (10s, 15s, 30s, 60s, 120s) and **Intensity** (Low, Medium, High).
   - Faulted routers transition to `FAULTED` status, display active perturbation banner with countdown timer, and automatically recover toward normal baseline upon expiration.

5. **Local Persistent Log Storage**:
   - Continually appends all generated telemetry records to `logs/telemetry.jsonl`.
   - Thread-safe, machine-readable JSON Lines format ready for ingestion by downstream pipeline modules.

---

### Project Structure

```
d:\Projects\Software Engg\
├── logs\
│   └── telemetry.jsonl          # Persisted JSON Lines log file
├── simulator\
│   ├── __init__.py
│   ├── models.py                # Data structures: Router, Fault, TelemetryRecord
│   ├── storage.py               # Local persistent JSON Lines storage manager
│   ├── engine.py                # Real-time simulation & stochastic telemetry engine
│   └── server.py                # FastAPI REST API & static web server
├── static\
│   ├── index.html               # Tactile clay simulator web interface
│   └── app.js                   # Real-time frontend controller & polling
├── Generator UI\
│   ├── code.html                # Standalone simulator UI (tactile clay interface)
│   └── DESIGN.md                # Tactile clay design system tokens
├── run_simulator.py             # One-click simulator runner
├── test_simulator.py            # Automated test suite (7 tests)
└── README.md                    # Project documentation
```

---

### How to Run the Simulator

#### 1. Start the Simulator Server

Run the Python launcher in your terminal:

```bash
python run_simulator.py
```

This will:
- Initialize the simulation engine with default nodes (`R1`, `R2`, `R3`, `R4`).
- Start real-time telemetry generation and log writing to `logs/telemetry.jsonl`.
- Host the REST API and tactile web UI at `http://127.0.0.1:8000`.
- Automatically open `http://127.0.0.1:8000` in your web browser.

#### 2. Run the Verification Test Suite

To verify all simulator components automatically:

```bash
python test_simulator.py
```

Tests run in under 0.1s and verify:
- Default router initialization.
- Dynamic router creation (`R5`, `R6`...).
- Metric variation and baseline stability.
- Fault injection behavior (`CPU Overload`, `Latency Spike`).
- Fault countdown and baseline recovery.
- Local JSON Lines log persistence and schema conformance.

---

### Telemetry Record Schema

Every generated record saved in `logs/telemetry.jsonl` contains:

```json
{
  "timestamp": "2026-10-08T14:29:42.441Z",
  "router_id": "R1",
  "latency": 14.44,
  "packet_loss": 0.08,
  "jitter": 2.73,
  "bandwidth_usage": 45.6,
  "cpu_usage": 34.2,
  "memory_usage": 35.5,
  "status": "ACTIVE",
  "active_fault": null
}
```

Under active fault conditions:

```json
{
  "timestamp": "2026-10-08T14:28:15.120Z",
  "router_id": "R3",
  "latency": 82.50,
  "packet_loss": 1.75,
  "jitter": 16.30,
  "bandwidth_usage": 48.0,
  "cpu_usage": 94.6,
  "memory_usage": 42.1,
  "status": "FAULTED",
  "active_fault": "CPU Overload"
}
```

---

## Part 2: Network Operations Platform & Data Layer

### Part 2 Architecture Overview

```
+--------------------------------------------------------------+
|            Simulator Telemetry Stream (Part 1)               |
|                   logs/telemetry.jsonl                       |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|              Continuous Log Collector Service                |
|        (Byte-offset Tracking • Deduplication • Validation)    |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|               Local SQLite Operations Database               |
|             network_ops_platform/data/ops_platform.db        |
|      (UNIQUE(router_id, timestamp) • WAL Mode • Indexes)     |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|                REST API Layer (FastAPI Port 8001)            |
|       (/api/status • /api/telemetry/* • /api/collector/*)    |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|              Monitor Dashboard (Port 8080)                   |
|        (Tactile Dark Skeuomorphic Mission-Control UI)        |
+--------------------------------------------------------------+
```

### Backend Components (`network_ops_platform/backend/`)

1. **`config.py`**:
   - Centralized paths for logs (`logs/telemetry.jsonl`) and database (`network_ops_platform/data/ops_platform.db`).
   - Configurable poll interval, batch size, and host/port.

2. **`models.py`**:
   - Pydantic validation schemas (`RawTelemetryInput`) enforcing data bounds and types.
   - Response models (`RouterLatestState`, `TelemetryStats`, `CollectorStatusResponse`).

3. **`database.py`**:
   - High-performance SQLite engine configured with `WAL` mode and indexed for fast time-series queries.
   - Enforces `UNIQUE(router_id, timestamp)` with `INSERT OR IGNORE` to guarantee zero duplicate records.
   - Methods: `insert_telemetry_batch`, `get_latest_telemetry`, `get_recent_telemetry`, `get_latest_router_states`, `get_telemetry_stats`.

4. **`collector.py`**:
   - Incremental Log Collector that tracks byte-offset bookmarks in SQLite.
   - Automatically handles file rotation, growth, and resets.
   - Graceful error resilience: skips corrupted/malformed lines without interrupting collection.

5. **`api.py`**:
   - REST API endpoints for telemetry querying, per-router inspection, health statistics, and collector diagnostics.

### How to Run the Operations Platform Backend

Start the Log Collector and REST API on port `8001`:

```bash
python run_ops_backend.py
```

* **API Base URL:** `http://127.0.0.1:8001`
* **Interactive Swagger Documentation:** `http://127.0.0.1:8001/docs`

### Key API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | `GET` | Platform operational health, DB location & statistics |
| `/api/collector/status` | `GET` | Detailed Log Collector diagnostics and counters |
| `/api/collector/trigger` | `POST` | Manually triggers an immediate ingestion cycle |
| `/api/telemetry/latest` | `GET` | Retrieves newest telemetry records across routers |
| `/api/telemetry/recent` | `GET` | Time-windowed telemetry (`?minutes=15&limit=200`) |
| `/api/telemetry/routers` | `GET` | Latest health and performance state of each router |
| `/api/telemetry/routers/{id}` | `GET` | Historical telemetry records for a specific router |
| `/api/telemetry/stats` | `GET` | Network-wide statistics: min/max/avg, status distribution |

### Run Backend Tests

```bash
python -m unittest test_ops_platform.py -v
```

