from __future__ import annotations

import re

import numpy as np
import pandas as pd

from common import LOCKED_DIR, OUTPUT_DIR, PROCESSED_DIR, ROOT, load_config


def passes(value: object, threshold: float, *, strict: bool = False) -> bool:
    if pd.isna(value):
        return False
    return float(value) > threshold if strict else float(value) >= threshold


def cutoff_verdict(row: pd.Series, cfg: dict) -> str:
    rule = cfg["admissibility_rule"]
    increment = (
        passes(row.get("median_delta_r2"), float(rule["minimum_median_delta_r2"]), strict=True)
        and passes(row.get("positive_share"), float(rule["minimum_positive_share"]))
    )
    benchmark = (
        passes(row.get("median_model_minus_benchmark_r2"), 0.0, strict=True)
        and passes(row.get("benchmark_positive_share"), float(rule["minimum_positive_share"]))
    )
    if increment and benchmark:
        return "Supported"
    if increment and not benchmark:
        return "Incremental_not_benchmark_competitive"
    if benchmark and not increment:
        return "Benchmark_competitive_increment_unsupported"
    return "Unsupported"


def setup_verdict(row: pd.Series, cfg: dict) -> str:
    rule = cfg["admissibility_rule"]
    if row["countries"] < int(rule["minimum_countries"]) or row["country_years"] < int(rule["minimum_country_years"]):
        return "Coverage-limited"

    increment_country = (
        passes(row.get("country_median_delta_r2"), float(rule["minimum_median_delta_r2"]), strict=True)
        and passes(row.get("country_positive_share"), float(rule["minimum_positive_share"]))
    )
    benchmark_country = (
        passes(row.get("country_median_model_minus_benchmark_r2"), 0.0, strict=True)
        and passes(row.get("country_benchmark_positive_share"), float(rule["minimum_positive_share"]))
    )
    country_supported = increment_country and benchmark_country

    cutoff_share = float(row.get("future_cutoff_supported_share", 0.0) or 0.0)
    future_supported = cutoff_share >= float(rule["minimum_future_cutoff_support_share"])
    some_cutoff_supported = cutoff_share > 0.0

    if country_supported and future_supported:
        return "Evidence-supported across country and cutoff tests"
    if country_supported or future_supported or some_cutoff_supported:
        return "Conditional/validation-cutoff-dependent"

    increment_any = increment_country or bool(row.get("future_any_increment_supported", False))
    benchmark_any = benchmark_country or bool(row.get("future_any_benchmark_supported", False))
    if increment_any and not benchmark_any:
        return "Incremental but not benchmark-competitive"
    if benchmark_any and not increment_any:
        return "Model competitive; signal increment unsupported"
    return "Not empirically supported under this setup"


def parse_cutoff(split_id: str) -> tuple[int, int]:
    match = re.fullmatch(r"train_to_(\d+)__test_from_(\d+)", split_id)
    if not match:
        raise ValueError(f"Unexpected future split id: {split_id}")
    return int(match.group(1)), int(match.group(2))


