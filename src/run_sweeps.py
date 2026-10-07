"""Regenerate the report experiments locally: python -m src.run_sweeps."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

# Each worker uses one numerical-library thread; avoid oversubscribing CPUs.
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(name, "1")

import matplotlib
import networkx
import numpy as np
import pandas as pd
import scipy
from scipy.integrate import solve_ivp

from .experiments import MODEL_ID, grid_configs, run_sweep


def experiment_configs(name: str) -> list[dict]:
    if name == "pilot":
        return grid_configs(rules=("observation", "imitation", "broadcast",
                                   "broadcast_hub", "none"))
    if name == "zoom":
        return grid_configs(rules=("broadcast", "broadcast_hub"),
                            alphas=(0.02, 0.05, 0.08, 0.1, 0.15),
                            deltas=(0.0, 0.05, 0.15, 0.3))
    if name == "beta":
        return [cfg for beta in (0.03, 0.06, 0.09, 0.12, 0.2)
                for cfg in grid_configs(rules=("none", "observation"),
                                        alphas=(0.75,), deltas=(0.1,),
                                        seeds=range(20), beta=beta)]
    if name == "mean-field":
        return [cfg for beta in (0.03, 0.06, 0.12, 0.2)
                for cfg in grid_configs(topologies=("ws",), rules=("none",),
                                        alphas=(0.0,), deltas=(0.0,),
                                        seeds=range(20), beta=beta)]
    raise ValueError(name)


def ode_final(beta: float) -> float:
    def rhs(t, y):
        s, i, r = y
        incidence = beta * 6 * s * i
        return [-incidence, incidence - 0.05 * i, 0.05 * i]

    sol = solve_ivp(rhs, (0, 5000), [0.99, 0.01, 0.0], rtol=1e-9, atol=1e-11)
    if not sol.success:
        raise RuntimeError(sol.message)
    return float(1 - sol.y[0, -1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", choices=("all", "pilot", "zoom", "beta",
                                                "mean-field"), default="all")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    names = {"pilot": "pilot_full", "zoom": "zoom_h2", "beta": "beta_sweep",
             "mean-field": "mean_field_runs"}
    selected = names if args.experiment == "all" else {args.experiment: names[args.experiment]}
    for name, filename in selected.items():
        frame = run_sweep(experiment_configs(name), str(data / f"{filename}.csv"),
                          workers=args.workers)
        assert frame.extinct.all() and frame.final_size.notna().all()
        print(f"{filename}: {len(frame)} completed runs; "
              f"longest epidemic {frame.duration.max()} steps", flush=True)
        if name == "mean-field":
            summary = frame.groupby("beta").final_size.agg(["mean", "std"]).reset_index()
            summary["ode_final_size"] = summary.beta.map(ode_final)
            summary.to_csv(data / "mean_field_summary.csv", index=False)
    versions = {name: module.__version__ for name, module in
                (("numpy", np), ("pandas", pd), ("scipy", scipy),
                 ("networkx", networkx), ("matplotlib", matplotlib))}
    (data / "provenance.json").write_text(
        json.dumps({"model_id": MODEL_ID, "versions": versions,
                    "safety_limit_steps": 5000, "cost_units": "edge-steps",
                    "primary_cost": "social_cost_degree"}, indent=2) + "\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
