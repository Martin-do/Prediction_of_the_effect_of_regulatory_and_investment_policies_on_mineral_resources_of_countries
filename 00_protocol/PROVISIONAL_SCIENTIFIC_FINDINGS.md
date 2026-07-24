# Provisional scientific findings — V0.3 merged controlled release

These findings are generated from the locked V0.3 configuration and should be interpreted as predictive, non-causal evidence.

## 1. The merged panel restores coverage without reintroducing legacy target contamination

The corrected panel contains 7,595 country-years across 217 economies for 1990-2024. It includes 6,635 verified annual inward FDI-flow observations, preserves 504 negative-flow observations, and contains 35 Nigerian observations. All 31 economies that were excluded from the legacy target at the reference oil-rent threshold now have corrected annual-flow outcomes. Thirty have at least one complete M3 country-year; Turkmenistan remains outcome-restored but M3-ineligible because the core inflation series is wholly absent.

No legacy stock-era FDI variables are present in the authoritative corrected panel.

## 2. The official flow/GDP series passes an independent consistency audit

The official World Bank annual inward FDI net-inflows-to-GDP series is the authoritative normalized outcome. An audit-only ratio independently derived from the included annual flow and GDP sources matches the official series to floating-point precision across 6,538 comparable country-years. The derived ratio is not used as a modelling target.

## 3. Extreme raw flow/GDP values justify the transformed normalized target

The official untransformed flow/GDP target contains 194 country-years with absolute values of at least 25% of GDP, 92 at least 50%, and 61 at least 100%. The observed range reaches approximately -1,303% to +1,710% of GDP. These values are retained rather than deleted, but they create severe leverage when whole countries are held out.

Across the raw-ratio stress tests, the worst split-level R2 is approximately -39.91 and the largest within-setup R2 range exceeds 40.3. After applying the signed inverse-hyperbolic-sine transformation to the same official ratio, the worst split-level R2 is approximately 0.078 and the largest range is below 0.37. The transformed ratio therefore remains the decision-bearing normalized robustness target; the untransformed ratio remains an explicit stress test and does not determine signal admissibility.

## 4. Oil-rent evidence is strong but not universal

Oil rents are evidence-supported in nine of the ten prespecified decision-bearing setups. Support holds for both target definitions in the full universe and at the 1%, 5%, and 10% oil-rent thresholds. The only conditional result is the primary annual-flow target at the narrowest 15% threshold, where future-period support is less stable.

The signal is therefore not labelled universally admissible. Its final provisional classification remains **conditionally admissible**, because one prespecified threshold/validation environment changes the verdict.

## 5. Regulatory Quality is more setup-dependent

Regulatory Quality is evidence-supported in four of ten decision-bearing setups: the full universe for both targets, and the 5% and 10% oil-rent universes for the primary annual-flow target. Five setups are conditional. At the 15% threshold for the primary target, the broader model remains benchmark-competitive but the incremental Regulatory Quality contribution is unsupported.

The evidence therefore does not justify treating Regulatory Quality as a universally admissible predictive criterion. Its provisional status is **conditionally admissible**, with stronger dependence on target, subgroup threshold, and validation geometry than oil rents.

## 6. Final provisional classifications

- **Oil rents:** conditionally admissible; nine of ten decision-bearing setups are evidence-supported and one is conditional.
- **Regulatory Quality:** conditionally admissible; four setups are evidence-supported, five are conditional, and one has a competitive broader model without a supported Regulatory Quality increment.

The classifications are not converted directly into AI-MCDM weights. They determine whether a signal may be considered for direct empirical use, conditional use, or non-predictive contextual treatment.

## 7. Standalone scope

The outcome is aggregate national inward FDI. These results concern the national investment context of resource-rich economies. They do not estimate petroleum-sector, mining-sector, or Nigerian tar-sand investment directly.

## 8. Main manuscript contribution

The central finding is not that one indicator is simply useful or useless. The same indicator receives different admissibility verdicts under prespecified changes in target definition, oil-rent threshold, future-period cutoff, and country-generalisation geometry. This demonstrates why candidate empirical signals should not be admitted into AI-MCDM weighting on the basis of one target, one sample, or one validation split.
