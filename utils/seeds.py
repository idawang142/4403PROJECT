"""Seed + misc helpers."""
from __future__ import annotations

import numpy as np


def make_seeds(master: int, k: int) -> list[int]:
    rng = np.random.default_rng(master)
    return [int(x) for x in rng.integers(0, 2**31 - 1, size=k)]
