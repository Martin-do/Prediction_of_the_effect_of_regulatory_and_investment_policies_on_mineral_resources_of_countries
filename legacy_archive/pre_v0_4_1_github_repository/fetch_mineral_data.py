import requests
import pandas as pd
import time

# =============================================================================
# WORLD BANK INDICATOR FETCH — PART 1 UPGRADE
# =============================================================================
# Run order: 1 of 3
# Output   : World_Bank_Indicators_Upgraded.csv
# =============================================================================

INDICATORS = {
    # Resource base
    'NY.GDP.PETR.RT.ZS': 'Oil_Rents_GDP_Percent',
    'NY.GDP.TOTL.RT.ZS': 'Total_NR_Rents_GDP_Percent',
    'NY.GDP.MINR.RT.ZS': 'Mineral_Rents_GDP_Percent',
    'NY.GDP.NGAS.RT.ZS': 'Gas_Rents_GDP_Percent',
    'NY.GDP.COAL.RT.ZS': 'Coal_Rents_GDP_Percent',
    # Market size / development
    'NY.GDP.MKTP.CD':    'GDP_Current_USD',
    'NY.GDP.PCAP.CD':    'GDP_Per_Capita_USD',
    'SP.POP.TOTL':       'Population',
    # Macro controls
    'NE.TRD.GNFS.ZS':   'Trade_GDP_Percent',
    'FP.CPI.TOTL.ZG':   'Inflation_CPI_Annual_Pct',
    'PA.NUS.FCRF':       'Exchange_Rate_LCU_USD',
    # Missing controls (political risk, infrastructure, connectivity)
    'PV.EST':            'Political_Stability_Score',
    'EG.ELC.ACCS.ZS':   'Electricity_Access_Pct',
    'IT.NET.BBND.P2':   'Broadband_Per100',
}

# Regional aggregate ISO3 codes — excluded from all fetches
REGIONAL_CODES = {
    'AFE','AFW','ARB','CEB','CSS','EAP','EAR','EAS','ECA','ECS',
    'EMU','EUU','FCS','HIC','HPC','IBD','IBT','IDA','IDB','IDX',
    'INX','LAC','LCN','LDC','LIC','LMC','LMY','LTE','MEA','MIC',
    'MNA','NAC','OED','OSS','PRE','PSS','PST','SAS','SSA','SSF',
    'SST','TEA','TEC','TLA','TMN','TSA','TSS','UMC','WLD'
}


def fetch_world_bank_data(indicator_code, indicator_name):
    print(f"Fetching {indicator_name} ({indicator_code})...")
    url = (f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
           f"?format=json&per_page=20000&date=1990:2025")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if len(data) < 2 or not data[1]:
                print("  No data returned.")
                return None

            records = []
            for entry in data[1]:
                iso3 = entry.get('countryiso3code', '')
                # Skip regional aggregates and entries with no value
                if not iso3 or iso3 in REGIONAL_CODES:
                    continue
                if entry.get('value') is None:
                    continue
                records.append({
                    'Country Name': entry['country']['value'],
                    'ISO3':         iso3,
                    'Year':         int(entry['date']),
                    indicator_name: entry['value'],
                })

            df = pd.DataFrame(records)
            print(f"  ✓ {len(df):,} country-year observations")
            return df

        except requests.exceptions.RequestException as e:
            print(f"  Error on attempt {attempt + 1}: {e}")
            time.sleep(2)

    return None


def main():
    print("=" * 60)
    print("WORLD BANK INDICATOR FETCH — PART 1 UPGRADE")
    print("=" * 60)

    dfs = []
    for code, name in INDICATORS.items():
        df = fetch_world_bank_data(code, name)
        if df is not None:
            dfs.append(df)
        time.sleep(0.8)

    if not dfs:
        print("✗ Failed to fetch any datasets.")
        return

    # Merge all indicators on ISO3 × Year
    master_df = dfs[0]
    for df in dfs[1:]:
        master_df = pd.merge(master_df, df, on=['Country Name', 'ISO3', 'Year'], how='outer')

    master_df = master_df.sort_values(['ISO3', 'Year']).reset_index(drop=True)

    output_file = 'World_Bank_Indicators_Upgraded.csv'
    master_df.to_csv(output_file, index=False)

    print(f"\n✅ Saved: {output_file}")
    print(f"   Rows      : {len(master_df):,}")
    print(f"   Countries : {master_df['ISO3'].nunique()}")
    print(f"   Year range: {master_df['Year'].min()}–{master_df['Year'].max()}")
    print(f"   Columns   : {list(master_df.columns)}")
    print("\nNext step: build_upgraded_dataset.py")


if __name__ == "__main__":
    main()
