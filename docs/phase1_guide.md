# Cloud-AI Network Assistant — Phase 1 Guide (Simulator Foundations)

This guide documents **Phase 1** of the project end-to-end: what you built, why each step exists, the architecture, and how to run/debug it.

---

## Phase 1 goal

Build a **realistic telemetry simulator** that emits validated network telemetry events and can output them to different “sinks” (stdout/file/http). This simulator becomes the data source for Phase 2+ (ingestion API, storage, anomaly detection, dashboard, etc.).

---

## What you learned (Phase 1 concepts)

- **Schema-first design** with Pydantic (data contracts, validation, fast feedback on bugs)
- **Time-series simulation** (baselines, cycles, correlations, noise)
- **Incident injection** (time-bounded abnormal behaviors with severity)
- **Decoupling output via “sinks”** (adapter pattern)
- **Config-driven runtime** (YAML defaults + CLI overrides)
- **Testing** (validation/ranges, determinism, incident timing)
- **Docker basics** (containerize, run, mount volumes)
- **Debugging** common issues (Pydantic literal mismatch, import paths in pytest, Docker engine, float vs list severity)

---

## Core event contract (TelemetryEvent)

### Fields
- `node: str`
- `latency_ms: float (>=0)`
- `packet_loss: float (0..1)`
- `throughput_mbps: float (>=0)`
- `cpu_pct: float (0..100)`
- `mem_pct: float (0..100)`
- `timestamp: int` (Unix seconds)
- `status: Literal["OK","WARN","CRITICAL"]`

### Why it matters
This is the **single source of truth** for all services: simulator emits it, backend ingests it, storage persists it, detection uses it, dashboard displays it.

---

## Phase 1 architecture

### High-level flow
```
NodeModel (baselines + cycles + correlations)
   + IncidentModel (time windows + severity)
        |
        v
TelemetryEvent (Pydantic schema)
        |
        v
Sink Adapter  ---> stdout
             ---> file (JSONL)
             ---> http (Phase 2 ingestion)
```

### Key design patterns
- **Adapter pattern (Sinks):** swap output destination without changing generation logic
- **Separation of concerns:** generation vs incident logic vs output vs configuration

---

## Recommended project structure (Phase 1)

```
cloud-ai-network-assistant/
  simulator/
    __init__.py
    main.py                # CLI entrypoint
    models.py              # TelemetryEvent schema
    node_model.py          # realistic per-node generator
    incident_model.py      # Incident objects + build_incidents()
    settings.py            # YAML config models + loader
    sinks/
      stdout_sink.py
      file_sink.py
      http_sink.py         # posts to ingestion API
  configs/
    simulator.dev.yaml
  tests/
    test_models.py
    test_determinism.py
    test_incidents.py
  docker/
    simulator.Dockerfile
  pytest.ini
  requirements.txt
```

---

## Step-by-step (what you built)

### Step 1 — TelemetryEvent schema + print JSON
**Purpose:** define the contract early and validate outputs from day 1.

Deliverables:
- `simulator/models.py` with `TelemetryEvent`
- Basic script that creates an event and prints JSON

Common bug you fixed:
- Schema required `latency_ms`, but code used a mismatched field name → Pydantic error.

Suggested commit:
- `feat: define TelemetryEvent model / event schema and print sample JSONL event`

---

### Step 2 — Streaming loop (async) + JSONL output
**Purpose:** emit continuous events like a live telemetry feed.

Deliverables:
- `asyncio` loop emitting N nodes at `emit_hz`

Suggested commit:
- `feat(simulator): stream telemetry events at fixed rate`

---

### Step 3 — Realistic node behavior (baselines + cycles + correlations)
**Purpose:** make data realistic for anomaly detection and dashboards.

Deliverables:
- `NodeModel` per node:
  - per-node baselines
  - smooth load cycle (demo 60s)
  - correlated metrics:
    - load↑ → cpu↑, latency↑, throughput↓, loss↑

Suggested commit:
- `feat(simulator): add NodeModel with correlated time-series telemetry`

---

### Step 4 — Incidents (time-bounded anomalies)
**Purpose:** produce labeled “abnormal” segments to test detection & alerting.

Deliverables:
- `Incident` dataclass with `start_ts/end_ts/severity`
- `build_incidents()` from config
- `effects_for_node()` / `effect_for_node()` to apply active incidents

Examples:
- router-3 latency spike
- router-2 loss burst
- global cpu spike

Suggested commit:
- `feat(simulator): add incident injection and apply effects per node`

---

### Step 5 — Sinks (stdout/file/http)
**Purpose:** decouple generation from output destination; prepare for ingestion.

Deliverables:
- `StdoutSink`, `FileSink`, `HttpSink` adapters
- `sink.emit(event)` in main loop

