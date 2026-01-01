import asyncio
import random
import time
from collections import defaultdict

from simulator.node_model import NodeModel
from simulator.incident_model import build_incidents

#multiple nodes + continuous emmission
NODES = ["router-1","router-2","router-3","router-4","router-5"]
EMIT_HZ = 1.0 # events per second
SEED = 7 # makes random values predictable for testing

INCIDENTS_CONFIG = [
    {"type": "latency_spike", "node": "router-3", "start_after_s": 5,  "duration_s": 12, "severity": 4.0},
    {"type": "packet_loss_burst", "node": "router-2", "start_after_s": 10, "duration_s": 8, "severity": 2.0},
    {"type": "cpu_spike", "node": None, "start_after_s": 20, "duration_s": 10, "severity": 1.8},
]

def effects_for_node(node: str, incidents, now: float) -> dict:
    effects = defaultdict(float)
    for inc in incidents:
        if not inc.active(now):
            continue
        if inc.node is not None and inc.node != node:
            continue
        # if multiple incidents of same type overlap, keep the strongest
        effects[inc.type] = max(effects[inc.type], inc.severity)
    return dict(effects)



async def main():
    rng = random.Random(SEED)
    models = [NodeModel(name, rng) for name in NODES]
    incidents = build_incidents(INCIDENTS_CONFIG)

    interval = 1.0 / EMIT_HZ
    while True:
        now = time.time()
        for m in models:
            effects = effects_for_node(m.name, incidents, now)
            event = m.generate(now, effects)
            print(event.model_dump_json())
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())