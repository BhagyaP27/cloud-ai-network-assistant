from pydantic import BaseModel, Field
from typing import Literal
import time

class TelemetryEvent(BaseModel):
    node: str
    latency_ms: float = Field(ge=0)
    packet_loss: float = Field(ge=0, le=1)
    throughput_mbps: float = Field(ge=0)
    cpu_pct: float = Field(ge=0, le=100)
    mem_pct: float = Field(ge=0, le=100)
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    status: Literal["OK", "WARN", "CRITICAL"] = "OK"