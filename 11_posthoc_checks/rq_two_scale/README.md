# Post hoc Regulatory Quality two-scale sensitivity

## Status

This check is **post hoc** and does not replace or enlarge the primary ten-setup Regulatory Quality classification. The WGI governance estimate remains the locked decision-bearing specification.

## Question

Does the Regulatory Quality conclusion depend on using the governance estimate rather than the alternative 0–100 governance score contained in the same frozen WGI 2025 Revision workbook?

## Result

The two scales are related by a fixed affine transformation in the archived workbook, to numerical precision:

`score = 15.771420637032 × estimate + 54.862791873371`

Across 180 matched decision-bearing units under shared country-bootstrap draws:

- maximum absolute point-ΔR² difference: approximately `1.1e-10`;
- unit-verdict changes: `0/180`;
- setup-verdict changes: `0/10`;
- both representations produce `10/10` setup-dependent setups.

The scale choice is therefore declared as a measurement decision, but it is representational rather than substantively different for this pipeline.

## Reproduce

From the repository root:

```bash
python 11_posthoc_checks/rq_two_scale/run_check.py
```

The script creates an isolated temporary copy, extracts the 0–100 score from the included WGI workbook, fits only the additional score-scale M3 models, applies the same matched rows and shared country-bootstrap draws, and regenerates the headline and comparison CSV files in this directory.

## Independent-draw diagnostic

The archived exploratory outputs with independently generated bootstrap draws show two unit-level verdict changes, whereas shared draws show none. This contrast is a Monte Carlo pairing diagnostic, not evidence of scale sensitivity, and it is not used in the manuscript classification.

## Interpretation boundary

This check addresses representation within the published WGI release. It does not independently establish the construct validity, dimensional distinctiveness or mineral-sector suitability of Regulatory Quality.
