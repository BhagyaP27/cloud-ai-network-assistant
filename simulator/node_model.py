import math 
import random
import time
from simulator.models import TelemetryEvent

class NodeModel:
    """
    Realistic telemetry generator for one node:
    baselines + cycles + correlated metrics + noise.
    """

    def __init__(self,name:str,rng: random.Random):
        self.name = name
        self.rng = rng

        # per-node baselines
        self.base_latency = rng.uniform(10,50)  # ms
        self.base_throughput = rng.uniform(200,1200)  # mbps
        self.base_cpu = rng.uniform(10,40)  # %
        self.base_mem = rng.uniform(30,70)  # %
        self.loss_floor = rng.uniform(0.0,0.005)  # %

    def _cycle(self, t: float)-> float:
        # try 60 second cycle so i can visually see paterns quickly
        return 0.5 + 0.5 * math.sin(2 * math.pi * (t % 60) / 60)
    
    def generate(self,t: float) -> TelemetryEvent:
        """
        Generate one telemetry event for this node at time t.
        
        :param t: Description
        :type t: float
        :return: Description
        :rtype: TelemetryEvent
        """

        cyc = self._cycle(t)

        # "load" drives correlated changes; add small noise
        load = 0.3 + 0.7 * cyc + self.rng.normalvariate(0, 0.05)
        load = max(0.0, min(1.2, load))

        cpu = self.base_cpu + 50 * load + self.rng.normalvariate(0, 3)
        cpu = max(0.0, min(100.0, cpu))

        mem = self.base_mem + 10 * load + self.rng.normalvariate(0, 2)
        mem = max(0.0, min(100.0, mem))

        throughput = self.base_throughput * (1.1 - 0.7 * load) + self.rng.normalvariate(0, 25)
        throughput = max(0.0, throughput)

        latency = self.base_latency * (1.0 + 2.2 * load) + self.rng.normalvariate(0, 3)
        latency = max(0.0, latency)

        # Loss increases noticeably when load is high (congestion threshold ~0.8)
        packet_loss = self.loss_floor + max(0.0, (load - 0.8)) * 0.03 + abs(self.rng.normalvariate(0, 0.001))
        packet_loss = max(0.0, min(1.0, packet_loss))

        status = "OK"
        if packet_loss > 0.03 or latency > 200 or cpu > 90:
            status = "WARN"
        if packet_loss > 0.10 or latency > 400 or cpu > 97:
            status = "CRITICAL"

        return TelemetryEvent(
            node=self.name,
            latency_ms=round(latency, 2),
            packet_loss=round(packet_loss, 4),
            throughput_mbps=round(throughput, 2),
            cpu_pct=round(cpu, 2),
            mem_pct=round(mem, 2),
            timestamp=int(time.time()),
            status=status,
        )