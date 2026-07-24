import pandas as pd
import numpy as np

# =============================================================================
# BUILD LAGGED FEATURES — PART 1 UPGRADE
# =============================================================================
# Run order: 3 of 3  (after build_upgraded_dataset.py)
# Input    : INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv
# Output   : INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv  (same file, new columns)
# =============================================================================

INPUT_FILE  = 'INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv'
OUTPUT_FILE = 'INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv'

LAG_YEARS   = [1, 2, 3]

# Columns to lag — script silently skips any not present in the dataset
COLS_TO_LAG = [
    # Resource base
    'Oil_Rents_GDP_Percent',
    'Total_NR_Rents_GDP_Percent',
    # Core governance
    'Regulatory_Quality',
    'CPI_Score',
    # Investment / restriction
    'Avg_FDI_Restriction_Index',
    'FDI_asinh',           # ← for persistence baseline in signal_audit_nb.py
    # Macro
    'Trade_GDP_Percent',
    'Inflation_CPI_Annual_Pct',
    'Exchange_Rate_LCU_USD',
    # IMF reform indices (renamed from 'Trade' in build_upgraded_dataset.py)
    'IMF_Trade_Reform_Index',
    'Domestic finance',
    'External finance',
    'Labor market',
    'Product market',
    # New Review Macro Controls
    'Political_Stability_Score',
    'Electricity_Access_Pct',
    'Broadband_Per100',
    'Oil_Price_Global_USD',
]

# Subset for 3-year rolling means (most economically meaningful)
COLS_ROLLING = [
    'Oil_Rents_GDP_Percent',
    'Total_NR_Rents_GDP_Percent',
    'Regulatory_Quality',
    'CPI_Score',
    'Avg_FDI_Restriction_Index',
    'Trade_GDP_Percent',
    'Inflation_CPI_Annual_Pct',
]

GROUP_COL = 'ISO3'
YEAR_COL  = 'Year'


def add_lags(df, cols, lags, group):
    df = df.sort_values([group, YEAR_COL]).copy()
    added = []
    for col in cols:
        if col not in df.columns:
            print(f"  ⚠ Lag skipped: '{col}' not found")
            continue
        for lag in lags:
            new = f"{col}_lag{lag}"
            df[new] = df.groupby(group)[col].shift(lag)
            added.append(new)
    print(f"  ✓ {len(added)} lag columns added")
    return df, added


def add_rolling_means(df, cols, window, group):
    """
    3-year rolling mean of the LAGGED series (shift-1 then roll).
    min_periods=2 avoids dropping all rows at the start of each country's series.
    """
    df = df.sort_values([group, YEAR_COL]).copy()
    added = []
    for col in cols:
        if col not in df.columns:
            print(f"  ⚠ Rolling skipped: '{col}' not found")
            continue
        new = f"{col}_roll{window}yr"
        df[new] = (
            df.groupby(group)[col]
            .transform(lambda x: x.shift(1).rolling(window, min_periods=2).mean())
        )
        added.append(new)
    print(f"  ✓ {len(added)} rolling-mean columns added")
    return df, added


def coverage(df, cols):
    print("\n  LAGGED FEATURE COVERAGE (% non-null):")
    for col in cols:
        pct = df[col].notna().sum() / len(df) * 100
        print(f"    {col:<48} {pct:5.1f}%")


def main():
    print("="*70)
    print("BUILD LAGGED FEATURES — PART 1 UPGRADE")
    print("="*70)

    # Load
    print(f"\nSTEP 1: Loading {INPUT_FILE} …")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"✗ {INPUT_FILE} not found — run build_upgraded_dataset.py first")
        return
    print(f"  ✓ {df.shape[0]:,} rows × {df.shape[1]} cols  "
          f"({df[GROUP_COL].nunique()} countries, "
          f"{df[YEAR_COL].min()}–{df[YEAR_COL].max()})")

    # Lags
    print(f"\nSTEP 2: Adding {LAG_YEARS}-year lags …")
    df, lag_cols = add_lags(df, COLS_TO_LAG, LAG_YEARS, GROUP_COL)

    # Rolling means
    print(f"\nSTEP 3: Adding 3-year rolling means (lagged by 1yr) …")
    df, roll_cols = add_rolling_means(df, COLS_ROLLING, 3, GROUP_COL)

    # ── STEP 4: FDI Responsiveness ────────────────────────────────────────────
    # = (FDI_t − FDI_t-1) / |FDI_t-1|  — year-over-year FDI change rate.
    # Captures investment responsiveness to prior-year conditions.
    # Clipped at ±10 (1000%) to suppress outliers from near-zero base years.
    print(f"\nSTEP 4: Computing FDI Responsiveness …")
    fdi_resp_cols = []
    if 'FDI_Flows_Millions_USD' in df.columns:
        df = df.sort_values([GROUP_COL, YEAR_COL])
        fdi_lag1 = df.groupby(GROUP_COL)['FDI_Flows_Millions_USD'].shift(1)
        df['FDI_Responsiveness'] = (
            (df['FDI_Flows_Millions_USD'] - fdi_lag1) / fdi_lag1.abs()
        ).clip(-10, 10)
        fdi_resp_cols.append('FDI_Responsiveness')
        print(f"  ✓ FDI_Responsiveness  ({df['FDI_Responsiveness'].notna().sum():,} obs)")
    else:
        print("  ⚠ FDI_Flows_Millions_USD not found — FDI_Responsiveness skipped")

    # ── STEP 5: Revenue Volatility ────────────────────────────────────────────
    # 3-year rolling standard deviation of oil rents and FDI inflows.
    # Captures instability — a real investment and regulatory concern.
    print(f"\nSTEP 5: Computing Revenue Volatility (3-year rolling std) …")
    vol_cols = []
    vol_targets = [
        ('Oil_Rents_GDP_Percent',   'Oil_Rents_Volatility_3yr'),
        ('Total_NR_Rents_GDP_Percent', 'NR_Rents_Volatility_3yr'),
        ('FDI_Flows_Millions_USD',  'FDI_Volatility_3yr'),
    ]
    df = df.sort_values([GROUP_COL, YEAR_COL])
    for src_col, new_col in vol_targets:
        if src_col not in df.columns:
            print(f"  ⚠ {src_col} not found — {new_col} skipped")
            continue
        df[new_col] = (
            df.groupby(GROUP_COL)[src_col]
            .transform(lambda x: x.shift(1).rolling(3, min_periods=2).std())
        )
        vol_cols.append(new_col)
        print(f"  ✓ {new_col}  ({df[new_col].notna().sum():,} obs)")

    # Coverage
    coverage(df, lag_cols + roll_cols + fdi_resp_cols + vol_cols)

    # Save
    print(f"\nSTEP 6: Saving {OUTPUT_FILE} …")
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"  ✓ {OUTPUT_FILE}")
    print(f"     Rows: {len(df):,}  |  Cols: {len(df.columns)}")
    print(f"     New lag cols         : {len(lag_cols)}")
    print(f"     New rolling cols     : {len(roll_cols)}")
    print(f"     FDI Responsiveness   : {len(fdi_resp_cols)}")
    print(f"     Volatility cols      : {len(vol_cols)}")

    print("\n" + "="*70)
    print("✅ LAGGED FEATURES COMPLETE  →  next: signal_audit_nb.py")
    print("="*70)


if __name__ == "__main__":
    main()