Suggested commit:
- `feat(simulator): add sink adapters for stdout, file, and http`

---

### Step 6 — YAML config + CLI overrides
**Purpose:** run the same code with different settings without editing code.

Deliverables:
- `configs/simulator.dev.yaml`
- `settings.py` with Pydantic config models
- CLI args:
  - `--config`
  - `--emit-hz`
  - `--nodes`
  - `--sink`
  - `--file-path`
  - `--http-url`

Suggested commit:
- `feat(simulator): add YAML config and CLI overrides`

---

### Step 7 — Tests (validation + determinism + incident timing)
**Purpose:** make your simulator reliable and debuggable.

Deliverables:
- `pytest.ini` with `pythonpath = .` (fix import errors)
- tests:
  - schema/range validation
  - deterministic generation with same seed/time
  - incident active window behavior

Suggested commit:
- `test(simulator): add validation, determinism, and incident timing tests`

---

### Step 8 — Dockerize simulator
**Purpose:** reproducible runtime environment; prepares for K8s later.

Deliverables:
- `docker/simulator.Dockerfile`
- `.dockerignore`
- `requirements.txt`

Suggested commit:
- `feat(simulator): dockerize phase 1 simulator`

---

## How to run (local)

### Stdout
```powershell
python -m simulator.main --config configs/simulator.dev.yaml
```

### File (JSONL)
```powershell
python -m simulator.main --config configs/simulator.dev.yaml --sink file --file-path telemetry.jsonl
```

### HTTP (Phase 2 ingestion)
```powershell
python -m simulator.main --config configs/simulator.dev.yaml --sink http --http-url http://127.0.0.1:8000/ingest
```

---

## How to run (Docker)

### Build
```powershell
docker build -f docker/simulator.Dockerfile -t simulator:phase1 .
```

### Run (stdout)
```powershell
docker run --rm simulator:phase1
```

### Run with host-mounted volume + file sink
```powershell
docker run --rm -v ${PWD}:/app simulator:phase1 python -m simulator.main --config configs/simulator.dev.yaml --sink file --file-path telemetry.jsonl
```

### Run in Docker while FastAPI runs on host (HTTP sink)
Use `host.docker.internal` inside container:
```yaml
sink:
  type: http
  url: "http://host.docker.internal:8000/ingest"
```

---

## Testing

```powershell
python -m pytest -q
```

If imports fail:
- ensure `simulator/__init__.py` exists
- ensure `pytest.ini` contains:
```ini
[pytest]
testpaths = tests
pythonpath = .
```

---

## Debugging cheatsheet (Phase 1)

### Pydantic literal mismatch for `status`
Error:
- allowed: `OK/WARN/CRIT` but generator emitted `CRITICAL`

Fix:
- align schema to `Literal["OK","WARN","CRITICAL"]` or adjust generator.

---

### Timestamp prints with `.0`
Cause:
- schema typed `timestamp` as float or older code in Docker image

Fix:
- `timestamp: int = Field(default_factory=lambda: int(time.time()))`
- rebuild docker image if needed.

---

### `ModuleNotFoundError: simulator` in pytest
Fix:
- add `simulator/__init__.py`
- add `pytest.ini` with `pythonpath=.`

---

### Docker engine connection error on Windows
Typical fix:
- start Docker Desktop
- switch to Linux containers / enable WSL2 engine
- `docker context use desktop-linux`

---

### `TypeError: '>' not supported between float and list` (severity)
Cause:
- `severity` loaded as list in config chain

Fix (robust):
- normalize severity to float in `effect_for_node` and/or `build_incidents`:
```py
if isinstance(sev, list): sev = sev[0] if sev else 1.0
sev = float(sev)
```

Suggested commit:
- `fix(simulator): normalize incident severity to float in effect mapping`

---

## Phase 1 completion checklist

- [x] Simulator emits realistic telemetry
- [x] Incident injection works and doesn’t crash
- [x] Sinks support stdout/file/http
- [x] YAML + CLI configuration works
- [x] Tests pass
- [x] Docker build/run works
- [x] Ready for Phase 2 ingestion + DB + dashboards

---

## Next phases (preview)

- **Phase 2:** FastAPI ingestion + database persistence + containerized stack
- **Phase 3:** Anomaly detection (statistical + optional Ollama explanations)
- **Phase 4:** Alerting + replay + evaluation metrics
- **Phase 5:** Frontend dashboard (charts, filters, drilldowns)
- **Phase 6:** Cloud deployment (Docker Compose → K8s basics)

---

If you want, I can generate a matching **Phase 2 guide** after you complete Step 2/3, and we’ll keep a consistent documentation style across phases.
