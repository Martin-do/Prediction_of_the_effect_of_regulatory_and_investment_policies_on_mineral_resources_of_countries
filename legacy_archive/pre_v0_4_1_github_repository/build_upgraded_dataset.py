import pandas as pd
import numpy as np

# =============================================================================
# BUILD UPGRADED DATASET — PART 1 UPGRADE
# =============================================================================
# Run order: 2 of 3  (after fetch_mineral_data.py)
# Inputs   : World_Bank_Indicators_Upgraded.csv   ← from fetch_mineral_data.py
#            Investment_FDI_Dataset.csv            ← from investment_nb.py pipeline
#            REGULATORY_MASTER.csv                 ← existing (contains EITI cols)
#            Global_Commodity_Prices.csv           ← from fetch_mineral_data.py (optional)
# Outputs  : INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv   (full dataset)
#            INVESTMENT_SIGNAL_AUDIT_EITI_FOCUSED.csv    (EITI two-track subset)
# =============================================================================

WB_FILE         = 'World_Bank_Indicators_Upgraded.csv'
INVESTMENT_FILE = 'Investment_FDI_Dataset.csv'       # built by investment_nb.py
REGULATORY_FILE = 'REGULATORY_MASTER.csv'
OIL_PRICE_FILE  = 'Global_Commodity_Prices.csv'      # optional year-level join

FULL_OUTPUT     = 'INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv'
EITI_OUTPUT     = 'INVESTMENT_SIGNAL_AUDIT_EITI_FOCUSED.csv'

REGIONAL_CODES = [
    'AFE','AFW','ARB','CEB','CSS','EAP','EAR','EAS','ECA','ECS',
    'EMU','EUU','FCS','HIC','HPC','IBD','IBT','IDA','IDB','IDX',
    'INX','LAC','LCN','LDC','LIC','LMC','LMY','LTE','MEA','MIC',
    'MNA','NAC','OED','OSS','PRE','PSS','PST','SAS','SSA','SSF',
    'SST','TEA','TEC','TLA','TMN','TSA','TSS','UMC','WLD'
]

