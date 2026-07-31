# Release V0.4.3 — manuscript-aligned reporting and scale-transparency release

V0.4.3 is an additive release over V0.4.2. It does **not** change the raw inputs, corrected panel, folds, matched samples, model specifications, benchmark definitions, bootstrap seeds, replicate counts, unit verdicts, setup verdicts, or final signal classifications.

## Why this release exists

The DSS manuscript introduced three reporting requirements that were not yet generated inside V0.4.2:

1. the corresponding base model's margin over the strongest naïve benchmark on the same 360 decision-bearing units;
2. manuscript-facing source tables and figure-source data generated directly from the locked outputs;
3. transparent declaration and verification of the WGI Regulatory Quality scale choice.

## Additions

### Deterministic manuscript-reporting outputs

`04_pipeline/09_generate_manuscript_reporting.py` generates:

- `07_outputs/Base_Model_vs_Best_Benchmark_Unit_Level.csv`;
- `07_outputs/Base_Model_Benchmark_Margin_Headline.csv`;
- `07_outputs/Figure2b_Threshold_Sensitivity_Source.csv`;
- `07_outputs/Manuscript_Table1_Data_and_Design.csv`;
- `07_outputs/Manuscript_Table3_Setup_Evidence_Long.csv`;
- `07_outputs/Manuscript_Table3_Setup_Evidence_Compact.csv`;
- `07_outputs/Manuscript_Table4_Final_Synthesis.csv`.

The unit-level identity is exact:

`base margin = added-model margin over strongest benchmark − matched signal increment`.

Decision-bearing headline values:

- oil rents: base model benchmark-positive in 180/180 units; median base margin 0.1759115; median signal increment 0.0050631;
- Regulatory Quality: base model benchmark-positive in 177/180 units; median base margin 0.1790498; median signal increment 0.0007481.

### Publication assets

`10_reporting_assets/` adds deterministic, non-generative source scripts and publication files for Figures 1 and 2. Figure 1 now declares the WGI 2025 Revision estimate scale and labels Stage 2 as **Construct provenance & coverage audit**.

### Post hoc Regulatory Quality two-scale check

`11_posthoc_checks/rq_two_scale/` archives the isolated comparison between the WGI governance estimate and the alternative 0–100 score from the same frozen workbook. Under shared bootstrap draws:

- 0/180 unit verdicts changed;
- 0/10 setup verdicts changed;
- maximum absolute point-ΔR² difference was approximately 1.1 × 10⁻¹⁰;
- both scales produced ten setup-dependent setups.

The check is post hoc and does not enlarge or replace the primary classification.

## Validation

- The V0.4.3 deterministic comparison passes at **209/209 files**: the inherited V0.4.2 layer remains byte-identical at 202/202, the new unit-level base-model benchmark-margin output reproduces at 1/1, and the six manuscript-reporting generator outputs reproduce at 6/6. All are now verified within a single comparison.
- The original V0.4.2 full clean-run record remains in `08_validation/` and documents two deterministic derivations from the archived raw workbooks.

See:

- `08_validation/V0_4_3_Frozen_Layer_Comparison_Result.txt`;
- `08_validation/V0_4_3_Reporting_Output_Reproducibility_Result.txt`;
- `00_protocol/TECHNICAL_AUDIT_TRAIL_V0_4_3.md`.

## DOI status

No DOI is embedded in this package. Add the final archive DOI to `README.md`, `CITATION.cff`, and the manuscript data-availability statement only after the V0.4.3 archive record is created.
