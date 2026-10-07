# Corrected scientific report

The submission is report.tex and report.pdf; report/figs/ contains its six
figures. The report has four main-text pages, excluding figures and references.
Captions and limitations in report.tex describe the corrected measurements.

From the repository root:

```bash
python -m src.run_sweeps --workers 4
python -m src.run_analysis
```

The first command resumes the 13,370 extinction-complete configurations in
data/. The second executes notebooks/04_analysis.ipynb, records its outputs,
and regenerates report/figs/ plus the summary CSVs in data/. The older command
python report/render_figures.py delegates to that same analysis.

Compile from report/ with two passes of pdflatex -halt-on-error report.tex.
The PDF was compiled and visually checked. The notebook is also usable
interactively, with equations, validation checks, tables and demonstrations.

data/legacy/ preserves the previous run-level CSVs. Earlier report/data/
summaries and figures/report/ images are historical plotting artifacts;
they are not inputs to the corrected report. All active inputs include full
configurations, model fingerprints and explicit extinction status.
