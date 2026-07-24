# Forensic archive only

This folder preserves the superseded developmental pipeline exactly for audit purposes. It is **not** used to generate the corrected manuscript results.

Known issues include:

- inward FDI stock relabelled as FDI flow;
- country coverage restricted through an inappropriate mapping source;
- stock/GDP clipped at 200%;
- per-model complete-case filtering that made adjacent rungs non-comparable;
- silently dropped intended features;
- environment-dependent fold and stochastic-output variation.

All corrected results are generated exclusively from `01_raw_data/`, `03_config/`, and `04_pipeline/`.
