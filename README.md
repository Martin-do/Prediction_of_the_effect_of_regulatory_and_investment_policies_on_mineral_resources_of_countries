# Before the Weights: Validation-First Signal-Admissibility Audit

This repository contains the locked **V0.4.3 reproducibility release** for a standalone study of empirical signal admissibility before AI–MCDM criteria weighting.

## Central idea

A model can beat a naïve benchmark while an individual candidate signal adds only a small, uncertain or setup-dependent increment. The repository therefore separates:

1. overall model predictiveness;
2. paired incremental signal value on matched observations;
3. stability and materiality across targets, country universes, thresholds, future cutoffs and uncertainty analysis.

The empirical application uses aggregate national inward FDI as an investment-context outcome in resource-rich economies. It does **not** measure petroleum-sector, mining-sector or project-level investment.

## Locked release

- Version: **V0.4.3**
- Panel: 217 economies, 1990–2024
- Primary target: annual inward FDI net flow, signed asinh transformed
- Normalized target: official FDI net inflows as % of GDP, signed asinh transformed
- Main bootstrap seed: **20260714**
- Main bootstrap: **2,000 paired country-cluster replicates per unit**
- Null-test seed: **20260715**
- Null test: **20 permutations × 500 replicates**
- V0.4.3 deterministic comparison: **209/209 files byte-identical** (202 inherited V0.4.2 files, one unit-level base-margin output, and six manuscript-reporting generator outputs)


## V0.4.3 additions

V0.4.3 adds only manuscript-aligned reporting and transparency layers:

- exact unit-level and headline base-model margins over the strongest naïve benchmark;
- deterministic manuscript source tables and Figure 2 threshold data;
- title-free publication assets and deterministic source scripts for Figures 1 and 2;
- an isolated post hoc check comparing the WGI Regulatory Quality estimate with the alternative 0–100 score.

The post hoc scale check found no unit or setup verdict changes under shared bootstrap draws. It does not alter the primary ten-setup classification. See `RELEASE_NOTES_V0_4_3.md`.

## Reproduce the release

Use the exact environment in `09_environment/requirements-lock.txt`, then run:

```bash
python run_pipeline.py
```

The command validates the raw workbooks, rebuilds the panel, recreates fixed folds and matched samples, runs the corrected analyses and uncertainty layer, generates all reporting annotations, and performs an independent deterministic rerun.

## Start here

- `RELEASE_NOTES_V0_4_3.md`
- `00_protocol/ANALYSIS_PLAN_LOCKED.md`
- `00_protocol/BOOTSTRAP_METHOD_AND_GUARDRAILS.md`
- `00_protocol/SCOPE_AND_CLAIMS_GUARDRAIL.md`
- `00_protocol/UNCERTAINTY_QUANTIFIED_FINDINGS.md`
- `08_validation/Reproducibility_Report.md`
- `00_protocol/TECHNICAL_AUDIT_TRAIL_V0_4_3.md`
- `DOCUMENTATION_CLARIFICATIONS_V0_4_3.md`
- `LICENSING.md` and `THIRD_PARTY_DATA_NOTICE.md`
- `07_outputs/Central_Verdict_Sensitivity_Table.csv`
- `07_outputs/Signal_Cross_Setup_Pattern.csv`
- `07_outputs/Null_Signal_Sanity_Summary.csv`
- `07_outputs/Material_Setup_Caveats.csv`
- `07_outputs/Base_Model_Benchmark_Margin_Headline.csv`
- `10_reporting_assets/MANUSCRIPT_ALIGNMENT_V0_4_3.md`
- `11_posthoc_checks/rq_two_scale/README.md`

## Repository layout

- `00_protocol/` — locked design, scope and interpretation rules
- `01_raw_data/` — included official source workbooks and provenance notes
- `02_forensic_archive/` — original pipeline artefacts retained only for forensic documentation
- `03_config/` — locked analysis settings
- `04_pipeline/` — panel, model, bootstrap and reporting code
- `05_processed_data/` — corrected analytical panel and audits
- `06_locked_design/` — fixed folds, matched samples and feature manifests
- `07_outputs/` — manuscript-facing and diagnostic result tables
- `08_validation/` — checksums, run logs and reproducibility reports
- `09_environment/` — exact software lock
- `10_reporting_assets/` — manuscript figures, source scripts and alignment map
- `11_posthoc_checks/` — isolated post hoc checks outside the primary classification
- `legacy_archive/` — snapshot of the previously published GitHub working tree; not used by V0.4.3

## Current scientific interpretation

The uncertainty-quantified cross-setup analysis classifies both oil rents and Regulatory Quality as **setup-dependent**. Oil rents show a more favourable pattern, including a small number of qualified material setups; Regulatory Quality is consistently more fragile. Neither signal is universally admissible for direct empirical weighting.

## Licensing

The research software is released under the **MIT License**. Author-created documentation and generated outputs are available under **CC BY 4.0**, except where third-party rights apply. Included World Bank and WGI workbooks remain under their original source terms and are not relicensed. See `LICENSE`, `LICENSING.md`, and `THIRD_PARTY_DATA_NOTICE.md`.

The historical V0.3 analysis-plan header and V0.1 trade-source wording are retained to preserve the frozen layer; their current V0.4.3 interpretation is stated in `DOCUMENTATION_CLARIFICATIONS_V0_4_3.md`.

## Citation

Citation metadata are provided in `CITATION.cff`. The repository-level technical evidence is consolidated in `00_protocol/TECHNICAL_AUDIT_TRAIL_V0_4_3.md`. A permanent archive DOI must be added to this README, `CITATION.cff`, and the manuscript data-availability statement after the GitHub release is deposited in Zenodo or another permanent repository.
