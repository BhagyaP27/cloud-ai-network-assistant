import httpx 
from simulator.models import TelemetryEvent

class HttpSink:
    def __init__(self, url: str, timeout_s: float = 2.0):
        self.url = url
        self.timeout_s = timeout_s
    
    def emit(self, event: TelemetryEvent) -> None:
        # Synchronous send for now , later make it async/batched

        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                client.post(self.url, json=event.model_dump())
        except Exception:
            #in production gonna log this but for now, fail silently
            pass