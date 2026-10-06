# Frozen report figures (issue #6)

`figures/report/` contains the five 300 dpi figures. `captions.md` has
copy-ready descriptions, sample counts, axis units, and cautions;
`limitations.md` has the draft report paragraph.

The four small `report/data/*_summary.csv` files are the committed plotting
inputs, aggregated from the run-level sweep CSVs in `data/`
(`pilot_full.csv`, `zoom_h2.csv`, `beta_sweep.csv`). Those run-level files
are regenerated with
`python -m src.run_sweeps --all --workers 12 --out-dir data`. `timeseries.png` is simulated again from the merged engine
at seed 0. The summaries contain mean values, sample SD where shown, and
counts (`runs`) so every plotted point remains auditable.

From the repository root, install `requirements.txt`, then regenerate the
figures from the committed summaries:

```bash
python report/render_figures.py
```

To rebuild the summaries **and** figures from the run-level CSVs:

```bash
python report/render_figures.py --data-dir data
```

All figure code uses the Agg backend and saves with `dpi=300`. The common
parameters are N = 1,000, γ = 0.05 per step, β = 0.12 per edge per step
except the β sweep, θ = 0.5, q = 0.8, and top-10% hub targeting. Both sweep
results and example trajectories are clearly identified in the captions.
