from simulator.models import TelemetryEvent

class FileSink:
    def __init__(self, path: str):
        self.path = path

    def emit(self, event: TelemetryEvent) -> None:
        # JSONL: 1 JSON object per line
        with open(self.path, 'a', encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")