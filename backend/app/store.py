from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional
from .models import TelemetryEvent

class InMemoryTelemetryStore:
    """
    Stores recent events per node (fixed-size) + latest per node.
    Good for now; later replace with a proper time-series DB.
    """

    def __init__(self, max_events_per_node: int = 2000):
        self._events: Dict[str, Deque[TelemetryEvent]] = defaultdict(lambda: deque(maxlen=max_events_per_node))
        self._latest_events: Dict[str, TelemetryEvent] = {}

    def add(self, event: TelemetryEvent):
        self._events[event.node].append(event)
        self._latest_events[event.node] = event

    def latest(self, node: Optional[str] = None) -> Optional[TelemetryEvent]:
        if node:
            return self._latest_events.get(node)
        
        #if no node specified, return latest across all nodes by timestamp
        if not self._latest:
            return None
        return max(self._latest.values(), key=lambda e: e.timestamp)
    
    def history(self, node:str, limit: int = 100) -> List[TelemetryEvent]:
        events = list(self._events.get(node, []))
        return events[-limit:]