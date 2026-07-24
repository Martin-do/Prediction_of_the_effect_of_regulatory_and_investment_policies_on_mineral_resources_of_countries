# Third-party data notice and attribution

The V0.4.3 pipeline is distributed with archived official workbooks so that the analysis can be reproduced offline. Those workbooks are third-party materials and are not relicensed under the repository's MIT or CC BY 4.0 licences.

## World Development Indicators workbooks

The included World Development Indicators series are identified individually in `01_raw_data/README_SOURCES.md`. The indicator landing pages identify the data licence and underlying data providers. The included workbooks are archived **unmodified**; the pipeline derives the analytical panel and transformations from them.

General attribution for the included WDI materials:

> The World Bank: World Development Indicators. Individual indicator names, codes, landing pages, and underlying data sources are listed in `01_raw_data/README_SOURCES.md`.

World Bank dataset terms:

https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets

Downstream users should retain the World Bank attribution, acknowledge the underlying provider where shown on an indicator page, state any modifications they make, and preserve the applicable terms when redistributing data.

## Worldwide Governance Indicators

The included governance workbook is:

> Worldwide Governance Indicators, 2025 Revision, World Bank.

Official landing page and citation guidance:

https://www.worldbank.org/en/publication/worldwide-governance-indicators

The repository uses the Regulatory Quality governance estimate from the archived workbook as the primary decision-bearing signal. The alternative 0–100 governance score is read only in the labelled post hoc scale check in `11_posthoc_checks/rq_two_scale/`. The workbook is included unmodified; subsequent panel construction, lagging, matching, modelling, and sensitivity checks are author-created analytical operations.

## Trade-series clarification

`WB_TRADE_GDP_PCT.xls` is retained as an optional archived source but is not part of the V0.4.3 decision-bearing feature ladder. The current reason is observability: trade is wholly unobserved for Nigeria and Trinidad and Tobago, and including it in the core complete-case ladder would remove Nigeria after the identifier correction restored it. The phrase “not a core feature in V0.1” in the historical source note is not the current methodological rationale.

## No endorsement

Inclusion and use of World Bank materials do not imply World Bank endorsement of this repository, its methods, findings, or interpretations.
