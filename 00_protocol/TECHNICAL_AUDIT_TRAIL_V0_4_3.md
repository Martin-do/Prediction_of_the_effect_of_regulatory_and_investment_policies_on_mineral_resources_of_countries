# Technical audit trail — V0.4.3

## Release character

V0.4.3 is additive. It adds manuscript-facing reporting outputs, figure assets and a post hoc WGI scale check without changing the locked empirical analysis.

## Frozen-layer comparison

The source V0.4.2 archive was compared file by file against V0.4.3 for every generated file in:

- `05_processed_data/`;
- `06_locked_design/`;
- the V0.4.2 files in `07_outputs/`.

Inherited-layer result: **202/202 byte-identical**, with no missing or altered V0.4.2 file. Adding the reproducible unit-level base-margin output gives a V0.4.3 analytical total of **203/203**. The detailed current comparison is `08_validation/Reproducibility_Rerun_Comparison.csv`; the inherited-layer comparison remains `08_validation/V0_4_3_Frozen_Layer_Comparison.csv`.

## Base-model benchmark-margin derivation

For each bootstrap-defined unit, V0.4.3 joins two existing point-estimate records on the complete unit key:

- added model minus strongest benchmark;
- added model minus corresponding base model.

It then derives:

`base model minus strongest benchmark = (added model minus strongest benchmark) − (added model minus base model)`.

The identity residual is zero for every unit. Decision-bearing summaries reproduce the manuscript values:

| Signal | Units | Base benchmark-positive | Median base margin | Median signal increment |
|---|---:|---:|---:|---:|
| Oil rents | 180 | 180 | 0.1759115037 | 0.0050631427 |
| Regulatory Quality | 180 | 177 | 0.1793236413 | 0.0006654433 |

These medians are separate distribution summaries and are not presented as a median-level additive decomposition.

## Reporting-output reproducibility

`04_pipeline/09_generate_manuscript_reporting.py` was run twice against the unchanged locked outputs. The new unit-level base-margin file is counted in the 203-file analytical comparison; the remaining **6/6 reporting-only files** were byte-identical. See `08_validation/V0_4_3_Reporting_Output_Reproducibility.csv`.

## Post hoc scale check

The two-scale check was conducted in an isolated working copy. It adds the WGI Regulatory Quality 0–100 score from the same archived workbook, preserves matched rows and design settings, and applies shared country-bootstrap draws. The primary estimate-scale files are not overwritten.

Headline result:

- fixed affine relation to numerical precision;
- no shared-draw unit or setup verdict changes;
- identical overall setup-dependent classification.

The complete package and execution source are in `11_posthoc_checks/rq_two_scale/`.

## Figure provenance

Figure 1 is rebuilt deterministically from author-specified text and vector primitives. No generative image tool is used. Figure 2 is archived with its generated source table and deterministic plotting script. Publication captions remain outside the artwork.

## Environment note

The original V0.4.2 clean-run validation records document full regeneration from the raw workbooks at 202/202 byte-identical outputs. V0.4.3 preserves those records, adds one independently reproduced analytical output to reach 203/203, and validates the six remaining reporting-only outputs separately.
