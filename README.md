# CITS4403 Research Project

**"Fear is contagious too": behavioural feedback in epidemic spreading**

| Name | Student ID |
|------|------------|
| Ruilei Wang | 24328412 |
| Xuan Truong Nguyen | 24012326 |

Unit: CITS4403 Computational Modelling, Semester 2 2026
---

## Project Idea

We want to model how *fear of getting sick* changes the course of an epidemic, not just the disease itself spreading, but people's behavioural responses spreading too.

The basic setup is an SIR (Susceptible–Infected–Recovered) epidemic running on a network, where infected nodes can also spread "risk awareness" to their neighbours. Nodes that become risk-aware temporarily reduce their contacts (cut edges), which in turn slows transmission. The interesting question is: which specific way that fear/awareness spreads is most effective at reducing the epidemic, and at what cost to social interaction?

This is a coupled-contagion problem, two things spreading on the same network simultaneously.

---

## Research Question

> **Which behavioural feedback rule (local imitation of neighbours' precautions, direct observation of sick contacts, or a broadcast nudge triggered at a prevalence threshold) minimises epidemic final size per unit of social cost (total contacts forgone)?**

### Hypotheses

- **H1:** Intermediate fear-memory decay (how fast people stop being cautious) produces multi-wave dynamics rather than a single epidemic peak.
- **H2:** On scale-free networks (BA-type, with hubs), hub-targeted nudges dominate; on homogeneous networks (WS-type) they don't matter as much.
- **H3:** Imitation-based behaviour tends to overshoot and produce oscillations rather than a clean suppression.

---

## Planned Modelling Approach

At this stage (end of Week 5), we have covered:

- **Complex systems** (W1): local rules → emergent global behaviour, exactly what we're modelling.
- **Graph theory** (W2–W3): network structure matters a lot for how contagion spreads.
  - Erdős–Rényi (ER) as a homogeneous baseline
  - Watts–Strogatz (WS) for small-world / high-clustering networks
  - Barabási–Albert (BA) for scale-free / hub-dominated networks
- **Cellular Automata** (W4–W5): demonstrated how simple local update rules produce complex emergent patterns. The same principle motivates our behavioural rules.

---

## Network Topologies to Test

| Topology | Why |
|----------|-----|
| Watts-Strogatz (WS) | Small-world, high clustering, typical of social/friendship networks |
| Barabasi-Albert (BA) | Scale-free, hub-driven, tests whether hub-targeting strategies matter |
| Empirical (TBD) | A real-world snapshot to ground the model, likely the SNAP Facebook dataset used in W3 |

---

## Preliminary Metrics

- **Final size**: what fraction of the population was ever infected
- **Peak prevalence**: highest simultaneous infection count
- **Time to peak**
- **Social cost**: total contact-hours forgone due to behavioural changes
- **Wave count**: does the epidemic resolve in one wave or multiple?

The target "hero figure" is a **phase diagram** plotting epidemic final size against behaviour coupling strength × fear memory decay, for each of the three feedback rules.

---

## Planned Experiments (Draft)

1. Grid sweep over fear-coupling strength × memory-decay rate for each of the 3 behavioural rules.
2. Run each parameter combination on all 3 network topologies.
3. 100+ independent random seeds per cell to average out stochasticity.
4. Compare final-size / social-cost tradeoff curves across rules.

---

## Work Split (Tentative)

- **Ruilei Wang:** epidemic engine (SIR dynamics), network generation and topology setup
- **Xuan Truong Nguyen:** behavioural feedback modules (the 3 rules), statistics/analysis pipeline

Both partners contribute to experimental design and report writing.

---

## Current Status

- [x] Project idea agreed on
- [x] GitHub repository created
- [ ] Background reading on coupled contagion literature
- [ ] Basic SIR-on-network prototype (post W7 lab)
- [ ] Behavioural rule implementations
- [ ] Experimental sweep setup

---

## Setup & Usage (scaffold v0.1)

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

Quick run:

```python
from src.simulation import SimParams, run_coupled
out = run_coupled(SimParams(topology="ws", n=500, seed=0, rule="observation", alpha=0.8, delta=0.1))
print(out["final_size"], out["peak"], out["waves"], out["social_cost"])
```

Pilot sweep (cached, parallel):

```python
from src.experiments import grid_configs, run_sweep
cfgs = grid_configs(topologies=("ws","ba"), rules=("observation","imitation","broadcast"),
                    alphas=(0.0,0.5,1.0), deltas=(0.0,0.1,0.3), seeds=range(5), n=300)
df = run_sweep(cfgs, "data/pilot.csv")
```

Notebooks: `notebooks/01_validation.ipynb`, `02_sweep.ipynb`, `03_figures.ipynb`.
Layout follows rubric spec: `src/ utils/ data/ notebooks/ requirements.txt README.md`.
