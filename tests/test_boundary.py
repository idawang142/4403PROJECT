"""Issue #3: boundary checks against the documented update rules."""
import numpy as np
import networkx as nx
import pytest
import src.simulation as sim
from src.behaviour import update_fear


def fear_step(rule="observation", fear=None, adj=None, infected=None, **kw):
    if fear is None: fear = np.zeros(10)
    n = len(fear)
    if adj is None: adj = np.ones((n,n)) - np.eye(n)
    if infected is None: infected = np.ones(n, dtype=bool)
    args = dict(alpha=1., delta=0., theta=.5, prevalence=1.)
    args.update(kw)
    return update_fear(fear=fear, rule=rule, infected=infected,
        cautious=fear>.5, adj=adj, degree=adj.sum(axis=1),
        rng=np.random.default_rng(0), **args)


def test_isolated_nodes_no_spread_or_cost(monkeypatch):
    # One initially infected node and one susceptible isolated node.
    monkeypatch.setattr(sim, "make_graph", lambda *a, **k: nx.empty_graph(2))
    out = sim.run_coupled(sim.SimParams(n=2, init_infected=1, beta=1.,
                          gamma=1., rule="observation"))
    assert out["final_size"] == .5
    assert out["social_cost"] == 0
    assert np.all(out["caut_series"] == 0)
    f = fear_step(fear=np.zeros(1), adj=np.zeros((1,1)),
                  infected=np.zeros(1, dtype=bool))
    np.testing.assert_array_equal(f, [0.])


def test_complete_graph_infects_everyone_in_one_step(monkeypatch):
    monkeypatch.setattr(sim, "make_graph", lambda *a, **k: nx.complete_graph(10))
    out = sim.run_coupled(sim.SimParams(n=10, init_infected=1, beta=1.,
                          gamma=0., rule="none", max_steps=1))
    assert out["duration"] == 1
    assert out["cumulative_size"] == 1.
    assert not out["extinct"]
    assert np.isnan(out["final_size"])


def test_alpha_zero_matches_none_exactly():
    common = dict(n=30, seed=7, init_infected=2, max_steps=80)
    a = sim.run_coupled(sim.SimParams(**common, rule="none"))
    b = sim.run_coupled(sim.SimParams(**common, rule="observation", alpha=0.))
    for key in a:
        if key in ("rule", "alpha"): continue
        np.testing.assert_array_equal(a[key], b[key], err_msg=key)
    np.testing.assert_array_equal(b["caut_series"], 0.)


def test_delta_one_erases_old_fear_but_keeps_new_signal():
    adj=np.array([[0.,1.],[1.,0.]])
    # No new signal: old fear disappears completely.
    f=fear_step(fear=np.ones(2), adj=adj, infected=np.zeros(2,dtype=bool), delta=1.)
    np.testing.assert_array_equal(f, [0.,0.])
    # New signal survives: delta=1 is not equivalent to rule='none'.
    f=fear_step(fear=np.ones(2), adj=adj, infected=np.array([True,False]), delta=1.)
    np.testing.assert_array_equal(f, [0.,1.])


def test_theta_equality_not_cautious(monkeypatch):
    monkeypatch.setattr(sim, "update_fear", lambda fear,*a,**k: np.full_like(fear,.5))
    out=sim.run_coupled(sim.SimParams(n=10, init_infected=1, beta=0.,
                        gamma=0., theta=.5, max_steps=2))
    np.testing.assert_array_equal(out["caut_series"], 0.)
    assert out["social_cost"] == 0.
    monkeypatch.setattr(sim, "update_fear", lambda fear,*a,**k: np.full_like(fear,.500001))
    out=sim.run_coupled(sim.SimParams(n=10, init_infected=1, beta=0.,
                        gamma=0., theta=.5, max_steps=2))
    assert out["caut_series"][0] == 10


def test_max_steps_cap():
    out=sim.run_coupled(sim.SimParams(n=10, init_infected=1, beta=0.,
                        gamma=0., rule="none", max_steps=7))
    assert out["duration"] == 7
    np.testing.assert_array_equal(out["prev_series"], np.full(7,.1))
    assert out["cumulative_size"] == .1
    assert not out["extinct"]
    assert out["remaining_infected"] == 1
    assert np.isnan(out["final_size"])


@pytest.mark.parametrize("budget", [.1,.5,1.])
def test_hub_budget_saturates_at_top_ten_percent(monkeypatch,budget):
    graph=nx.star_graph(19)
    monkeypatch.setattr(sim,"make_graph",lambda *a,**k: graph)
    expected=np.zeros(20,dtype=bool)
    expected[np.argsort([d for _,d in graph.degree()], kind="stable")[-2:]]=True
    original=sim.update_fear
    seen=[]
    def checked(*a,**kw):
        np.testing.assert_array_equal(kw["hub_mask"],expected)
        f=original(*a,**kw)
        np.testing.assert_array_equal(f>.5,expected)
        seen.append(True)
        return f
    monkeypatch.setattr(sim,"update_fear",checked)
    out=sim.run_coupled(sim.SimParams(n=20,init_infected=1, beta=0.,gamma=0.,
        rule="broadcast_hub",p_comply=budget,hub_frac=.1,prev_thresh=0.,max_steps=3))
    assert seen
    assert max(out["caut_series"]) == 2


def test_hub_tie_break_is_node_order_deterministic(monkeypatch):
    graph = nx.cycle_graph(5)  # equal degrees make the cutoff a tie
    monkeypatch.setattr(sim, "make_graph", lambda *a, **k: graph)
    original = sim.update_fear
    masks = []

    def capture(*args, **kwargs):
        masks.append(kwargs["hub_mask"].copy())
        return original(*args, **kwargs)

    monkeypatch.setattr(sim, "update_fear", capture)
    sim.run_coupled(sim.SimParams(n=5, init_infected=5, beta=0, gamma=1,
        rule="broadcast_hub", p_comply=0.4, hub_frac=0.4, max_steps=1))
    np.testing.assert_array_equal(masks[0], [False, False, False, True, True])
