from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional, List
from sqlalchemy.orm import Session

from .models import TelemetryEvent
from .db import SessionLocal, init_db
from . import crud

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
