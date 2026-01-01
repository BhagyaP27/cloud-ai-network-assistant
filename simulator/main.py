import asyncio
import random
import time
from simulator.node_model import NodeModel

#multiple nodes + continuous emmission
NODES = ["router-1","router-2","router-3","router-4","router-5"]
EMIT_HZ = 1.0 # events per second
SEED = 7 # makes random values predictable for testing

async def main():
    rng = random.Random(SEED)
    models = [NodeModel(name, rng) for name in NODES]

    interval = 1.0 / EMIT_HZ
    while True:
        now = time.time()
        for m in models:
            event = m.generate(now)
            print(event.model_dump_json())
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())