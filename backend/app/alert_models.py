from pydantic import BaseModel
from typing import Optional, Literal

Severity = Literal["INFO","WARN","CRITICAL"]

class AlertOut(BaseModel):
    id: int
    node: str
    rule_id: str
    severity: Severity
    message: str
    created_ts: int
    resolved_ts: Optional[int] = None
    is_active: bool
