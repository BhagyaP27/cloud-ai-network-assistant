from pydantic import BaseModel, Field
from typing import Literal, Optional
import yaml

class IncidentConfig(BaseModel):
    type:str
    node: Optional[str] = None
    start_after_s: int= 10
    duration_s: int = 10
    severity: float = 1.0

class SinkConfig(BaseModel):
    type: Literal["stdout","file", "http"] = "stdout"
    path: str = "telemetry.jsonl"# used when type="file"
    url: str = "http://localhost:8000/ingest"# used when type="http"

class SimulatorConfig(BaseModel):
    emit_hz: float = Field(default=1.0, gt=0)
    seed: int = 7
    nodes: list[str] = Field(default_factory=lambda: ["router-1"])
    sink: SinkConfig = Field(default_factory=SinkConfig)
    incidents: list[IncidentConfig] = Field(default_factory=list)

def load_config(path: str) -> SimulatorConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return SimulatorConfig.model_validate(data)

