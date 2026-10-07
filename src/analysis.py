"""Paired, seed-clustered summaries of the report experiments."""
from pathlib import Path

import numpy as np
import pandas as pd

from .experiments import MODEL_ID


def load_experiments(data: Path) -> dict[str, pd.DataFrame]:
    expected = {"pilot_full": 9090, "zoom_h2": 3600,
                "beta_sweep": 600, "mean_field_runs": 80}
    frames = {}
    for name, count in expected.items():
        frame = pd.read_csv(data / f"{name}.csv")
        assert len(frame) == count, (name, len(frame))
        assert not frame.isna().any().any(), name
        assert not frame.config_key.duplicated().any(), name
        assert frame.model_id.eq(MODEL_ID).all(), f"Stale model outputs: {name}"
        assert frame.extinct.all() and frame.remaining_infected.eq(0).all(), name
        assert frame.n.eq(1000).all(), name
        frames[name] = frame
    return frames


def efficiency_summary(frame: pd.DataFrame, baseline: pd.DataFrame,
                       groups: list[str]) -> pd.DataFrame:
    """Ratio of grid-mean benefit to cost, with paired seed-bootstrap intervals.

    Repeated parameter cells sharing a seed form a cluster. We resample these
    clusters, retaining the matching no-behaviour baseline, rather than treating
    all 600 parameter/seed rows as independent observations at one setting.
    """
    base = baseline.groupby(["topology", "seed"]).final_size.mean()
    rows = []
    for labels, sub in frame.groupby(groups):
        labels = labels if isinstance(labels, tuple) else (labels,)
        by_seed = sub.groupby("seed")[["final_size", "social_cost",
                                       "social_cost_degree"]].mean()
        topology = sub.topology.iloc[0]
        benefit = base.loc[topology].reindex(by_seed.index).to_numpy() - by_seed.final_size.to_numpy()
        assert np.isfinite(benefit).all()
        population = int(sub.n.iloc[0])
        rng = np.random.default_rng(2026)
        draws = rng.integers(0, len(by_seed), size=(2000, len(by_seed)))
        row = dict(zip(groups, labels))
        row.update(final_size=float(by_seed.final_size.mean()),
                   social_cost=float(by_seed.social_cost.mean()),
                   social_cost_degree=float(by_seed.social_cost_degree.mean()),
                   reduction=float(benefit.mean()), runs=len(sub), seeds=len(by_seed))
        for cost, suffix in (("social_cost_degree", ""), ("social_cost", "_mean_degree")):
            values = by_seed[cost].to_numpy()
            row["eff" + suffix] = population * benefit.mean() / (values.mean() + 1)
            boot = population * benefit[draws].mean(axis=1) / (values[draws].mean(axis=1) + 1)
            row["eff_low" + suffix], row["eff_high" + suffix] = np.quantile(boot, [0.025, 0.975])
        rows.append(row)
    return pd.DataFrame(rows)


def summarise(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    pilot = frames["pilot_full"]
    baseline = pilot[pilot.rule == "none"]
    tradeoff = efficiency_summary(pilot[(pilot.alpha > 0) & (pilot.rule != "none")],
                                  baseline, ["topology", "rule"])
    zoom = efficiency_summary(frames["zoom_h2"], baseline,
                              ["topology", "rule", "alpha"])
    cells = efficiency_summary(pilot[(pilot.alpha > 0) & (pilot.rule != "none")],
                               baseline, ["topology", "alpha", "delta", "rule"])
    phase = pilot.groupby(["topology", "rule", "alpha", "delta"])[
        ["final_size", "waves"]].mean().reset_index()
    return {"tradeoff": tradeoff.sort_values("eff", ascending=False),
            "zoom": zoom, "cells": cells, "phase": phase}


if __name__ == "__main__":
    data = Path(__file__).resolve().parents[1] / "data"
    tables = summarise(load_experiments(data))
    for name, table in tables.items():
        table.to_csv(data / f"{name}_summary.csv", index=False)
    print(tables["tradeoff"].to_string(index=False))
