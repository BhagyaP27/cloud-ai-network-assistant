from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import Optional, List

from simulator.models import TelemetryEvent
from .db_models import TelemetryEventRow

def insert_event(db: Session, event: TelemetryEvent) -> TelemetryEventRow:
    row = TelemetryEventRow(**event.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def get_latest(db: Session, node: Optional[str] = None) -> Optional[TelemetryEventRow]:
    stmt = select(TelemetryEventRow)
    if node:
        stmt = stmt.where(TelemetryEventRow.node == node)
    
    stmt = stmt.order_by(desc(TelemetryEventRow.timestamp), desc(TelemetryEventRow.id)).limit(1)

    row = db.execute(stmt).scalars().first()
    return TelemetryEvent.model_validate(row.__dict__) if row else None


def get_history(db: Session, node: str, limit: int=100) -> List[TelemetryEventRow]:
    stmt =(
        select(TelemetryEventRow)
        .where(TelemetryEventRow.node == node)
        .order_by(desc(TelemetryEventRow.timestamp), desc(TelemetryEventRow.id))
        .limit(limit)
    )

    rows = db.execute(stmt).scalars().all()
    #reverse so oldest->newest in the response
    rows = list(reversed(rows))
    return [TelemetryEvent.model_validate(row.__dict__) for row in rows]