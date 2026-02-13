# Cloud-AI Network Assistant — Phase 2 Guide (Ingestion + Storage + Query APIs)

This guide documents **Phase 2** end-to-end: what you built, why each step exists, the architecture, how to run it, and how to debug it.

---

## Phase 2 goal

Turn Phase 1 telemetry into a **backend ingestion system** that can:
- **receive** telemetry over HTTP,
- **validate** it,
- **persist** it to a database,
- **query** it efficiently (events/history/latest),
- **summarize** it (stats/rollups),
- **generate and store alerts** (Phase 2 rule-based plumbing).

This becomes the foundation for **Phase 3 anomaly detection** and a **dashboard**.

---

## What you learned (Phase 2 concepts)

- **API design** (ingestion endpoint, query endpoints, docs, health checks)
- **Schema enforcement** (Pydantic models shared across services)
- **Persistence** (SQLite + SQLAlchemy ORM)
- **Clean architecture** (CRUD layer + models + DB layer)
- **Query patterns** (filters, time ranges, pagination, ordering)
- **Aggregation** (SQL GROUP BY / AVG / MIN / MAX / COUNT)
- **Alert pipeline** (alerts as first-class persisted entities)
- **Docker/Compose** (multi-service stack, networking, persistence, healthchecks)
- **Debugging** (SQLAlchemy mapping errors, primary keys, URL routing)

---

## Phase 2 architecture

### High-level flow
```
Phase 1 Simulator (HTTP sink)
        |
        v
FastAPI Ingestion API  ---> validates TelemetryEvent schema
        |
        v
SQLite (SQLAlchemy ORM)
  - telemetry_events table
  - alerts table
        |
        +--> Query APIs (/latest, /history, /events)
        +--> Rollups (/stats)
        +--> Alerts APIs (/alerts, /alerts/{id}/resolve)
```

### Key design decisions
- **Contract-first:** Pydantic schema defines what “valid telemetry” is.
- **DB-backed:** data survives restarts; supports real queries and future scale-up.
- **CRUD separation:** queries and inserts live in a dedicated module for maintainability.
- **Composable endpoints:** “raw events” + “aggregated rollups” for dashboard readiness.
- **Alert table:** keeps alert lifecycle separate from high-volume telemetry.

---

## Recommended Phase 2 project structure

```
cloud-ai-network-assistant/
  backend/
    requirements.txt
    app/
      __init__.py
      main.py             # FastAPI routes
      models.py           # TelemetryEvent (API schema)
      db.py               # engine, session, Base, init_db()
      db_models.py        # SQLAlchemy ORM tables (TelemetryEventRow, AlertRow)
      crud.py             # inserts + queries (events, latest, history, alerts, stats)
      stats_models.py     # NodeStats response model
      alert_models.py     # AlertOut response model
  docker/
    backend.Dockerfile
    simulator.Dockerfile
  docker-compose.yml
  telemetry.db            # SQLite file (created at runtime)
```

---

## Phase 2 steps (what you built)

### Step 1 — FastAPI ingestion backend (in-memory store)
**Purpose:** stand up an API quickly to integrate simulator → backend.

Deliverables:
- FastAPI app with:
  - `POST /ingest`
  - `GET /health`
  - `GET /latest`
  - `GET /history`
- In-memory store using deques per node.

Suggested commit:
- `feat(backend): add FastAPI telemetry ingestion API with in-memory store`

---

### Step 2 — Persist telemetry to SQLite with SQLAlchemy
**Purpose:** make telemetry durable and queryable across restarts.

Deliverables:
- `db.py` (engine/session/Base/init_db)
- `db_models.py` (TelemetryEventRow table)
- `crud.py` (insert + queries)
- Updated `main.py` to use DB session per request.

Common bug you fixed:
- `Primary_key=True` typo prevented SQLAlchemy from detecting a PK:
  - Correct: `primary_key=True`

Suggested commits:
- `feat(backend): persist telemetry to SQLite using SQLAlchemy`
- `fix(backend): correct SQLAlchemy primary_key field on telemetry_events`

---

### Step 3 — Dockerize backend + run simulator→backend pipeline
**Purpose:** reproducible runtime, easier collaboration, cloud readiness.

Deliverables:
- `docker/backend.Dockerfile`
- Compose/networking pattern:
  - Host access: `http://127.0.0.1:8000`
  - Service-to-service: `http://backend:8000` (inside Compose)

Suggested commit:
- `feat(devops): dockerize backend service`

---

### Step 4 — Add production-style queries: filters + time range + pagination
**Purpose:** enable dashboard-like querying and scalable reads.

Deliverables:
- `GET /events` with:
  - `node` repeat param (`?node=r1&node=r2`)
  - `start_ts`, `end_ts`
  - `limit`, `offset`
- Ordering: newest-first.
- Index usage: `(node, timestamp)`.

Suggested commit:
- `feat(backend): add filtered /events endpoint with time range and pagination`

---

### Step 5 — Add rollups endpoint: `/stats`
**Purpose:** dashboard-ready aggregations; baseline summaries for Phase 3.