def build_future_cutoff_table(delta: pd.DataFrame, benchmark_delta: pd.DataFrame, feasibility: pd.DataFrame,
                              cfg: dict) -> pd.DataFrame:
    d = delta[delta["validation"] == "Future_Period"].copy()
    b = benchmark_delta[benchmark_delta["validation"] == "Future_Period"].copy()
    group_keys = ["signal", "target_role", "target", "universe", "sample_id", "split_id"]
    dsum = d.groupby(group_keys, as_index=False).agg(
        comparisons=("delta_r2", "count"),
        median_delta_r2=("delta_r2", "median"),
        positive_share=("delta_r2", lambda values: float((values > 0).mean())),
        median_delta_mae=("delta_mae", "median"),
        mae_improvement_share=("delta_mae", lambda values: float((values < 0).mean())),
    )
    bsum = b.groupby(group_keys, as_index=False).agg(
        benchmark_comparisons=("model_minus_best_benchmark_r2", "count"),
        median_model_minus_benchmark_r2=("model_minus_best_benchmark_r2", "median"),
        benchmark_positive_share=("model_minus_best_benchmark_r2", lambda values: float((values > 0).mean())),
        median_model_minus_benchmark_mae=("model_minus_best_benchmark_mae", "median"),
        benchmark_mae_improvement_share=("model_minus_best_benchmark_mae", lambda values: float((values < 0).mean())),
    )
    table = dsum.merge(bsum, on=group_keys, how="outer", validate="one_to_one")
    table[["train_end", "test_start"]] = table["split_id"].apply(lambda value: pd.Series(parse_cutoff(str(value))))
    feas = feasibility[["sample_id", "country_years", "countries", "nigeria_included", "universe_threshold"]].drop_duplicates()
    table = table.merge(feas, on="sample_id", how="left", validate="many_to_one")
    table["cutoff_verdict"] = table.apply(lambda row: cutoff_verdict(row, cfg), axis=1)
    return table.sort_values(["signal", "target_role", "universe", "train_end"]).reset_index(drop=True)


