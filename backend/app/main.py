from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from .models import TelemetryEvent
from .store import InMemoryTelemetryStore

app = FastAPI(title="Telemetry Ingestion API", version="0.1.0")
store = InMemoryTelemetryStore(max_events_per_node=2000)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest(event: TelemetryEvent):
    store.add(event)
    return {"accepted": True, "node": event.node, "timestamp": event.timestamp}

@app.get("/latest", response_model=TelemetryEvent)
def latest(node: Optional[str] = None):
    ev = store.latest(node=node)
    if ev is None:
        raise HTTPException(status_code=404, detail="No telemetry available")
    return ev

@app.get("/history", response_model=List[TelemetryEvent])
def history(
    node: str,
    limit: int = Query(default=100, ge=1, le=2000),
):
    return store.history(node=node, limit=limit)
