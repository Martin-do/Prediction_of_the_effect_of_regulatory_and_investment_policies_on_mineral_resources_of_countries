# Version Notes — V0.4.2 Persistence-Baseline Forensics Update

V0.4.2 makes no changes to the panel, folds, matched samples, model specifications, benchmark set, bootstrap seeds, replicate counts, verdicts, or scientific numerical results. It is additive.

## Changes

1. A new step, `04_pipeline/08_persistence_baseline_forensics.py`, generates the lag-1 persistence baseline for the legacy stock-mislabelled target and the corrected annual-flow target across identical scales, samples and estimands. The step is read-only with respect to the frozen layer and reads the forensic archive solely to quantify the legacy defect.
2. Two new outputs are added: `07_outputs/Persistence_Baseline_Forensics.csv` (full matrix) and `07_outputs/Persistence_Headline_Comparison.csv` (like-for-like contrasts).
3. `run_pipeline.py` and `04_pipeline/07_verify_deterministic_rerun.py` register the new step. The verifier change is required for correctness: without it the new outputs would persist on disk across the second derivation and be scored byte-identical without having been re-derived.
4. The lock-record claim "lag-1 persistence R² falls from about 0.98 (stock) to about 0.04 (flow)" is superseded. The two values were different estimands. The generated like-for-like contrast on common support is 0.9869 against −0.1591.

## Corrections to the 14 July 2026 lock record

Identified during drafting and carried into V0.4.2 documentation:

1. **§3** states the two-derivation check passes 199 of 199 files. The V0.4.1 package reports 200/200 (`Reproducibility_Rerun_Result.txt`; `Reproducibility_Rerun_Comparison.csv` has 200 rows, all byte-identical). Under V0.4.2 the count is 202/202, verified by full regeneration on 15 July 2026.
2. **§5** describes a feature ladder beginning "M0 oil rents". No M0 rung exists in the corrected configuration. `analysis_config.json` defines M1, M2 and M3 only, and the sole comparisons are M1→M2 and M2→M3. `M0` appears only in `02_forensic_archive/` and `legacy_archive/`; it is a legacy artefact and cannot be nested by construction in any case.
3. **§5** describes M1 as GDP, population, inflation and electricity access, omitting the lagged outcome. Every rung carries `__TARGET_LAG1__`. The omission matters because `Lagged_Flow` is separately one of the three naive benchmarks, and the distinction between the two roles must be explicit.
4. **§4 / core_feature_decisions** attribute the trade-openness exclusion to observability gaps in the restored resource economies. Missingness among the 31 restored economies is 19.7% against 21.1% panel-wide — not disproportionate. The defensible reason is that `Trade_GDP_Pct` is wholly absent for two restored economies, Nigeria and Trinidad and Tobago, so admitting trade to the core ladder would remove Nigeria from every complete-case M3 sample.
5. **§10** lists a clean end-to-end regeneration as optional belt-and-braces. It was treated as mandatory for V0.4.2 and has been completed: PASS at 202/202, with the frozen layer byte-identical to the V0.4.1 package.

## Canonical environment closure

A clean root-command regeneration was completed under the pinned Python 3.13.5 environment and exact package lock. The deterministic check passed at 202/202, and `08_validation/Environment_Metadata.json` now agrees with `09_environment/python-version.txt`. The earlier independent Python 3.12.3 run remains documented as cross-version evidence.

## Locked computation

Unchanged from V0.4.1. Main bootstrap seed 20260714; 2,000 replicates per algorithm-validation unit; null seed 20260715; 20 permutations × 500 replicates. The persistence baseline is fit-free and consumes no seed.

## Additional change made during regeneration

`04_pipeline/07_build_reproducibility_report.py` previously hardcoded the release string. The report now derives the release label from `03_config/analysis_config.json`, closing the defect for this and subsequent releases.
