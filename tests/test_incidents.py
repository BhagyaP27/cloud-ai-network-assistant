from simulator.incident_model import build_incidents

def test_incident_active_only_in_window():
    base = 1000.0
    cfg= [
        {"type":"latency_spike", "node": "router-1", "start_after_s": 10, "duration_s": 5, "severity": 3.0}
    ]
    incidents = build_incidents(cfg, base_time=base)
    inc = incidents[0]

    
    assert inc.active(base + 9) is False
    assert inc.active(base + 10) is True
    assert inc.active(base + 12) is True
    assert inc.active(base + 16) is False