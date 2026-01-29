from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
import time

from .models import TelemetryEvent
from .db import SessionLocal, init_db
from . import crud
from .stats_models import NodeStats
from .db_models import AlertRow
from .alert_models import AlertOut

app = FastAPI(title="Telemetry Ingestion API", version="0.2.0")

@app.on_event("startup")
def on_startup():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest(event: TelemetryEvent, db: Session = Depends(get_db)):
    crud.insert_event(db, event)

    # --- Phase 2 rule-based alerting (simple thresholds) ---
    # Cooldown so we don't spam duplicate alerts
    cooldown_s = 30

    def maybe_alert(rule_id: str, severity: str, message: str):
        existing = crud.get_active_alert(db, event.node, rule_id)
        if existing and (event.timestamp - existing.created_ts) < cooldown_s:
            return
        crud.create_alert(db, event.node, rule_id, severity, message)

    if event.latency_ms >= 200:
        maybe_alert("latency_high", "WARN", f"High latency: {event.latency_ms:.1f} ms")

    if event.packet_loss >= 0.02:
        maybe_alert("packet_loss_high", "WARN", f"High packet loss: {event.packet_loss:.3f}")

    if event.cpu_pct >= 90:
        maybe_alert("cpu_high", "CRITICAL", f"High CPU: {event.cpu_pct:.1f}%")

    return {"accepted": True, "node": event.node, "timestamp": event.timestamp}


@app.get("/latest", response_model=TelemetryEvent)
def latest(node: Optional[str] = None, db: Session = Depends(get_db)):
    ev = crud.get_latest(db, node=node)
    if ev is None:
        raise HTTPException(status_code=404, detail="No telemetry available")
    return ev

@app.get("/history", response_model=List[TelemetryEvent])
def history(
    node: str,
    limit: int = Query(default=100, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    return crud.get_history(db, node=node, limit=limit)

@app.get("/events", response_model=List[TelemetryEvent])
def events(
    node: Optional[List[str]] = Query(default=None, description="Repeat param: ?node=r1&node=r2"),
    start_ts: Optional[int] = Query(default=None, description="Unix seconds, inclusive"),
    end_ts: Optional[int] = Query(default=None, description="Unix seconds, inclusive"),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.query_events(
        db,
        nodes=node,
        start_ts=start_ts,
        end_ts=end_ts,
        limit=limit,
        offset=offset,
    )

@app.get("/stats", response_model=list[NodeStats])
def stats(
    node: Optional[list[str]] = Query(default=None, description="Repeat param: ?node=r1&node=r2"),
    start_ts: Optional[int] = Query(default=None),
    end_ts: Optional[int] = Query(default=None),
    window_s: int = Query(default=900, ge=60, le=86400, description="Default window if start/end not provided"),
    db: Session = Depends(get_db),
):
    # Default to last window_s seconds if no explicit range passed
    now = int(time.time())
    if start_ts is None and end_ts is None:
        end_ts = now
        start_ts = now - window_s
    elif start_ts is None and end_ts is not None:
        start_ts = end_ts - window_s
    elif start_ts is not None and end_ts is None:
        end_ts = start_ts + window_s

    return crud.get_node_stats(db, nodes=node, start_ts=start_ts, end_ts=end_ts)


@app.get("/alerts", response_model=list[AlertOut])
def alerts(
    node: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.list_alerts(db, node=node, is_active=is_active, limit=limit, offset=offset)

@app.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve(alert_id: int, db: Session = Depends(get_db)):
    row = crud.resolve_alert(db, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut(
        id=row.id,
        node=row.node,
        rule_id=row.rule_id,
        severity=row.severity,  # type: ignore
        message=row.message,
        created_ts=row.created_ts,
        resolved_ts=row.resolved_ts,
        is_active=row.is_active,
    )
