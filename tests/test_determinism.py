import random
from simulator.node_model import NodeModel

def test_node_model_is_deterministic_for_same_seed_and_time():
    t = 123456.0
    seed = 42

    rng1 = random.Random(seed)
    rng2 = random.Random(seed)

    m1 = NodeModel("router-1", rng1)
    m2 = NodeModel("router-1", rng2)

    # Use empty effects if your generate signature is (t, effects)
    e1 = m1.generate(t, {})
    e2 = m2.generate(t, {})

    assert e1.model_dump() == e2.model_dump()
