"""Smoke checks: boundaries + determinism (run with pytest or python -m pytest)."""
import numpy as np

from src.networks import make_graph
from src.simulation import SimParams, run_coupled


def test_beta_zero_no_spread():
    out = run_coupled(SimParams(topology="ws", n=200, seed=1, beta=0.0, rule="none"))
    assert out["final_size"] <= 10 / 200 + 1e-9


def test_gamma_one_recovers_initial_infections():
    out = run_coupled(SimParams(topology="ws", n=200, seed=1, gamma=1.0, beta=0.0, rule="none"))
    assert out["duration"] == 1
    assert out["extinct"] and out["remaining_infected"] == 0


def test_determinism():
    a = run_coupled(SimParams(topology="ba", n=300, seed=42, rule="observation"))
    b = run_coupled(SimParams(topology="ba", n=300, seed=42, rule="observation"))
    assert a["final_size"] == b["final_size"]


def test_behaviour_reduces_or_equal():
    base = run_coupled(SimParams(topology="ws", n=300, seed=3, rule="none"))
    beh = run_coupled(SimParams(topology="ws", n=300, seed=3, rule="observation",
                                alpha=1.0, delta=0.05))
    assert beh["final_size"] <= base["final_size"] + 0.05


def test_ws_small_n_no_crash():
    for n in range(1, 7):
        G = make_graph("ws", n=n, seed=0)
        assert G.number_of_nodes() == n


def test_all_rules_run_finite():
    for rule in ("none", "observation", "imitation", "broadcast", "broadcast_hub"):
        out = run_coupled(SimParams(topology="ws", n=100, seed=5, rule=rule))
        assert np.isfinite(out["final_size"]) and np.isfinite(out["social_cost"])
        assert 0.0 <= out["final_size"] <= 1.0
