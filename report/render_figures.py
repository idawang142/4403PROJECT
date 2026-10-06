"""Render the five report figures from frozen sweep summaries.

To refresh summaries from the run-level sweep CSVs in data/::

    python report/render_figures.py --data-dir data

Without --data-dir, the committed CSVs in report/data/ are used. All PNGs
are written to figures/report/ at 300 dpi. The dynamics panel is rerun from
src/simulation.py with a fixed seed because prevalence traces are not in CSVs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.simulation import SimParams, run_coupled  # noqa: E402

TOPOLOGIES = ("ws", "ba", "er")
POLICIES = {"none": "#34495e", "observation": "#007f86",
            "imitation": "#72934e", "broadcast": "#d98332",
            "broadcast_hub": "#7952a2"}
NAMES = {"none": "No behaviour", "observation": "Observation",
         "imitation": "Imitation", "broadcast": "Uniform broadcast",
         "broadcast_hub": "Hub broadcast"}
MARKERS = {"ws": "o", "ba": "D", "er": "s"}
STYLES = {"ws": "-", "ba": "--", "er": ":"}
FILES = ("phase_summary", "tradeoff_summary", "zoom_summary", "beta_summary")


def freeze_summaries(raw_dir: Path, summary_dir: Path) -> None:
    """Aggregate runs, retaining sample sizes and the figure input values."""
    pilot = pd.read_csv(raw_dir / "pilot_full.csv")
    zoom = pd.read_csv(raw_dir / "zoom_h2.csv")
    beta = pd.read_csv(raw_dir / "beta_sweep.csv")
    for name, frame in (("pilot_full", pilot), ("zoom_h2", zoom),
                        ("beta_sweep", beta)):
        if frame.empty or frame.isna().any().any():
            raise ValueError(f"{name} is empty or contains missing values")
        if not (frame.n.eq(1000).all() and frame.gamma.eq(0.05).all()):
            raise ValueError(f"{name} must use N=1000 and gamma=0.05")

    phase = (pilot[pilot.rule.isin(("observation", "broadcast"))]
             .groupby(["topology", "rule", "delta", "alpha"])
             .agg(final_size=("final_size", "mean"), waves=("waves", "mean"),
                  runs=("seed", "size")).reset_index())
    tradeoff = (pilot[(pilot.alpha > 0) & (pilot.rule != "none")]
                .groupby(["topology", "rule"])
                .agg(final_size=("final_size", "mean"),
                     social_cost=("social_cost", "mean"),
                     runs=("seed", "size")).reset_index())
    zoomed = (zoom.groupby(["topology", "rule", "alpha"])
              .agg(final_size=("final_size", "mean"),
                   sd=("final_size", "std"), runs=("seed", "size"))
              .reset_index())
    swept = (beta.groupby(["topology", "rule", "beta"])
             .agg(final_size=("final_size", "mean"),
                  sd=("final_size", "std"), runs=("seed", "size"))
             .reset_index())
    if len(phase) != 150 or len(tradeoff) != 12 or len(zoomed) != 30 or len(swept) != 30:
        raise ValueError("Sweep grid is incomplete; expected 150/12/30/30 groups")
    summary_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in zip(FILES, (phase, tradeoff, zoomed, swept)):
        frame.to_csv(summary_dir / f"{name}.csv", index=False, float_format="%.12g")


def load_summaries(summary_dir: Path) -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(summary_dir / f"{name}.csv") for name in FILES}


def style() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 11, "axes.labelsize": 10,
                         "legend.fontsize": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "white",
                         "axes.facecolor": "white", "savefig.facecolor": "white"})


def save(fig: plt.Figure, output_dir: Path, name: str) -> None:
    fig.savefig(output_dir / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_phase(df: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 7), layout="constrained")
    for col, topo in enumerate(TOPOLOGIES):
        for row, (rule, metric, cmap, lo, hi) in enumerate((
            ("observation", "final_size", "viridis", 0, 1),
            ("broadcast", "waves", "magma", 0, 16),
        )):
            sub = df[(df.topology == topo) & (df.rule == rule)]
            grid = sub.pivot(index="delta", columns="alpha", values=metric)
            assert grid.shape == (5, 5) and grid.notna().all().all()
            ax = axes[row, col]
            image = ax.imshow(grid.to_numpy(), vmin=lo, vmax=hi, cmap=cmap,
                              aspect="auto")
            ax.set_xticks(range(5), [f"{a:g}" for a in grid.columns])
            ax.set_yticks(range(5), [f"{d:g}" for d in grid.index])
            ax.set_title(topo.upper(), weight="bold")
            if col == 0:
                ax.set_ylabel("Fear decay δ")
            if row == 1:
                ax.set_xlabel("Coupling / compliance α")
            if col == 2:
                fig.colorbar(image, ax=axes[row, :], shrink=0.78, pad=0.025,
                             label=("Final infected fraction" if row == 0
                                    else "Mean detected waves (count)"))
    fig.suptitle("Observation: final size  ·  Broadcast: recurrent waves", weight="bold")
    save(fig, output_dir, "phase_panels")


def render_tradeoff(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.3), layout="constrained")
    for row in df.itertuples(index=False):
        ax.scatter(row.social_cost / 1000, row.final_size,
                   color=POLICIES[row.rule], marker=MARKERS[row.topology],
                   s=95, edgecolors="white", linewidths=0.9, zorder=3)
    ax.set(xlabel="Mean estimated contact reduction (10³ edge-days)",
           ylabel="Mean final infected fraction", ylim=(0.45, 1.03),
           title="Health benefit versus social cost")
    ax.grid(alpha=0.16, zorder=0)
    policy_legend = ax.legend(
        [Line2D([], [], marker="o", linestyle="None", color=color, markersize=8)
         for key, color in POLICIES.items() if key != "none"],
        [NAMES[key] for key in POLICIES if key != "none"],
        title="Behaviour rule", loc="upper right", frameon=False)
    ax.add_artist(policy_legend)
    ax.legend([Line2D([], [], marker=MARKERS[topo], linestyle="None",
                      color="#34495e", markersize=7) for topo in TOPOLOGIES],
              [topo.upper() for topo in TOPOLOGIES], title="Topology",
              loc="center right", bbox_to_anchor=(1, 0.33), frameon=False)
    save(fig, output_dir, "tradeoff")


def render_zoom(df: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.1), sharey=True,
                             layout="constrained")
    for ax, topo in zip(axes, TOPOLOGIES):
        for rule in ("broadcast", "broadcast_hub"):
            sub = df[(df.topology == topo) & (df.rule == rule)].sort_values("alpha")
            ax.plot(sub.alpha, sub.final_size, marker="o", markersize=4.5,
                    linewidth=2, color=POLICIES[rule], label=NAMES[rule])
        ax.axvline(0.1, color="#6b7280", linewidth=1, linestyle=":")
        ax.set(xlim=(0.015, 0.16), ylim=(0.62, 1.01),
               title=topo.upper(), xlabel="Compliance budget (fraction of nodes)")
        ax.grid(alpha=0.16)
    axes[0].set_ylabel("Mean final infected fraction")
    axes[0].legend(loc="lower left", frameon=False)
    fig.suptitle("Targeting hubs: benefit plateaus beyond a 10% hub pool",
                 weight="bold")
    save(fig, output_dir, "zoom_h2")


def render_beta(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.3), layout="constrained")
    for rule in ("none", "observation"):
        for topo in TOPOLOGIES:
            sub = df[(df.rule == rule) & (df.topology == topo)].sort_values("beta")
            x, y, sd = (sub[col].to_numpy() for col in ("beta", "final_size", "sd"))
            ax.plot(x, y, color=POLICIES[rule], linestyle=STYLES[topo],
                    marker=MARKERS[topo], linewidth=1.9, markersize=4)
            ax.fill_between(x, np.maximum(0, y - sd), np.minimum(1, y + sd),
                            color=POLICIES[rule], alpha=0.09, linewidth=0)
    ax.set(xlabel="Per-edge transmission probability β (per step)",
           ylabel="Mean final infected fraction", ylim=(0, 1.04),
           title="Observation remains effective as transmission increases")
    ax.grid(alpha=0.16)
    policy_legend = ax.legend(
        [Line2D([], [], color=POLICIES[r], linewidth=2) for r in ("none", "observation")],
        [NAMES[r] for r in ("none", "observation")],
        title="Rule", loc="upper left", frameon=False)
    ax.add_artist(policy_legend)
    ax.legend([Line2D([], [], marker=MARKERS[t], linestyle=STYLES[t],
                      color="#34495e", markersize=5) for t in TOPOLOGIES],
              [t.upper() for t in TOPOLOGIES], title="Topology",
              loc="center left", frameon=False)
    save(fig, output_dir, "beta_sweep")


def render_timeseries(output_dir: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(8.7, 6.5), layout="constrained")
    cases = (("observation", 1.0, (0, 0.15, 0.6),
              "Local observation (α = 1)"),
             ("broadcast", 0.75, (0, 0.05, 0.3),
              "Global broadcast (75% compliance)"))
    shades = ("#34495e", "#d98332", "#007f86")
    for ax, (rule, alpha, deltas, title) in zip(axes, cases):
        for delta, color in zip(deltas, shades):
            out = run_coupled(SimParams(topology="ws", n=1000, seed=0,
                                        beta=0.12, gamma=0.05, rule=rule,
                                        alpha=alpha, p_comply=alpha,
                                        delta=delta, prev_thresh=0.02))
            ax.plot(np.arange(len(out["prev_series"])), out["prev_series"],
                    color=color, linewidth=1.7, label=f"δ = {delta:g}")
        ax.set(title=title, ylabel="Infectious fraction")
        ax.grid(alpha=0.16)
        ax.legend(loc="upper right", ncol=3, frameon=False)
    axes[1].set_xlabel("Simulation step (one synchronous update)")
    fig.suptitle("Behavioural memory changes epidemic trajectories", weight="bold")
    save(fig, output_dir, "timeseries")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path,
                        help="raw pilot_full/zoom_h2/beta_sweep CSV directory")
    parser.add_argument("--summaries-dir", type=Path, default=ROOT / "report/data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "figures/report")
    args = parser.parse_args()
    if args.data_dir:
        freeze_summaries(args.data_dir, args.summaries_dir)
    data = load_summaries(args.summaries_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    style()
    render_phase(data["phase_summary"], args.output_dir)
    render_tradeoff(data["tradeoff_summary"], args.output_dir)
    render_zoom(data["zoom_summary"], args.output_dir)
    render_beta(data["beta_summary"], args.output_dir)
    render_timeseries(args.output_dir)
    print(f"Rendered 5 figures at 300 dpi in {args.output_dir}")


if __name__ == "__main__":
    main()
