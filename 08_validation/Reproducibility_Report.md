# Reproducibility report — release V0.4.3

## Build status

- Raw source validation: 10/10 files passed.
- Corrected panel: 7,595 country-year rows, 217 economies, 1990-2024.
- Verified annual FDI-flow observations: 6,635.
- Negative annual FDI-flow observations retained: 504.
- Nigeria annual-flow observations: 35.
- Setup-specific verdict rows: 22.
- Future-cutoff sensitivity rows: 110 across five prespecified cutoffs.
- Oil-rent-threshold sensitivity rows: 16 across 1%, 5%, 10%, and 15% pre-2016 maximum-rent thresholds.
- Signal-level preliminary classifications: 2.
- Deterministic rerun verification: PASS: two deterministic derivations from the included raw workbooks produced byte-identical processed data, locked samples/folds, and corrected outputs (209/209 files).

## Four robustness issues closed

1. **Extreme raw flow/GDP folds.** The untransformed percentage ratio is retained as a stress test, not as the decision-bearing robustness target. The signed `asinh(flow/GDP)` target is the principal normalized outcome. Its worst split-level R2 is 0.078, compared with -39.910 for the raw ratio. Extreme observations and prediction spans are exported explicitly.
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

The V0.4.3 release is suitable for scientific interpretation of setup-dependent signal admissibility, subject to the conditional-bootstrap estimand and material-setup caveat below. The raw flow/GDP ratio remains available as an intentionally harsh leverage stress test but is excluded from final admissibility classification. Final classifications are based only on the transformed annual-flow level and transformed normalized-flow targets.

## Bootstrap estimand

The paired country-cluster bootstrap resamples countries from frozen out-of-fold or future-period country contributions. Each selected country contributes its complete held-out block of years, and the same country multiplicities are applied to the baseline and added-signal models within each replicate. The intervals therefore quantify uncertainty associated with the composition of the evaluated country population, conditional on the fitted models and frozen predictions. They do not include model-refitting variability and may be narrower than total training-and-sampling uncertainty intervals.

## Material-cell qualification

One oil-rent setup in the pre-2016 >=1% universe meets the prespecified materiality rule: the normalized outcome specification. It is treated as supportive rather than standalone confirmatory evidence because its lower uncertainty bound is close to zero and its interval is conditional on fixed predictions. The corresponding primary-outcome >=1% setup is directionally positive but marginal. The material category is not required to be populated for the paper's conclusion.

## Scope limitation

Aggregate inward FDI captures the national investment environment. It does not identify petroleum, mining, tar-sand, or extractive-project investment. Findings must therefore be framed as evidence about candidate signals for decision support in resource-rich economies, not as direct prediction of resource-sector capital flows.
