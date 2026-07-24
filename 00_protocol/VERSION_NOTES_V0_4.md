# Version Notes — V0.4 Uncertainty-Quantified Release

V0.4 adds a genuinely paired country-cluster bootstrap to the V0.3 empirical pipeline.

## Locked mechanics
- Resampling unit: ISO3 country.
- Each replicate draws exactly N countries with replacement.
- Every selected country contributes its complete frozen block of held-out years.
- Duplicate country draws are retained as integer multiplicities and are never deduplicated.
- Baseline and added-signal predictions are evaluated on the same resampled countries in every replicate.
- Per-country sufficient statistics are frozen from out-of-fold or future-period predictions before resampling.
- Bootstrap seed: 20260714.
- Replicates: 2,000 per algorithm-validation unit.
- Null-signal seed: 20260715.
- Null check: 20 within-year signal permutations × 500 paired bootstrap replicates.

## Reporting
- 95% percentile confidence intervals.
- P(Delta R2 > t) reported continuously from -0.02 to 0.03 in 0.0005 increments.
- Five-way verdict scheme: material; marginal; setup-dependent; unsupported; coverage-limited.
- Cross-setup conclusions use the full prespecified pattern; no single favorable setup controls the classification.
- The material category is not required to be populated.
