from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import openpyxl
import pandas as pd
import scipy
import sklearn
import threadpoolctl
import xlrd

from common import LOCKED_DIR, OUTPUT_DIR, PROCESSED_DIR, RAW_DIR, ROOT, VALIDATION_DIR, load_config, sha256_file


def checksum_table(directory: Path, label: str) -> pd.DataFrame:
    rows = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            rows.append({
                "group": label,
                "relative_path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    return pd.DataFrame(rows)


def main() -> None:
    config = load_config()
    release_label = config["release"]

    root_rows = pd.DataFrame([
        {
            "group": "root_orchestrator",
            "relative_path": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in (ROOT / "README.md", ROOT / "run_pipeline.py")
    ])
    frames = [
        root_rows,
        checksum_table(ROOT / "00_protocol", "protocol"),
        checksum_table(ROOT / "01_raw_data", "raw_input"),
        checksum_table(ROOT / "02_forensic_archive", "forensic_archive"),
        checksum_table(ROOT / "03_config", "configuration"),
        checksum_table(ROOT / "04_pipeline", "pipeline_code"),
        checksum_table(PROCESSED_DIR, "processed_data"),
        checksum_table(LOCKED_DIR, "locked_design"),
        checksum_table(OUTPUT_DIR, "outputs"),
        checksum_table(ROOT / "09_environment", "environment_lock"),
        checksum_table(ROOT / "10_reporting_assets", "reporting_assets"),
        checksum_table(ROOT / "11_posthoc_checks", "posthoc_checks"),
    ]
    checksums = pd.concat(frames, ignore_index=True)
    checksums.to_csv(VALIDATION_DIR / "Release_Checksums.csv", index=False)

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "threadpoolctl": threadpoolctl.__version__,
        "xlrd": xlrd.__version__,
        "openpyxl": openpyxl.__version__,
    }
    with (VALIDATION_DIR / "Environment_Metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(environment, handle, indent=2)

    panel = pd.read_csv(PROCESSED_DIR / "MS2_SIGNAL_ADMISSIBILITY_PANEL_V3.csv")
    verdicts = pd.read_csv(OUTPUT_DIR / "Central_Verdict_Sensitivity_Table.csv")
    decisions = pd.read_csv(OUTPUT_DIR / "Preliminary_Signal_Admissibility_Decisions.csv")
    cutoffs = pd.read_csv(OUTPUT_DIR / "Future_Cutoff_Sensitivity_Table.csv")
    thresholds = pd.read_csv(OUTPUT_DIR / "Oil_Rent_Threshold_Sensitivity_Table.csv")
    stability = pd.read_csv(OUTPUT_DIR / "Normalized_vs_Raw_Ratio_Stability.csv")
    source_validation = pd.read_csv(VALIDATION_DIR / "Raw_Source_Validation.csv")
    rerun_path = VALIDATION_DIR / "Reproducibility_Rerun_Result.txt"
    rerun_result = rerun_path.read_text(encoding="utf-8").strip() if rerun_path.exists() else "NOT RUN"

    raw = stability[stability["target_role"] == "raw_ratio_stress"]
    norm = stability[stability["target_role"] == "normalized"]
    raw_min = raw["min_r2"].min() if len(raw) else float("nan")
    norm_min = norm["min_r2"].min() if len(norm) else float("nan")

    report = f"""# Reproducibility report — release {release_label}

## Build status

- Raw source validation: {int((source_validation['validation_status'] == 'PASS').sum())}/{len(source_validation)} files passed.
- Corrected panel: {len(panel):,} country-year rows, {panel['ISO3'].nunique():,} economies, {panel['Year'].min()}-{panel['Year'].max()}.
- Verified annual FDI-flow observations: {panel['Inward_FDI_Net_Flow_USD'].notna().sum():,}.
- Negative annual FDI-flow observations retained: {(panel['Inward_FDI_Net_Flow_USD'] < 0).sum():,}.
- Nigeria annual-flow observations: {panel.loc[panel['ISO3']=='NGA', 'Inward_FDI_Net_Flow_USD'].notna().sum():,}.
- Setup-specific verdict rows: {len(verdicts):,}.
- Future-cutoff sensitivity rows: {len(cutoffs):,} across five prespecified cutoffs.
- Oil-rent-threshold sensitivity rows: {len(thresholds):,} across 1%, 5%, 10%, and 15% pre-2016 maximum-rent thresholds.
- Signal-level preliminary classifications: {len(decisions):,}.
- Deterministic rerun verification: {rerun_result}

## Four robustness issues closed

1. **Extreme raw flow/GDP folds.** The untransformed percentage ratio is retained as a stress test, not as the decision-bearing robustness target. The signed `asinh(flow/GDP)` target is the principal normalized outcome. Its worst split-level R2 is {norm_min:.3f}, compared with {raw_min:.3f} for the raw ratio. Extreme observations and prediction spans are exported explicitly.
2. **Future-period cutoff sensitivity.** Five cutoffs are prespecified: 2012/2013, 2014/2015, 2015/2016, 2016/2017, and 2018/2019. Setup decisions use the share of cutoffs that independently satisfy the incremental and benchmark rules.
3. **Oil-rent threshold sensitivity.** The 5% subgroup is no longer treated as uniquely authoritative. The same analysis is repeated at 1%, 5%, 10%, and 15% thresholds, all defined from the 1990-2015 classification window.
4. **Sector-alignment limitation.** Aggregate FDI is explicitly defined as a national investment-context outcome. The paper and repository prohibit claims that it directly measures petroleum- or mining-sector investment. The standalone scope is resource-rich economies, not sector-specific investment prediction.

## Pipeline invariants

1. Corrected results use only the official World Bank workbooks in `01_raw_data/world_bank`.
2. The forensic archive is never imported by corrected data construction or modelling; it is read only to quantify legacy defects.
3. Target names preserve flow, normalized flow, and raw-ratio stress-test distinctions.
4. Negative annual flows are retained.
5. No corrected target is clipped.
6. Predictors are lagged only across consecutive country-years.
7. ISO3-to-fold assignments are persisted before modelling.
8. Every incremental comparison uses a saved common country-year sample.
9. Missing core features stop the run.
10. Added models are compared with the strongest prespecified naive benchmark on the same split.
11. Future-cutoff and oil-rent-threshold sensitivity grids are declared in configuration before modelling.
12. Exact package versions, inputs, code, samples, and outputs are checksum-locked.

## Scientific status

The {release_label} release is suitable for scientific interpretation of setup-dependent signal admissibility, subject to the conditional-bootstrap estimand and correlated-setup caveats below. The raw flow/GDP ratio remains available as an intentionally harsh leverage stress test but is excluded from final admissibility classification. Final classifications are based only on the transformed annual-flow level and transformed normalized-flow targets.


## Bootstrap estimand

The paired country-cluster bootstrap resamples countries from frozen out-of-fold or future-period country contributions. Each selected country contributes its complete held-out block of years, and the same country multiplicities are applied to the baseline and added-signal models within each replicate. The intervals therefore quantify uncertainty associated with the composition of the evaluated country population, conditional on the fitted models and frozen predictions. They do not include model-refitting variability and may be narrower than total training-and-sampling uncertainty intervals.

## Material-cell qualification

Two oil-rent setups in the pre-2016 >=1% universe meet the prespecified materiality rule. They are treated as supportive components of the complete cross-setup pattern, not as independent confirmatory replications, because the setups are correlated, their lower uncertainty bounds are close to zero, and their intervals are conditional on fixed predictions. The material category is not required to be populated for the paper's conclusion.

## Scope limitation

Aggregate inward FDI captures the national investment environment. It does not identify petroleum, mining, tar-sand, or extractive-project investment. Findings must therefore be framed as evidence about candidate signals for decision support in resource-rich economies, not as direct prediction of resource-sector capital flows.
"""
    (VALIDATION_DIR / "Reproducibility_Report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
