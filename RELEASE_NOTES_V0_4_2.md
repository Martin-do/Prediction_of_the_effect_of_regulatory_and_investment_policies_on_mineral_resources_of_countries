# Release V0.4.2 — additive persistence-baseline forensics

V0.4.2 is an additive release over V0.4.1. It makes no change to the panel, folds, matched samples, model specifications, benchmarks, bootstrap seeds, replicate counts, verdicts, or any scientific numerical result carried forward from V0.4.1.

## Why this release exists

The construct-correction claim — that the legacy target's apparent persistence was an artefact of stock being mislabelled as flow — was carried in the lock record as a pair of numbers (R² ≈ 0.98 falling to ≈ 0.04) with no generated table behind either value. This breached the release's own guardrail that every reported value must trace to a generated output. V0.4.2 closes that gap by generating the quantity rather than asserting it.

On generation, the pair did not hold as stated. The two values are different estimands:

- `0.98` reproduces as **0.9871** — the pooled lag-1 persistence R² of the legacy stock series on the signed-asinh scale, computed in sample across consecutive country-years.
- `0.04` reproduces as **0.0384** — but this is not the corrected series' persistence R² on the same basis. It is the `Lagged_Flow` benchmark's median country-holdout R² on the primary target, taken from the matched modelling sample (complete-case on all M1 features) and already present in `07_outputs/Corrected_Benchmark_Performance.csv`.

Computed on the same basis as the legacy figure, the corrected flow's pooled persistence R² is **0.1989**, not 0.04. The former pairing moved estimand mid-comparison.

## What is added

- `04_pipeline/08_persistence_baseline_forensics.py` — generates the persistence matrix across both series, two scales, two samples, and two estimands. The baseline is fit-free (ŷ[t] = y[t−1]); no model is trained and no seed is consumed.
- `07_outputs/Persistence_Baseline_Forensics.csv` — the full 16-cell matrix.
- `07_outputs/Persistence_Headline_Comparison.csv` — the like-for-like contrasts, in which scale, sample and estimand are held identical so that only the series varies.

## Locked headline contrast (supersedes 0.98 → 0.04)

| Sample | Estimand | Legacy stock R² | Corrected flow R² | Drop |
|---|---|---|---|---|
| All available | Pooled | 0.9871 | 0.1989 | 0.7882 |
| All available | Country-fold median | 0.9856 | 0.1885 | 0.7971 |
| **Common support** | **Pooled** | **0.9869** | **−0.1591** | **1.1460** |
| Common support | Country-fold median | 0.9856 | −0.1073 | 1.0929 |

The common-support rows are the defensible headline. On the identical 2,321 country-years and 92 economies where the legacy series exists, under the same transform and the same estimand, persistence on the legacy stock target scores 0.99 while persistence on the corrected flow target scores −0.16 — worse than predicting the sample mean. Nothing varies between the two figures except the series.

The all-available rows are the conservative alternative, retained because they use each series at its full observed coverage. The legacy series covers 92 economies against the corrected panel's 202, which is itself a coverage finding rather than a nuisance.

`0.0384` is retired as a headline and retained in Results as what it is: the lagged-flow benchmark's country-holdout median R² on the primary target.

## Changes to existing files

Two orchestration scripts only; no analysis logic altered.

- `run_pipeline.py` — registers the new step in the root command.
- `04_pipeline/07_verify_deterministic_rerun.py` — registers the new step in the second derivation. Without this, the new outputs would remain on disk untouched during verification and would have been counted as byte-identical without ever being re-derived — a false pass on two files.

## Verification status

**Verified — full clean regeneration completed.**

- **Two-derivation check: PASS at 202/202 files.** An independent re-derivation from the included raw workbooks reproduced every compared output in `05_processed_data`, `06_locked_design` and `07_outputs` byte for byte (`08_validation/Reproducibility_Rerun_Result.txt`; `Reproducibility_Rerun_Comparison.csv`, 202 rows, all byte-identical). Both new persistence outputs were genuinely re-derived during the second derivation, not carried over.
- **The frozen layer survived re-derivation intact.** Compared against the pristine V0.4.1 package after the full rebuild: 200 of 200 original outputs byte-identical, 0 differing, 2 added. The V0.4.2 additions perturb nothing.
- **Canonical pinned-environment regeneration.** A clean root-command run under Python 3.13.5 and the exact package lock passed at 202/202; `Environment_Metadata.json` now agrees with `python-version.txt`.
- **Independent cross-version reproduction.** A separate regeneration under Python 3.12.3 and the same pinned data stack also reproduced the frozen analytical layer, providing additional evidence that determinism is not brittle to the interpreter minor version.
- **The new step is separately deterministic.** Two derivations produce byte-identical outputs; identical checksums are also obtained under a materially newer data stack (pandas 3.0.2, numpy 2.4.4), indicating the result does not depend on the aggregation backend.
- **Regenerated validation artefacts:** `Reproducibility_Rerun_Result.txt`, `Reproducibility_Rerun_Comparison.csv`, `Deterministic_Manifest_A.csv`, `Reproducibility_Report.md` (now labelled V0.4.2 and reporting 202/202), `Release_Checksums.csv` (260 rows, including the technical audit trail and the new step and outputs), and `GITHUB_RELEASE_MANIFEST.csv` (311 rows).

**DOI-ready technical audit trail added.** `00_protocol/TECHNICAL_AUDIT_TRAIL_V0_4_2.md` consolidates the cross-machine reproduction, construct and coverage audit, matched-sample discipline, bootstrap implementation, null and calibration diagnostics, verdict construction, integrity controls, manuscript repository pointer, and archive-verification procedure. This is documentation-only and changes no analytical output.

**Release-label derivation closed.** `04_pipeline/07_build_reproducibility_report.py` now reads the release label from `03_config/analysis_config.json` rather than carrying a hardcoded version string. This prevents subsequent releases from inheriting a stale report label.

## Interpretive status

The construct correction is strengthened, not weakened. The corrected demonstration is that a mislabelled stock target made a fit-free persistence rule appear near-perfect on observations where the correct flow target makes the same rule worse than useless. This is a sharper statement of the original point than the number it replaces, and it is now generated rather than remembered.
