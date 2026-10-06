# Frozen report figures (issue #6)

`figures/report/` contains the five 300 dpi figures. `captions.md` has
copy-ready descriptions, sample counts, axis units, and cautions;
`limitations.md` has the draft report paragraph.

The four small `report/data/*_summary.csv` files are the committed plotting
inputs. They were aggregated from the Kaggle sweep outputs
`pilot_full.csv` (9,090 rows), `zoom_h2.csv` (3,600 rows), and
`beta_sweep.csv` (600 rows); the raw run-level files are not part of this
figure-freeze PR. `timeseries.png` is simulated again from the merged engine
at seed 0. The summaries contain mean values, sample SD where shown, and
counts (`runs`) so every plotted point remains auditable.

From the repository root, install `requirements.txt`, then regenerate the
figures from the committed summaries:

```bash
python report/render_figures.py
```

To rebuild the summaries **and** figures from the original Kaggle CSVs:

```bash
python report/render_figures.py --data-dir /path/to/kaggle/output/data
```

All figure code uses the Agg backend and saves with `dpi=300`. The common
parameters are N = 1,000, γ = 0.05 per step, β = 0.12 per edge per step
except the β sweep, θ = 0.5, q = 0.8, and top-10% hub targeting. Both sweep
results and example trajectories are clearly identified in the captions.
