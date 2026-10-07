# Current figure captions

The authoritative captions are in report.tex; current images are report/figs/.
All runs use synthetic N=1000 networks and stop at disease extinction.

- tradeoff.png: grid-average final infected fraction versus degree-aware
  protective effort in edge-steps; 600 runs per point.
- phase_panels.png: observation final fractions and broadcast detected peaks;
  30 seeds per cell, fixed colour scales 0–1 and 0–30 respectively.
- zoom_h2.png: final fractions and degree-aware efficiency versus per-trigger
  compliance budget; 120 runs per point, with 95% paired seed-bootstrap
  efficiency intervals. The dotted line marks the 10% hub-pool cap.
- beta_sweep.png: observation versus no behaviour over transmission rates;
  20 seeds per setting, bands show one sample SD. Line style identifies
  topology and colour identifies rule.
- timeseries.png: seed-0 WS trajectories for observation and broadcast;
  all illustrated runs end at extinction rather than the previous cutoff.
- mean_field.png: WS final fractions with sample SD against a continuous-time
  homogeneous ODE. The mismatch is reported without isolating its causes.

Efficiency counts infections averted per edge-step. Costs are endpoint-effort
proxies, not economic loss or literal deleted-edge counts. Nominal decay does
not match effective memory across rules, and detected peaks are not necessarily
independent outbreaks. Parameter-grid averages are not an optimisation frontier.
