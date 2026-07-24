# Technical audit trail — V0.4.2

## Purpose

This record documents the computational and release-control evidence supporting the V0.4.2 signal-admissibility audit. It is intended to carry implementation detail that is not required in the journal article's main Methods section while preserving a complete, inspectable trail for reviewers and reusers.

This file does not replace the decision-bearing methodological description in the manuscript. The article must still state the outcome, feature ladder, validation geometries, matched-sample comparisons, paired country-cluster bootstrap estimand, five verdict definitions, and setup- and signal-level aggregation rules.

## Release identity

- Release: **V0.4.2**
- Release label source: `03_config/analysis_config.json`
- Root command: `python run_pipeline.py`
- Pinned interpreter: Python **3.13.5**
- Exact package lock: `09_environment/requirements-lock.txt`
- Analysis seed: **20260713**
- Bootstrap seed: **20260714**
- Null-check seed: **20260715**
- Primary analytical layer: `05_processed_data/`, `06_locked_design/`, and `07_outputs/`

## Canonical reproduction performed for the DOI-ready package

A clean root-command reproduction was completed on **15 July 2026** from the official raw workbooks included in the archive.

- Start: `2026-07-15T17:33:09.560177+00:00`
- End: `2026-07-15T17:37:58.134468+00:00`
- Raw-source validation: **10/10 PASS**
- Independent two-derivation comparison: **202/202 files byte-identical**
- Regenerated analytical layer versus the clean V0.4.2 release: **202/202 files byte-identical**
- Regenerated V0.4.1 frozen layer: **200/200 files byte-identical**
- Additive V0.4.2 outputs: **2 files**, with no change to the 200-file frozen layer

The canonical run used the versions recorded in `08_validation/Environment_Metadata.json`:

- pandas 2.2.3
- NumPy 2.3.5
- SciPy 1.17.0
- scikit-learn 1.8.0
- joblib 1.5.3
- threadpoolctl 3.6.0
- xlrd 2.0.2
- openpyxl 3.1.5

The complete console record is stored in `08_validation/Clean_Run_Log.txt`. The deterministic comparison is stored in `08_validation/Reproducibility_Rerun_Comparison.csv`, and the pass statement is stored in `08_validation/Reproducibility_Rerun_Result.txt`.

## Cross-machine persistence-forensics reproduction

The two V0.4.2 persistence-forensics outputs reproduced with the same SHA-256 hashes under the canonical Python 3.13.5 run as under the independent Python 3.12.3 run:

| File | SHA-256 |
|---|---|
| `07_outputs/Persistence_Baseline_Forensics.csv` | `cf17a4edf62c95d09843f6862f30688e153edab194c1a967249695342dec47d3` |
| `07_outputs/Persistence_Headline_Comparison.csv` | `9b3bb269107599c7ac1657e2f11ec81f7c51adf32dd9804346cdf86d263267c2` |

This step is fit-free and uses the rule \(\hat{y}_{t}=y_{t-1}\). It adds no trained model and consumes no random seed.

## Data and construct audit

The corrected panel is generated once by `04_pipeline/02_build_panel_v3.py`; downstream modelling reads the built panel and does not independently reconstruct modelled variables.

Key generated records are:

- `05_processed_data/Source_Provenance_Log.csv` — source workbook and indicator provenance;
- `05_processed_data/Data_Dictionary_V3.csv` — modelled fields and definitions;
- `05_processed_data/Missingness_and_Coverage.csv` — coverage by field;
- `06_locked_design/WGI_to_World_Bank_Country_Mapping_Audit.csv` — identifier crosswalk audit;
- `07_outputs/Country_Coverage_Audit.csv` — country-universe restoration results;
- `07_outputs/Restored_But_Incomplete_Log.csv` — restored economies that remain feature-limited;
- `07_outputs/Persistence_Baseline_Forensics.csv` — stock-versus-flow construct forensics.

