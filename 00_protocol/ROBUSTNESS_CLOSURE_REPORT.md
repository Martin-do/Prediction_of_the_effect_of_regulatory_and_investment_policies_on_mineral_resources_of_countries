# Robustness closure report — V0.3 merged controlled release

## Issue 1: extreme flow/GDP folds

**Closed by design change and explicit stress testing.** The raw official ratio is retained unaltered but does not carry the admissibility decision. The signed `asinh(flow/GDP)` target preserves negatives and ordering while controlling leverage. Worst split-level R2 improves from approximately -39.91 on the raw ratio to 0.078 on the transformed ratio. Extreme observations and prediction ranges remain fully visible in dedicated audit tables.

## Issue 2: future-period cutoff sensitivity

**Closed by a five-cutoff grid.** The single-cutoff design is replaced by 2012/13, 2014/15, 2015/16, 2016/17, and 2018/19 splits. Final setup decisions require support across at least three of five cutoffs.

## Issue 3: 5% oil-rent threshold sensitivity

**Closed by a prespecified threshold grid.** The analysis is repeated at 1%, 5%, 10%, and 15% thresholds, all based on the fixed 1990-2015 maximum-rent window. The 5% definition is not treated as uniquely correct.

## Issue 4: aggregate FDI versus sector investment

**Addressed through scope correction, not false precision.** The paper is framed around national investment-context signals in resource-rich economies. It explicitly prohibits claims about petroleum-, mining-, or tar-sand-sector investment. Sector-specific extension remains future research unless a harmonized sector-level outcome is acquired.

## Issue 5: country restoration versus complete-case eligibility

**Closed by separate reporting and self-test.** All 31 reference-threshold economies excluded by the legacy outcome mapping are restored on the corrected annual-flow outcome. Thirty enter at least one complete M3 country-year. Turkmenistan is logged separately because inflation is wholly missing. Outcome restoration is no longer conflated with model eligibility.

## Issue 6: official versus internally derived flow/GDP ratio

**Closed by an independent consistency audit.** The official World Bank flow/GDP series remains authoritative. A ratio independently calculated from the included annual-flow and GDP sources matches it to floating-point precision across 6,538 comparable country-years and is retained only as an audit variable.

## Issue 7: legacy-variable contamination

**Closed by panel separation.** The corrected authoritative panel contains no legacy stock-era FDI variables. The mislabelled stock target and related variables remain only in the read-only forensic archive.

## Resulting signal classifications

- Oil rents: conditionally admissible; nine of ten decision-bearing setups are evidence-supported and one is conditional.
- Regulatory Quality: conditionally admissible; four setups are supported, five conditional, and one benchmark-competitive without a supported signal increment.

These are predictive and non-causal classifications. They are not direct AI-MCDM weights.
