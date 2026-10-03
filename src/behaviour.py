"""Behavioural feedback rules (vectorized).

All rules operate on a fear array f in [0,1]. A node is cautious if f > theta.
- 'none': no behaviour, fear stays 0.
- 'observation': fear excited by fraction of infected neighbours, decays geometrically.
- 'imitation': fear tracks fraction of cautious neighbours (social copying).
- 'broadcast': global prevalence trigger sets fear=1 for compliers (uniform or hub-targeted).
"""
from __future__ import annotations

import numpy as np


def update_fear(
    fear: np.ndarray,
    rule: str,
    alpha: float,
    delta: float,
    theta: float,
    infected: np.ndarray,
    cautious: np.ndarray,
    adj: np.ndarray,
    degree: np.ndarray,
    prevalence: float,
    rng: np.random.Generator,
    prev_thresh: float = 0.02,
    p_comply: float = 0.8,
    hub_mask: np.ndarray | None = None,
) -> np.ndarray:
    """One-step fear update, returns new fear array (copy)."""
    rule = rule.lower()
    n = fear.shape[0]
    deg_safe = np.where(degree > 0, degree, 1.0)
    new = fear.copy()

    if rule == "none":
        return new * 0.0

    if rule == "observation":
        # infected-neighbour fraction
        inf_frac = (adj @ infected.astype(float)) / deg_safe
        new = new + alpha * inf_frac - delta * new
    elif rule == "imitation":
        caut_frac = (adj @ cautious.astype(float)) / deg_safe
        # Social copying amplified by a local risk cue. Rationale: averaging
        # drag alpha*(caut_frac - fear) caps fear at ~0.5*inf_frac with a 0.5
        # coefficient (verified: plateau ~0.23, never crosses theta=0.5).
        # Full alpha weight on inf_frac gives equilibrium fear ~= inf_frac,
        # so the disease seeds innovators and imitation amplifies from there.
        inf_frac = (adj @ infected.astype(float)) / deg_safe
        new = new + alpha * (caut_frac - new) + alpha * inf_frac
        new = new * (1.0 - 0.5 * delta)
    elif rule in ("broadcast", "broadcast_hub"):
        # decay by default
        new = new * (1.0 - delta)
        if prevalence >= prev_thresh:
            if rule == "broadcast_hub" and hub_mask is not None:
                # Fix (3) equal-budget targeting: p_comply (=alpha in sweeps)
                # is the population budget fraction. Uniform spends it on
                # random nodes; hub-targeted concentrates it on top-degree
                # nodes: hub_prob = budget/hub_frac (capped at 1), so at
                # budget <= hub_frac both policies act on equal expected
                # counts (e.g. budget 0.1 -> 10% random vs all top-10% hubs).
                # Above hub_frac, hubs saturate while uniform keeps spending.
                hub_frac = float(hub_mask.mean()) if len(hub_mask) else 0.1
                hub_prob = min(1.0, p_comply / max(1e-9, hub_frac))
                comply = hub_mask & (rng.random(n) < hub_prob)
            else:
                comply = rng.random(n) < p_comply
            new[comply] = 1.0
    else:
        raise ValueError(f"Unknown rule '{rule}'")

    np.clip(new, 0.0, 1.0, out=new)
    return new