The decision-bearing outcome is annual inward FDI net flow, not inward FDI stock. Signed inverse-hyperbolic-sine transformation retains zero and negative flow years. The raw flow/GDP percentage is preserved as a leverage stress test and is excluded from final signal classification.

The independent ISO3 crosswalk restored 31 oil-rent-intensive economies at the reference threshold, including Nigeria. Thirty enter the full M3 complete-case sample; Turkmenistan is explicitly recorded as coverage-limited because lagged inflation is unavailable.

## Frozen design and matched-sample discipline

The following files define the validation geometry before model interpretation:

- `03_config/analysis_config.json` — targets, model ladder, cutoffs, thresholds, seeds, and decision rules;
- `06_locked_design/Country_Fold_Assignments.csv` — fixed country-grouped folds;
- `06_locked_design/Country_Fold_Counts.csv` — fold composition;
- `06_locked_design/Feature_Set_Manifest.csv` — M1–M3 feature definitions;
- `06_locked_design/Matched_Sample_Registry.csv` — all adjacent-rung comparisons;
- `06_locked_design/Matched_Sample__*.csv` — exact country-year rows used by each comparison.

Each adjacent-rung comparison fits and evaluates both models on the same stored country-year rows. The pipeline fails if row identifiers, row order, or required variables differ. This prevents sample-composition changes from being misread as incremental signal value.

## Validation geometry and computational probes

The audit uses:

- five fixed country-grouped folds;
- one pooled out-of-fold unit across the five country folds;
- five future-period cutoffs;
- three algorithms: Ridge, Elastic Net, and Random Forest;
- two decision-bearing outcomes;
- five country universes per outcome;
- two adjacent-rung signal comparisons.

Each setup therefore contains **18 signal-increment units**: three algorithms multiplied by one pooled country-holdout unit plus five future-period units. Benchmark-competitiveness units are generated and reported separately; they do not enter the signal-verdict aggregation.

The algorithms are controlled specification probes rather than claims of optimally tuned forecasting models. Exact settings are stored in `04_pipeline/05_run_corrected_audit.py` and the environment lock.

## Benchmark and incremental comparisons

The model-level audit compares the added model with the strongest of three naïve forecasts on the same test observations:

1. zero flow;
2. training-sample mean;
3. lagged annual flow.

The signal-level audit uses paired adjacent-rung differences:

- oil rents: M2 minus M1;
- Regulatory Quality: M3 minus M2.

Model-versus-benchmark outputs and signal increments remain separate throughout the pipeline:

- `07_outputs/Corrected_Model_vs_Best_Benchmark.csv`;
- `07_outputs/Corrected_Benchmark_Competitiveness_Summary.csv`;
- `07_outputs/Corrected_Incremental_Delta.csv`;
- `07_outputs/Corrected_Incremental_Summary.csv`.

## Paired country-cluster bootstrap

The uncertainty layer resamples whole countries from frozen out-of-fold or future-period country contributions. The same country multiplicity vector is applied to the base and added models within each replicate. Separately bootstrapped marginal distributions are never differenced.

- Main replicates: **2,000 per unit**
- Bootstrap units: **792** across signal-increment and benchmark comparisons
- Exact-N draw diagnostic: **792/792 PASS**
- Stored country contributions: `07_outputs/Bootstrap_Country_Contributions.csv`
- Unit summaries: `07_outputs/Bootstrap_Unit_Summary.csv`
- Draw diagnostics: `07_outputs/Bootstrap_Draw_Diagnostics.csv`
- Threshold curve: `07_outputs/Bootstrap_Threshold_Probability_Curve.csv`
- Point-estimate alignment: `07_outputs/Bootstrap_Point_Estimate_Alignment.csv`

The intervals quantify uncertainty in the composition of the evaluated country population conditional on fitted models and frozen predictions. They exclude model-refitting variability and are therefore a lower bound on total training-and-sampling uncertainty.

## Null and calibration diagnostics

