# Figure captions for the final report

Figures are in `figures/report/`. All use synthetic Watts–Strogatz (WS),
Barabási–Albert (BA), and degree-matched Erdős–Rényi (ER) networks with
N = 1,000, recovery probability γ = 0.05 per synchronous step, and default
transmission probability β = 0.12 per infected edge per step unless specified.
Final size is the **fraction of nodes ever infected**, not peak prevalence.
Error shading, where shown, is sample standard deviation (SD), not a
confidence interval.

## 1. `phase_panels.png` — parameter regimes

Mean final infected fraction (upper row, local observation) and mean detected
epidemic wave count (lower row, global uniform broadcast) across coupling or
compliance α and fear decay δ for WS, BA, and ER networks. Each cell averages
30 independent seeds from `pilot_full.csv`; colour scales are fixed across
topologies within a row (fraction 0–1; waves 0–16). For observation α controls
fear gained from infected neighbours; for broadcast α is the compliance
probability. Higher δ weakens protection; at small positive δ, broadcast can
produce repeated low-prevalence peaks. The wave count is an algorithmic peak
count, not an independent measure of distinct epidemic outbreaks.

## 2. `tradeoff.png` — final size versus social cost

Mean final infected fraction versus mean **estimated** contact reduction in
thousands of edge-days for four behaviour rules on three topologies. Each point
averages the positive-α parameter grid (α = 0.25, 0.5, 0.75, 1; δ = 0, 0.05,
0.15, 0.3, 0.6) and 30 seeds per combination from `pilot_full.csv` (600 runs
per point). Lower and further left indicate fewer infections at less cost.
Cost is the proxy Σₜ cautious_nodes(t) × mean_degree × q / 2 with q = 0.8;
its unit is **edge-days forgone**, not measured economic cost. The points
summarise parameter grids, not an optimisation frontier; baseline (`none`) is
not plotted.

## 3. `zoom_h2.png` — equal-budget hub targeting

Mean final infected fraction versus intended compliance budget (fraction of
nodes) for uniform broadcast and broadcast restricted to the top 10% by
degree. Each point pools 30 seeds at each of four fear-decay values (δ = 0,
0.05, 0.15, 0.3), for 120 runs per rule–topology–budget combination from
`zoom_h2.csv`; β = 0.12. The dotted line marks the 10% hub-pool limit.
**At budgets up to 10%**, the two rules target equal expected numbers of
nodes; above 10%, hub targeting saturates but uniform broadcast can reach
more nodes, so the high-budget comparison is no longer equal coverage. On BA,
mean hub-policy final size stays at 0.944 at budgets 0.10 and 0.15; lower
final size is better. This is a limitation of the chosen hub-pool rule, not
evidence that hubs cannot matter more under another targeting policy.

## 4. `beta_sweep.png` — transmission sensitivity

Mean final infected fraction as per-edge transmission probability β varies
from 0.03 to 0.20 per synchronous step, comparing no behaviour with local
observation (α = 0.75, δ = 0.10) on WS, BA, and ER networks. Points are
20-seed means from `beta_sweep.csv`; translucent bands show ±1 sample SD,
clipped to the feasible 0–1 interval. Line style and marker identify topology;
colour identifies rule. At larger β, no-behaviour outbreaks approach
saturation, while observation still reduces final size under this fixed
parameter choice. Bands are descriptive variability across seeds, not
confidence intervals.

## 5. `timeseries.png` — contrasting epidemic trajectories

Illustrative infectious fraction (currently infectious nodes / 1,000) versus
synchronous simulation step for a **single seed (0)** on WS at β = 0.12,
γ = 0.05. Upper panel: local observation with α = 1 and three fear-decay
rates. Lower panel: uniform broadcast with 75% compliance, a prevalence
trigger of 0.02, and three decay rates. Curves end at infection extinction or
the 500-step simulation limit (the δ = 0.05 and δ = 0.3 broadcast traces reach
that limit). Increasing decay can produce a larger initial outbreak or
persistent low-level fluctuations. These are example trajectories, not averages or a
claim that every seed behaves similarly.
