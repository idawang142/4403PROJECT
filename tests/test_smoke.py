"""Smoke checks: boundaries + determinism (run with pytest or python -m pytest)."""
from src.simulation import SimParams, run_coupled


def test_beta_zero_no_spread():
    out = run_coupled(SimParams(topology="ws", n=200, seed=1, beta=0.0, rule="none"))
    assert out["final_size"] <= 10 / 200 + 1e-9


def test_gamma_one_fast_recovery():
    out = run_coupled(SimParams(topology="ws", n=200, seed=1, gamma=1.0, rule="none"))
    assert out["duration"] <= 5


def test_determinism():
    a = run_coupled(SimParams(topology="ba", n=300, seed=42, rule="observation"))
    b = run_coupled(SimParams(topology="ba", n=300, seed=42, rule="observation"))
    assert a["final_size"] == b["final_size"]


def test_behaviour_reduces_or_equal():
    base = run_coupled(SimParams(topology="ws", n=300, seed=3, rule="none"))
    beh = run_coupled(SimParams(topology="ws", n=300, seed=3, rule="observation",
                                alpha=1.0, delta=0.05))
    assert beh["final_size"] <= base["final_size"] + 0.05
