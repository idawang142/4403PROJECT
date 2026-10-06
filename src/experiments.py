"""Parameter sweep harness with multiprocessing + incremental CSV caching."""
from __future__ import annotations

import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable

import pandas as pd
from tqdm import tqdm

from .simulation import SimParams, run_coupled


def _run_one(cfg: dict) -> dict:
    p = SimParams(**cfg)
    out = run_coupled(p)
    out.pop("prev_series", None)
    out.pop("caut_series", None)
    return out


def grid_configs(topologies=("ws", "ba", "er"),
                 rules=("observation", "imitation", "broadcast"),
                 alphas=(0.0, 0.25, 0.5, 0.75, 1.0),
                 deltas=(0.0, 0.05, 0.15, 0.3, 0.6),
                 seeds=range(30), n: int = 1000,
                 beta: float = 0.12, gamma: float = 0.05) -> list[dict]:
    cfgs = []
    for topo, rule, a, d, s in itertools.product(topologies, rules, alphas, deltas, seeds):
        # 'none' ignores alpha/delta: keep one cell to avoid 25x wasted runs
        if rule == "none" and not (a == alphas[0] and d == deltas[0]):
            continue
        cfg = {"topology": topo, "rule": rule, "alpha": a, "delta": d,
               "seed": int(s), "n": n, "beta": beta, "gamma": gamma}
        # Fix (2): broadcast ignores alpha in simulation (uses p_comply).
        # Map alpha -> p_comply so the shared alpha axis means
        # compliance/budget for broadcast variants (0=no campaign).
        if rule.startswith("broadcast"):
            cfg["p_comply"] = float(a)
        cfgs.append(cfg)
    return cfgs


def run_sweep(cfgs: Iterable[dict], out_csv: str, workers: int | None = None,
              chunksize: int = 8) -> pd.DataFrame:
    cfgs = list(cfgs)
    done_keys = set()
    if os.path.exists(out_csv):
        try:
            prev = pd.read_csv(out_csv)
            for _, r in prev.iterrows():
                done_keys.add((r["topology"], r["rule"], float(r["alpha"]),
                               float(r["delta"]), int(r["seed"])))
        except Exception:
            pass
    todo = [c for c in cfgs if (c["topology"], c["rule"], float(c["alpha"]),
                                float(c["delta"]), int(c["seed"])) not in done_keys]
    print(f"sweep: {len(todo)} todo / {len(cfgs)} total (cached {len(done_keys)})")
    rows: list[dict] = []
    FLUSH_EVERY = 200

    def _flush():
        nonlocal rows
        if not rows:
            return
        df_new = pd.DataFrame(rows)
        header = not os.path.exists(out_csv)
        df_new.to_csv(out_csv, mode="a", header=header, index=False)
        rows = []

    if todo:
        try:
            if workers == 1:
                # sequential: avoids spawn memory pressure on constrained machines
                for cfg in tqdm(todo):
                    rows.append(_run_one(cfg))
                    if len(rows) >= FLUSH_EVERY:
                        _flush()
            else:
                with ProcessPoolExecutor(max_workers=workers) as ex:
                    for out in tqdm(ex.map(_run_one, todo, chunksize=chunksize), total=len(todo)):
                        rows.append(out)
                        if len(rows) >= FLUSH_EVERY:
                            _flush()
        finally:
            _flush()
    return pd.read_csv(out_csv)
