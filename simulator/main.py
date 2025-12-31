from simulator.models import TelemetryEvent

def main():
    event = TelemetryEvent(
        node = "router-1",
        latency_ms=25.4,
        packet_loss=0.002,
        throughput_mbps=850.2,
        cpu_pct=32.1,
        mem_pct=55.0,
        status="OK",
    )
    print(event.model_dump_json())

if __name__ == "__main__":
    main()