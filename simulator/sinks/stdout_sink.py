from simulator.models import TelemetryEvent

class StdoutSink:
    def emit(self, event: TelemetryEvent) -> None:
        print(event.model_dump_json())