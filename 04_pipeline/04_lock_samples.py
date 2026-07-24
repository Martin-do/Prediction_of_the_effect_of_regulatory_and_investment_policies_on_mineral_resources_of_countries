from __future__ import annotations

import json

import pandas as pd

from common import LOCKED_DIR, PROCESSED_DIR, load_config


def target_lag(target: str) -> str:
    mapping = {
        "Inward_FDI_Net_Flow_asinh": "Inward_FDI_Net_Flow_asinh_lag1",
        "Inward_FDI_Net_Flow_GDP_Pct_asinh": "Inward_FDI_Net_Flow_GDP_Pct_asinh_lag1",
        "Inward_FDI_Net_Flow_GDP_Pct": "Inward_FDI_Net_Flow_GDP_Pct_lag1",
    }
    if target not in mapping:
        raise KeyError(f"No lag mapping declared for target {target}")
    return mapping[target]


def resolve(features: list[str], target: str) -> list[str]:
    lag = target_lag(target)
    return [lag if feature == "__TARGET_LAG1__" else feature for feature in features]


def slug(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value).strip("_")


def subset_universe(panel: pd.DataFrame, definition: dict) -> pd.DataFrame:
    if definition["type"] == "all":
        return panel.copy()
    if definition["type"] == "oil_rent_threshold":
        threshold = float(definition["threshold"])
        return panel[panel["Max_Oil_Rents_Pre2016"] >= threshold].copy()
    raise KeyError(f"Unknown universe type: {definition['type']}")


def main() -> None:
    cfg = load_config()
    panel = pd.read_csv(PROCESSED_DIR / "MS2_SIGNAL_ADMISSIBILITY_PANEL_V3.csv")
    folds = pd.read_csv(LOCKED_DIR / "Country_Fold_Assignments.csv", usecols=["ISO3", "Country_Fold"])
    panel = panel.merge(folds, on="ISO3", how="left", validate="many_to_one")
    if panel["Country_Fold"].isna().any():
        raise RuntimeError("Every panel country must have a persisted fold assignment")

    feature_manifest: list[dict[str, object]] = []
    for model_name, features in cfg["feature_sets"].items():
        for target_role, target in cfg["targets"].items():
            for feature in resolve(features, target):
                available = feature in panel.columns
                feature_manifest.append({
                    "model": model_name,
                    "target_role": target_role,
                    "target": target,
                    "expected_feature": feature,
                    "available": available,
                    "used": available,
                    "reason_if_absent": "" if available else "CORE FEATURE MISSING",
                })
                if not available:
                    raise KeyError(f"Core feature missing: {feature} for {model_name}/{target}")
    pd.DataFrame(feature_manifest).to_csv(LOCKED_DIR / "Feature_Set_Manifest.csv", index=False)

    sample_summary: list[dict[str, object]] = []
    sample_registry: list[dict[str, str]] = []
    reference_cutoff = cfg["reference_future_cutoff"]
    for comparison in cfg["comparisons"]:
        base_name = comparison["base_model"]
        added_name = comparison["added_model"]
        signal = comparison["signal"]
        for target_role, target in cfg["targets"].items():
            base_features = resolve(cfg["feature_sets"][base_name], target)
            added_features = resolve(cfg["feature_sets"][added_name], target)
            for universe_def in cfg["universes"]:
                universe = str(universe_def["name"])
                # The untransformed flow/GDP ratio is an extreme-value stress test only;
                # it is not multiplied across subgroup thresholds or used for final decisions.
                if target_role == "raw_ratio_stress" and universe != "All_Eligible":
                    continue
                subset = subset_universe(panel, universe_def)
                required = [target, "ISO3", "Year", "Country_Fold", "Row_ID"] + added_features
                locked = subset.dropna(subset=required).copy()
                locked = locked.sort_values(["ISO3", "Year", "Row_ID"]).reset_index(drop=True)
                sample_id = f"{slug(base_name)}_vs_{slug(added_name)}__{slug(target_role)}__{slug(universe)}"
                file_name = f"Matched_Sample__{sample_id}.csv"
                columns = [
                    "Row_ID", "Country Name", "ISO3", "Year", "Country_Fold",
                    "Max_Oil_Rents_Pre2016", target,
                ] + sorted(set(base_features + added_features))
                locked[columns].to_csv(LOCKED_DIR / file_name, index=False)
                sample_registry.append({
                    "sample_id": sample_id,
                    "file": file_name,
                    "signal": signal,
                    "base_model": base_name,
                    "added_model": added_name,
                    "target_role": target_role,
                    "target": target,
                    "universe": universe,
                    "universe_type": str(universe_def["type"]),
                    "universe_threshold": universe_def.get("threshold", ""),
                    "base_features_json": json.dumps(base_features),
                    "added_features_json": json.dumps(added_features),
                })
                by_country = locked.groupby("ISO3").size() if len(locked) else pd.Series(dtype=float)
                sample_summary.append({
                    "sample_id": sample_id,
                    "signal": signal,
                    "base_model": base_name,
                    "added_model": added_name,
                    "target_role": target_role,
                    "target": target,
                    "universe": universe,
                    "universe_type": str(universe_def["type"]),
                    "universe_threshold": universe_def.get("threshold", ""),
                    "country_years": int(len(locked)),
                    "countries": int(locked["ISO3"].nunique()),
                    "year_min": int(locked["Year"].min()) if len(locked) else None,
                    "year_max": int(locked["Year"].max()) if len(locked) else None,
                    "median_years_per_country": float(by_country.median()) if len(by_country) else None,
                    "nigeria_included": bool((locked["ISO3"] == "NGA").any()),
                    "reference_future_train_rows": int((locked["Year"] <= int(reference_cutoff["train_end"])).sum()),
                    "reference_future_test_rows": int((locked["Year"] >= int(reference_cutoff["test_start"])).sum()),
                })

    pd.DataFrame(sample_registry).to_csv(LOCKED_DIR / "Matched_Sample_Registry.csv", index=False)
    summary = pd.DataFrame(sample_summary)
    summary.to_csv(LOCKED_DIR / "Matched_Sample_Feasibility.csv", index=False)
    print(summary[["signal", "target_role", "universe", "country_years", "countries", "nigeria_included"]].to_string(index=False))


if __name__ == "__main__":
    main()
