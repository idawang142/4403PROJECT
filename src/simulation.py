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
- Cost per step: cautious_nodes * mean_degree * q / 2 (edge-days forgone).

This avoids per-edge Python loops: each step is 2 matvecs (A @ vec).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .behaviour import update_fear
from .metrics import count_waves, oscillation_index, summarize_run
from .networks import make_graph, to_arrays, top_degree_mask


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
    max_steps: int = 500
    hub_frac: float = 0.1  # top-degree fraction targeted by broadcast_hub


def run_coupled(p: SimParams) -> dict:
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
        hub_mask = top_degree_mask(degree, p.hub_frac)

    prev_series, caut_series, inf_series = [], [], []
    cautious = np.zeros(n, dtype=bool)

    for _ in range(p.max_steps):
        infected = status == 1
        n_inf = int(infected.sum())
        if n_inf == 0:
            break
        prevalence = n_inf / n
        prev_series.append(prevalence)
        caut_series.append(float(cautious.sum()))
        inf_series.append(n_inf)

        # 1) behaviour update
        fear = update_fear(
            fear, p.rule, p.alpha, p.delta, p.theta,
            infected, cautious, A, degree, prevalence, rng,
            prev_thresh=p.prev_thresh, p_comply=p.p_comply, hub_mask=hub_mask,
        )
        cautious = fear > p.theta

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
        # recovered infectors cannot infect onward this step is approximated;
        # ordering effect is negligible at these probabilities.

        status[rec] = 2
        status[new_inf] = 1

    prev_arr = np.array(prev_series)
    caut_arr = np.array(caut_series)
    final_size = float((status != 0).sum() / n)  # ever infected = I+R at end (I=0)
    base = summarize_run(prev_arr, caut_arr, deg_mean, p.q, n)
    base.update({
        "final_size": final_size,
        "waves": count_waves(prev_arr),
        "oscillation": oscillation_index(prev_arr),
        "topology": p.topology, "rule": p.rule,
        "alpha": p.alpha, "delta": p.delta,
        "beta": p.beta, "gamma": p.gamma, "seed": p.seed, "n": n,
        "prev_series": prev_arr, "caut_series": caut_arr,
    })
    return base
