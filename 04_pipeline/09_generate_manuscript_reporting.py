from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import ROOT, OUTPUT_DIR, PROCESSED_DIR, LOCKED_DIR, load_config


SIGNAL_LABELS = {
    "Oil_Rents_GDP_Pct_lag1": "Oil rents (t-1)",
    "Regulatory_Quality_lag1": "Regulatory Quality (t-1)",
}
TARGET_ORDER = ["primary", "normalized"]
UNIVERSE_ORDER = [
    "All_Eligible",
    "Oil_Rent_Intensive_Pre2016_ge1pct",
    "Oil_Rent_Intensive_Pre2016_ge5pct",
    "Oil_Rent_Intensive_Pre2016_ge10pct",
    "Oil_Rent_Intensive_Pre2016_ge15pct",
]
UNIVERSE_LABELS = {
    "All_Eligible": "All",
    "Oil_Rent_Intensive_Pre2016_ge1pct": ">=1%",
    "Oil_Rent_Intensive_Pre2016_ge5pct": ">=5%",
    "Oil_Rent_Intensive_Pre2016_ge10pct": ">=10%",
    "Oil_Rent_Intensive_Pre2016_ge15pct": ">=15%",
}
VERDICT_SHORT = {
    "Supported and practically material": "Material",
    "Directionally positive but marginal": "Marginal",
    "Setup-dependent": "Setup-dependent",
    "Unsupported": "Unsupported",
    "Coverage-limited": "Coverage-limited",
}


def _read_matched_counts() -> pd.DataFrame:
    registry = pd.read_csv(LOCKED_DIR / "Matched_Sample_Registry.csv")
    rows = []
    for _, row in registry.iterrows():
        path = LOCKED_DIR / str(row["file"])
        sample = pd.read_csv(path, usecols=["ISO3"])
        rows.append({
            "sample_id": row["sample_id"],
            "matched_rows": len(sample),
            "matched_countries": sample["ISO3"].nunique(),
        })
    return registry.merge(pd.DataFrame(rows), on="sample_id", validate="one_to_one")


def generate_base_margin_outputs() -> None:
    units = pd.read_csv(OUTPUT_DIR / "Bootstrap_Unit_Summary.csv")
    keys = ["sample_id", "signal", "target_role", "target", "universe", "validation", "split_id", "algorithm"]
    benchmark = units.loc[
        units["comparison_type"] == "added_model_vs_strongest_benchmark",
        keys + ["point_delta_r2", "left_predictor", "right_predictor"],
    ].rename(columns={
        "point_delta_r2": "added_model_minus_strongest_benchmark_r2",
        "left_predictor": "strongest_benchmark",
        "right_predictor": "added_model",
    })
    increment = units.loc[
        units["comparison_type"] == "signal_increment",
        keys + ["point_delta_r2", "left_predictor", "right_predictor"],
    ].rename(columns={
        "point_delta_r2": "signal_increment_r2",
        "left_predictor": "base_model",
        "right_predictor": "added_model_increment_record",
    })
    merged = benchmark.merge(increment, on=keys, validate="one_to_one")
    if not (merged["added_model"] == merged["added_model_increment_record"]).all():
        raise RuntimeError("Added-model identity failed while deriving base-model benchmark margins.")
    merged["base_model_minus_strongest_benchmark_r2"] = (
        merged["added_model_minus_strongest_benchmark_r2"] - merged["signal_increment_r2"]
    )
    merged["identity_residual"] = (
        merged["added_model_minus_strongest_benchmark_r2"]
        - merged["signal_increment_r2"]
        - merged["base_model_minus_strongest_benchmark_r2"]
    )
    merged = merged.drop(columns=["added_model_increment_record"])
    merged.to_csv(OUTPUT_DIR / "Base_Model_vs_Best_Benchmark_Unit_Level.csv", index=False)

    decision = merged[merged["target_role"].isin(TARGET_ORDER)].copy()
    headline = []
    for signal, group in decision.groupby("signal", sort=False):
        headline.append({
            "signal": signal,
            "signal_label": SIGNAL_LABELS.get(signal, signal),
            "decision_bearing_units": len(group),
            "base_model_benchmark_positive_units": int((group["base_model_minus_strongest_benchmark_r2"] > 0).sum()),
            "median_base_model_minus_strongest_benchmark_r2": float(group["base_model_minus_strongest_benchmark_r2"].median()),
            "median_signal_increment_r2": float(group["signal_increment_r2"].median()),
            "maximum_absolute_identity_residual": float(group["identity_residual"].abs().max()),
            "interpretation": "Benchmark competitiveness was generally established before the signal under test entered its corresponding model rung.",
        })
    pd.DataFrame(headline).to_csv(OUTPUT_DIR / "Base_Model_Benchmark_Margin_Headline.csv", index=False)


