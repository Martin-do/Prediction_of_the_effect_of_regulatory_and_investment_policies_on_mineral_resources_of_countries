# Release V0.4.1 — locked empirical results layer

V0.4.1 is the locked results release for manuscript drafting.

## Core corrections

- verified annual inward FDI net flows replace the mislabelled stock outcome;
- negative flows are retained;
- official World Bank and WGI sources rebuild the predictor panel;
- Nigeria and previously excluded oil-rent-intensive economies are restored;
- lagged predictors, matched samples and fixed country folds are used;
- future-cutoff and oil-rent-threshold sensitivity are included;
- the normalized outcome uses a signed asinh transformation rather than clipping;
- uncertainty uses a genuinely paired country-cluster bootstrap over frozen prediction contributions;
- a permuted-signal null test is included;
- five-way setup verdicts replace binary admissibility language.

## Locked settings

- bootstrap seed: `20260714`;
- bootstrap replicates: `2000` per algorithm-validation unit;
- null-test seed: `20260715`;
- null test: `20` permutations × `500` replicates;
- deterministic rerun: `200/200` files byte-identical.

## Scientific interpretation

Oil rents and Regulatory Quality are both classified overall as setup-dependent. Oil rents display the more favourable cross-setup pattern, but neither signal is universally admissible. The contribution concerns validation-dependent signal admissibility before AI–MCDM weighting, not strong prediction or causal inference.
