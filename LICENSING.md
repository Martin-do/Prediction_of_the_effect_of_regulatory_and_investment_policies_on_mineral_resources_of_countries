# Licensing

This repository uses a mixed-licensing structure so that the reusable research software, author-created documentation and outputs, and third-party source data are not conflated.

## Research software — MIT

The author-created Python code, configuration files, orchestration scripts, and software documentation are licensed under the **MIT License**. The full text is in [`LICENSE`](LICENSE).

This applies primarily to:

- `run_pipeline.py`;
- `03_config/`;
- `04_pipeline/`;
- author-created software documentation that explains how to execute or adapt the pipeline.

## Author-created documentation and generated outputs — CC BY 4.0

Except where third-party rights apply, the author-created protocol documents, technical audit trail, data dictionaries, generated result tables, validation reports, and other original non-software materials are licensed under the **Creative Commons Attribution 4.0 International License (CC BY 4.0)**:

https://creativecommons.org/licenses/by/4.0/

Suggested attribution:

> Ige, Oladeji Oluremi (2026). *Before the Weights: Reproducibility Package for a Validation-First Signal-Admissibility Audit*, version 0.4.3.

## Third-party data and archived materials — original terms

The licences above do **not** relicense third-party materials. In particular:

- files in `01_raw_data/world_bank/` remain subject to the applicable World Bank dataset terms and indicator-specific source acknowledgements;
- the Worldwide Governance Indicators workbook remains subject to the World Bank terms and WGI citation guidance;
- files in `02_forensic_archive/` and `legacy_archive/` retain any rights and restrictions attached to their original sources.

Required source acknowledgements and links are recorded in [`THIRD_PARTY_DATA_NOTICE.md`](THIRD_PARTY_DATA_NOTICE.md) and `01_raw_data/README_SOURCES.md`. Downstream users must preserve those acknowledgements and verify any source-specific restrictions before redistribution or reuse.

## Zenodo and citation metadata

The primary object deposited as this release is research software, so `CITATION.cff` records `license: MIT`. The mixed licensing of the complete archive is governed by this file. A reserved archive DOI must be inserted into `README.md` and `CITATION.cff` before the Zenodo record is published.