Two diagnostics test whether the procedure can return no evidence:

1. **Within-year null-signal permutations:** 20 permutations × 500 paired bootstrap replicates for each signal. Oil rents passes with caution because its positive-increment probability is outside the strict ±0.10 band but inside the predeclared ±0.15 caution band; Regulatory Quality passes the strict reference band. Both null medians are near zero and both intervals cross zero.
2. **Paired label-swap calibration:** 10,000 replicates. The positive-increment probabilities are 0.4954 for oil rents and 0.5040 for Regulatory Quality, confirming symmetry around 0.5.

Generated records:

- `07_outputs/Null_Signal_Sanity_Per_Permutation.csv`;
- `07_outputs/Null_Signal_Sanity_Summary.csv`;
- `07_outputs/Paired_Label_Swap_Calibration.csv`.

## Verdict construction

Classification proceeds through three tiers and no tier may be bypassed:

1. **Bootstrap unit:** coverage-limited; supported and practically material; directionally positive but marginal; unsupported; or setup-dependent.
2. **Setup:** aggregates 18 signal-increment units using the predeclared 60% positive/material and 80% unsupported rules, including the requirement that no unsupported unit be present before a positive setup verdict can be issued.
3. **Signal:** reads all ten decision-bearing setups per signal across two outcomes and five country universes.

Complete generated rules and outputs are available in:

- `00_protocol/BOOTSTRAP_METHOD_AND_GUARDRAILS.md`;
- `07_outputs/Bootstrap_Protocol_Parameters.csv`;
- `07_outputs/Bootstrap_Five_Way_Setup_Verdicts.csv`;
- `07_outputs/Central_Verdict_Sensitivity_Table.csv`;
- `07_outputs/Final_Signal_Role_and_Admissibility.csv`;
- `07_outputs/Signal_Cross_Setup_Pattern.csv`.

The final pattern is setup-dependent for both signals. Oil rents has two qualified material setups, three marginal setups, and five setup-dependent setups. Regulatory Quality has ten setup-dependent setups. No single favourable cell controls the conclusion.

## Integrity controls

The release enforces the following controls:

- offline execution from archived official workbooks;
- raw-source validation before panel construction;
- derive-once panel construction;
- fixed one-year temporal alignment;
- fixed country folds and future cutoffs;
- saved matched samples for every incremental comparison;
- no hardcoded manuscript results;
- annotations generated from configuration tolerances;
- exact package-version lock;
- single-thread deterministic execution;
- two independent derivations within the root command;
- SHA-256 release checksums and a whole-package release manifest;
- exclusion of `__pycache__` and `.pyc` files from the archival package.

## Scope and interpretation boundaries

The empirical outcome is aggregate national inward FDI. It does not identify petroleum-sector, mining-sector, tar-sand, or project-level investment. The analysis is predictive and diagnostic, not causal. Signal-admissibility verdicts indicate whether a candidate variable warrants direct, conditional, or excluded use in downstream decision-support models; they do not establish that oil rents or Regulatory Quality cause investment changes.

## Manuscript repository pointer

Recommended Methods sentence:

> Detailed data provenance, fixed country-fold assignments, matched-sample registries, computational settings, bootstrap diagnostics, verdict-sensitivity outputs and complete regeneration records are available in the versioned reproducibility repository [DOI].

Recommended data and code availability statement:

> The archived source workbooks, analytical code, fixed validation geometry, matched-sample registries, generated outputs and reproducibility records supporting this study are available in the versioned repository [DOI]. The release regenerates through a single root command under the documented computational environment.

Replace `[DOI]` only after the permanent archive has been created. Do not cite the mutable GitHub branch as the sole archival record.

## Archive verification

For an archival download, verify `GITHUB_RELEASE_MANIFEST.csv`. Every listed path must be present with the recorded byte size and SHA-256 digest. `GITHUB_RELEASE_MANIFEST.csv` necessarily excludes itself because including its own digest would be self-referential.
