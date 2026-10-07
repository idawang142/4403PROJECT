"""Vectorized coupled SIR + behaviour simulation.

Transmission model (fast, vectorized):
- Each step, count for every node:
    c1 = # infected non-cautious neighbours
    c2 = # infected cautious neighbours
- Susceptible node i with cautious state ci has per-neighbour escape probs:
    escape1 = 1 - beta * (1 - q*ci)            (from non-cautious infector)
    escape2 = 1 - beta * (1 - q) * (1 - q*ci)  (from cautious infector)
  infection prob p_i = 1 - escape1^c1 * escape2^c2.
  One uniform random per susceptible node decides infection (not per edge).
- Recovery: I -> R with prob gamma each step.
- Cost per step: cautious_nodes * mean_degree * q / 2 (mean-degree proxy),
  plus sum of cautious nodes' degrees * q / 2 (degree-aware proxy).
  Units are edge-steps; the model does not calibrate one step to a day.

Sparse adjacency keeps neighbour counting proportional to the number of edges.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .behaviour import update_fear
from .metrics import count_waves, oscillation_index, summarize_run
from .networks import make_graph, to_arrays


@dataclass
class SimParams:
    topology: str = "ws"
    n: int = 1000
    seed: int = 0
    beta: float = 0.12
    gamma: float = 0.05
    rule: str = "observation"  # none | observation | imitation | broadcast | broadcast_hub
    alpha: float = 0.5
    delta: float = 0.1
    theta: float = 0.5
    q: float = 0.8
    prev_thresh: float = 0.02
    p_comply: float = 0.8
    init_infected: int = 10
    max_steps: int = 5000  # safety limit; unfinished runs have no final_size
    hub_frac: float = 0.1  # top-degree fraction targeted by broadcast_hub


def run_coupled(p: SimParams) -> dict:
    """Simulate to extinction or the safety limit; explicitly flag unfinished runs."""
    if p.n < 1 or p.max_steps < 1:
        raise ValueError("n and max_steps must be positive")
    rng = np.random.default_rng(p.seed)
    G = make_graph(p.topology, n=p.n, seed=p.seed)
    A, degree, _ = to_arrays(G)
    n = p.n
    deg_mean = float(degree.mean()) if n else 0.0

    status = np.zeros(n, dtype=np.int8)  # 0=S,1=I,2=R
    init = rng.choice(n, size=min(p.init_infected, n), replace=False)
    status[init] = 1
    fear = np.zeros(n, dtype=float)
    # Imitation needs innovators (Rogers diffusion): seed 2% cautious at t=0,
    # otherwise pure copying from zero stays zero forever.
    if p.rule == "imitation":
        n_innov = max(1, int(0.02 * n))
        innov = rng.choice(n, size=n_innov, replace=False)
        fear[innov] = 1.0

    hub_mask = None
    if p.rule == "broadcast_hub":
        k = max(1, int(n * p.hub_frac))
        hub_idx = np.argsort(degree, kind="stable")[-k:]
        hub_mask = np.zeros(n, dtype=bool)
        hub_mask[hub_idx] = True

    prev_series, caut_series, caut_degree_series = [], [], []
    cautious = fear > p.theta

    for _ in range(p.max_steps):
        infected = status == 1
        n_inf = int(infected.sum())
        if n_inf == 0:
            break
        prevalence = n_inf / n
        prev_series.append(prevalence)

        # 1) behaviour update
        fear = update_fear(
            fear, p.rule, p.alpha, p.delta, p.theta,
            infected, cautious, A, degree, prevalence, rng,
            prev_thresh=p.prev_thresh, p_comply=p.p_comply, hub_mask=hub_mask,
        )
        cautious = fear > p.theta
        caut_series.append(float(cautious.sum()))
        caut_degree_series.append(float(degree[cautious].sum()))

        # 2) neighbour counts split by infector caution
        inf_f = infected.astype(float)
        inf_caut = (infected & cautious).astype(float)
        inf_plain = inf_f - inf_caut
        c1 = A @ inf_plain  # non-cautious infectors
        c2 = A @ inf_caut   # cautious infectors

        # 3) recovery
        rec = (rng.random(n) < p.gamma) & infected

        # 4) infection of susceptibles
        sus = status == 0
        ci = cautious.astype(float)
        e1 = 1.0 - p.beta * (1.0 - p.q * ci)
        e2 = 1.0 - p.beta * (1.0 - p.q) * (1.0 - p.q * ci)
        # numerical safety
        e1 = np.clip(e1, 0.0, 1.0)
        e2 = np.clip(e2, 0.0, 1.0)
        p_inf = 1.0 - np.power(e1, c1) * np.power(e2, c2)
        new_inf = sus & (rng.random(n) < p_inf)
        # Both transitions use the disease state at the start of the step:
        # an infector can transmit and recover during the same update.

        status[rec] = 2
        status[new_inf] = 1

    prev_arr = np.array(prev_series)
    caut_arr = np.array(caut_series)
    remaining = int((status == 1).sum())
    cumulative_size = float((status != 0).sum() / n)
    base = summarize_run(prev_arr, caut_arr, deg_mean, p.q, n,
                         np.asarray(caut_degree_series))
    base.update({
        "final_size": cumulative_size if remaining == 0 else float("nan"),
        "cumulative_size": cumulative_size,
        "extinct": remaining == 0, "remaining_infected": remaining,
        "waves": count_waves(prev_arr),
        "oscillation": oscillation_index(prev_arr),
        "topology": p.topology, "rule": p.rule,
        "alpha": p.alpha, "delta": p.delta,
        "beta": p.beta, "gamma": p.gamma, "seed": p.seed, "n": n,
        "prev_series": prev_arr, "caut_series": caut_arr,
    })
    return base