def main() -> None:
    cfg = load_config()
    corrected = pd.read_csv(PROCESSED_DIR / "MS2_SIGNAL_ADMISSIBILITY_PANEL_V3.csv")
    legacy = pd.read_csv(ROOT / "02_forensic_archive" / "LEGACY_INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv")
    feasibility = pd.read_csv(LOCKED_DIR / "Matched_Sample_Feasibility.csv")
    incremental = pd.read_csv(OUTPUT_DIR / "Corrected_Incremental_Summary.csv")
    benchmark = pd.read_csv(OUTPUT_DIR / "Corrected_Benchmark_Competitiveness_Summary.csv")
    delta = pd.read_csv(OUTPUT_DIR / "Corrected_Incremental_Delta.csv")
    benchmark_delta = pd.read_csv(OUTPUT_DIR / "Corrected_Model_vs_Best_Benchmark.csv")
    performance = pd.read_csv(OUTPUT_DIR / "Corrected_Model_Performance.csv")

    future_cutoffs = build_future_cutoff_table(delta, benchmark_delta, feasibility, cfg)
    future_cutoffs.to_csv(OUTPUT_DIR / "Future_Cutoff_Sensitivity_Table.csv", index=False)

    cutoff_summary = (
        future_cutoffs.groupby(["signal", "target_role", "target", "universe"], as_index=False)
        .agg(
            future_cutoffs_tested=("split_id", "nunique"),
            future_cutoffs_supported=("cutoff_verdict", lambda s: int((s == "Supported").sum())),
            future_cutoff_supported_share=("cutoff_verdict", lambda s: float((s == "Supported").mean())),
            future_any_increment_supported=("median_delta_r2", lambda s: bool((s > 0).any())),
            future_any_benchmark_supported=("median_model_minus_benchmark_r2", lambda s: bool((s > 0).any())),
            future_min_median_delta_r2=("median_delta_r2", "min"),
            future_max_median_delta_r2=("median_delta_r2", "max"),
        )
    )

    keys = ["signal", "target_role", "target", "universe"]
    pivot_rows: list[dict[str, object]] = []
    for key_values, group in incremental.groupby(keys, dropna=False):
        row = dict(zip(keys, key_values))
        country = group[group["validation"] == "Country_Holdout_CV"]
        future = group[group["validation"] == "Future_Period"]
        if len(country):
            item = country.iloc[0]
            row["country_median_delta_r2"] = item["median_delta_r2"]
            row["country_positive_share"] = item["positive_share"]
            row["country_increment_comparisons"] = item["comparisons"]
            row["country_median_delta_mae"] = item["median_delta_mae"]
        if len(future):
            item = future.iloc[0]
            row["future_aggregate_median_delta_r2"] = item["median_delta_r2"]
            row["future_aggregate_positive_share"] = item["positive_share"]
        pivot_rows.append(row)
    verdicts = pd.DataFrame(pivot_rows)

    benchmark_rows: list[dict[str, object]] = []
    for key_values, group in benchmark.groupby(keys, dropna=False):
        row = dict(zip(keys, key_values))
        country = group[group["validation"] == "Country_Holdout_CV"]
        future = group[group["validation"] == "Future_Period"]
        if len(country):
            item = country.iloc[0]
            row["country_median_model_minus_benchmark_r2"] = item["median_model_minus_benchmark_r2"]
            row["country_benchmark_positive_share"] = item["benchmark_positive_share"]
            row["country_benchmark_comparisons"] = item["comparisons"]
        if len(future):
            item = future.iloc[0]
            row["future_aggregate_median_model_minus_benchmark_r2"] = item["median_model_minus_benchmark_r2"]
            row["future_aggregate_benchmark_positive_share"] = item["benchmark_positive_share"]
        benchmark_rows.append(row)
    verdicts = verdicts.merge(pd.DataFrame(benchmark_rows), on=keys, how="left", validate="one_to_one")
    verdicts = verdicts.merge(cutoff_summary, on=keys, how="left", validate="one_to_one")

    feasibility_keys = feasibility[
        ["signal", "target_role", "target", "universe", "universe_type", "universe_threshold",
         "country_years", "countries", "nigeria_included"]
    ].drop_duplicates()
    verdicts = verdicts.merge(feasibility_keys, on=keys, how="left", validate="one_to_one")
    verdicts["setup_verdict"] = verdicts.apply(lambda row: setup_verdict(row, cfg), axis=1)
    verdicts = verdicts.sort_values(["signal", "target_role", "universe_threshold", "universe"]).reset_index(drop=True)
    verdicts.to_csv(OUTPUT_DIR / "Central_Verdict_Sensitivity_Table.csv", index=False)

    # Threshold sensitivity is a declared robustness analysis, not a post-hoc subgroup search.
    threshold_table = verdicts[verdicts["universe_type"] == "oil_rent_threshold"].copy()
    threshold_table.to_csv(OUTPUT_DIR / "Oil_Rent_Threshold_Sensitivity_Table.csv", index=False)

    # Only the primary and transformed normalized outcomes determine admissibility.
    # The untransformed ratio is a stress test documenting leverage and R2 instability.
    decision_roles = set(cfg["decision_target_roles"])
    signal_rows: list[dict[str, object]] = []
    supported_label = "Evidence-supported across country and cutoff tests"
    conditional_label = "Conditional/validation-cutoff-dependent"
    unsupported_label = "Not empirically supported under this setup"
    for signal, group in verdicts[verdicts["target_role"].isin(decision_roles)].groupby("signal"):
        eligible = group[group["setup_verdict"] != "Coverage-limited"]
        supported = int((eligible["setup_verdict"] == supported_label).sum())
        conditional = int((eligible["setup_verdict"] == conditional_label).sum())
        unsupported = int((eligible["setup_verdict"] == unsupported_label).sum())
        if len(eligible) == 0:
            final = "Insufficient evidence"
        elif supported == len(eligible):
            final = "Admissible across all prespecified decision setups"
        elif supported > 0 or conditional > 0:
            final = "Conditionally admissible; verdict depends on target, threshold, or validation geometry"
        elif unsupported == len(eligible):
            final = "Not empirically admissible across tested decision setups"
        else:
            final = "Inconclusive/unstable"
        signal_rows.append({
            "signal": signal,
            "final_preliminary_classification": final,
            "decision_setups_total": int(len(group)),
            "decision_setups_eligible": int(len(eligible)),
            "evidence_supported_setups": supported,
            "conditional_setups": conditional,
            "not_supported_setups": unsupported,
            "coverage_limited_setups": int((group["setup_verdict"] == "Coverage-limited").sum()),
            "raw_ratio_stress_test_excluded_from_classification": True,
        })
    pd.DataFrame(signal_rows).to_csv(OUTPUT_DIR / "Preliminary_Signal_Admissibility_Decisions.csv", index=False)

    # Raw ratio extreme-value and fold leverage audit.
    raw = corrected.dropna(subset=["Inward_FDI_Net_Flow_GDP_Pct"]).copy()
    raw["Absolute_Flow_GDP_Pct"] = raw["Inward_FDI_Net_Flow_GDP_Pct"].abs()
    extreme_rows = []
    for threshold in cfg["raw_ratio_extreme_thresholds_pct"]:
        subset = raw[raw["Absolute_Flow_GDP_Pct"] >= float(threshold)].copy()
        extreme_rows.append({
            "absolute_threshold_pct": float(threshold),
            "country_years": int(len(subset)),
            "countries": int(subset["ISO3"].nunique()),
            "minimum": float(subset["Inward_FDI_Net_Flow_GDP_Pct"].min()) if len(subset) else np.nan,
            "maximum": float(subset["Inward_FDI_Net_Flow_GDP_Pct"].max()) if len(subset) else np.nan,
        })
    pd.DataFrame(extreme_rows).to_csv(OUTPUT_DIR / "Raw_Flow_GDP_Extreme_Value_Summary.csv", index=False)
    raw.nlargest(100, "Absolute_Flow_GDP_Pct")[[
        "Country Name", "ISO3", "Year", "Inward_FDI_Net_Flow_GDP_Pct", "Absolute_Flow_GDP_Pct"
    ]].to_csv(OUTPUT_DIR / "Raw_Flow_GDP_Top_100_Extreme_Observations.csv", index=False)

    raw_perf = performance[performance["target_role"] == "raw_ratio_stress"].copy()
    raw_perf["prediction_span"] = raw_perf["prediction_max"] - raw_perf["prediction_min"]
    raw_perf["target_span"] = raw_perf["target_max"] - raw_perf["target_min"]
    raw_perf.to_csv(OUTPUT_DIR / "Raw_Ratio_Fold_Leverage_Audit.csv", index=False)

    stability = (
        performance[performance["target_role"].isin(["normalized", "raw_ratio_stress"])]
        .groupby(["signal", "target_role", "universe", "validation", "algorithm", "model"], as_index=False)
        .agg(min_r2=("r2", "min"), median_r2=("r2", "median"), max_r2=("r2", "max"), r2_range=("r2", lambda s: float(s.max()-s.min())))
    )
    stability.to_csv(OUTPUT_DIR / "Normalized_vs_Raw_Ratio_Stability.csv", index=False)

    old_avail = legacy[["ISO3", "Year", "FDI_Flows_Millions_USD"]].copy()
    old_avail["Legacy_Target_Available"] = old_avail["FDI_Flows_Millions_USD"].notna()
    new_avail = corrected[["Country Name", "ISO3", "Year", "Oil_Rents_GDP_Pct", "Inward_FDI_Net_Flow_USD"]].copy()
    new_avail["Corrected_Flow_Available"] = new_avail["Inward_FDI_Net_Flow_USD"].notna()
    audit = new_avail.merge(old_avail[["ISO3", "Year", "Legacy_Target_Available"]], on=["ISO3", "Year"], how="left")
    audit["Legacy_Target_Available"] = audit["Legacy_Target_Available"].fillna(False).astype(bool)

    country = (
        audit.groupby(["Country Name", "ISO3"], as_index=False)
        .agg(
            Max_Oil_Rents_1990_2021=("Oil_Rents_GDP_Pct", "max"),
            Legacy_Target_Observations=("Legacy_Target_Available", "sum"),
            Corrected_Flow_Observations=("Corrected_Flow_Available", "sum"),
        )
    )
    country["Previously_Excluded"] = country["Legacy_Target_Observations"] == 0
    country["Restored_By_Corrected_Flow"] = (country["Legacy_Target_Observations"] == 0) & (country["Corrected_Flow_Observations"] > 0)
    country["Nigeria"] = country["ISO3"] == "NGA"
    for threshold in cfg["oil_rent_thresholds_pct_gdp"]:
        label = str(threshold).replace(".", "p")
        country[f"Oil_Rent_Intensive_ge{label}pct"] = country["Max_Oil_Rents_1990_2021"] >= float(threshold)
    country.to_csv(OUTPUT_DIR / "Country_Coverage_Audit.csv", index=False)

    summary = []
    for threshold in cfg["oil_rent_thresholds_pct_gdp"]:
        high_rows = audit[audit["Oil_Rents_GDP_Pct"] >= float(threshold)]
        flag = country["Max_Oil_Rents_1990_2021"] >= float(threshold)
        summary.extend([
            {"threshold_pct": threshold, "metric": "Oil-rent-intensive economies", "value": int(flag.sum())},
            {"threshold_pct": threshold, "metric": "Previously excluded oil-rent-intensive economies", "value": int((flag & country["Previously_Excluded"]).sum())},
            {"threshold_pct": threshold, "metric": "Previously excluded economies restored by corrected flow", "value": int((flag & country["Restored_By_Corrected_Flow"]).sum())},
            {"threshold_pct": threshold, "metric": "High-oil-rent country-years", "value": int(len(high_rows))},
            {"threshold_pct": threshold, "metric": "High-oil-rent country-years with legacy target", "value": int(high_rows["Legacy_Target_Available"].sum())},
            {"threshold_pct": threshold, "metric": "High-oil-rent country-years with corrected flow", "value": int(high_rows["Corrected_Flow_Available"].sum())},
        ])
    summary.append({"threshold_pct": np.nan, "metric": "Nigeria corrected FDI-flow observations", "value": int(audit.loc[audit["ISO3"] == "NGA", "Corrected_Flow_Available"].sum())})

    # Restoration and complete-case eligibility are different. A country can have the
    # corrected FDI-flow outcome but remain outside M3 because a core predictor is absent.
    reference_threshold = float(cfg["reference_oil_rent_threshold_pct_gdp"])
    high_reference = country["Max_Oil_Rents_1990_2021"] >= reference_threshold
    previously_excluded = set(country.loc[high_reference & country["Previously_Excluded"], "ISO3"])
    restored = set(country.loc[high_reference & country["Restored_By_Corrected_Flow"], "ISO3"])
    if restored != previously_excluded:
        missing_restoration = sorted(previously_excluded - restored)
        raise RuntimeError(f"Outcome restoration incomplete for reference oil-rent universe: {missing_restoration}")

    primary_target = str(cfg["targets"]["primary"])
    m3_features = [
        "Inward_FDI_Net_Flow_asinh_lag1" if feature == "__TARGET_LAG1__" else feature
        for feature in cfg["feature_sets"]["M3_Macro_Oil_RegQuality"]
    ]
    restored_gaps = []
    restored_m3_eligible = 0
    for iso3 in sorted(restored):
        flow_rows = corrected[(corrected["ISO3"] == iso3) & corrected[primary_target].notna()].copy()
        eligible_rows = flow_rows.dropna(subset=[primary_target] + m3_features)
        if len(eligible_rows):
            restored_m3_eligible += 1
            continue
        always_missing = [feature for feature in m3_features if feature in flow_rows and flow_rows[feature].notna().sum() == 0]
        partially_missing = [
            feature for feature in m3_features
            if feature in flow_rows and feature not in always_missing and flow_rows[feature].isna().any()
        ]
        restored_gaps.append({
            "ISO3": iso3,
            "country_name": str(flow_rows["Country Name"].dropna().iloc[0]) if len(flow_rows["Country Name"].dropna()) else "",
            "flow_years": int(len(flow_rows)),
            "always_missing_core_fields": "; ".join(always_missing),
            "partially_missing_core_fields": "; ".join(partially_missing),
            "status": "Outcome restored; no complete M3 country-year",
        })
    pd.DataFrame(restored_gaps, columns=[
        "ISO3", "country_name", "flow_years", "always_missing_core_fields",
        "partially_missing_core_fields", "status",
    ]).to_csv(OUTPUT_DIR / "Restored_But_Incomplete_Log.csv", index=False)

    restoration_test = pd.DataFrame([
        {"check": "previously_excluded_reference_economies", "value": len(previously_excluded), "status": "INFO"},
        {"check": "restored_with_corrected_flow", "value": len(restored), "status": "PASS" if restored == previously_excluded else "FAIL"},
        {"check": "restored_with_at_least_one_complete_M3_row", "value": restored_m3_eligible, "status": "INFO"},
        {"check": "restored_without_complete_M3_row", "value": len(restored_gaps), "status": "INFO"},
        {"check": "negative_annual_flows_retained", "value": int((corrected["Inward_FDI_Net_Flow_USD"] < 0).sum()), "status": "PASS" if (corrected["Inward_FDI_Net_Flow_USD"] < 0).any() else "FAIL"},
    ])
    restoration_test.to_csv(OUTPUT_DIR / "Restoration_Self_Test.csv", index=False)
    summary.extend([
        {"threshold_pct": reference_threshold, "metric": "Previously excluded reference-threshold economies restored with corrected flow", "value": len(restored)},
        {"threshold_pct": reference_threshold, "metric": "Restored reference-threshold economies with at least one complete M3 row", "value": restored_m3_eligible},
        {"threshold_pct": reference_threshold, "metric": "Restored reference-threshold economies without a complete M3 row", "value": len(restored_gaps)},
    ])
    pd.DataFrame(summary).to_csv(OUTPUT_DIR / "Coverage_Audit_Summary.csv", index=False)

    us_2021 = legacy.loc[(legacy["ISO3"] == "USA") & (legacy["Year"] == 2021), "FDI_Flows_Millions_USD"]
    forensic = [
        {
            "finding": "Legacy target was labelled as flow but had stock-scale magnitude",
            "evidence": f"USA 2021 legacy value = {float(us_2021.iloc[0]):,.0f} US$ millions" if len(us_2021) else "USA 2021 not found",
            "corrective_action": "Use official annual net-inflow series as primary target; retain stock only as forensic evidence.",
        },
        {
            "finding": "Legacy target contained no negative observations",
            "evidence": f"Legacy negatives = {int((legacy['FDI_Flows_Millions_USD'] < 0).sum())}; corrected annual-flow negatives = {int((corrected['Inward_FDI_Net_Flow_USD'] < 0).sum())}",
            "corrective_action": "Preserve negative annual flows and use asinh transformation on US$ millions.",
        },
        {
            "finding": "Legacy target-to-GDP ratio was clipped at exactly 200",
            "evidence": f"Legacy observations exactly equal to 200 = {int((legacy['FDI_GDP_Pct'] == 200).sum())}",
            "corrective_action": "Use official World Bank annual net inflows as % GDP without clipping; treat raw ratio as stress test and asinh ratio as normalized robustness target.",
        },
        {
            "finding": "Legacy country mapping excluded Nigeria and many oil-rent-intensive economies",
            "evidence": f"Nigeria legacy observations = {int(legacy.loc[legacy['ISO3']=='NGA', 'FDI_Flows_Millions_USD'].notna().sum())}; corrected flow observations = {int(corrected.loc[corrected['ISO3']=='NGA', 'Inward_FDI_Net_Flow_USD'].notna().sum())}",
            "corrective_action": "Use World Bank ISO3 codes directly; never map outcome countries through a policy-data subset.",
        },
    ]
    pd.DataFrame(forensic).to_csv(OUTPUT_DIR / "Forensic_Audit_Findings.csv", index=False)

    print(verdicts.to_string(index=False))
    print("\nPreliminary signal classifications")
    print(pd.DataFrame(signal_rows).to_string(index=False))


if __name__ == "__main__":
    main()