def generate_figure2_source() -> None:
    curve = pd.read_csv(OUTPUT_DIR / "Bootstrap_Threshold_Probability_Curve.csv")
    curve = curve[
        (curve["comparison_type"] == "signal_increment")
        & (curve["target_role"].isin(TARGET_ORDER))
        & (curve["threshold_delta_r2"] >= 0)
        & (curve["threshold_delta_r2"] <= 0.03)
    ].copy()
    out = (
        curve.groupby(["signal", "threshold_delta_r2"], as_index=False)
        .agg(
            units=("p_delta_r2_gt_threshold", "size"),
            units_meeting_probability_rule=("p_delta_r2_gt_threshold", lambda x: int((x >= 0.80).sum())),
        )
    )
    out["share_meeting_probability_rule"] = out["units_meeting_probability_rule"] / out["units"]
    out.to_csv(OUTPUT_DIR / "Figure2b_Threshold_Sensitivity_Source.csv", index=False)


def generate_table1_source() -> None:
    config = load_config()
    panel = pd.read_csv(PROCESSED_DIR / "MS2_SIGNAL_ADMISSIBILITY_PANEL_V3.csv")
    folds = pd.read_csv(LOCKED_DIR / "Country_Fold_Counts.csv")
    coverage = pd.read_csv(OUTPUT_DIR / "Coverage_Audit_Summary.csv")

    restored_31 = 31
    restored_complete_m3 = 30
    values = [
        ("Panel A. Construct provenance and coverage audit", "Panel period", f"{int(panel['Year'].min())}-{int(panel['Year'].max())}"),
        ("Panel A. Construct provenance and coverage audit", "Economies", str(panel["ISO3"].nunique())),
        ("Panel A. Construct provenance and coverage audit", "Country-year rows", f"{len(panel):,}"),
        ("Panel A. Construct provenance and coverage audit", "Observed annual FDI-flow rows", f"{panel['Inward_FDI_Net_Flow_USD'].notna().sum():,}"),
        ("Panel A. Construct provenance and coverage audit", "Preserved negative-flow years", f"{(panel['Inward_FDI_Net_Flow_USD'] < 0).sum():,}"),
        ("Panel A. Construct provenance and coverage audit", "Observed normalized FDI-flow rows", f"{panel['Inward_FDI_Net_Flow_GDP_Pct_asinh'].notna().sum():,}"),
        ("Panel A. Construct provenance and coverage audit", "Oil-rents observations", f"{panel['Oil_Rents_GDP_Pct'].notna().sum():,}"),
        ("Panel A. Construct provenance and coverage audit", "Regulatory Quality observations", f"{panel['Regulatory_Quality'].notna().sum():,}"),
        ("Panel A. Construct provenance and coverage audit", ">=5% oil-rent economies excluded by prior mapping, all restored", str(restored_31)),
        ("Panel A. Construct provenance and coverage audit", "Restored economies entering complete M3 sample", str(restored_complete_m3)),
        ("Panel A. Construct provenance and coverage audit", "Nigeria annual FDI-flow observations", str(panel.loc[panel['ISO3'] == 'NGA', 'Inward_FDI_Net_Flow_USD'].notna().sum())),
        ("Panel B. Feature ladder and validation design", "M1", "Lagged outcome, GDP, population, inflation, electricity access"),
        ("Panel B. Feature ladder and validation design", "M2", "M1 plus lagged oil rents"),
        ("Panel B. Feature ladder and validation design", "M3", "M2 plus lagged Regulatory Quality"),
        ("Panel B. Feature ladder and validation design", "Algorithms", ", ".join({"ElasticNet": "Elastic Net", "RandomForest": "Random Forest"}.get(x, x) for x in config["algorithms"])),
        ("Panel B. Feature ladder and validation design", "Country validation", "Five country-grouped folds pooled into one out-of-fold unit"),
        ("Panel B. Feature ladder and validation design", "Fold sizes (economies)", ", ".join(str(int(x)) for x in folds.sort_values('Country_Fold')['countries'])),
        ("Panel B. Feature ladder and validation design", "Future validation", "Five prespecified cutoffs (train to 2012/2014/2015/2016/2018)"),
        ("Panel B. Feature ladder and validation design", "Country universes", "All economies; >=1%, >=5%, >=10%, >=15% oil-rent groups"),
        ("Panel B. Feature ladder and validation design", "Units per setup", "3 algorithms x 6 validation environments = 18"),
        ("Panel B. Feature ladder and validation design", "Uncertainty", "2,000-replicate paired country-cluster bootstrap"),
        ("Panel B. Feature ladder and validation design", "Decision-bearing setups", "10 per signal"),
        ("Panel B. Feature ladder and validation design", "Regulatory Quality scale", "WGI governance estimate; alternative 0-100 score checked post hoc"),
    ]
    pd.DataFrame(values, columns=["panel", "item", "locked_value"]).to_csv(
        OUTPUT_DIR / "Manuscript_Table1_Data_and_Design.csv", index=False
    )


