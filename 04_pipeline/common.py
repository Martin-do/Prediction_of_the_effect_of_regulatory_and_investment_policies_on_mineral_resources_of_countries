from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "03_config" / "analysis_config.json"
RAW_DIR = ROOT / "01_raw_data" / "world_bank"
PROCESSED_DIR = ROOT / "05_processed_data"
LOCKED_DIR = ROOT / "06_locked_design"
OUTPUT_DIR = ROOT / "07_outputs"
VALIDATION_DIR = ROOT / "08_validation"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_dirs() -> None:
    for directory in (PROCESSED_DIR, LOCKED_DIR, OUTPUT_DIR, VALIDATION_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_fold(iso3: str, n_folds: int, salt: str) -> int:
    key = f"{salt}:{iso3}".encode("utf-8")
    value = int(hashlib.sha256(key).hexdigest()[:16], 16)
    return value % n_folds


def read_world_bank_xls(path: Path, value_name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Read a World Bank indicator workbook into long format.

    Returns data, country metadata, indicator metadata, and source metadata.
    """
    raw = pd.read_excel(path, sheet_name="Data", header=None)
    if raw.shape[0] < 5:
        raise ValueError(f"Unexpected World Bank workbook format: {path}")

    last_updated = raw.iloc[1, 1]
    header_row = 3
    data = pd.read_excel(path, sheet_name="Data", header=header_row)
    required = {"Country Name", "Country Code", "Indicator Name", "Indicator Code"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path.name}: {sorted(missing)}")

    year_cols = [column for column in data.columns if str(column).isdigit()]
    long = data.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
        value_vars=year_cols,
        var_name="Year",
        value_name=value_name,
    )
    long["Year"] = pd.to_numeric(long["Year"], errors="raise").astype(int)
    long = long.rename(columns={"Country Code": "ISO3"})

    country_meta = pd.read_excel(path, sheet_name="Metadata - Countries")
    indicator_meta = pd.read_excel(path, sheet_name="Metadata - Indicators")
    source_meta = {
        "file": path.name,
        "last_updated": str(pd.to_datetime(last_updated).date()) if pd.notna(last_updated) else "",
        "indicator_code": str(long["Indicator Code"].dropna().iloc[0]),
        "indicator_name": str(long["Indicator Name"].dropna().iloc[0]),
    }
    return long, country_meta, indicator_meta, source_meta


def consecutive_lag(group: pd.DataFrame, column: str, periods: int = 1) -> pd.Series:
    shifted = group[column].shift(periods)
    shifted_year = group["Year"].shift(periods)
    valid = (group["Year"] - shifted_year) == periods
    return shifted.where(valid)


def safe_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2 or np.nanvar(y_true) == 0:
        return float("nan")
    residual = np.nansum((y_true - y_pred) ** 2)
    total = np.nansum((y_true - np.nanmean(y_true)) ** 2)
    if total == 0:
        return float("nan")
    return float(1.0 - residual / total)
