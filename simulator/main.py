import asyncio
import random
import time
from simulator.models import TelemetryEvent

#multiple nodes + continuous emmission
NODES = ["router-1","router-2","router-3","router-4","router-5"]
EMIT_HZ = 1.0 # events per second
SEED = 7 # makes random values predictable for testing

rng = random.Random(SEED)

def generate_event(node: str) -> TelemetryEvent:
    """
    generator: intentionally simple/random. later
    will replace with more realistic simulation logic.
    
    :param node: Description
    :type node: str
    :return: Description
    :rtype: TelemetryEvent
    """

    return TelemetryEvent(
        node=node,
        latency_ms=round(rng.uniform(10,80),2),
        packet_loss=round(rng.uniform(0,0.02),4),
        throughput_mbps=round(rng.uniform(200,1200),2),
        cpu_pct=round(rng.uniform(5,95),2),
        mem_pct=round(rng.uniform(10,90),2),
        status="OK",
        timestamp=time.time(),
    )

async def main():
    interval = 1.0 / EMIT_HZ

    while True: 
        #one tick: emit event for each node
        for node in NODES:
            event = generate_event(node)
            print(event.model_dump_json())

        #wait until next tick
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())