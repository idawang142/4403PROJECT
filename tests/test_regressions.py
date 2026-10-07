"""Regression checks for termination, behaviour, costs and sweep provenance."""
import numpy as np
import pandas as pd
import pytest

import src.simulation as simulation
from src.experiments import grid_configs, run_sweep
from src.metrics import count_waves, efficiency
from src.networks import make_graph, to_arrays
from src.simulation import SimParams, run_coupled


def test_empty_wave_series():
    assert count_waves(np.array([])) == 0


def test_zero_initial_infections():
    out = run_coupled(SimParams(n=100, init_infected=0))
    assert out["extinct"] and out["remaining_infected"] == 0
    assert out["final_size"] == out["duration"] == out["waves"] == 0
    assert out["social_cost"] == out["social_cost_degree"] == 0


def test_cutoff_is_not_reported_as_final_size():
    out = run_coupled(SimParams(n=100, gamma=0, beta=0, max_steps=1))
    assert not out["extinct"] and out["remaining_infected"] == 10
    assert np.isnan(out["final_size"])
    assert out["cumulative_size"] == 0.1


def test_cost_uses_caution_applied_to_this_step():
    out = run_coupled(SimParams(n=100, init_infected=100, gamma=1,
                                rule="broadcast", p_comply=1, max_steps=1))
    assert out["extinct"]
    assert out["caut_series"].tolist() == [100]
    assert out["social_cost"] == pytest.approx(100 * 6 * 0.8 / 2)
    assert out["social_cost_degree"] == pytest.approx(out["social_cost"])


def test_hub_cost_uses_actual_degrees():
    p = SimParams(topology="ba", n=100, init_infected=100, gamma=1,
                  rule="broadcast_hub", p_comply=0.1, max_steps=1)
    _, degree, _ = to_arrays(make_graph("ba", n=100, seed=p.seed))
    expected = np.sort(degree)[-10:].sum() * p.q / 2
    out = run_coupled(p)
    assert out["social_cost_degree"] == pytest.approx(expected)
    assert out["social_cost_degree"] > out["social_cost"]


def test_imitation_first_update_sees_innovators(monkeypatch):
    original = simulation.update_fear
    seen = []

    def capture(*args, **kwargs):
        seen.append(int(args[6].sum()))
        return original(*args, **kwargs)

    monkeypatch.setattr(simulation, "update_fear", capture)
    run_coupled(SimParams(n=100, rule="imitation", beta=0, gamma=1))
    assert seen == [2]


@pytest.mark.parametrize("rule", ["none", "imitation", "broadcast_hub"])
def test_sparse_and_dense_trajectories_match(monkeypatch, rule):
    p = SimParams(n=100, rule=rule, seed=7)
    sparse = run_coupled(p)
    original = simulation.to_arrays

    def dense(graph):
        adjacency, degree, nodes = original(graph)
        return adjacency.toarray(), degree, nodes

    monkeypatch.setattr(simulation, "to_arrays", dense)
    reference = run_coupled(p)
    assert np.array_equal(sparse["prev_series"], reference["prev_series"])
    assert np.array_equal(sparse["caut_series"], reference["caut_series"])
    assert sparse["social_cost_degree"] == reference["social_cost_degree"]


@pytest.mark.parametrize("change", [{"beta": 0.2}, {"gamma": 0.5},
                                    {"n": 40}, {"q": 0.3},
                                    {"p_comply": 0.4}, {"max_steps": 6000}])
def test_cache_distinguishes_complete_configuration(tmp_path, change):
    path = tmp_path / "runs.csv"
    cfg = grid_configs(topologies=("ws",), rules=("none",),
                       alphas=(0,), deltas=(0,), seeds=(2,), n=30, beta=0)[0]
    run_sweep([cfg], str(path), workers=1)
    changed = dict(cfg, **change)
    result = run_sweep([changed], str(path), workers=1)
    assert len(result) == 1
    for key, value in change.items():
        assert result.iloc[0][key] == value
    assert len(pd.read_csv(path)) == 2
    run_sweep([changed], str(path), workers=1)
    assert len(pd.read_csv(path)) == 2


def test_legacy_cache_is_rejected(tmp_path):
    path = tmp_path / "legacy.csv"
    pd.DataFrame([{"topology": "ws", "rule": "none", "alpha": 0,
                   "delta": 0, "seed": 0}]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="legacy"):
        run_sweep([{"n": 30, "rule": "none"}], str(path), workers=1)


def test_efficiency_counts_infections():
    assert efficiency(1.0, 0.6, 80000, n=1000) == pytest.approx(400 / 80001)


def test_cache_rejects_different_model(tmp_path):
    path = tmp_path / "stale.csv"
    cfg = {"n": 30, "rule": "none", "beta": 0}
    run_sweep([cfg], str(path), workers=1)
    frame = pd.read_csv(path)
    frame["model_id"] = "old-model"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="different model"):
        run_sweep([cfg], str(path), workers=1)


@pytest.mark.parametrize("topology", ["ws", "ba", "er"])
def test_small_networks(topology):
    for n in range(1, 7):
        assert make_graph(topology, n=n).number_of_nodes() == n


def test_sweep_rejects_unfinished_epidemic(tmp_path):
    with pytest.raises(RuntimeError, match="extinction"):
        run_sweep([{"n": 30, "gamma": 0, "max_steps": 1}],
                  str(tmp_path / "capped.csv"), workers=1)
