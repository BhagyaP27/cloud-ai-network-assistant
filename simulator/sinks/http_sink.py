import httpx 
from simulator.models import TelemetryEvent

class HttpSink:
    def __init__(self, url: str, timeout_s: float = 2.0):
        self.url = url
        self.timeout_s = timeout_s
    
    def emit(self, event: TelemetryEvent) -> None:
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(self.url, json=event.model_dump())
            r.raise_for_status()