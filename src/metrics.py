"""Quantitative metrics for epidemic + behaviour runs."""
from __future__ import annotations

import numpy as np

try:
    from scipy.signal import find_peaks
    _HAS_SCIPY = True
except Exception:  # pragma: no cover
    _HAS_SCIPY = False


def summarize_run(prev_series: np.ndarray, cautious_series: np.ndarray,
                  degree_mean: float, q: float, n: int) -> dict:
    prev = np.asarray(prev_series, dtype=float)
    caut = np.asarray(cautious_series, dtype=float)
    peak = float(prev.max()) if len(prev) else 0.0
    t_peak = int(np.argmax(prev)) if len(prev) else 0
    # final size needs recovered count; caller passes it separately if needed.
    # social cost: edge-days forgone ~= sum_t cautious_nodes(t) * mean_k * q / 2
    social_cost = float((caut * degree_mean * q / 2.0).sum())
    cautious_days = float(caut.sum())
    return {
        "peak": peak,
        "t_peak": t_peak,
        "social_cost": social_cost,
        "cautious_days": cautious_days,
        "duration": int(len(prev)),
    }


def count_waves(prev_series: np.ndarray, prominence: float | None = None,
                distance: int = 10) -> int:
    """Count epidemic waves via peak detection on prevalence series."""
    prev = np.asarray(prev_series, dtype=float)
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
    """Std of detrended prevalence / mean, simple overshoot proxy for H3."""
    prev = np.asarray(prev_series, dtype=float)
    if prev.mean() <= 1e-9:
        return 0.0
    return float(prev.std() / (prev.mean() + 1e-9))


def efficiency(final_baseline: float, final_rule: float, cost: float,
               eps: float = 1.0) -> float:
    """Reduction in final size per unit social cost (RQ tradeoff).

    eps avoids div-by-zero; cost is edge-days so eps=1 is negligible.
    """
    return float((final_baseline - final_rule) / (cost + eps))
