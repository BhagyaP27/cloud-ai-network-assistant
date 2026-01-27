from sqlalchemy import Column, Integer, Float, String, Index
from .db import Base

class TelemetryEventRow(Base):
    __tablename__ = "telemetry_events"

    id = Column(Integer, Primary_key=True,index=True)
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
