from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class Incident:
    type: str # "latency_spike", "packet_loss_burst", "throughput_drop", "cpu_spike"
    node: Optional[str] # None means all nodes
    start_ts: float
    end_ts: float
    severity: float #multiplier/intensity

    def active(self, now:float) -> bool:
        return self.start_ts <= now <= self.end_ts

def build_incidents(incident_dicts: list[dict]) -> list[Incident]:
    """
    Docstring for build_incidents
    
    :param incident_dicts: Description
    :type incident_dicts: list[dict]
    :return: Description
    :rtype: list[Incident]
    """
    now = time.time()
    incidents: list[Incident] = []
    for d in incident_dicts:
        start = now + int(d["start_after_s"])
        end = start + int(d["duration_s"])
        incidents.append(
            Incident(
                type=d["type"],
                node=d.get("node"),
                start_ts=start,
                end_ts=end,
                severity=float(d.get("severity", 1.0)),
            )
        )
    return incidents
