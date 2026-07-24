from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from common import RAW_DIR, VALIDATION_DIR, ensure_dirs, read_world_bank_xls, sha256_file


EXPECTED = {
    "WB_FDI_NET_INFLOWS_CURRENT_USD.xls": "BX.KLT.DINV.CD.WD",
    "WB_FDI_NET_INFLOWS_GDP_PCT.xls": "BX.KLT.DINV.WD.GD.ZS",
    "WB_OIL_RENTS_GDP_PCT.xls": "NY.GDP.PETR.RT.ZS",
    "WB_GDP_CURRENT_USD.xls": "NY.GDP.MKTP.CD",
    "WB_POPULATION_TOTAL.xls": "SP.POP.TOTL",
    "WB_TRADE_GDP_PCT.xls": "NE.TRD.GNFS.ZS",
    "WB_INFLATION_CPI_ANNUAL_PCT.xls": "FP.CPI.TOTL.ZG",
    "WB_ELECTRICITY_ACCESS_PCT.xls": "EG.ELC.ACCS.ZS",
    "WB_GDP_GROWTH_ANNUAL_PCT.xls": "NY.GDP.MKTP.KD.ZG",
}


def main() -> None:
    ensure_dirs()
    records: list[dict[str, object]] = []
    for filename, expected_code in EXPECTED.items():
        path = RAW_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Required raw file missing: {path}")
        long, _, indicator_meta, source_meta = read_world_bank_xls(path, "Value")
        codes = sorted(long["Indicator Code"].dropna().astype(str).unique().tolist())
        if codes != [expected_code]:
            raise ValueError(f"{filename}: expected {expected_code}, found {codes}")
        values = pd.to_numeric(long["Value"], errors="coerce")
        records.append(
            {
                **source_meta,
                "expected_indicator_code": expected_code,
                "sha256": sha256_file(path),
                "rows_long": int(len(long)),
                "non_null_values": int(values.notna().sum()),
                "minimum_year": int(long.loc[values.notna(), "Year"].min()),
                "maximum_year": int(long.loc[values.notna(), "Year"].max()),
                "metadata_rows": int(len(indicator_meta)),
                "validation_status": "PASS",
            }
        )

    wgi_path = RAW_DIR / "WGI_2025_Governance_Estimates_and_Scores.xlsx"
    if not wgi_path.exists():
        raise FileNotFoundError(f"Required WGI workbook missing: {wgi_path}")
    rq = pd.read_excel(wgi_path, sheet_name="rq")
    required_wgi = {"Economy (name)", "Economy (code)", "Year", "Governance estimate (approx. -2.5 to +2.5)"}
    missing_wgi = required_wgi - set(rq.columns)
    if missing_wgi:
        raise ValueError(f"WGI workbook missing columns: {sorted(missing_wgi)}")
    estimates = pd.to_numeric(rq["Governance estimate (approx. -2.5 to +2.5)"], errors="coerce")
    if estimates.dropna().abs().max() > 4:
        raise ValueError("WGI Regulatory Quality estimates outside plausible standardized range")
    records.append({
        "file": wgi_path.name,
        "last_updated": "2026-03-11",
        "indicator_code": "WGI-2025-RQ-ESTIMATE",
        "indicator_name": "Regulatory Quality governance estimate",
        "expected_indicator_code": "WGI-2025-RQ-ESTIMATE",
        "sha256": sha256_file(wgi_path),
        "rows_long": int(len(rq)),
        "non_null_values": int(estimates.notna().sum()),
        "minimum_year": int(rq.loc[estimates.notna(), "Year"].min()),
        "maximum_year": int(rq.loc[estimates.notna(), "Year"].max()),
        "metadata_rows": 1,
        "validation_status": "PASS",
    })

    output = pd.DataFrame(records).sort_values("indicator_code")
    output.to_csv(VALIDATION_DIR / "Raw_Source_Validation.csv", index=False)
    with (VALIDATION_DIR / "Raw_Source_Validation.json").open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)
    print(output[["indicator_code", "non_null_values", "minimum_year", "maximum_year", "validation_status"]].to_string(index=False))


if __name__ == "__main__":
    main()
