"""Persistence-baseline forensics.

Quantifies the lag-1 persistence baseline on the legacy (stock-mislabelled) target and
on the corrected annual-flow target, across identical scales, samples and estimands.

The manuscript's construct-correction claim rests on the collapse of persistence
performance between the two series. This step exists so that no such number is
asserted from memory: every cell is generated here and traces to this file.

The persistence baseline is fit-free (y_hat[t] = y[t-1]), so no model is trained and no
seed is consumed. The only quantity that changes between estimands is how the R-squared
denominator is formed and aggregated, which is precisely why both are reported.

Read-only with respect to the frozen layer. The forensic archive is read solely to
quantify the legacy defect, never to construct a corrected result.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import LOCKED_DIR, OUTPUT_DIR, PROCESSED_DIR, ROOT, load_config, safe_r2

LEGACY_PATH = ROOT / "02_forensic_archive" / "LEGACY_INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv"
PANEL_PATH = PROCESSED_DIR / "MS2_SIGNAL_ADMISSIBILITY_PANEL_V3.csv"
FOLD_PATH = LOCKED_DIR / "Country_Fold_Assignments.csv"

SERIES = {
    "Legacy_Stock_Mislabelled_As_Flow": {
        "source": "forensic_archive",
        "raw_column": "FDI_Flows_Millions_USD",
        "role": "Legacy target retained as forensic exhibit only",
    },
    "Corrected_Annual_Net_Flow": {
        "source": "corrected_panel",
        "raw_column": "Inward_FDI_Net_Flow_USD_Millions",
        "role": "Decision-bearing primary target (BX.KLT.DINV.CD.WD)",
    },
}


def require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns in {label}: {missing}")


def build_series(frame: pd.DataFrame, raw_column: str) -> pd.DataFrame:
    """Return consecutive country-years with raw and asinh levels and their lag-1 values."""
    work = frame[["ISO3", "Year", raw_column]].copy()
    work = work.rename(columns={raw_column: "raw"})
    work["asinh"] = np.arcsinh(work["raw"])
    work = work.sort_values(["ISO3", "Year"]).reset_index(drop=True)

    grouped = work.groupby("ISO3", sort=False)
    prior_year = grouped["Year"].shift(1)
    consecutive = (work["Year"] - prior_year) == 1
    work["raw_lag1"] = grouped["raw"].shift(1).where(consecutive)
    work["asinh_lag1"] = grouped["asinh"].shift(1).where(consecutive)
    return work.loc[consecutive].reset_index(drop=True)


def evaluate(frame: pd.DataFrame, scale: str, folds: pd.DataFrame) -> tuple[float, float, int, int, int]:
    """Return pooled R2, country-fold median R2, observations, countries, folds used."""
    usable = frame[[f"{scale}", f"{scale}_lag1", "ISO3"]].dropna()
    if usable.empty:
        return float("nan"), float("nan"), 0, 0, 0

    pooled = safe_r2(usable[scale].to_numpy(), usable[f"{scale}_lag1"].to_numpy())

    merged = usable.merge(folds[["ISO3", "Country_Fold"]], on="ISO3", how="left")
    fold_scores: list[float] = []
    for _, block in merged.dropna(subset=["Country_Fold"]).groupby("Country_Fold", sort=True):
        score = safe_r2(block[scale].to_numpy(), block[f"{scale}_lag1"].to_numpy())
        if np.isfinite(score):
            fold_scores.append(score)

    fold_median = float(np.median(fold_scores)) if fold_scores else float("nan")
    return pooled, fold_median, len(usable), usable["ISO3"].nunique(), len(fold_scores)


def main() -> None:
    load_config()  # fail fast if configuration is unreadable

    legacy = pd.read_csv(LEGACY_PATH)
    panel = pd.read_csv(PANEL_PATH)
    folds = pd.read_csv(FOLD_PATH)

    require_columns(legacy, ["ISO3", "Year", "FDI_Flows_Millions_USD"], LEGACY_PATH.name)
    require_columns(panel, ["ISO3", "Year", "Inward_FDI_Net_Flow_USD_Millions"], PANEL_PATH.name)
    require_columns(folds, ["ISO3", "Country_Fold"], FOLD_PATH.name)

    frames = {
        "Legacy_Stock_Mislabelled_As_Flow": build_series(legacy, "FDI_Flows_Millions_USD"),
        "Corrected_Annual_Net_Flow": build_series(panel, "Inward_FDI_Net_Flow_USD_Millions"),
    }

    # Common support: country-years observed on both series, so coverage cannot drive the contrast.
    keys = [
        set(map(tuple, frame.loc[frame["raw"].notna() & frame["raw_lag1"].notna(), ["ISO3", "Year"]].to_numpy()))
        for frame in frames.values()
    ]
    common = keys[0].intersection(keys[1])
    common_index = pd.MultiIndex.from_tuples(sorted(common), names=["ISO3", "Year"])

    rows: list[dict[str, object]] = []
    for series_name, spec in SERIES.items():
        frame = frames[series_name]
        subsets = {
            "all_available": frame,
            "common_support": frame.set_index(["ISO3", "Year"]).reindex(common_index).reset_index(),
        }
        for sample_name, subset in subsets.items():
            for scale, scale_label in (("asinh", "signed asinh of US$ millions"), ("raw", "US$ millions")):
                pooled, fold_median, n_obs, n_countries, n_folds = evaluate(subset, scale, folds)
                for estimand, value, folds_used in (
                    ("pooled_consecutive_country_years", pooled, 0),
                    ("country_fold_median", fold_median, n_folds),
                ):
                    rows.append({
                        "series": series_name,
                        "series_role": spec["role"],
                        "source": spec["source"],
                        "scale": scale,
                        "scale_definition": scale_label,
                        "sample": sample_name,
                        "estimand": estimand,
                        "persistence_r2": round(value, 6) if np.isfinite(value) else np.nan,
                        "observations": n_obs,
                        "countries": n_countries,
                        "folds_used": folds_used,
                        "predictor": "y[t-1]",
                        "model_fitted": False,
                    })

    matrix = pd.DataFrame(rows).sort_values(
        ["series", "sample", "scale", "estimand"]
    ).reset_index(drop=True)
    matrix.to_csv(OUTPUT_DIR / "Persistence_Baseline_Forensics.csv", index=False)

    # Headline contrast: identical scale, identical sample, identical estimand.
    def cell(series: str, scale: str, sample: str, estimand: str) -> float:
        hit = matrix[
            (matrix["series"] == series)
            & (matrix["scale"] == scale)
            & (matrix["sample"] == sample)
            & (matrix["estimand"] == estimand)
        ]
        return float(hit["persistence_r2"].iloc[0])

    headline: list[dict[str, object]] = []
    for sample_name in ("all_available", "common_support"):
        for estimand in ("pooled_consecutive_country_years", "country_fold_median"):
            legacy_r2 = cell("Legacy_Stock_Mislabelled_As_Flow", "asinh", sample_name, estimand)
            corrected_r2 = cell("Corrected_Annual_Net_Flow", "asinh", sample_name, estimand)
            headline.append({
                "scale": "asinh",
                "sample": sample_name,
                "estimand": estimand,
                "legacy_stock_persistence_r2": round(legacy_r2, 6),
                "corrected_flow_persistence_r2": round(corrected_r2, 6),
                "absolute_drop": round(legacy_r2 - corrected_r2, 6),
                "like_for_like": True,
                "interpretation": (
                    "Same transform, same sample, same estimand; the contrast is attributable to the "
                    "series, not to the evaluation choice."
                ),
            })

    pd.DataFrame(headline).to_csv(OUTPUT_DIR / "Persistence_Headline_Comparison.csv", index=False)

    print(matrix.to_string(index=False))
    print("\nLike-for-like headline contrasts")
    print(pd.DataFrame(headline).to_string(index=False))


if __name__ == "__main__":
    main()
