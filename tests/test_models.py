import pytest
from simulator.models import TelemetryEvent

def Test_event_accepts_valid_values():
    ev = TelemetryEvent(
        node="router-1",
        latency_ms= 10,
        packet_loss=0.2,
        throughput_mbps=500,
        cpu_pct=50,
        mem_pct=60,
        status="OK",
    )
    assert ev.node == "router-1"

def Test_event_rejects_invalid_latency():
    with pytest.raises(ValueError):
        TelemetryEvent(
            node="router-1",
            latency_ms=10,
            packet_loss=1.5,#invalid packet loss
            throughput_mbps=500,
            cpu_pct=50,
            mem_pct=60,
            status="OK",
        )