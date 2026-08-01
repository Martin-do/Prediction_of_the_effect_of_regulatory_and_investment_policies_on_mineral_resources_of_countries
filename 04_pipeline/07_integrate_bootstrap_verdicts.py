from __future__ import annotations

import pandas as pd

from common import OUTPUT_DIR


def main() -> None:
    central = pd.read_csv(OUTPUT_DIR / "Central_Verdict_Sensitivity_Table.csv")
    bootstrap = pd.read_csv(OUTPUT_DIR / "Bootstrap_Five_Way_Setup_Verdicts.csv")

    merge_keys = ["signal", "target_role", "target", "universe"]
    bootstrap_columns = [
        "bootstrap_units",
        "material_units",
        "marginal_units",
        "setup_dependent_units",
        "unsupported_units",
        "coverage_limited_units",
        "positive_or_better_share",
        "bootstrap_five_way_setup_verdict",
        "verdict_scheme_order",
    ]
    cols = merge_keys + bootstrap_columns

    # On a fresh pre-bootstrap table, preserve the point-estimate verdict for audit comparison.
    # On an already integrated table, remove the previous integration layer before merging again.
    already_integrated = "bootstrap_five_way_setup_verdict" in central.columns
    if already_integrated:
        central = central.drop(columns=["setup_verdict"], errors="ignore")
    elif (
        "setup_verdict" in central.columns
        and "point_estimate_setup_verdict_deprecated" not in central.columns
    ):
        central = central.rename(
            columns={"setup_verdict": "point_estimate_setup_verdict_deprecated"}
        )

    integration_columns = bootstrap_columns + [
        "decision_basis",
        "material_setup_requires_caution",
        "material_setup_interpretation",
    ]
    central = central.drop(
        columns=[column for column in integration_columns if column in central.columns],
        errors="ignore",
    )

    merged = central.merge(
        bootstrap[cols],
        on=merge_keys,
        how="left",
        validate="one_to_one",
    )
    merged["setup_verdict"] = merged["bootstrap_five_way_setup_verdict"]
    merged["decision_basis"] = (
        "Paired country-cluster bootstrap across algorithms and prespecified validation geometries; "
        "point-estimate verdict retained only for audit comparison."
    )
    merged["material_setup_requires_caution"] = (
        (merged["setup_verdict"] == "Supported and practically material")
        & (merged["universe"] == "Oil_Rent_Intensive_Pre2016_ge1pct")
    )
    merged["material_setup_interpretation"] = merged["material_setup_requires_caution"].map({
        True: (
            "Supportive but not standalone confirmatory evidence: the single ge1pct material setup is the "
            "normalized outcome specification, has a lower uncertainty bound close to zero, and uses a conditional "
            "fixed-prediction bootstrap interval that excludes model-refitting variability."
        ),
        False: "No additional material-cell qualification beyond the five-way verdict and cross-setup guardrail.",
    })
    merged = merged.sort_values(["signal", "target_role", "universe_threshold", "universe"]).reset_index(drop=True)
    merged.to_csv(OUTPUT_DIR / "Central_Verdict_Sensitivity_Table.csv", index=False)
    merged[merged["universe_type"] == "oil_rent_threshold"].to_csv(
        OUTPUT_DIR / "Oil_Rent_Threshold_Sensitivity_Table.csv", index=False
    )
    merged.loc[merged["material_setup_requires_caution"], [
        "signal", "target_role", "target", "universe", "setup_verdict",
        "material_units", "bootstrap_units", "material_setup_requires_caution",
        "material_setup_interpretation",
    ]].to_csv(OUTPUT_DIR / "Material_Setup_Caveats.csv", index=False)

    pattern = (
        merged[merged["target_role"].isin(["primary", "normalized"])]
        .groupby("signal", as_index=False)
        .agg(
            decision_setups=("setup_verdict", "count"),
            material_setups=("setup_verdict", lambda s: int((s == "Supported and practically material").sum())),
            marginal_setups=("setup_verdict", lambda s: int((s == "Directionally positive but marginal").sum())),
            setup_dependent_setups=("setup_verdict", lambda s: int((s == "Setup-dependent").sum())),
            unsupported_setups=("setup_verdict", lambda s: int((s == "Unsupported").sum())),
            coverage_limited_setups=("setup_verdict", lambda s: int((s == "Coverage-limited").sum())),
        )
    )
    pattern["cross_setup_classification"] = pattern.apply(
        lambda r: (
            "Coverage-limited" if r["coverage_limited_setups"] == r["decision_setups"]
            else "Unsupported" if r["unsupported_setups"] == r["decision_setups"]
            else "Supported and practically material" if r["material_setups"] == r["decision_setups"]
            else "Directionally positive but marginal" if (r["material_setups"] + r["marginal_setups"] == r["decision_setups"])
            else "Setup-dependent"
        ), axis=1
    )
    pattern["interpretation_guardrail"] = (
        "Classification reads the complete prespecified setup pattern; no single setup with a confidence interval excluding zero controls the conclusion."
    )
    pattern.to_csv(OUTPUT_DIR / "Signal_Cross_Setup_Pattern.csv", index=False)

    decisions = pattern.rename(columns={"cross_setup_classification": "final_uncertainty_quantified_classification"})
    decisions["material_bin_required"] = False
    decisions["raw_ratio_stress_test_excluded_from_classification"] = True
    decisions.to_csv(OUTPUT_DIR / "Preliminary_Signal_Admissibility_Decisions.csv", index=False)
    print(merged[["signal", "target_role", "universe", "setup_verdict"]].to_string(index=False))
    print("\nCross-setup classifications")
    print(pattern.to_string(index=False))


if __name__ == "__main__":
    main()