Deliverables:
- `GET /stats` returning per-node rollups:
  - count
  - avg/min/max latency
  - avg packet loss, throughput, cpu, mem
  - first/last timestamps
- Default window (e.g., last 15 minutes) if no range supplied.

Suggested commit:
- `feat(backend): add /stats endpoint with per-node time-window rollups`

---

### Step 6 — Persist alerts + expose `/alerts` APIs
**Purpose:** create a real alert pipeline (data model + queries + lifecycle).

Deliverables:
- `alerts` table:
  - node, rule_id, severity, message
  - created_ts, resolved_ts, is_active
- Endpoints:
  - `GET /alerts` (+ filters)
  - `POST /alerts/{id}/resolve`

Rule-based generation (Phase 2 scope):
- simple thresholds + cooldown (spam control)

Suggested commit:
- `feat(backend): persist alerts and add /alerts endpoints with rule-based thresholds`

---

### Step 7 — Docker Compose full stack + healthcheck + smoke tests
**Purpose:** “one command” to run the entire Phase 2 system.

Deliverables:
- `docker-compose.yml`:
  - backend healthcheck (`/health`)
  - simulator depends on backend healthy
  - persistent `telemetry.db` volume mount

Suggested commit:
- `feat(devops): add docker compose stack for simulator-to-backend pipeline`

---

## How to run (local development)

### Start backend
```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

### Verify backend
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

### Run simulator → backend (HTTP sink)
Use the backend URL:
- local: `http://127.0.0.1:8000/ingest`

Example:
```powershell
python -m simulator.main --config configs/simulator.dev.yaml --sink http --http-url http://127.0.0.1:8000/ingest
```

---

## How to run (Docker Compose)

```powershell
docker compose up --build
```

Then open:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/latest`
- `http://127.0.0.1:8000/events?limit=50`
- `http://127.0.0.1:8000/stats`
- `http://127.0.0.1:8000/alerts`

Stop:
```powershell
docker compose down
```

### Compose networking rule
Inside the simulator container, send to:
- `http://backend:8000/ingest`

---

## API reference (Phase 2)

### Health
- `GET /health` → `{ "status": "ok" }`

### Ingestion
- `POST /ingest` (TelemetryEvent JSON) → `{ accepted, node, timestamp }`

### Raw event queries
- `GET /latest`
- `GET /latest?node=router-1`
- `GET /history?node=router-1&limit=100`
- `GET /events?limit=200&offset=0`
- `GET /events?node=router-1&node=router-2&start_ts=...&end_ts=...`

### Rollups
- `GET /stats` (defaults to recent window)
- `GET /stats?window_s=300`
- `GET /stats?node=router-1&node=router-2&start_ts=...&end_ts=...`

### Alerts
- `GET /alerts`
- `GET /alerts?is_active=true`
- `GET /alerts?node=router-1`
- `POST /alerts/{id}/resolve`

---

## Smoke test checklist (Phase 2)

1) **Backend up**
- `GET /health` → 200

2) **Ingestion works**
- simulator running OR manual POST
- `GET /latest` → 200 + JSON event

3) **DB persistence**
- restart backend; data should still be queryable (SQLite file persists)

4) **Query endpoints**
- `/events` supports node/time filters and pagination
- `/history` returns correct node events

5) **Stats works**
- `/stats` returns rollups per node

6) **Alerts pipeline**
- thresholds triggered create alerts
- `/alerts` returns them
- `/alerts/{id}/resolve` flips `is_active=false`

---

## Debugging cheatsheet (Phase 2)

### SQLAlchemy error: “could not assemble any primary key columns”
Cause:
- PK not defined (often typo)

Fix:
- ensure column is: `primary_key=True` (lowercase, underscore)

---

### `/latest` returns 404
Cause:
- no telemetry ingested yet

Fix:
- start simulator HTTP sink or POST a sample event to `/ingest`

---

### Simulator in Docker cannot reach backend on localhost
Cause:
- `127.0.0.1` inside container points to itself

Fix:
- Use `http://backend:8000/ingest` (Compose) OR `host.docker.internal` (Docker Desktop → host)

---

### SQLite file not persisting
Cause:
- DB file created inside container filesystem only

Fix:
- mount `./telemetry.db:/app/telemetry.db`

---

## Phase 2 completion checklist

- [x] FastAPI ingestion running and documented (`/docs`)
- [x] Telemetry persisted to SQLite via SQLAlchemy
- [x] Query endpoints working (`/latest`, `/history`, `/events`)
- [x] Aggregated stats endpoint working (`/stats`)
- [x] Alerts stored and queryable (`/alerts`, resolve flow)
- [x] Docker Compose full stack runs
- [x] Ready for Phase 3 anomaly detection

---

## Next phase preview (Phase 3)

- Replace threshold alerts with **baseline-driven anomaly detection**
- Add baseline persistence (survive restarts)
- Evaluate detection quality (precision/recall on incident windows)
- Optional: Ollama to generate human-readable incident summaries (free/local)
