from __future__ import annotations

from functools import reduce

import numpy as np
import pandas as pd

from common import (
    LOCKED_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    consecutive_lag,
    ensure_dirs,
    load_config,
    read_world_bank_xls,
)



SOURCE_URLS = {
    "BX.KLT.DINV.CD.WD": "https://data.worldbank.org/indicator/BX.KLT.DINV.CD.WD",
    "BX.KLT.DINV.WD.GD.ZS": "https://data.worldbank.org/indicator/BX.KLT.DINV.WD.GD.ZS",
    "NY.GDP.PETR.RT.ZS": "https://data.worldbank.org/indicator/NY.GDP.PETR.RT.ZS",
    "NY.GDP.MKTP.CD": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
    "SP.POP.TOTL": "https://data.worldbank.org/indicator/SP.POP.TOTL",
    "NE.TRD.GNFS.ZS": "https://data.worldbank.org/indicator/NE.TRD.GNFS.ZS",
    "FP.CPI.TOTL.ZG": "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG",
    "EG.ELC.ACCS.ZS": "https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS",
    "NY.GDP.MKTP.KD.ZG": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG",
}

INDICATORS = {
    "WB_FDI_NET_INFLOWS_CURRENT_USD.xls": "Inward_FDI_Net_Flow_USD",
    "WB_FDI_NET_INFLOWS_GDP_PCT.xls": "Inward_FDI_Net_Flow_GDP_Pct",
    "WB_OIL_RENTS_GDP_PCT.xls": "Oil_Rents_GDP_Pct",
    "WB_GDP_CURRENT_USD.xls": "GDP_Current_USD",
    "WB_POPULATION_TOTAL.xls": "Population",
    "WB_TRADE_GDP_PCT.xls": "Trade_GDP_Pct",
    "WB_INFLATION_CPI_ANNUAL_PCT.xls": "Inflation_CPI_Annual_Pct",
    "WB_ELECTRICITY_ACCESS_PCT.xls": "Electricity_Access_Pct",
    "WB_GDP_GROWTH_ANNUAL_PCT.xls": "GDP_Growth_Annual_Pct",
}


