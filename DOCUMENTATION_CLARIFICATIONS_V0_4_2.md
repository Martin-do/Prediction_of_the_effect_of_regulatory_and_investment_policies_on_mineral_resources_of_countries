# V0.4.2 documentation clarifications

This note preserves the byte-identical V0.4.1 frozen layer while preventing two historical labels from being mistaken for current V0.4.2 rules. It changes no data, model, fold, sample, prediction, bootstrap result, or scientific verdict.

## Historical analysis-plan header

`00_protocol/ANALYSIS_PLAN_LOCKED.md` is intentionally retained as the historical **V0.3 locked base**. It is not the complete current verdict specification. The authoritative V0.4.2 uncertainty and classification layer is documented in:

- `00_protocol/BOOTSTRAP_METHOD_AND_GUARDRAILS.md`;
- `00_protocol/UNCERTAINTY_QUANTIFIED_FINDINGS.md`;
- `00_protocol/VERSION_NOTES_V0_4_2.md`;
- `00_protocol/TECHNICAL_AUDIT_TRAIL_V0_4_2.md`;
- `03_config/analysis_config.json`.

## Historical trade-source wording

`01_raw_data/README_SOURCES.md` retains the phrase “not a core feature in V0.1” as part of the earlier frozen documentation. For V0.4.2, trade openness is excluded from the decision-bearing ladder because it is wholly unobserved for Nigeria and Trinidad and Tobago; including it would remove Nigeria from every complete-case M3 sample. See `THIRD_PARTY_DATA_NOTICE.md` and the manuscript Methods.

## Licensing

The current repository licensing structure is recorded in `LICENSE`, `LICENSING.md`, and `THIRD_PARTY_DATA_NOTICE.md`. These files govern the distributed archive without modifying the frozen analytical layer.