def generate_table3_sources() -> None:
    units = pd.read_csv(OUTPUT_DIR / "Bootstrap_Unit_Summary.csv")
    verdicts = pd.read_csv(OUTPUT_DIR / "Bootstrap_Five_Way_Setup_Verdicts.csv")
    registry = _read_matched_counts()

    bench = units[
        (units["comparison_type"] == "added_model_vs_strongest_benchmark")
        & (units["target_role"].isin(TARGET_ORDER))
    ]
    inc = units[
        (units["comparison_type"] == "signal_increment")
        & (units["target_role"].isin(TARGET_ORDER))
    ]

    long_rows = []
    for signal in SIGNAL_LABELS:
        for target_role in TARGET_ORDER:
            for universe in UNIVERSE_ORDER:
                r = registry[(registry["signal"] == signal) & (registry["target_role"] == target_role) & (registry["universe"] == universe)]
                b = bench[(bench["signal"] == signal) & (bench["target_role"] == target_role) & (bench["universe"] == universe)]
                d = inc[(inc["signal"] == signal) & (inc["target_role"] == target_role) & (inc["universe"] == universe)]
                v = verdicts[(verdicts["signal"] == signal) & (verdicts["target_role"] == target_role) & (verdicts["universe"] == universe)]
                if not (len(r) == len(v) == 1 and len(b) == len(d) == 18):
                    raise RuntimeError(f"Unexpected manuscript table source cardinality: {signal}, {target_role}, {universe}")
                rr, vv = r.iloc[0], v.iloc[0]
                long_rows.append({
                    "signal": signal,
                    "signal_label": SIGNAL_LABELS[signal],
                    "target_role": target_role,
                    "universe": universe,
                    "universe_label": UNIVERSE_LABELS[universe],
                    "matched_rows": int(rr["matched_rows"]),
                    "matched_countries": int(rr["matched_countries"]),
                    "benchmark_positive_units_of_18": int((b["point_delta_r2"] > 0).sum()),
                    "median_point_model_minus_benchmark_r2": float(b["point_delta_r2"].median()),
                    "median_point_signal_increment_r2": float(d["point_delta_r2"].median()),
                    "material_units": int(vv["material_units"]),
                    "marginal_units": int(vv["marginal_units"]),
                    "setup_dependent_units": int(vv["setup_dependent_units"]),
                    "unsupported_units": int(vv["unsupported_units"]),
                    "coverage_limited_units": int(vv["coverage_limited_units"]),
                    "setup_verdict": VERDICT_SHORT[vv["bootstrap_five_way_setup_verdict"]],
                })
    long_df = pd.DataFrame(long_rows)
    long_df.to_csv(OUTPUT_DIR / "Manuscript_Table3_Setup_Evidence_Long.csv", index=False)

    compact_rows = []
    for signal in SIGNAL_LABELS:
        for universe in UNIVERSE_ORDER:
            g = long_df[(long_df["signal"] == signal) & (long_df["universe"] == universe)].set_index("target_role")
            p, n = g.loc["primary"], g.loc["normalized"]
            compact_rows.append({
                "signal": SIGNAL_LABELS[signal],
                "country_universe": UNIVERSE_LABELS[universe],
                "matched_rows_P_N_and_countries": f"{p.matched_rows:,} / {n.matched_rows:,} ({p.matched_countries})",
                "benchmark_positive_units_P_N": f"{p.benchmark_positive_units_of_18} / {n.benchmark_positive_units_of_18}",
                "median_point_model_minus_benchmark_r2_P_N": f"{p.median_point_model_minus_benchmark_r2:.5f} / {n.median_point_model_minus_benchmark_r2:.5f}",
                "median_point_signal_increment_r2_P_N": f"{p.median_point_signal_increment_r2:.5f} / {n.median_point_signal_increment_r2:.5f}",
                "unit_verdicts_M_Mg_SD_U_CL_P_N": (
                    f"{p.material_units}/{p.marginal_units}/{p.setup_dependent_units}/{p.unsupported_units}/{p.coverage_limited_units} / "
                    f"{n.material_units}/{n.marginal_units}/{n.setup_dependent_units}/{n.unsupported_units}/{n.coverage_limited_units}"
                ),
                "setup_verdict_P_N": f"{p.setup_verdict} / {n.setup_verdict}",
            })
    pd.DataFrame(compact_rows).to_csv(OUTPUT_DIR / "Manuscript_Table3_Setup_Evidence_Compact.csv", index=False)


