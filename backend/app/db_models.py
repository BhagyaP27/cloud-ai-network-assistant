from sqlalchemy import Column, Integer, Float, String, Index
from sqlalchemy import Boolean
from .db import Base

class TelemetryEventRow(Base):
    __tablename__ = "telemetry_events"

    id = Column(Integer, primary_key=True,index=True)
    node = Column(String, index=True, nullable=False)

    latency_ms = Column(Float, nullable=False)
    packet_loss = Column(Float, nullable=False)
    throughput_mbps = Column(Float, nullable=False)
    cpu_pct = Column(Float, nullable=False)
    mem_pct = Column(Float, nullable=False)

    timestamp = Column(Integer, index=True, nullable=False)
    status = Column(String, nullable=False)

#index for node history queries
Index("ix_node_timestamp", TelemetryEventRow.node, TelemetryEventRow.timestamp)

class AlertRow(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    node = Column(String, index=True, nullable=False)
    rule_id = Column(String, index=True, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)

    created_ts = Column(Integer, index=True, nullable=False)
    resolved_ts = Column(Boolean, default=False, nullable=False)

    is_active = Column(Boolean, index=True, nullable=False,default=True)

Index("ix_alert_node_rule_active", AlertRow.node, AlertRow.rule_id, AlertRow.is_active)
