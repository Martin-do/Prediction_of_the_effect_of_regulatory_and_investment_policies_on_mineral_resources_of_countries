# Paired Country-Cluster Bootstrap Method and Guardrails

The bootstrap is clustered at country level and paired at replicate level. Country-years are never sampled independently. For each validation unit, out-of-fold or future-period predictions are first frozen and reduced to per-country sufficient statistics: row count, sum(y), sum(y^2), SSE and SAE.

For a sample containing N countries, each bootstrap replicate draws exactly N country labels with replacement using a multinomial count vector. Duplicate selections remain as multiplicities. The identical count vector is applied to the baseline and added-signal country contributions. Delta R2 and Delta MAE are calculated inside the replicate. Separately bootstrapped model distributions are never subtracted.

The package records draw-count hashes, minimum and maximum draw totals, distinct-country counts, and duplicate-draw counts. All 792 bootstrap units passed the exact-N test.

Point-estimate alignment is reported rather than assumed. Large median-to-point divergences are flagged for review and are not hidden.

The null-signal check permutes each candidate signal within year, separately in training and test data, then refits Ridge models under fixed country folds. The null distribution is expected to be centered near zero; P(Delta R2 > 0) is used as a diagnostic rather than a significance guarantee. Oil rents returned 0.371 and Regulatory Quality 0.467. Both null confidence intervals cross zero and medians are approximately zero; the oil-rent probability is reported with caution rather than rounded to 0.5.

## Estimand and uncertainty boundary

The bootstrap estimand is the paired change in performance under country-cluster resampling of fixed out-of-fold or future-period predictions. The model fits and country-level prediction contributions are frozen before resampling. The resulting intervals quantify uncertainty in the composition of the evaluated country population, conditional on those fitted predictions. They do not incorporate model-refitting variability and should be interpreted as potentially narrower than total training-and-sampling uncertainty intervals.

## Material-cell guardrail

The two ge1pct setups that meet the materiality rule are supportive, not standalone confirmatory findings. They arise from correlated prespecified validation environments, have lower uncertainty bounds close to zero, and are evaluated with the conditional fixed-prediction bootstrap described above. Cross-setup conclusions do not count the setups as independent replications and do not depend on the material bin being populated.

