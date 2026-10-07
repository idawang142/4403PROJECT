"""Quantitative metrics for epidemic + behaviour runs."""
from __future__ import annotations

import numpy as np

try:
    from scipy.signal import find_peaks
    _HAS_SCIPY = True
except Exception:  # pragma: no cover
    _HAS_SCIPY = False


def summarize_run(prev_series: np.ndarray, cautious_series: np.ndarray,
                  degree_mean: float, q: float, n: int,
                  cautious_degree_series: np.ndarray | None = None) -> dict:
    prev = np.asarray(prev_series, dtype=float)
    caut = np.asarray(cautious_series, dtype=float)
    peak = float(prev.max()) if len(prev) else 0.0
    t_peak = int(np.argmax(prev)) if len(prev) else 0
    # final size needs recovered count; caller passes it separately if needed.
    # Both are contact-cost proxies in edge-steps, accumulated until termination.
    social_cost = float((caut * degree_mean * q / 2.0).sum())
    degree_counts = (caut * degree_mean if cautious_degree_series is None
                     else np.asarray(cautious_degree_series, dtype=float))
    social_cost_degree = float(degree_counts.sum() * q / 2.0)
    cautious_days = float(caut.sum())
    return {
        "peak": peak,
        "t_peak": t_peak,
        "social_cost": social_cost,
        "social_cost_degree": social_cost_degree,
        "cautious_days": cautious_days,
        "duration": int(len(prev)),
    }


def count_waves(prev_series: np.ndarray, prominence: float | None = None,
                distance: int = 10) -> int:
    """Count epidemic waves via peak detection on prevalence series."""
    prev = np.asarray(prev_series, dtype=float)
    if len(prev) == 0:
        return 0
    if len(prev) < 3:
        return 1 if prev.max() > 0 else 0
    if prominence is None:
        # relative prominence: ignore low-level flicker around the
        # broadcast threshold (peak~0.03 would otherwise give 10+ waves)
        prominence = max(0.01, 0.2 * float(prev.max()))
    if _HAS_SCIPY:
        peaks, props = find_peaks(prev, prominence=prominence, distance=distance)
        return int(len(peaks))
    # fallback: count up-crossings of half-peak
    thr = prev.max() * 0.5
    above = prev > thr
    crossings = np.sum((~above[:-1]) & (above[1:]))
    return int(max(1, crossings)) if prev.max() > 0 else 0


def oscillation_index(prev_series: np.ndarray) -> float:
    """Prevalence coefficient of variation; does not identify oscillations."""
    prev = np.asarray(prev_series, dtype=float)
    if len(prev) == 0 or prev.mean() <= 1e-9:
        return 0.0
    return float(prev.std() / (prev.mean() + 1e-9))


def efficiency(final_baseline: float, final_rule: float, cost: float,
               n: int, eps: float = 1.0) -> float:
    """Infections averted per edge-step of social cost.

    Final sizes are fractions, so multiply the reduction by population size.
    eps avoids division by zero; cost is in edge-steps.
    """
    return float(n * (final_baseline - final_rule) / (cost + eps))
