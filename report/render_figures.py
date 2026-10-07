"""Regenerate corrected report figures and summaries through the canonical analysis.

Run python report/render_figures.py or python -m src.run_analysis.
Inputs are data/; figures are written to report/figs/. Earlier report/data/
summaries and figures/report/ images are historical artifacts.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    from src.run_analysis import main as run_analysis
    run_analysis()


if __name__ == "__main__":
    main()
