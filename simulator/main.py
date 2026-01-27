import asyncio
import random
import time
import argparse
from collections import defaultdict

from simulator.node_model import NodeModel
from simulator.incident_model import build_incidents
from simulator.settings import load_config, SimulatorConfig, SinkConfig, IncidentConfig

from simulator.sinks.stdout_sink import StdoutSink
from simulator.sinks.file_sink import FileSink
from simulator.sinks.http_sink import HttpSink


from simulator.node_model import NodeModel
from simulator.incident_model import build_incidents

def make_sink(sink_cfg: SinkConfig):
    if sink_cfg.type == "stdout":
        return StdoutSink()

    if sink_cfg.type == "file":
        return FileSink(sink_cfg.path)

    if sink_cfg.type == "http":
        return HttpSink(sink_cfg.url)
        raise NotImplementedError("HTTP sink not implemented yet")

    raise ValueError(f"Unknown sink type: {sink_cfg.type}")

def effect_for_node(node:str, incidents, now:float) -> dict:
    effects = defaultdict(list)
    for inc in incidents:
        if not inc.active(now):
            continue
        if inc.node is not None and inc.node != node:
            continue
        effects[inc.type] = max(effects[inc.type], inc.severity)
    return dict(effects)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/simulator.dev.yaml")
    p.add_argument("--emit-hz", type=float)
    p.add_argument("--seed", type=int)
    p.add_argument("--sink", choices=["stdout", "file", "http"])
    p.add_argument("--file-path")
    p.add_argument("--http-url")
    p.add_argument("--nodes", help="Comma-separated node names, e.g. router-1,router-2")
    return p.parse_args()

def apply_overrides(cfg: SimulatorConfig, args)-> SimulatorConfig:
    #muatate safely via model_copy/update pattern
    data = cfg.model_dump()

    if args.emit_hz is not None:
        data["emit_hz"] = args.emit_hz
    if args.seed is not None:
        data["seed"] = args.seed
    if args.nodes is not None:
        data["nodes"] =  [n.strip() for n in args.nodes.split(",") if n.strip()]
    if args.sink is not None:
        data["sink"]["type"] = args.sink
    if args.file_path is not None:
        data["sink"]["file_path"] = args.file_path
    if args.http_url is not None:
        data["sink"]["url"] = args.http_url
    
    return SimulatorConfig.model_validate(data)


async def main():
    args = parse_args()
    cfg = load_config(args.config)
    cfg = apply_overrides(cfg, args)

    rng = random.Random(cfg.seed)
    models = [NodeModel(name, rng) for name in cfg.nodes]

    incidents = build_incidents([i.model_dump() for i in cfg.incidents])
    sink = make_sink(cfg.sink)

    interval = 1.0 / cfg.emit_hz
    while True:
        now = time.time()
        for m in models:
            effects = effect_for_node(m.name, incidents, now)
            event = m.generate(now, effects)
            sink.emit(event)
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())