def main() -> None:
    ensure_dirs()
    cfg = load_config()
    year_min = int(cfg["analysis_year_min"])
    year_max = int(cfg["analysis_year_max"])

    frames: list[pd.DataFrame] = []
    source_log: list[dict[str, object]] = []
    country_meta: pd.DataFrame | None = None

    for filename, value_name in INDICATORS.items():
        long, meta, _, source_meta = read_world_bank_xls(RAW_DIR / filename, value_name)
        if country_meta is None:
            country_meta = meta.copy()
        keep = long[["Country Name", "ISO3", "Year", value_name]].copy()
        keep[value_name] = pd.to_numeric(keep[value_name], errors="coerce")
        keep = keep[(keep["Year"] >= year_min) & (keep["Year"] <= year_max)]
        frames.append(keep)
        source_log.append({**source_meta, "panel_variable": value_name, "official_url": SOURCE_URLS[source_meta["indicator_code"]]})

    assert country_meta is not None
    country_meta = country_meta.rename(columns={"Country Code": "ISO3"})
    actual = country_meta[country_meta["Region"].notna()][["ISO3", "TableName", "Region", "IncomeGroup"]].drop_duplicates("ISO3")
    actual = actual.rename(columns={"TableName": "Country_Name_Metadata"})

    panel = reduce(
        lambda left, right: pd.merge(left, right, on=["Country Name", "ISO3", "Year"], how="outer"),
        frames,
    )
    panel = panel.merge(actual, on="ISO3", how="inner")
    panel["Country Name"] = panel["Country_Name_Metadata"].fillna(panel["Country Name"])
    panel = panel.drop(columns=["Country_Name_Metadata"])
    panel = panel.drop_duplicates(["ISO3", "Year"]).sort_values(["ISO3", "Year"]).reset_index(drop=True)

    wgi_path = RAW_DIR / "WGI_2025_Governance_Estimates_and_Scores.xlsx"
    rq = pd.read_excel(wgi_path, sheet_name="rq")[[
        "Economy (name)",
        "Economy (code)",
        "Year",
        "Governance estimate (approx. -2.5 to +2.5)",
    ]].copy()
    rq = rq.rename(columns={
        "Economy (name)": "WGI_Economy_Name",
        "Economy (code)": "ISO3",
        "Governance estimate (approx. -2.5 to +2.5)": "Regulatory_Quality",
    })
    rq["Year"] = pd.to_numeric(rq["Year"], errors="raise").astype(int)
    rq["Regulatory_Quality"] = pd.to_numeric(rq["Regulatory_Quality"], errors="coerce")
    rq = rq[rq["ISO3"].isin(set(actual["ISO3"]))].drop_duplicates(["ISO3", "Year"])
    panel = panel.merge(rq[["ISO3", "Year", "Regulatory_Quality"]], on=["ISO3", "Year"], how="left")
    wgi_unmatched = pd.read_excel(wgi_path, sheet_name="rq")[["Economy (name)", "Economy (code)"]].drop_duplicates()
    wgi_unmatched["Mapped_to_WB_ISO3"] = wgi_unmatched["Economy (code)"].isin(set(actual["ISO3"]))
    wgi_unmatched.to_csv(LOCKED_DIR / "WGI_to_World_Bank_Country_Mapping_Audit.csv", index=False)
    source_log.append({
        "file": wgi_path.name,
        "last_updated": "2026-03-11",
        "indicator_code": "WGI-2025-RQ-ESTIMATE",
        "indicator_name": "Regulatory Quality governance estimate",
        "panel_variable": "Regulatory_Quality",
        "official_url": "https://www.worldbank.org/en/publication/worldwide-governance-indicators",
    })

    panel["Inward_FDI_Net_Flow_USD_Millions"] = panel["Inward_FDI_Net_Flow_USD"] / 1_000_000.0
    panel["Inward_FDI_Net_Flow_asinh"] = np.arcsinh(panel["Inward_FDI_Net_Flow_USD_Millions"])
    # Independent consistency calculation. The official World Bank flow/GDP series remains
    # authoritative; this derived ratio is audit-only and never used as a model target.
    panel["Inward_FDI_Net_Flow_GDP_Pct_Derived"] = (
        panel["Inward_FDI_Net_Flow_USD"] / panel["GDP_Current_USD"] * 100.0
    )
    panel["Flow_GDP_Pct_Official_Minus_Derived"] = (
        panel["Inward_FDI_Net_Flow_GDP_Pct"] - panel["Inward_FDI_Net_Flow_GDP_Pct_Derived"]
    )
    # Signed, monotonic normalization of the official flow-to-GDP ratio.
    # This retains negative disinvestment observations while reducing the leverage of
    # conduit/financial-centre observations with ratios in the hundreds of percent.
    panel["Inward_FDI_Net_Flow_GDP_Pct_asinh"] = np.arcsinh(panel["Inward_FDI_Net_Flow_GDP_Pct"])
    panel["GDP_log"] = np.log1p(panel["GDP_Current_USD"].where(panel["GDP_Current_USD"] >= 0))
    panel["Population_log"] = np.log1p(panel["Population"].where(panel["Population"] >= 0))

    lag_columns = [
        "Inward_FDI_Net_Flow_asinh",
        "Inward_FDI_Net_Flow_GDP_Pct",
        "Inward_FDI_Net_Flow_GDP_Pct_asinh",
        "Oil_Rents_GDP_Pct",
        "GDP_log",
        "Population_log",
        "Trade_GDP_Pct",
        "Inflation_CPI_Annual_Pct",
        "Electricity_Access_Pct",
        "GDP_Growth_Annual_Pct",
        "Regulatory_Quality",
    ]
    pieces: list[pd.DataFrame] = []
    for _, group in panel.groupby("ISO3", sort=False):
        group = group.sort_values("Year").copy()
        for column in lag_columns:
            group[f"{column}_lag1"] = consecutive_lag(group, column, periods=1)
        pieces.append(group)
    panel = pd.concat(pieces, ignore_index=True).sort_values(["ISO3", "Year"]).reset_index(drop=True)

    exposure = (
        panel[(panel["Year"] <= int(cfg["oil_rent_classification_end_year"]))]
        .groupby("ISO3", as_index=False)["Oil_Rents_GDP_Pct"]
        .max()
        .rename(columns={"Oil_Rents_GDP_Pct": "Max_Oil_Rents_Pre2016"})
    )
    for threshold in cfg["oil_rent_thresholds_pct_gdp"]:
        label = str(threshold).replace(".", "p")
        exposure[f"Oil_Rent_Intensive_Pre2016_ge{label}pct"] = (
            exposure["Max_Oil_Rents_Pre2016"] >= float(threshold)
        )
    panel = panel.merge(exposure, on="ISO3", how="left")
    for threshold in cfg["oil_rent_thresholds_pct_gdp"]:
        label = str(threshold).replace(".", "p")
        column = f"Oil_Rent_Intensive_Pre2016_ge{label}pct"
        panel[column] = panel[column].fillna(False).astype(bool)

    panel["Row_ID"] = panel["ISO3"].astype(str) + "-" + panel["Year"].astype(str)
    ordered = [
        "Row_ID",
        "Country Name",
        "ISO3",
        "Year",
        "Region",
        "IncomeGroup",
        "Max_Oil_Rents_Pre2016",
    ] + [column for column in panel.columns if column not in {
        "Row_ID", "Country Name", "ISO3", "Year", "Region", "IncomeGroup",
        "Max_Oil_Rents_Pre2016"
    }]
    panel = panel[ordered]

    panel.to_csv(PROCESSED_DIR / "MS2_SIGNAL_ADMISSIBILITY_PANEL_V3.csv", index=False)
    pd.DataFrame(source_log).to_csv(PROCESSED_DIR / "Source_Provenance_Log.csv", index=False)

    ratio = panel.dropna(subset=[
        "Inward_FDI_Net_Flow_GDP_Pct",
        "Inward_FDI_Net_Flow_GDP_Pct_Derived",
    ]).copy()
    ratio["Absolute_Difference_Pct_Points"] = ratio["Flow_GDP_Pct_Official_Minus_Derived"].abs()
    ratio_summary = pd.DataFrame([
        {
            "metric": "comparable_country_years",
            "value": int(len(ratio)),
        },
        {
            "metric": "median_absolute_difference_pct_points",
            "value": float(ratio["Absolute_Difference_Pct_Points"].median()) if len(ratio) else np.nan,
        },
        {
            "metric": "p95_absolute_difference_pct_points",
            "value": float(ratio["Absolute_Difference_Pct_Points"].quantile(0.95)) if len(ratio) else np.nan,
        },
        {
            "metric": "maximum_absolute_difference_pct_points",
            "value": float(ratio["Absolute_Difference_Pct_Points"].max()) if len(ratio) else np.nan,
        },
        {
            "metric": "observations_abs_difference_gt_0_1_pct_points",
            "value": int((ratio["Absolute_Difference_Pct_Points"] > 0.1).sum()),
        },
        {
            "metric": "observations_abs_difference_gt_1_pct_point",
            "value": int((ratio["Absolute_Difference_Pct_Points"] > 1.0).sum()),
        },
    ])
    ratio_summary.to_csv(PROCESSED_DIR / "Flow_GDP_Ratio_Consistency_Summary.csv", index=False)
    ratio.nlargest(100, "Absolute_Difference_Pct_Points")[[
        "Country Name", "ISO3", "Year",
        "Inward_FDI_Net_Flow_GDP_Pct",
        "Inward_FDI_Net_Flow_GDP_Pct_Derived",
        "Flow_GDP_Pct_Official_Minus_Derived",
        "Absolute_Difference_Pct_Points",
    ]].to_csv(PROCESSED_DIR / "Flow_GDP_Ratio_Consistency_Top100.csv", index=False)

    dictionary_rows: list[dict[str, str]] = []
    definitions = {
        "Inward_FDI_Net_Flow_USD": "Annual inward FDI net inflows, balance of payments, current US dollars.",
        "Inward_FDI_Net_Flow_USD_Millions": "Annual inward FDI net inflows in current US$ millions.",
        "Inward_FDI_Net_Flow_asinh": "Inverse-hyperbolic-sine transform of annual inward FDI net inflows in US$ millions; negatives retained.",
        "Inward_FDI_Net_Flow_GDP_Pct": "Annual inward FDI net inflows as a percentage of GDP; official World Bank series; no clipping; retained as a raw-ratio stress test.",
        "Inward_FDI_Net_Flow_GDP_Pct_asinh": "Inverse-hyperbolic-sine transform of the official annual inward FDI net inflows as a percentage of GDP; negatives retained; primary size-normalised robustness target.",
        "Inward_FDI_Net_Flow_GDP_Pct_Derived": "Audit-only ratio calculated from annual inward FDI net inflows divided by GDP current US$; not used as a model target.",
        "Flow_GDP_Pct_Official_Minus_Derived": "Audit-only difference between the official World Bank flow/GDP series and the internally derived ratio, in percentage points.",
        "Oil_Rents_GDP_Pct": "Oil rents as a percentage of GDP.",
        "GDP_log": "Natural log of one plus GDP in current US dollars.",
        "Population_log": "Natural log of one plus total population.",
        "Regulatory_Quality": "Worldwide Governance Indicators Regulatory Quality estimate.",
        "Max_Oil_Rents_Pre2016": "Maximum oil rents as a percentage of GDP during the predeclared 1990-2015 classification window.",
    }
    for column in panel.columns:
        dictionary_rows.append({
            "variable": column,
            "definition": definitions.get(column, "Derived or source variable; see Source_Provenance_Log and pipeline code."),
            "type": str(panel[column].dtype),
        })
    pd.DataFrame(dictionary_rows).to_csv(PROCESSED_DIR / "Data_Dictionary_V3.csv", index=False)

    missingness = pd.DataFrame({
        "variable": panel.columns,
        "non_null": [int(panel[column].notna().sum()) for column in panel.columns],
        "missing": [int(panel[column].isna().sum()) for column in panel.columns],
        "missing_pct": [float(panel[column].isna().mean() * 100) for column in panel.columns],
    })
    missingness.to_csv(PROCESSED_DIR / "Missingness_and_Coverage.csv", index=False)

    country_years = panel.groupby("ISO3")["Year"].agg(["min", "max", "count"]).reset_index()
    country_years = country_years.merge(actual, on="ISO3", how="left")
    country_years.to_csv(LOCKED_DIR / "Country_Universe.csv", index=False)

    print(f"Panel rows: {len(panel):,}")
    print(f"Countries: {panel['ISO3'].nunique():,}")
    print(f"Years: {panel['Year'].min()}-{panel['Year'].max()}")
    print(f"FDI flow observations: {panel['Inward_FDI_Net_Flow_USD'].notna().sum():,}")
    print(f"Negative FDI flows retained: {(panel['Inward_FDI_Net_Flow_USD'] < 0).sum():,}")
    nga = panel[panel['ISO3'] == 'NGA']
    print(f"Nigeria rows: {len(nga):,}; FDI observations: {nga['Inward_FDI_Net_Flow_USD'].notna().sum():,}")


if __name__ == "__main__":
    main()
