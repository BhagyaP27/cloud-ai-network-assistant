from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from sqlalchemy import and_
from sqlalchemy import func
from typing import Optional, List
import time

from simulator.models import TelemetryEvent
from .db_models import TelemetryEventRow, AlertRow
from .alert_models import AlertOut
from .stats_models import NodeStats

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

def query_events(
    db: Session,
    nodes: Optional[List[str]] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[TelemetryEvent]:
    stmt = select(TelemetryEventRow)

    if nodes:
        stmt = stmt.where(TelemetryEventRow.node.in_(nodes))
    if start_ts is not None:
        stmt = stmt.where(TelemetryEventRow.timestamp >= start_ts)
    if end_ts is not None:
        stmt = stmt.where(TelemetryEventRow.timestamp <= end_ts)

    stmt = (
        stmt.order_by(desc(TelemetryEventRow.timestamp), desc(TelemetryEventRow.id))
        .limit(limit)
        .offset(offset)
    )

    rows = db.execute(stmt).scalars().all()
    # Return newest->oldest (monitoring-style). If you want oldest->newest, reverse.
    return [TelemetryEvent.model_validate(r.__dict__) for r in rows]

def get_node_stats(
    db: Session,
    nodes: Optional[List[str]] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
) -> List[NodeStats]:
    stmt = select(
        TelemetryEventRow.node.label("node"),
        func.count(TelemetryEventRow.id).label("count"),

        func.avg(TelemetryEventRow.latency_ms).label("latency_avg"),
        func.min(TelemetryEventRow.latency_ms).label("latency_min"),
        func.max(TelemetryEventRow.latency_ms).label("latency_max"),

        func.avg(TelemetryEventRow.packet_loss).label("packet_loss_avg"),
        func.avg(TelemetryEventRow.throughput_mbps).label("throughput_avg"),
        func.avg(TelemetryEventRow.cpu_pct).label("cpu_avg"),
        func.avg(TelemetryEventRow.mem_pct).label("mem_avg"),

        func.min(TelemetryEventRow.timestamp).label("first_ts"),
        func.max(TelemetryEventRow.timestamp).label("last_ts"),
    ).group_by(TelemetryEventRow.node)

    if nodes:
        stmt = stmt.where(TelemetryEventRow.node.in_(nodes))
    if start_ts is not None:
        stmt = stmt.where(TelemetryEventRow.timestamp >= start_ts)
    if end_ts is not None:
        stmt = stmt.where(TelemetryEventRow.timestamp <= end_ts)

    rows = db.execute(stmt).all()

    # rows are tuples with named labels; map them into NodeStats
    out: List[NodeStats] = []
    for r in rows:
        m = r._mapping  # SQLAlchemy row mapping
        out.append(NodeStats(**dict(m)))
    return out

def _now_ts() -> int:
    return int(time.time())

def create_alert(
    db: Session,
    node: str,
    rule_id: str,
    severity: str,
    message: str,
) -> AlertRow:
    row = AlertRow(
        node=node,
        rule_id=rule_id,
        severity=severity,
        message=message,
        created_ts=_now_ts(),
        resolved_ts=None,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def get_active_alert(db: Session, node: str, rule_id: str) -> Optional[AlertRow]:
    stmt = (
        select(AlertRow)
        .where(AlertRow.node == node, AlertRow.rule_id == rule_id, AlertRow.is_active == True)  # noqa: E712
        .order_by(desc(AlertRow.created_ts), desc(AlertRow.id))
        .limit(1)
    )
    return db.execute(stmt).scalars().first()

def resolve_alert(db: Session, alert_id: int) -> Optional[AlertRow]:
    row = db.get(AlertRow, alert_id)
    if not row:
        return None
    row.is_active = False
    row.resolved_ts = _now_ts()
    db.commit()
    db.refresh(row)
    return row

def list_alerts(
    db: Session,
    node: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 200,
    offset: int = 0,
) -> list[AlertOut]:
    stmt = select(AlertRow)

    if node:
        stmt = stmt.where(AlertRow.node == node)
    if is_active is not None:
        stmt = stmt.where(AlertRow.is_active == is_active)

    stmt = stmt.order_by(desc(AlertRow.created_ts), desc(AlertRow.id)).limit(limit).offset(offset)
    rows = db.execute(stmt).scalars().all()

    return [
        AlertOut(
            id=r.id,
            node=r.node,
            rule_id=r.rule_id,
            severity=r.severity,  # type: ignore
            message=r.message,
            created_ts=r.created_ts,
            resolved_ts=r.resolved_ts,
            is_active=r.is_active,
        )
        for r in rows
    ]
