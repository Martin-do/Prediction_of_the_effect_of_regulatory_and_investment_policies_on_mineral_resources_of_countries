# Locked analysis plan — merged controlled release V0.3

## Standalone paper identity

The paper tests whether candidate oil-rent and governance signals retain decision-support value when outcome definition, country coverage, benchmark choice, country-universe definition, future-period cutoff, sample construction, and validation geometry are controlled explicitly.

## Central contribution

The contribution is a reproducible demonstration that a signal's apparent admissibility is not intrinsic to the variable alone. It can change across individually defensible evaluation environments. The audit procedure is the method used to distinguish stable signal evidence from setup-induced verdicts.

## Outcomes

1. Primary: `asinh(annual inward FDI net flow in US$ millions)`.
2. Normalized: `asinh(annual inward FDI net flow as % of GDP)`.
3. Stress test: raw annual inward FDI net flow as % of GDP, un-clipped.
4. Legacy inward stock: forensic archive only.

The raw percentage ratio does not determine final admissibility because a small number of extreme financial-centre and conduit-economy observations produce severe fold leverage. It remains fully reported as a stress test.

## Predictive timing

All predictors are lagged one year: predictors at year t-1 predict the outcome at year t. Lags are created only for consecutive country-years.

## Validation environments

### Country generalisation

Fixed five-fold country holdout validation uses the persisted ISO3-to-fold file.

### Future-period sensitivity

Five cutoffs are declared before interpretation:

- train through 2012, test from 2013;
- train through 2014, test from 2015;
- train through 2015, test from 2016;
- train through 2016, test from 2017;
- train through 2018, test from 2019.

A setup is future-supported only when at least 60% of these cutoffs independently satisfy both incremental-signal and benchmark-competitiveness rules.

### Oil-rent threshold sensitivity

Subgroups are defined from maximum oil rents during the fixed 1990-2015 classification window. Four thresholds are tested:

- at least 1% of GDP;
- at least 5%;
- at least 10%;
- at least 15%.

The 5% threshold is the reference subgroup, not a uniquely privileged definition.

## Signal tests

- Oil-rent increment: M1 macro baseline versus M2 macro + oil rents.
- Regulatory-quality increment: M2 versus M3 macro + oil rents + Regulatory Quality.
- Every incremental comparison uses the exact same saved country-year rows for both models.

## Model classes

1. Ridge regression;
2. Elastic Net;
3. Random Forest.

The model classes are used to test whether signal conclusions depend on linearity assumptions. Exact seeds and one-thread execution are fixed.

## Benchmarks

- zero-flow benchmark;
- training-sample mean;
- lagged annual flow.

For each split, the added model is compared with the strongest naive benchmark on the same observations.

## Setup-specific decision rule

A setup is evidence-supported only when:

1. minimum country and country-year coverage is met;
2. the country-holdout median incremental R2 is positive;
3. at least 60% of country-holdout algorithm/fold comparisons show positive incremental R2;
4. the added model beats the strongest naive benchmark under the same country-holdout rule;
5. at least 60% of the five future cutoffs independently satisfy both the incremental and benchmark rules.

A signal may be conditionally admissible when support depends on target, oil-rent threshold, or validation geometry. The raw-ratio stress test is reported but excluded from classification.
