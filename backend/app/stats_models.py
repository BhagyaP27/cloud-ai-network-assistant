from pydantic import BaseModel
from typing import Optional


class NodeStats(BaseModel):
    node: str
    count: int

    latency_avg: Optional[float] = None
    latency_max: Optional[float] = None
    latency_min: Optional[float] = None

    packet_loss_avg: Optional[float] = None
    throughput_avg: Optional[float] = None
    cpu_avg: Optional[float] = None
    mem_avg: Optional[float] = None

    first_ts: Optional[int] = None
    last_ts: Optional[int] = None