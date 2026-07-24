# Included raw sources

The corrected pipeline is offline. It reads the included, unmodified official workbooks and does not call an API during execution.

| File | Indicator / source | Official landing page |
|---|---|---|
| `WB_FDI_NET_INFLOWS_CURRENT_USD.xls` | `BX.KLT.DINV.CD.WD` — Foreign direct investment, net inflows (BoP, current US$) | https://data.worldbank.org/indicator/BX.KLT.DINV.CD.WD |
| `WB_FDI_NET_INFLOWS_GDP_PCT.xls` | `BX.KLT.DINV.WD.GD.ZS` — Foreign direct investment, net inflows (% of GDP) | https://data.worldbank.org/indicator/BX.KLT.DINV.WD.GD.ZS |
| `WB_OIL_RENTS_GDP_PCT.xls` | `NY.GDP.PETR.RT.ZS` — Oil rents (% of GDP) | https://data.worldbank.org/indicator/NY.GDP.PETR.RT.ZS |
| `WB_GDP_CURRENT_USD.xls` | `NY.GDP.MKTP.CD` — GDP (current US$) | https://data.worldbank.org/indicator/NY.GDP.MKTP.CD |
| `WB_POPULATION_TOTAL.xls` | `SP.POP.TOTL` — Population, total | https://data.worldbank.org/indicator/SP.POP.TOTL |
| `WB_TRADE_GDP_PCT.xls` | `NE.TRD.GNFS.ZS` — Trade (% of GDP); retained as an optional source, not a core feature in V0.1 | https://data.worldbank.org/indicator/NE.TRD.GNFS.ZS |
| `WB_INFLATION_CPI_ANNUAL_PCT.xls` | `FP.CPI.TOTL.ZG` — Inflation, consumer prices (annual %) | https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG |
| `WB_ELECTRICITY_ACCESS_PCT.xls` | `EG.ELC.ACCS.ZS` — Access to electricity (% of population) | https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS |
| `WB_GDP_GROWTH_ANNUAL_PCT.xls` | `NY.GDP.MKTP.KD.ZG` — GDP growth (annual %) | https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG |
| `WGI_2025_Governance_Estimates_and_Scores.xlsx` | Worldwide Governance Indicators 2025 Revision, Regulatory Quality governance estimate and alternative 0–100 score | https://www.worldbank.org/en/publication/worldwide-governance-indicators |

The workbook metadata and SHA-256 checksums are generated during the clean build. The corrected panel is built for 1990-2024 so the annual FDI-flow outcome is preserved through its latest included year. The oil-rents source ends in 2021, so oil-rent-bearing matched model samples naturally end in 2021. No post-2021 oil-rent values are imputed.