# Columns that cause data leakage — excluded from the ML dataset
LEAKAGE_COLS = [
    'Resource_Rich', 'Resource_Category', 'Has_Mineral_Data',
    'Mineral_Rents_Log', 'FDI_Restriction_Scaled', 'FDI_Flows_Scaled',
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load(path, label):
    try:
        df = pd.read_csv(path)
        print(f"  ✓ {label}: {df.shape[0]:,} rows × {df.shape[1]} cols")
        return df
    except FileNotFoundError:
        print(f"  ⚠ {label}: NOT FOUND ({path}) — skipped")
        return None


def clean_keys(df, iso_col='ISO3', year_col='Year'):
    if 'Country Code' in df.columns and iso_col not in df.columns:
        df = df.rename(columns={'Country Code': iso_col})
    df[iso_col] = df[iso_col].astype(str).str.upper().str.strip()
    df = df[~df[iso_col].isin(REGIONAL_CODES)]
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    df = df.dropna(subset=[year_col])
    df[year_col] = df[year_col].astype(int)
    return df


def add_log(df, raw_col, log_col):
    if raw_col in df.columns and log_col not in df.columns:
        df[log_col] = np.log(df[raw_col].where(df[raw_col] > 0))
        print(f"  ✓ {log_col} = log({raw_col})")
    return df


def add_fdi_targets(df):
    if 'FDI_Flows_Millions_USD' in df.columns:
        df['FDI_asinh'] = np.arcsinh(df['FDI_Flows_Millions_USD'])
        print("  ✓ FDI_asinh  = arcsinh(FDI_Flows_Millions_USD)  [primary target]")
        if 'GDP_Current_USD' in df.columns:
            gdp_m = df['GDP_Current_USD'] / 1e6
            df['FDI_GDP_Pct'] = (df['FDI_Flows_Millions_USD'] / gdp_m * 100).clip(upper=200)
            print("  ✓ FDI_GDP_Pct = FDI / GDP × 100 (clipped 200%)  [robustness target]")
    return df


def add_derived_resource_cols(df):
    """
    Mineral_Rents_Excl_OilGas : already = Mineral_Rents_GDP_Percent by WB definition
                                  (NY.GDP.MINR.RT.ZS excludes oil/gas/coal).
                                  We keep a renamed copy for clarity.
    Hydrocarbon_Rents_GDP_Percent : Oil + Gas + Coal rents.
    Mining_GDP_Proxy              : All rents summed — best available WB proxy for
                                    mining share of GDP (rents-based, not value-added).
    """
    if 'Mineral_Rents_GDP_Percent' in df.columns:
        df['Mineral_Rents_Excl_OilGas'] = df['Mineral_Rents_GDP_Percent']
        print("  ✓ Mineral_Rents_Excl_OilGas (= Mineral_Rents_GDP_Percent; "
              "WB definition already excludes oil/gas/coal)")

    hydrocarbon_cols = [c for c in ['Oil_Rents_GDP_Percent','Gas_Rents_GDP_Percent',
                                     'Coal_Rents_GDP_Percent'] if c in df.columns]
    if hydrocarbon_cols:
        df['Hydrocarbon_Rents_GDP_Percent'] = df[hydrocarbon_cols].sum(axis=1, min_count=1)
        print(f"  ✓ Hydrocarbon_Rents_GDP_Percent = {' + '.join(hydrocarbon_cols)}")

    all_rent_cols = [c for c in ['Oil_Rents_GDP_Percent','Gas_Rents_GDP_Percent',
                                  'Coal_Rents_GDP_Percent','Mineral_Rents_GDP_Percent']
                     if c in df.columns]
    if all_rent_cols:
        df['Mining_GDP_Proxy'] = df[all_rent_cols].sum(axis=1, min_count=1)
        print(f"  ✓ Mining_GDP_Proxy = sum of all rents "
              f"(rents-based proxy for mining share of GDP)")

    # Revenue Capture Efficiency
    # = Total_Revenue_USD / (Total_NR_Rents_GDP_Percent / 100 × GDP_Current_USD)
    # Measures how much of the country's natural resource wealth actually becomes
    # public revenue. Uses Total_NR_Rents as denominator to match EITI's broad
    # scope (oil + gas + mining combined).
    if all(c in df.columns for c in
           ['Total_Revenue_USD', 'Total_NR_Rents_GDP_Percent', 'GDP_Current_USD']):
        nr_wealth_usd = (df['Total_NR_Rents_GDP_Percent'] / 100) * df['GDP_Current_USD']
        df['Revenue_Capture_Efficiency'] = (
            df['Total_Revenue_USD'] / nr_wealth_usd
        ).clip(upper=5)   # >5 implies data error — can't capture >500% of resource rents
        print("  ✓ Revenue_Capture_Efficiency = Total_Revenue_USD / "
              "(Total_NR_Rents_GDP_Percent/100 × GDP_Current_USD)  [EITI target]")

    # EITI Revenue per unit Mineral Rent (solid-minerals focused version)
    if all(c in df.columns for c in
           ['Total_Revenue_USD', 'Mineral_Rents_GDP_Percent', 'GDP_Current_USD']):
        mineral_wealth_usd = (df['Mineral_Rents_GDP_Percent'] / 100) * df['GDP_Current_USD']
        df['EITI_Revenue_Per_Mineral_Rent'] = (
            df['Total_Revenue_USD'] / mineral_wealth_usd
        ).clip(upper=5)
        print("  ✓ EITI_Revenue_Per_Mineral_Rent = Total_Revenue_USD / "
              "(Mineral_Rents_GDP_Percent/100 × GDP_Current_USD)")

    return df


def coverage_report(df, label="COVERAGE"):
    key = [
        'Oil_Rents_GDP_Percent','Total_NR_Rents_GDP_Percent','Mineral_Rents_GDP_Percent',
        'Mineral_Rents_Excl_OilGas','Hydrocarbon_Rents_GDP_Percent','Mining_GDP_Proxy',
        'FDI_Flows_Millions_USD','FDI_asinh','FDI_GDP_Pct',
        'Avg_FDI_Restriction_Index','Regulatory_Quality','CPI_Score',
        'GDP_log','GDP_Per_Capita_log','Population_log',
        'Trade_GDP_Percent','Inflation_CPI_Annual_Pct',
        'Exchange_Rate_LCU_USD','Political_Stability_Score','Electricity_Access_Pct',
        'Oil_Price_Global_USD',
        'IMF_Trade_Reform_Index','Domestic finance','External finance',
        'Total_Revenue_USD',
    ]
    present = [c for c in key if c in df.columns]
    print(f"\n  {label}:")
    print(f"  {'Column':<40} {'Non-null':>9}  {'%':>6}")
    print(f"  {'-'*58}")
    for col in present:
        n   = df[col].notna().sum()
        pct = n / len(df) * 100
        print(f"  {col:<40} {n:>9,}  {pct:>5.1f}%")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("="*70)
    print("BUILD UPGRADED DATASET — PART 1 UPGRADE")
    print("="*70)

    # ── 1. Load ───────────────────────────────────────────────────────────────
    print("\nSTEP 1: Loading source files …")
    wb_df   = load(WB_FILE,         "World Bank indicators")
    inv_df  = load(INVESTMENT_FILE, "Investment / FDI")
    reg_df  = load(REGULATORY_FILE, "Regulatory master")
    oil_df  = load(OIL_PRICE_FILE,  "Global oil price (year-level)")

    if wb_df is None and inv_df is None:
        print("✗ Neither WB nor Investment file loaded. Cannot continue.")
        return

    # ── 2. Clean keys ─────────────────────────────────────────────────────────
    print("\nSTEP 2: Cleaning keys and stripping regional aggregates …")
    if wb_df is not None:  wb_df  = clean_keys(wb_df)
    if inv_df is not None: inv_df = clean_keys(inv_df)
    if reg_df is not None: reg_df = clean_keys(reg_df)

    # ── 3. Base frame from World Bank ─────────────────────────────────────────
    print("\nSTEP 3: Building base frame …")
    if wb_df is not None:
        base = wb_df.copy()
    else:
        base = inv_df[['ISO3','Year','Country Name']].drop_duplicates().copy()
    print(f"  Base: {len(base):,} rows")

    # ── 4. Merge Investment / FDI ─────────────────────────────────────────────
    print("\nSTEP 4: Merging Investment / FDI data …")
    if inv_df is not None:
        inv_cols = [c for c in ['ISO3','Year','Avg_FDI_Restriction_Index',
                                 'FDI_Flows_Millions_USD'] if c in inv_df.columns]
        base = base.merge(inv_df[inv_cols], on=['ISO3','Year'], how='left')
        print(f"  After merge: {len(base):,} rows")

    # ── 5. Merge Regulatory / Governance ──────────────────────────────────────
    print("\nSTEP 5: Merging regulatory / governance data …")
    if reg_df is not None:
        reg_want = [
            'ISO3','Year',
            'Regulatory_Quality','Regulatory_Quality_Filled',
            'CPI_Score','CPI_Rank','World Bank CPIA',
            'Domestic finance','External finance',
            'Labor market','Product market',
            'Trade',          # ← IMF trade reform index — renamed below
            'PRS International Country Risk Guide',
            'DSTRI_Composite_Score',
            'Total_Revenue_USD','Total_Revenue_Local','Currency',
            'Region_Europe & Central Asia',
            'Region_Latin America & Caribbean',
            'Region_Middle East & North Africa',
            'Region_North America','Region_South Asia',
            'Region_Sub-Saharan Africa',
            'IncomeGroup_Low income',
            'IncomeGroup_Lower middle income',
            'IncomeGroup_Upper middle income',
        ]
        # Exclude Mineral_Rents_GDP_Percent — already in WB data
        reg_want = [c for c in reg_want
                    if c in reg_df.columns and c != 'Mineral_Rents_GDP_Percent']

        reg_slim = reg_df[reg_want].copy()

        # ── RENAME 'Trade' (IMF reform index) to avoid clash with Trade_GDP_Percent
        if 'Trade' in reg_slim.columns:
            reg_slim = reg_slim.rename(columns={'Trade': 'IMF_Trade_Reform_Index'})

        base = base.merge(reg_slim, on=['ISO3','Year'], how='left')

        # Fill Regulatory_Quality gaps from _Filled
        if 'Regulatory_Quality_Filled' in base.columns:
            base['Regulatory_Quality'] = (
                base['Regulatory_Quality']
                .fillna(base['Regulatory_Quality_Filled'])
            )
            base.drop(columns=['Regulatory_Quality_Filled'], inplace=True)

        print(f"  After merge: {len(base):,} rows")
        eiti_cov = base['Total_Revenue_USD'].notna().sum() / len(base) * 100
        print(f"  EITI coverage: {eiti_cov:.1f}% of rows")

    # ── 6. Merge global oil price (year-join only) ────────────────────────────
    print("\nSTEP 6: Merging global oil price (year-level) …")
    if oil_df is not None:
        oil_df['Year'] = oil_df['Year'].astype(int)
        base = base.merge(oil_df[['Year','Oil_Price_Global_USD']], on='Year', how='left')
        oil_cov = base['Oil_Price_Global_USD'].notna().sum() / len(base) * 100
        print(f"  ✓ Oil price coverage: {oil_cov:.1f}%")
    else:
        print("  ⚠ Skipped (Global_Commodity_Prices.csv not available)")

    # ── 7. FDI targets ────────────────────────────────────────────────────────
    print("\nSTEP 7: Building FDI targets …")
    base = add_fdi_targets(base)

    # ── 8. Log transforms ─────────────────────────────────────────────────────
    print("\nSTEP 8: Log transforms …")
    base = add_log(base, 'GDP_Current_USD',   'GDP_log')
    base = add_log(base, 'GDP_Per_Capita_USD','GDP_Per_Capita_log')
    base = add_log(base, 'Population',         'Population_log')

    # ── 9. Derived resource columns ───────────────────────────────────────────
    print("\nSTEP 9: Derived resource columns …")
    base = add_derived_resource_cols(base)

    # ── 10. Drop leakage columns ──────────────────────────────────────────────
    print("\nSTEP 10: Dropping leakage columns …")
    dropped = [c for c in LEAKAGE_COLS if c in base.columns]
    base.drop(columns=dropped, inplace=True)
    print(f"  Dropped: {dropped}")

    # ── 11. Column order ──────────────────────────────────────────────────────
    id_cols     = ['Country Name','ISO3','Year']
    target_cols = ['FDI_asinh','FDI_GDP_Pct','FDI_Flows_Millions_USD']
    resource_cols = ['Oil_Rents_GDP_Percent','Gas_Rents_GDP_Percent',
                     'Coal_Rents_GDP_Percent','Mineral_Rents_GDP_Percent',
                     'Mineral_Rents_Excl_OilGas','Total_NR_Rents_GDP_Percent',
                     'Hydrocarbon_Rents_GDP_Percent','Mining_GDP_Proxy']
    gov_cols    = ['Avg_FDI_Restriction_Index','Regulatory_Quality',
                   'CPI_Score','CPI_Rank','World Bank CPIA',
                   'IMF_Trade_Reform_Index','Domestic finance','External finance',
                   'Labor market','Product market',
                   'PRS International Country Risk Guide','DSTRI_Composite_Score']
    macro_cols  = ['GDP_Current_USD','GDP_log','GDP_Per_Capita_USD','GDP_Per_Capita_log',
                   'Population','Population_log',
                   'Trade_GDP_Percent','Inflation_CPI_Annual_Pct',
                   'Exchange_Rate_LCU_USD','Political_Stability_Score',
                   'Electricity_Access_Pct','Broadband_Per100',
                   'Oil_Price_Global_USD']
    eiti_cols   = ['Total_Revenue_USD','Total_Revenue_Local','Currency']
    region_cols = [c for c in base.columns
                   if c.startswith('Region_') or c.startswith('IncomeGroup_')]

    order   = id_cols+target_cols+resource_cols+gov_cols+macro_cols+eiti_cols+region_cols
    present = [c for c in order if c in base.columns]
    rest    = [c for c in base.columns if c not in present]
    base    = base[present + rest].sort_values(['ISO3','Year']).reset_index(drop=True)

    # ── 12. Coverage report ───────────────────────────────────────────────────
    coverage_report(base, "FULL DATASET COVERAGE")

    # ── 13. Save full dataset ─────────────────────────────────────────────────
    print(f"\nSTEP 11: Saving {FULL_OUTPUT} …")
    base.to_csv(FULL_OUTPUT, index=False)
    print(f"  ✓ {FULL_OUTPUT}")
    print(f"     Rows: {len(base):,}  |  Cols: {len(base.columns)}"
          f"  |  Countries: {base['ISO3'].nunique()}"
          f"  |  Years: {base['Year'].min()}–{base['Year'].max()}")

    # ── 14. EITI focused two-track ────────────────────────────────────────────
    print(f"\nSTEP 12: Building EITI focused track …")
    if 'Total_Revenue_USD' in base.columns:
        eiti_df = base.dropna(subset=['Total_Revenue_USD']).copy()
        eiti_df.to_csv(EITI_OUTPUT, index=False)
        print(f"  ✓ {EITI_OUTPUT}")
        print(f"     Rows: {len(eiti_df):,}  |  Countries: {eiti_df['ISO3'].nunique()}")
        print(f"     → Broad track  : {FULL_OUTPUT}  (all countries)")
        print(f"     → Focused track: {EITI_OUTPUT}  (EITI-reporting countries only)")
    else:
        print("  ⚠ Total_Revenue_USD not present — EITI track skipped")

    print("\n" + "="*70)
    print("✅ UPGRADED DATASET BUILT  →  next: build_lagged_features.py")
    print("="*70)


if __name__ == "__main__":
    main()
