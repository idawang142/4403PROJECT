# Corrected experiment inputs

Regenerate with `python -m src.run_sweeps --workers 4` from the repository root.
`pilot_full.csv`, `zoom_h2.csv`, `beta_sweep.csv` and `mean_field_runs.csv`
contain completed epidemics, full configurations and model/cache identities.
`mean_field_summary.csv` records the continuous-time reference comparison.
`provenance.json` records library versions and measurement conventions.

The analysis notebook writes `tradeoff_summary.csv`, `zoom_summary.csv`,
`cells_summary.csv` and `phase_summary.csv`. Efficiency is in infections averted
per edge-step; degree-aware cost is primary and mean-degree cost is retained
for sensitivity analysis. Bootstrap intervals resample paired seed clusters.

`legacy/` preserves the previous run-level CSVs, including results stopped after 500 steps.
Do not mix those files with the corrected inputs.
