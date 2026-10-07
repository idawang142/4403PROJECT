# CITS4403 Research Project

**Fear is contagious too: behavioural feedback in epidemic spreading**

Ruilei Wang (24328412) and Xuan Truong Nguyen (24012326).
CITS4403 Computational Modelling, Semester 2 2026.

We compare local observation, social imitation, uniform broadcast and
hub-targeted broadcast in a network SIR model. The research question is which
response averts the most infections per unit of protective effort, and how this
depends on network structure and memory. WS, BA and degree-matched ER networks
are synthetic; these experiments compare model assumptions rather than predict
real populations.

## Setup and validation

Use Python 3.x (the regenerated results were produced with Python 3.13).

~~~bash
python -m pip install -r requirements.txt
python -m pytest tests/ -q
~~~

Tests cover transmission/recovery boundaries, zero initial infections,
termination flags, initial innovators, cost timing, degree-aware accounting,
sparse/dense equivalence, determinism and complete sweep cache identities.

## Reproduce the submission

Run from the repository root:

~~~bash
python -m src.run_sweeps --workers 4
python -m src.run_analysis
~~~

The first command runs 9,090 pilot, 3,600 targeting, 600 transmission and 80
mean-field configurations. It resumes matching completed runs. Use
--experiment pilot, zoom, beta or mean-field to run one component, and
--workers 1 for sequential execution. Corrected inputs live in data/.
The analysis notebook prints all results, writes summary CSVs and regenerates
the six figures in report/figs/. It works from the root or notebooks/.

Each CSV stores the complete simulation configuration, a model-source
fingerprint and a configuration key. Legacy caches without this provenance are
rejected. Changing model source requires regenerating inputs; the analysis
notebook rejects outputs from a different model version.

data/provenance.json records the numerical-library versions. Earlier outputs
are preserved under data/legacy/ and Git history;
they are historical records and are not inputs to the corrected report.
The root cits4403-groupproject.ipynb is a Kaggle-specific runner and requires
attaching the current project as a dataset. The local commands above are the
submission's primary reproduction procedure.

## Model and measurement conventions

The graph is fixed. Caution reduces transmission probability at both endpoints;
the simulator does not delete edges. Disease transitions use the start-of-step
disease state, while transmission uses newly updated caution.

Runs stop at extinction, subject to a 5,000-step safety limit. Returned
extinct and remaining_infected fields distinguish completed epidemics.
For unfinished runs, final_size is NaN and cumulative_size reports the
fraction infected so far. The sweep runner rejects unfinished epidemics.

`social_cost` retains the original mean-degree proxy. `social_cost_degree`
weights each cautious node by its actual degree and is the primary report
measure. Both count protective effort until disease extinction, in edge-steps,
using an endpoint-accounting factor of one half; neither is an exact count of
removed contacts or economic loss. Steps are not calibrated to days.
Efficiency converts infected fractions to infection counts using N.

Imitation keeps the original half-decay rule; the same nominal delta does not
imply equal memory across response rules. The oscillation index is the
coefficient of variation of prevalence, which cannot establish overshoot.

## Quick simulation

~~~python
from src.simulation import SimParams, run_coupled

out = run_coupled(SimParams(topology="ws", n=500, seed=0,
                            rule="observation", alpha=0.8, delta=0.1))
print(out["extinct"], out["final_size"], out["social_cost_degree"])
~~~

Main functions are in src/; plotting helpers are in utils/. The scientific
report is report/report.tex and report/report.pdf. Compile from report/
with two passes of pdflatex -halt-on-error report.tex when using local LaTeX.
