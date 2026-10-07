"""Plotting helpers: phase heatmaps, tradeoff curves, time series."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def phase_heatmap(df: pd.DataFrame, value: str = "final_size",
                  rule: str = "observation", topology: str = "ws", ax=None):
    sub = df[(df.rule == rule) & (df.topology == topology)]
    piv = sub.pivot_table(index="delta", columns="alpha", values=value, aggfunc="mean")
    ax = ax or plt.gca()
    sns.heatmap(piv, ax=ax, annot=False, cbar_kws={"label": value})
    ax.set_title(f"{rule} on {topology}: {value}")
    ax.set_xlabel("alpha (coupling)")
    ax.set_ylabel("delta (decay)")
    return ax


def tradeoff_curve(df: pd.DataFrame, ax=None):
    ax = ax or plt.gca()
    agg = df.groupby(["topology", "rule"])[["final_size", "social_cost_degree"]].mean().reset_index()
    sns.scatterplot(data=agg, x="social_cost_degree", y="final_size",
                    hue="rule", style="topology", s=100, ax=ax)
    ax.set_xlabel("mean degree-aware protective effort (edge-steps)")
    ax.set_ylabel("mean final size")
    ax.set_title("Efficiency tradeoff: final size vs social cost")
    return ax
