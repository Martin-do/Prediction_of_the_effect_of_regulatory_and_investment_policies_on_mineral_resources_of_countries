"""Rebuild Figure 2 from V0.4.3 generated reporting sources."""
from __future__ import annotations

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SIGNALS = ["Oil_Rents_GDP_Pct_lag1", "Regulatory_Quality_lag1"]
SIGNAL_LABELS = ["Oil rents (t−1)", "Regulatory Quality (t−1)"]
TARGETS = ["primary", "normalized"]
TARGET_LABELS = ["Annual FDI net flow", "FDI net flow / GDP"]
UNIVERSES = ["All_Eligible", "Oil_Rent_Intensive_Pre2016_ge1pct", "Oil_Rent_Intensive_Pre2016_ge5pct", "Oil_Rent_Intensive_Pre2016_ge10pct", "Oil_Rent_Intensive_Pre2016_ge15pct"]
UNIVERSE_LABELS = ["All", "≥1%", "≥5%", "≥10%", "≥15%"]
VERDICT_CODE = {"Supported and practically material": 0, "Directionally positive but marginal": 1, "Setup-dependent": 2, "Unsupported": 3, "Coverage-limited": 4}
VERDICT_LETTER = {0: "M", 1: "G", 2: "S", 3: "U", 4: "C"}


def main() -> None:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[2]
    parser.add_argument("--repo-root", type=Path, default=root_default)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "figures")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    verdicts = pd.read_csv(args.repo_root / "07_outputs/Bootstrap_Five_Way_Setup_Verdicts.csv")
    curve = pd.read_csv(args.repo_root / "07_outputs/Figure2b_Threshold_Sensitivity_Source.csv")

    fig = plt.figure(figsize=(10, 8.8), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.45])
    ax1 = fig.add_subplot(gs[0])
    matrix = np.zeros((2, 10), dtype=int)
    for i, signal in enumerate(SIGNALS):
        col = 0
        for target in TARGETS:
            for universe in UNIVERSES:
                row = verdicts[(verdicts.signal == signal) & (verdicts.target_role == target) & (verdicts.universe == universe)].iloc[0]
                matrix[i, col] = VERDICT_CODE[row.bootstrap_five_way_setup_verdict]
                col += 1
    ax1.imshow(matrix, aspect="auto", interpolation="nearest")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax1.text(j, i, VERDICT_LETTER[matrix[i, j]], ha="center", va="center", fontweight="bold")
    ax1.set_yticks(range(2), SIGNAL_LABELS)
    ax1.set_xticks(range(10), UNIVERSE_LABELS * 2)
    ax1.axvline(4.5)
    ax1.text(2, -0.75, TARGET_LABELS[0], ha="center", fontweight="bold")
    ax1.text(7, -0.75, TARGET_LABELS[1], ha="center", fontweight="bold")
    ax1.set_xlabel("Country universe defined by maximum pre-2016 oil-rent share of GDP")
    ax1.text(0.0, -0.34, "(a)", transform=ax1.transAxes, ha="left", va="top", fontweight="bold")

    ax2 = fig.add_subplot(gs[1])
    for signal, label in zip(SIGNALS, SIGNAL_LABELS):
        g = curve[curve.signal == signal]
        ax2.plot(g.threshold_delta_r2, g.share_meeting_probability_rule, label=label)
    ax2.axvline(0.005, linestyle="--")
    ax2.text(0.0052, 0.92, "Declared threshold\nδ = 0.005", va="top")
    ax2.set_xlim(0, 0.03)
    ax2.set_ylim(0, 1)
    ax2.set_xlabel("Practical materiality threshold, δ, for incremental ΔR²")
    ax2.set_ylabel("Share of 180 units with P(ΔR² > δ) ≥ 0.80")
    ax2.text(0.0, -0.16, "(b)", transform=ax2.transAxes, ha="left", va="top", fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.25)
    for signal, xoff, yoff in [("Oil_Rents_GDP_Pct_lag1", 0.0002, 0.025), ("Regulatory_Quality_lag1", 0.0002, -0.045)]:
        row = curve[(curve.signal == signal) & np.isclose(curve.threshold_delta_r2, 0.005)].iloc[0]
        ax2.scatter([0.005], [row.share_meeting_probability_rule])
        ax2.text(0.005 + xoff, row.share_meeting_probability_rule + yoff, f"{int(row.units_meeting_probability_rule)}/180 ({row.share_meeting_probability_rule:.1%})")

    png_path = args.output_dir / "Figure2_Admissibility_and_Threshold_Sensitivity.png"
    tiff_path = args.output_dir / "Figure2_Admissibility_and_Threshold_Sensitivity.tiff"
    fig.savefig(png_path, dpi=600, bbox_inches="tight")
    from PIL import Image
    with Image.open(png_path) as image:
        image.save(tiff_path, format="TIFF", compression="tiff_lzw", dpi=(600, 600))


if __name__ == "__main__":
    main()