def generate_table4_source() -> None:
    verdicts = pd.read_csv(OUTPUT_DIR / "Bootstrap_Five_Way_Setup_Verdicts.csv")
    roles = pd.read_csv(OUTPUT_DIR / "Final_Signal_Role_and_Admissibility.csv")
    verdicts = verdicts[verdicts["target_role"].isin(TARGET_ORDER)]
    rows = []
    for signal, label in SIGNAL_LABELS.items():
        g = verdicts[verdicts["signal"] == signal]
        role = roles[roles["variable_or_block"] == signal].iloc[0]
        counts = g["bootstrap_five_way_setup_verdict"].value_counts()
        rows.append({
            "signal": label,
            "setups": len(g),
            "material": int(counts.get("Supported and practically material", 0)),
            "marginal": int(counts.get("Directionally positive but marginal", 0)),
            "setup_dependent": int(counts.get("Setup-dependent", 0)),
            "unsupported": int(counts.get("Unsupported", 0)),
            "coverage_limited": int(counts.get("Coverage-limited", 0)),
            "overall_classification": role["five_way_classification"],
            "locked_decision_role": role["decision_role"],
        })
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "Manuscript_Table4_Final_Synthesis.csv", index=False)


def main() -> None:
    generate_base_margin_outputs()
    generate_figure2_source()
    generate_table1_source()
    generate_table3_sources()
    generate_table4_source()
    print("Generated V0.4.3 manuscript-reporting outputs.")


if __name__ == "__main__":
    main()
