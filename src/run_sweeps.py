"""Regenerate the frozen sweep CSVs locally (exact committed recipes).

Recipes reproduce data/{pilot_full,zoom_h2,beta_sweep}.csv
row-for-row (9,090 / 3,600 / 600 configs). run_sweep() is resume-safe:
re-running skips completed (topology, rule, alpha, delta, seed) keys and
appends, so a 13k-config grid can be built across several time-boxed
invocations. Full grid is ~30-45 min on 12 workers at N=1000.

Examples (from the repository root):
    python -m src.run_sweeps --which beta_sweep --workers 4
    python -m src.run_sweeps --all --workers 12 --out-dir data

Resume note: run_sweep() skips completed (topology, rule, alpha, delta,
seed) keys, so pilot/zoom grids resume correctly across time-boxed
invocations. beta_sweep.csv spans five betas under shared keys, so run it
uninterrupted (600 configs, a few minutes).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .experiments import grid_configs, run_sweep

TOPOS = ("ws", "ba", "er")
EXPECTED = {"pilot_full": 9090, "zoom_h2": 3600, "beta_sweep": 600}


def pilot_configs() -> list[dict]:
    return grid_configs(
        topologies=TOPOS,
        rules=("observation", "imitation", "broadcast", "broadcast_hub", "none"),
        alphas=(0.0, 0.25, 0.5, 0.75, 1.0), deltas=(0.0, 0.05, 0.15, 0.3, 0.6),
        seeds=range(30), n=1000)


def zoom_configs() -> list[dict]:
    return grid_configs(
        topologies=TOPOS, rules=("broadcast", "broadcast_hub"),
        alphas=(0.02, 0.05, 0.08, 0.1, 0.15), deltas=(0.0, 0.05, 0.15, 0.3),
        seeds=range(30), n=1000)


def beta_configs() -> list[dict]:
    cfgs: list[dict] = []
    for b in (0.03, 0.06, 0.09, 0.12, 0.2):
        cfgs += grid_configs(
            topologies=TOPOS, rules=("none", "observation"),
            alphas=(0.75,), deltas=(0.1,), seeds=range(20), n=1000, beta=b)
    return cfgs


RECIPES = {"pilot_full": pilot_configs, "zoom_h2": zoom_configs,
           "beta_sweep": beta_configs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--which", choices=list(RECIPES),
                        help="single grid to run")
    parser.add_argument("--all", action="store_true",
                        help="run all three grids")
    parser.add_argument("--workers", type=int, default=None,
                        help="parallel workers (default: all CPUs; 1 = sequential)")
    parser.add_argument("--out-dir", type=Path, default=Path("data"),
                        help="output directory for CSVs")
    args = parser.parse_args()
    if bool(args.which) == bool(args.all):
        parser.error("pass exactly one of --which NAME or --all")
    names = list(RECIPES) if args.all else [args.which]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        cfgs = RECIPES[name]()
        assert len(cfgs) == EXPECTED[name], (name, len(cfgs))
        out_csv = args.out_dir / f"{name}.csv"
        print(f"{name}: {len(cfgs)} configs -> {out_csv} "
              f"(workers={args.workers})")
        df = run_sweep(cfgs, str(out_csv), workers=args.workers)
        assert len(df) == EXPECTED[name], (name, len(df))
        print(f"{name}: done, {len(df)} rows")


if __name__ == "__main__":
    main()
