# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python [conda env:base] *
#     language: python
#     name: conda-base-py
# ---

# %% editable=true slideshow={"slide_type": ""}
import pandas as pd
import numpy as np

# %%
# --- FILE NAMES (Ensure these match your local file names) ---
fdi_file = 'datasets/OECD.DAF.INV,DSD_FDIRRI_REG_DATABASE@DF_FDIRRI_REG_DATABASE,2.0+all.csv'


# =================================================================
# 1. INVESTMENT POLICY DATASETS (OECD FDI Index)
# =================================================================
print("Processing Investment Policy Data...")
fdi_df = pd.read_csv(fdi_file)

# A. Numerical FDI Data (For Regression/Classification)
inv_num_cols = ['REF_AREA', 'Reference area', 'ACTIVITY', 'Economic activity', 
                'POL_CAT', 'Policy category', 'TIME_PERIOD', 'OBS_VALUE']
investment_numerical = fdi_df[inv_num_cols].copy()
investment_numerical.rename(columns={
    'REF_AREA': 'ISO3', 
    'Reference area': 'Country', 
    'TIME_PERIOD': 'Year', 
    'OBS_VALUE': 'FDI_Restriction_Score'
}, inplace=True)
investment_numerical.to_csv('Investment_Policy_Numerical.csv', index=False)

# B. Text FDI Data (For NLP/LLM Training)
inv_text_cols = ['REF_AREA', 'Reference area', 'ACTIVITY', 'Economic activity', 
                 'POL_CAT', 'Policy category', 'TIME_PERIOD', 'EXPLANATORY_NOTES', 'LEG_PROV']
investment_text = fdi_df[inv_text_cols].copy()
investment_text.rename(columns={
    'REF_AREA': 'ISO3', 
    'Reference area': 'Country', 
    'TIME_PERIOD': 'Year', 
    'EXPLANATORY_NOTES': 'Policy_Description', 
    'LEG_PROV': 'Legal_Basis'
}, inplace=True)
investment_text.to_csv('Investment_Policy_Text.csv', index=False)

# %% [markdown]
# # check file shape

# %%
inv_text = pd.read_csv("Investment_Policy_Text.csv")
inv_num = pd.read_csv("Investment_Policy_Numerical.csv")
print(inv_text.shape)
inv_num.shape

# %%

# %% [markdown]
# ## AGGREGATING DATA

# %%
# import pandas as pd

# # --- 1. Load Files ---
# # Load your current Master Dataset (to use as the 'Anchor' for ISO codes)
# # Ensure you have this file in your working directory, or the code will fail at this step.
# # If you haven't created it yet, use the previous steps to generate it.
# try:
#     df_master = pd.read_csv('Master_Integrated_Dataset.csv')
# except FileNotFoundError:
#     print("Warning: 'Master_Integrated_Dataset.csv' not found. Please ensure it exists.")
#     # For demonstration, creating a dummy master if missing, but in your notebook, this should be real.
#     df_master = pd.DataFrame(columns=['Country Name', 'Country Code', 'Year']) 

# # Load the new datasets
# df_inv_policy = pd.read_csv('Investment_Policy_Numerical.csv')
# df_unctad = pd.read_csv('UNCTAD__US.FdiFlowsStock_20260118_145539.csv')

# # --- 2. Process Investment Policy Data (Aggregation) ---
# print("Aggregating Investment Policy Data...")

# # FIX: Convert FDI_Restriction_Score to numeric, coercing errors to NaN
# # This handles entries like "Not scored/considered"
# df_inv_policy['FDI_Restriction_Score'] = pd.to_numeric(df_inv_policy['FDI_Restriction_Score'], errors='coerce')

# # Check how many were converted to NaN (optional, for verification)
# # print(f"Non-numeric values converted to NaN: {df_inv_policy['FDI_Restriction_Score'].isna().sum()}")

# # We group by Country (ISO3) and Year, taking the average of the numeric restriction scores
# # This converts the data from "Sector-Level" to "National-Level"
# df_inv_agg = df_inv_policy.groupby(['ISO3', 'Year'])['FDI_Restriction_Score'].mean().reset_index()
# df_inv_agg.rename(columns={'FDI_Restriction_Score': 'Avg_FDI_Restriction_Index'}, inplace=True)

# # --- 3. Process UNCTAD Data (Name Mapping) ---
# print("Processing UNCTAD Data...")

# # Step A: Create a mapping dictionary from your Master Dataset (Name -> Code)
# # This ensures we use the exact ISO codes your analysis already relies on
# if not df_master.empty:
#     name_map = dict(zip(df_master['Country Name'], df_master['Country Code']))

#     # Step B: Apply mapping to UNCTAD
#     # Note: UNCTAD names might differ slightly. This maps exact matches.
#     df_unctad['ISO3'] = df_unctad['Economy_Label'].map(name_map)
# else:
#     print("Master dataset is empty or not loaded, skipping name mapping based on master.")
#     # Fallback or manual mapping would be needed here if master is truly missing.
#     df_unctad['ISO3'] = None

# # Step C: Filter out unmapped rows (e.g., 'World', 'G20', or unmatched names)
# # We calculate how many were lost to inform you
# missing_iso = df_unctad[df_unctad['ISO3'].isnull()]['Economy_Label'].unique()
# print(f"Note: {len(missing_iso)} entities in UNCTAD could not be mapped (mostly aggregates like 'World').")

# # Select and Rename columns
# # Only keep rows where we successfully found an ISO code
# df_unctad_clean = df_unctad.dropna(subset=['ISO3'])[['ISO3', 'Year', 'US_at_current_prices_in_millions_Value']]
# df_unctad_clean.rename(columns={'US_at_current_prices_in_millions_Value': 'FDI_Inflows_Stock_USD_Millions'}, inplace=True)

# # --- 4. Merge Everything into Master ---
# print("Merging into Master Dataset...")

# if not df_master.empty:
#     # Merge 1: Master + Investment Policy
#     # Left join ensures we don't lose any rows from your original study
#     master_v2 = pd.merge(
#         df_master,
#         df_inv_agg,
#         left_on=['Country Code', 'Year'],
#         right_on=['ISO3', 'Year'],
#         how='left'
#     )
#     # Cleanup duplicate keys
#     if 'ISO3' in master_v2.columns:
#         master_v2.drop(columns=['ISO3'], inplace=True)

#     # Merge 2: + UNCTAD FDI Data
#     final_dataset = pd.merge(
#         master_v2,
#         df_unctad_clean,
#         left_on=['Country Code', 'Year'],
#         right_on=['ISO3', 'Year'],
#         how='left'
#     )
#     # Cleanup duplicate keys
#     if 'ISO3' in final_dataset.columns:
#         final_dataset.drop(columns=['ISO3'], inplace=True)

#     # --- 5. Export ---
#     output_filename = 'Master_Dataset_With_FDI.csv'
#     final_dataset.to_csv(output_filename, index=False)

#     print("-" * 30)
#     print(f"Integration Complete!")
#     print(f"New variables added: 'Avg_FDI_Restriction_Index', 'FDI_Inflows_Stock_USD_Millions'")
#     print(f"Saved to: {output_filename}")
#     print(f"Total Rows: {len(final_dataset)}")
#     print(final_dataset.head())
# else:
#     print("Skipping merge because Master Dataset is empty.")

# %%

# %% [markdown]
# ## VISUALIZING GAPS

# %%
# import pandas as pd
# import seaborn as sns
# import matplotlib.pyplot as plt

# # Load your dataset
# df = pd.read_csv('Master_Dataset_With_FDI.csv')

# # Visualize the sparsity of the data
# plt.figure(figsize=(12, 8))
# sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
# plt.title('Missing Value Map (Yellow indicates missing data)')
# plt.show()

# %%

# %% [markdown]
# ## TEMPORRAL IMPUTATION

# %%
# # Sort by country and year to ensure filling happens chronologically
# df = df.sort_values(['Country Code', 'Year'])

# # Identify numeric columns to fill (excluding Year)
# cols_to_fill = df.select_dtypes(include=['float64', 'int64']).columns.drop('Year')

# # Forward fill and then backward fill within each country group
# # This ensures that if a policy was enacted in 2014, it is applied to 2015-2023
# df[cols_to_fill] = df.groupby('Country Code')[cols_to_fill].ffill().bfill()

# print(f"Missing values after imputation: {df['Domestic finance'].isnull().sum()}")

# %%

# %% [markdown]
# ## FEATURER ENGINEERING CREATING COMPOSITE INDICES

# %%
# # Identify the policy columns (the numbered ones)
# policy_cols = [c for c in df.columns if any(char.isdigit() for char in c) and '_' in c]

# # Create an 'Aggregate Policy Openness' score
# df['Investment_Openness_Score'] = df[policy_cols].mean(axis=1)

# # Create category scores (e.g., all columns starting with '6' are usually one category)
# df['Telecom_Infrastructure_Score'] = df[[c for c in policy_cols if c.startswith('6_')]].mean(axis=1)
# df['Business_Environment_Score'] = df[[c for c in policy_cols if c.startswith('7_')]].mean(axis=1)

# print("New composite features created.")

# %%

# %% [markdown]
# ## MERGINF FDI DATA FROM UNCTAD

# %%
# import pandas as pd

# # 1. Load the files
# master = pd.read_csv('Master_Dataset_With_FDI.csv')
# unctad = pd.read_csv('US.FdiFlowsStock_20260125_165417.csv')

# # 2. Map country names to ensure a high match rate
# mapping = {
#     'Bolivia': 'Bolivia (Plurinational State of)',
#     'Congo, Dem. Rep.': 'Democratic Republic of the Congo',
#     'Korea, Rep.': 'Republic of Korea',
#     'Tanzania': 'United Republic of Tanzania',
#     'Vietnam': 'Viet Nam',
#     'Egypt, Arab Rep.': 'Egypt',
#     'Turkiye': 'Türkiye'
# }
# master['Country_Match'] = master['Country Name'].replace(mapping)

# # 3. Merge the FDI data
# df_merged = pd.merge(
#     master.drop(columns=['FDI_Inflows_Stock_USD_Millions']),
#     unctad[['Economy_Label', 'Year', 'US_at_current_prices_in_millions_Value']],
#     left_on=['Country_Match', 'Year'],
#     right_on=['Economy_Label', 'Year'],
#     how='left'
# )

# # 4. Cleanup and Rename
# df_final = df_merged.rename(columns={'US_at_current_prices_in_millions_Value': 'FDI_Inflows_Stock_USD_Millions'})
# df_final = df_final.drop(columns=['Country_Match', 'Economy_Label'])

# # 5. Temporal Imputation (Forward-Fill within countries)
# # This fills the gaps where policy data only existed for one year
# df_final = df_final.sort_values(['Country Code', 'Year'])
# numeric_cols = df_final.select_dtypes(include=['float64', 'int64']).columns.drop('Year')
# df_final[numeric_cols] = df_final.groupby('Country Code')[numeric_cols].ffill().bfill()

# # 6. Final Save
# df_final.to_csv('ML_Ready_Investment_Dataset.csv', index=False)
# print("Dataset is now ready for analysis!")

# %%

# %% [markdown]
# ## AGGRREGATING WITH A CLEANER UNCTAD FILE

# %%
import pandas as pd

# --- 1. Load the Datasets ---
# New UNCTAD file
unctad_file = 'US.FdiFlowsStock_20260125_165417.csv'
df_unctad = pd.read_csv(unctad_file)

# Investment Policy file (Will serve as both Data and Dictionary)
inv_file = 'Investment_Policy_Numerical.csv'
df_inv_policy = pd.read_csv(inv_file)

# --- 2. Create the Country Mapping Dictionary (The Fix) ---
# We use the Investment Policy dataset to build the Name -> Code map
# This replaces the need for the missing Regulatory dataset
country_map = df_inv_policy[['Country', 'ISO3']].drop_duplicates().set_index('Country')['ISO3'].to_dict()

# --- 3. Process UNCTAD Data ---
print("Processing UNCTAD FDI Data...")

# Map Country Names to ISO Codes using our new map
df_unctad['ISO3'] = df_unctad['Economy_Label'].map(country_map)

# Keep only rows where we successfully found a Country Code
# (This filters out aggregates like "World" or countries not in your study)
df_unctad_clean = df_unctad.dropna(subset=['ISO3']).copy()

# Select and rename columns
df_unctad_clean = df_unctad_clean[['ISO3', 'Year', 'US_at_current_prices_in_millions_Value']]
df_unctad_clean.rename(columns={'US_at_current_prices_in_millions_Value': 'FDI_Flows_Millions_USD'}, inplace=True)

# Ensure Year is integer
df_unctad_clean['Year'] = pd.to_numeric(df_unctad_clean['Year'], errors='coerce')
df_unctad_clean = df_unctad_clean.dropna(subset=['Year'])
df_unctad_clean['Year'] = df_unctad_clean['Year'].astype(int)

# --- 4. Process Investment Policy Data ---
print("Processing Investment Policy Data...")

# Convert Restriction Score to numeric (handling "Not scored" text)
df_inv_policy['FDI_Restriction_Score'] = pd.to_numeric(df_inv_policy['FDI_Restriction_Score'], errors='coerce')

# Aggregate: Calculate Mean Score per Country per Year
df_inv_agg = df_inv_policy.groupby(['ISO3', 'Year'])['FDI_Restriction_Score'].mean().reset_index()
df_inv_agg.rename(columns={'FDI_Restriction_Score': 'Avg_FDI_Restriction_Index'}, inplace=True)
df_inv_agg['Year'] = df_inv_agg['Year'].astype(int)

# --- 5. Merge the Datasets (Investment Only) ---
print("Merging Investment Datasets...")

# Outer join ensures we keep all investment data available
investment_dataset = pd.merge(
    df_inv_agg,
    df_unctad_clean,
    on=['ISO3', 'Year'],
    how='outer'
)

# Add Country Names back for readability
# We reverse the map we created earlier
iso_to_name = {v: k for k, v in country_map.items()}
investment_dataset['Country Name'] = investment_dataset['ISO3'].map(iso_to_name)

# Reorder columns
cols = ['Country Name', 'ISO3', 'Year', 'Avg_FDI_Restriction_Index', 'FDI_Flows_Millions_USD']
investment_dataset = investment_dataset[cols]

# --- 6. Save ---
output_file = 'Investment_FDI_Dataset.csv'
investment_dataset.to_csv(output_file, index=False)

print("-" * 30)
print("SUCCESS: Investment Dataset Created (Without Regulatory Data)")
print(f"File Saved: {output_file}")
print(f"Total Rows: {len(investment_dataset)}")
print(investment_dataset.head())

# %%

# %% [markdown]
# ## Merging mineral resources with regulatory dataset

# %%
"""
SEPARATE MASTER DATASETS: REGULATORY vs INVESTMENT
===================================================
This script creates TWO independent master datasets:

1. REGULATORY_MASTER = Regulatory policies + Minerals
   → For analyzing: How regulatory policies affect mineral resources

2. INVESTMENT_MASTER = Investment policies + Minerals
   → For analyzing: How investment policies affect mineral resources

Author: Your Name
Date: February 2026
"""

import pandas as pd
import numpy as np

print("="*80)
print("CREATING TWO SEPARATE MASTER DATASETS")
print("="*80)

# ============================================================================
# PART 1: CLEAN MINERAL DATASETS (Same for Both)
# ============================================================================

print("\nPART 1: CLEANING MINERAL DATASETS")
print("-"*80)

# Load original datasets
print("\n1. Loading original datasets...")
minerals_raw = pd.read_csv('Mineral_Resources_Dataset.csv')
eiti_raw = pd.read_csv('EITI_Governance_Dataset.csv')

print(f"   ✓ Minerals (raw): {minerals_raw.shape}")
print(f"   ✓ EITI (raw): {eiti_raw.shape}")

# Remove regional aggregates from minerals
print("\n2. Removing regional aggregates...")

regional_codes = [
    'AFE', 'AFW', 'ARB', 'CEB', 'CSS', 'EAP', 'EAR', 'EAS', 'ECA', 'ECS', 
    'EMU', 'EUU', 'FCS', 'HIC', 'HPC', 'IBD', 'IBT', 'IDA', 'IDB', 'IDX',
    'INX', 'LAC', 'LCN', 'LDC', 'LIC', 'LMC', 'LMY', 'LTE', 'MEA', 'MIC',
    'MNA', 'NAC', 'OED', 'OSS', 'PRE', 'PSS', 'PST', 'SAS', 'SSA', 'SSF',
    'SST', 'TEA', 'TEC', 'TLA', 'TMN', 'TSA', 'TSS', 'UMC', 'WLD'
]

before = len(minerals_raw)
minerals = minerals_raw[~minerals_raw['Country Code'].isin(regional_codes)].copy()
removed = before - len(minerals)

print(f"   Removed {removed:,} regional rows")
print(f"   Remaining: {len(minerals):,} country observations")

# Standardize column names
print("\n3. Standardizing column names...")

minerals = minerals.rename(columns={
    'Country Code': 'ISO3',
    'Mineral_Rents_Percent_GDP': 'Mineral_Rents_GDP_Percent'
})

eiti = eiti_raw.rename(columns={
    'Country Code': 'ISO3'
})

print(f"   ✓ Renamed 'Country Code' to 'ISO3' in both datasets")

# Ensure Year is integer
minerals['Year'] = minerals['Year'].astype(int)
eiti['Year'] = eiti['Year'].astype(int)

print(f"   ✓ Year columns are integers")

# Save cleaned versions for reference
minerals.to_csv('Mineral_Resources_Clean.csv', index=False)
eiti.to_csv('EITI_Governance_Clean.csv', index=False)

print(f"\n   ✓ Saved cleaned datasets for reference")

# ============================================================================
# PART 2: CREATE INVESTMENT MASTER DATASET
# ============================================================================

print("\n" + "="*80)
print("PART 2: CREATING INVESTMENT MASTER DATASET")
print("-"*80)

# Load investment data
print("\n4. Loading Investment policy dataset...")
investment = pd.read_csv('Investment_FDI_Dataset.csv')
print(f"   ✓ Investment: {investment.shape}")

# Merge with minerals (World Bank)
print("\n5. Merging Investment + World Bank minerals...")

investment_master = investment.merge(
    minerals[['ISO3', 'Year', 'Country Name', 'Mineral_Rents_GDP_Percent']],
    on=['ISO3', 'Year'],
    how='left',
    suffixes=('', '_minerals')
)

# Handle duplicate Country Name columns if they exist
if 'Country Name_minerals' in investment_master.columns:
    investment_master['Country Name'] = investment_master['Country Name'].fillna(
        investment_master['Country Name_minerals']
    )
    investment_master = investment_master.drop(columns=['Country Name_minerals'])

print(f"   ✓ Merged shape: {investment_master.shape}")
print(f"   ✓ Rows with mineral data: {investment_master['Mineral_Rents_GDP_Percent'].notna().sum():,}")

# Add EITI data
print("\n6. Adding EITI revenue data...")

investment_master = investment_master.merge(
    eiti[['ISO3', 'Year', 'Total_Revenue_USD', 'Total_Revenue_Local', 'Currency']],
    on=['ISO3', 'Year'],
    how='left'
)

print(f"   ✓ Rows with EITI data: {investment_master['Total_Revenue_USD'].notna().sum():,}")

# Add derived variables
print("\n7. Adding derived mineral variables...")

# Resource-rich flag (>5% GDP from minerals)
investment_master['Resource_Rich'] = (
    investment_master['Mineral_Rents_GDP_Percent'] >= 5.0
).astype(int)
investment_master.loc[investment_master['Mineral_Rents_GDP_Percent'].isna(), 'Resource_Rich'] = np.nan

# Has mineral data flag
investment_master['Has_Mineral_Data'] = (
    investment_master['Mineral_Rents_GDP_Percent'].notna()
).astype(int)

# Resource category
investment_master['Resource_Category'] = pd.cut(
    investment_master['Mineral_Rents_GDP_Percent'],
    bins=[0, 1, 5, 10, 100],
    labels=['Minimal', 'Low', 'Moderate', 'High']
)

print(f"   ✓ Added: Resource_Rich, Has_Mineral_Data, Resource_Category")

# Save Investment Master
print("\n8. Saving INVESTMENT MASTER dataset...")

investment_master.to_csv('INVESTMENT_MASTER.csv', index=False)

print(f"   ✓ Saved: INVESTMENT_MASTER.csv")
print(f"   ✓ Final shape: {investment_master.shape}")
print(f"   ✓ Countries: {investment_master['ISO3'].nunique()}")
print(f"   ✓ Year range: {investment_master['Year'].min()}-{investment_master['Year'].max()}")

# ============================================================================
# PART 3: CREATE REGULATORY MASTER DATASET
# ============================================================================

print("\n" + "="*80)
print("PART 3: CREATING REGULATORY MASTER DATASET")
print("-"*80)

# Load regulatory data
print("\n9. Loading Regulatory policy dataset...")
regulatory = pd.read_csv('Regulatory_Dataset_Clustered.csv')
print(f"   ✓ Regulatory: {regulatory.shape}")

# Standardize column name if needed
if 'Country Code' in regulatory.columns and 'ISO3' not in regulatory.columns:
    regulatory = regulatory.rename(columns={'Country Code': 'ISO3'})
    print(f"   ✓ Renamed 'Country Code' to 'ISO3'")

# Merge with minerals (World Bank)
print("\n10. Merging Regulatory + World Bank minerals...")

regulatory_master = regulatory.merge(
    minerals[['ISO3', 'Year', 'Country Name', 'Mineral_Rents_GDP_Percent']],
    on=['ISO3', 'Year'],
    how='left',
    suffixes=('', '_minerals')
)

# Handle duplicate Country Name columns if they exist
if 'Country Name_minerals' in regulatory_master.columns:
    regulatory_master['Country Name'] = regulatory_master['Country Name'].fillna(
        regulatory_master['Country Name_minerals']
    )
    regulatory_master = regulatory_master.drop(columns=['Country Name_minerals'])

print(f"   ✓ Merged shape: {regulatory_master.shape}")
print(f"   ✓ Rows with mineral data: {regulatory_master['Mineral_Rents_GDP_Percent'].notna().sum():,}")

# Add EITI data
print("\n11. Adding EITI revenue data...")

regulatory_master = regulatory_master.merge(
    eiti[['ISO3', 'Year', 'Total_Revenue_USD', 'Total_Revenue_Local', 'Currency']],
    on=['ISO3', 'Year'],
    how='left'
)

print(f"   ✓ Rows with EITI data: {regulatory_master['Total_Revenue_USD'].notna().sum():,}")

# Add derived variables
print("\n12. Adding derived mineral variables...")

# Resource-rich flag
regulatory_master['Resource_Rich'] = (
    regulatory_master['Mineral_Rents_GDP_Percent'] >= 5.0
).astype(int)
regulatory_master.loc[regulatory_master['Mineral_Rents_GDP_Percent'].isna(), 'Resource_Rich'] = np.nan

# Has mineral data flag
regulatory_master['Has_Mineral_Data'] = (
    regulatory_master['Mineral_Rents_GDP_Percent'].notna()
).astype(int)

# Resource category
regulatory_master['Resource_Category'] = pd.cut(
    regulatory_master['Mineral_Rents_GDP_Percent'],
    bins=[0, 1, 5, 10, 100],
    labels=['Minimal', 'Low', 'Moderate', 'High']
)

print(f"   ✓ Added: Resource_Rich, Has_Mineral_Data, Resource_Category")

# Save Regulatory Master
print("\n13. Saving REGULATORY MASTER dataset...")

regulatory_master.to_csv('REGULATORY_MASTER.csv', index=False)

print(f"   ✓ Saved: REGULATORY_MASTER.csv")
print(f"   ✓ Final shape: {regulatory_master.shape}")
print(f"   ✓ Countries: {regulatory_master['ISO3'].nunique()}")
print(f"   ✓ Year range: {regulatory_master['Year'].min()}-{regulatory_master['Year'].max()}")

# ============================================================================
# PART 4: COMPARATIVE SUMMARY STATISTICS
# ============================================================================

print("\n" + "="*80)
print("PART 4: SUMMARY STATISTICS - BOTH DATASETS")
print("-"*80)

print("\n" + "="*40 + " INVESTMENT MASTER " + "="*40)
print(f"\nDATASET OVERVIEW:")
print(f"   Total observations: {len(investment_master):,}")
print(f"   Countries: {investment_master['ISO3'].nunique()}")
print(f"   Year range: {investment_master['Year'].min()}-{investment_master['Year'].max()}")

print(f"\nKEY VARIABLE COVERAGE:")
print(f"   FDI Restriction Index: {investment_master['Avg_FDI_Restriction_Index'].notna().sum():,} ({investment_master['Avg_FDI_Restriction_Index'].notna().sum()/len(investment_master)*100:.1f}%)")
print(f"   FDI Flows: {investment_master['FDI_Flows_Millions_USD'].notna().sum():,} ({investment_master['FDI_Flows_Millions_USD'].notna().sum()/len(investment_master)*100:.1f}%)")
print(f"   Mineral Rents (WB): {investment_master['Mineral_Rents_GDP_Percent'].notna().sum():,} ({investment_master['Mineral_Rents_GDP_Percent'].notna().sum()/len(investment_master)*100:.1f}%)")
print(f"   Mining Revenue (EITI): {investment_master['Total_Revenue_USD'].notna().sum():,} ({investment_master['Total_Revenue_USD'].notna().sum()/len(investment_master)*100:.1f}%)")

complete_inv = investment_master.dropna(subset=['Avg_FDI_Restriction_Index', 'Mineral_Rents_GDP_Percent'])
print(f"\nCOMPLETE CASES (Investment Policy + Minerals):")
print(f"   Observations: {len(complete_inv):,}")
print(f"   Countries: {complete_inv['ISO3'].nunique()}")

print("\n" + "="*40 + " REGULATORY MASTER " + "="*40)
print(f"\nDATASET OVERVIEW:")
print(f"   Total observations: {len(regulatory_master):,}")
print(f"   Countries: {regulatory_master['ISO3'].nunique()}")
print(f"   Year range: {regulatory_master['Year'].min()}-{regulatory_master['Year'].max()}")

print(f"\nKEY VARIABLE COVERAGE:")
print(f"   Regulatory Quality: {regulatory_master['Regulatory_Quality'].notna().sum():,} ({regulatory_master['Regulatory_Quality'].notna().sum()/len(regulatory_master)*100:.1f}%)")
if 'CPI_Score' in regulatory_master.columns:
    print(f"   CPI Score: {regulatory_master['CPI_Score'].notna().sum():,} ({regulatory_master['CPI_Score'].notna().sum()/len(regulatory_master)*100:.1f}%)")
print(f"   Mineral Rents (WB): {regulatory_master['Mineral_Rents_GDP_Percent'].notna().sum():,} ({regulatory_master['Mineral_Rents_GDP_Percent'].notna().sum()/len(regulatory_master)*100:.1f}%)")
print(f"   Mining Revenue (EITI): {regulatory_master['Total_Revenue_USD'].notna().sum():,} ({regulatory_master['Total_Revenue_USD'].notna().sum()/len(regulatory_master)*100:.1f}%)")

complete_reg = regulatory_master.dropna(subset=['Regulatory_Quality', 'Mineral_Rents_GDP_Percent'])
print(f"\nCOMPLETE CASES (Regulatory Policy + Minerals):")
print(f"   Observations: {len(complete_reg):,}")
print(f"   Countries: {complete_reg['ISO3'].nunique()}")

# Resource-rich countries in each dataset
print(f"\n" + "="*80)
print("RESOURCE-RICH COUNTRIES (>5% GDP from minerals)")
print("-"*80)

inv_resource_rich = investment_master[investment_master['Resource_Rich'] == 1]['ISO3'].unique()
reg_resource_rich = regulatory_master[regulatory_master['Resource_Rich'] == 1]['ISO3'].unique()

print(f"\nIn Investment Master: {len(inv_resource_rich)} countries")
print(f"   {sorted(inv_resource_rich)}")

print(f"\nIn Regulatory Master: {len(reg_resource_rich)} countries")
print(f"   {sorted(reg_resource_rich)}")

# Top 10 mineral countries in each
print(f"\n" + "="*80)
print("TOP 10 MINERAL-DEPENDENT COUNTRIES IN EACH DATASET")
print("-"*80)

print("\nINVESTMENT MASTER - Top 10:")
inv_recent = investment_master.sort_values('Year').groupby('ISO3').tail(1)
inv_top10 = inv_recent.nlargest(10, 'Mineral_Rents_GDP_Percent')[
    ['ISO3', 'Country Name', 'Year', 'Mineral_Rents_GDP_Percent', 'Avg_FDI_Restriction_Index']
]
print(inv_top10.to_string(index=False))

print("\nREGULATORY MASTER - Top 10:")
reg_recent = regulatory_master.sort_values('Year').groupby('ISO3').tail(1)
reg_top10 = reg_recent.nlargest(10, 'Mineral_Rents_GDP_Percent')[
    ['ISO3', 'Country Name', 'Year', 'Mineral_Rents_GDP_Percent', 'Regulatory_Quality']
]
print(reg_top10.to_string(index=False))

# ============================================================================
# PART 5: SAVE DETAILED SUMMARY REPORTS
# ============================================================================

print("\n14. Saving detailed summary reports...")

# Investment Master Summary
with open('INVESTMENT_MASTER_Summary.txt', 'w') as f:
    f.write("INVESTMENT MASTER DATASET - SUMMARY REPORT\n")
    f.write("="*80 + "\n\n")
    
    f.write("RESEARCH QUESTION:\n")
    f.write("How do investment policies (FDI restrictions, flows) affect mineral resources?\n\n")
    
    f.write("DATASET:\n")
    f.write(f"File: INVESTMENT_MASTER.csv\n")
    f.write(f"Observations: {len(investment_master):,}\n")
    f.write(f"Countries: {investment_master['ISO3'].nunique()}\n")
    f.write(f"Year range: {investment_master['Year'].min()}-{investment_master['Year'].max()}\n\n")
    
    f.write("KEY VARIABLES:\n")
    f.write("-"*80 + "\n")
    f.write("INDEPENDENT VARIABLES (Investment Policies):\n")
    f.write("  - Avg_FDI_Restriction_Index: How restricted is foreign investment?\n")
    f.write("  - FDI_Flows_Millions_USD: Actual investment flows\n\n")
    
    f.write("DEPENDENT VARIABLES (Mineral Outcomes):\n")
    f.write("  - Mineral_Rents_GDP_Percent: Mineral sector size (% of GDP)\n")
    f.write("  - Total_Revenue_USD: Government mining revenues (EITI)\n\n")
    
    f.write("CONTROL/CLASSIFICATION VARIABLES:\n")
    f.write("  - Resource_Rich: Binary (1 if >5% GDP from minerals)\n")
    f.write("  - Resource_Category: Minimal/Low/Moderate/High\n")
    f.write("  - Has_Mineral_Data: Binary (1 if mineral data available)\n\n")
    
    f.write("DATA COVERAGE:\n")
    f.write("-"*80 + "\n")
    f.write(f"FDI Restriction Index: {investment_master['Avg_FDI_Restriction_Index'].notna().sum():,} obs\n")
    f.write(f"Mineral Rents: {investment_master['Mineral_Rents_GDP_Percent'].notna().sum():,} obs\n")
    f.write(f"Complete cases: {len(complete_inv):,} obs ({complete_inv['ISO3'].nunique()} countries)\n\n")
    
    f.write("TOP 10 MINERAL-DEPENDENT COUNTRIES:\n")
    f.write("-"*80 + "\n")
    f.write(inv_top10.to_string(index=False))
    
    f.write("\n\nSUGGESTED ANALYSES:\n")
    f.write("-"*80 + "\n")
    f.write("1. Does FDI openness increase mineral production?\n")
    f.write("2. Do resource-rich countries attract more/less FDI?\n")
    f.write("3. How do mineral prices affect FDI policy changes?\n")

# Regulatory Master Summary
with open('REGULATORY_MASTER_Summary.txt', 'w') as f:
    f.write("REGULATORY MASTER DATASET - SUMMARY REPORT\n")
    f.write("="*80 + "\n\n")
    
    f.write("RESEARCH QUESTION:\n")
    f.write("How do regulatory policies (quality, reforms, transparency) affect mineral resources?\n\n")
    
    f.write("DATASET:\n")
    f.write(f"File: REGULATORY_MASTER.csv\n")
    f.write(f"Observations: {len(regulatory_master):,}\n")
    f.write(f"Countries: {regulatory_master['ISO3'].nunique()}\n")
    f.write(f"Year range: {regulatory_master['Year'].min()}-{regulatory_master['Year'].max()}\n\n")
    
    f.write("KEY VARIABLES:\n")
    f.write("-"*80 + "\n")
    f.write("INDEPENDENT VARIABLES (Regulatory Policies):\n")
    f.write("  - Regulatory_Quality: World Bank governance indicator\n")
    f.write("  - CPI_Score: Corruption Perceptions Index\n")
    f.write("  - IMF Reform Indices: Trade, finance, labor, product market\n")
    f.write("  - OECD Digital Trade barriers\n\n")
    
    f.write("DEPENDENT VARIABLES (Mineral Outcomes):\n")
    f.write("  - Mineral_Rents_GDP_Percent: Mineral sector size (% of GDP)\n")
    f.write("  - Total_Revenue_USD: Government mining revenues (EITI)\n\n")
    
    f.write("CONTROL/CLASSIFICATION VARIABLES:\n")
    f.write("  - Resource_Rich: Binary (1 if >5% GDP from minerals)\n")
    f.write("  - Resource_Category: Minimal/Low/Moderate/High\n")
    f.write("  - Regional and income-level dummies\n\n")
    
    f.write("DATA COVERAGE:\n")
    f.write("-"*80 + "\n")
    f.write(f"Regulatory Quality: {regulatory_master['Regulatory_Quality'].notna().sum():,} obs\n")
    f.write(f"Mineral Rents: {regulatory_master['Mineral_Rents_GDP_Percent'].notna().sum():,} obs\n")
    f.write(f"Complete cases: {len(complete_reg):,} obs ({complete_reg['ISO3'].nunique()} countries)\n\n")
    
    f.write("TOP 10 MINERAL-DEPENDENT COUNTRIES:\n")
    f.write("-"*80 + "\n")
    f.write(reg_top10.to_string(index=False))
    
    f.write("\n\nSUGGESTED ANALYSES:\n")
    f.write("-"*80 + "\n")
    f.write("1. Does regulatory quality improve mining revenue collection?\n")
    f.write("2. Do transparency reforms (EITI) increase government receipts?\n")
    f.write("3. How do structural reforms affect mineral sector growth?\n")
    f.write("4. Resource curse: Do minerals worsen governance?\n")

print(f"   ✓ Saved: INVESTMENT_MASTER_Summary.txt")
print(f"   ✓ Saved: REGULATORY_MASTER_Summary.txt")

# ============================================================================
# FINAL MESSAGE
# ============================================================================

print("\n" + "="*80)
print("✅ COMPLETE! TWO SEPARATE MASTER DATASETS CREATED!")
print("="*80)

print("\nFILES CREATED:")
print("\n📊 MAIN ANALYSIS FILES:")
print("   1. INVESTMENT_MASTER.csv")
print("      → Use for: Investment policies → Mineral outcomes")
print(f"      → {len(investment_master):,} observations, {investment_master['ISO3'].nunique()} countries")
print()
print("   2. REGULATORY_MASTER.csv")
print("      → Use for: Regulatory policies → Mineral outcomes")
print(f"      → {len(regulatory_master):,} observations, {regulatory_master['ISO3'].nunique()} countries")

print("\n📄 SUMMARY REPORTS:")
print("   3. INVESTMENT_MASTER_Summary.txt - Detailed summary for investment analysis")
print("   4. REGULATORY_MASTER_Summary.txt - Detailed summary for regulatory analysis")

print("\n📁 REFERENCE FILES:")
print("   5. Mineral_Resources_Clean.csv - Cleaned World Bank data")
print("   6. EITI_Governance_Clean.csv - Cleaned EITI data")

print("\n" + "="*80)
print("🎯 YOUR TWO RESEARCH QUESTIONS:")
print("="*80)
print("\n1. INVESTMENT ANALYSIS (use INVESTMENT_MASTER.csv):")
print("   How do FDI restrictions and investment flows affect mineral resources?")
print("   → Model: Mineral_Outcomes = f(FDI_Policies, Controls)")

print("\n2. REGULATORY ANALYSIS (use REGULATORY_MASTER.csv):")
print("   How do regulatory quality, transparency, and reforms affect mineral resources?")
print("   → Model: Mineral_Outcomes = f(Regulatory_Policies, Controls)")

print("\n" + "="*80)
print("✅ READY FOR ANALYSIS!")
print("="*80)

print("\n🎯 NEXT STEPS:")
print("   1. Review: INVESTMENT_MASTER_Summary.txt")
print("   2. Review: REGULATORY_MASTER_Summary.txt")
print("   3. Open each CSV file to verify merge worked correctly")
print("   4. Show both summary files to your supervisor")
print("   5. Begin separate analyses for each research question")

print("\n" + "="*80)

# %%

# %% [markdown]
# ## Handling data leakage and some other isssuess

# %%
"""
FIX INVESTMENT DATASET FOR MACHINE LEARNING
============================================
This script applies all critical fixes to make your dataset ML-ready.

Fixes applied:
1. Removes data leakage (Resource_Rich, Resource_Category)
2. Drops sparse columns (EITI variables)
3. Creates clean ML-ready dataset
4. Generates both regression and classification versions
5. Provides train/test splits

Run this script, then use the output files for ML!
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

print("="*80)
print("FIXING INVESTMENT DATASET FOR MACHINE LEARNING")
print("="*80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print("\nSTEP 1: Loading data...")
df = pd.read_csv('INVESTMENT_MASTER_REFINED.csv')
print(f"   Original shape: {df.shape}")

# ============================================================================
# STEP 2: REMOVE SPARSE COLUMNS (>90% missing)
# ============================================================================

print("\nSTEP 2: Removing sparse columns...")
sparse_cols = ['Total_Revenue_USD', 'Total_Revenue_Local', 'Currency']

print(f"   Dropping: {sparse_cols}")
df_clean = df.drop(columns=sparse_cols)
print(f"   New shape: {df_clean.shape}")

# ============================================================================
# STEP 3: IDENTIFY VALID FEATURES (NO DATA LEAKAGE!)
# ============================================================================

print("\nSTEP 3: Identifying valid features...")

# These are SAFE to use (independent variables)
valid_features = [
    'Avg_FDI_Restriction_Index',
    'FDI_Flows_Millions_USD'
]

# These CAUSE DATA LEAKAGE - DO NOT USE!
leakage_cols = [
    'Resource_Rich',          # Derived from target (>5% threshold)
    'Resource_Category',      # Derived from target
    'Has_Mineral_Data'        # Derived from target being non-null
]

# These are for identification only
id_cols = ['Country Name', 'ISO3', 'Year']

# This is the target
target_col = 'Mineral_Rents_GDP_Percent'

print(f"   ✓ Valid features: {valid_features}")
print(f"   ✗ Leakage columns (excluded): {leakage_cols}")

# ============================================================================
# STEP 4: CREATE REGRESSION DATASET
# ============================================================================

print("\nSTEP 4: Creating REGRESSION dataset...")

# Select columns for regression
regression_cols = id_cols + valid_features + [target_col]
df_regression = df_clean[regression_cols].copy()

# Remove rows with missing values
before = len(df_regression)
df_regression = df_regression.dropna()
after = len(df_regression)

print(f"   Removed {before - after} rows with missing values")
print(f"   Final regression dataset: {df_regression.shape}")

# Add log-transformed target (for models that need it)
df_regression['Mineral_Rents_Log'] = np.log1p(df_regression[target_col])

# Add scaled features (for models that need it)
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
df_regression[['FDI_Restriction_Scaled', 'FDI_Flows_Scaled']] = scaler.fit_transform(
    df_regression[valid_features]
)

# Save
df_regression.to_csv('INVESTMENT_ML_REGRESSION.csv', index=False)
print(f"   ✓ Saved: INVESTMENT_ML_REGRESSION.csv")

# ============================================================================
# STEP 5: CREATE CLASSIFICATION DATASET
# ============================================================================

print("\nSTEP 5: Creating CLASSIFICATION dataset...")

# Create binary target: Resource-rich (≥5%) or not
df_classification = df_regression.copy()
df_classification['Resource_Rich_Target'] = (
    df_classification[target_col] >= 5.0
).astype(int)

# Check class balance
class_counts = df_classification['Resource_Rich_Target'].value_counts()
print(f"\n   Class distribution:")
print(f"      Not resource-rich (0): {class_counts[0]} ({class_counts[0]/len(df_classification)*100:.1f}%)")
print(f"      Resource-rich (1):     {class_counts[1]} ({class_counts[1]/len(df_classification)*100:.1f}%)")
print(f"      Imbalance ratio: {class_counts[0]/class_counts[1]:.1f}:1")

# Save
df_classification.to_csv('INVESTMENT_ML_CLASSIFICATION.csv', index=False)
print(f"   ✓ Saved: INVESTMENT_ML_CLASSIFICATION.csv")

# ============================================================================
# STEP 6: CREATE TRAIN/TEST SPLITS
# ============================================================================

print("\nSTEP 6: Creating train/test splits...")

# For REGRESSION
X_reg = df_regression[valid_features]
y_reg = df_regression['Mineral_Rents_Log']  # Use log-transformed target

X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
    X_reg, y_reg, test_size=0.2, random_state=42
)

print(f"\n   REGRESSION splits:")
print(f"      Training set: {X_train_reg.shape[0]} observations")
print(f"      Test set: {X_test_reg.shape[0]} observations")

# For CLASSIFICATION (with stratification)
X_cls = df_classification[valid_features]
y_cls = df_classification['Resource_Rich_Target']

X_train_cls, X_test_cls, y_train_cls, y_test_cls = train_test_split(
    X_cls, y_cls, test_size=0.2, random_state=42, stratify=y_cls
)

print(f"\n   CLASSIFICATION splits (stratified):")
print(f"      Training set: {X_train_cls.shape[0]} observations")
print(f"         Class 0: {(y_train_cls==0).sum()}")
print(f"         Class 1: {(y_train_cls==1).sum()}")
print(f"      Test set: {X_test_cls.shape[0]} observations")
print(f"         Class 0: {(y_test_cls==0).sum()}")
print(f"         Class 1: {(y_test_cls==1).sum()}")

# ============================================================================
# STEP 7: GENERATE SUMMARY STATISTICS
# ============================================================================

print("\nSTEP 7: Generating summary statistics...")

summary = {
    'Dataset': ['Original', 'After Cleaning', 'Regression Ready', 'Classification Ready'],
    'Observations': [
        len(df),
        len(df_clean),
        len(df_regression),
        len(df_classification)
    ],
    'Features': [
        len(df.columns),
        len(df_clean.columns),
        len(valid_features),
        len(valid_features)
    ],
    'Status': [
        'Has issues',
        'Cleaned',
        'ML Ready ✓',
        'ML Ready ✓'
    ]
}

summary_df = pd.DataFrame(summary)
print("\n" + summary_df.to_string(index=False))

# ============================================================================
# STEP 8: SAVE DATA DICTIONARY
# ============================================================================

print("\nSTEP 8: Creating data dictionary...")

data_dict = pd.DataFrame({
    'Column': [
        'Country Name',
        'ISO3',
        'Year',
        'Avg_FDI_Restriction_Index',
        'FDI_Flows_Millions_USD',
        'Mineral_Rents_GDP_Percent',
        'Mineral_Rents_Log',
        'FDI_Restriction_Scaled',
        'FDI_Flows_Scaled',
        'Resource_Rich_Target'
    ],
    'Type': [
        'Identifier',
        'Identifier',
        'Identifier',
        'Feature (Independent Variable)',
        'Feature (Independent Variable)',
        'Target (Dependent Variable)',
        'Target (Log-transformed)',
        'Feature (Standardized)',
        'Feature (Standardized)',
        'Target (Binary)'
    ],
    'Description': [
        'Country name',
        'ISO3 country code',
        'Year of observation',
        'FDI restriction index (0-1, higher = more restrictive)',
        'FDI inflows in millions USD',
        'Mineral rents as % of GDP',
        'Log(1 + Mineral_Rents_GDP_Percent)',
        'Standardized FDI restriction index',
        'Standardized FDI flows',
        '1 if mineral rents ≥5%, 0 otherwise'
    ],
    'Use': [
        'For grouping/filtering',
        'For grouping/filtering',
        'For time-series analysis or filtering',
        'Use in ML models',
        'Use in ML models',
        'Predict this (regression)',
        'Predict this (regression with log target)',
        'Use in models requiring scaled features',
        'Use in models requiring scaled features',
        'Predict this (classification)'
    ]
})

data_dict.to_csv('DATA_DICTIONARY.csv', index=False)
print(f"   ✓ Saved: DATA_DICTIONARY.csv")

# ============================================================================
# STEP 9: GENERATE QUICK START GUIDE
# ============================================================================

print("\nSTEP 9: Creating quick start guide...")

with open('QUICK_START_ML.txt', 'w') as f:
    f.write("QUICK START GUIDE FOR MACHINE LEARNING\n")
    f.write("="*80 + "\n\n")
    
    f.write("FILES CREATED:\n")
    f.write("-"*80 + "\n")
    f.write("1. INVESTMENT_ML_REGRESSION.csv - For regression tasks\n")
    f.write("2. INVESTMENT_ML_CLASSIFICATION.csv - For classification tasks\n")
    f.write("3. DATA_DICTIONARY.csv - Column descriptions\n")
    f.write("4. This guide (QUICK_START_ML.txt)\n\n")
    
    f.write("FEATURES (INDEPENDENT VARIABLES):\n")
    f.write("-"*80 + "\n")
    f.write("1. Avg_FDI_Restriction_Index - How restrictive is FDI policy?\n")
    f.write("2. FDI_Flows_Millions_USD - Actual FDI inflows\n\n")
    
    f.write("TARGET (DEPENDENT VARIABLE):\n")
    f.write("-"*80 + "\n")
    f.write("• REGRESSION: Mineral_Rents_GDP_Percent (continuous)\n")
    f.write("• CLASSIFICATION: Resource_Rich_Target (binary: 0 or 1)\n\n")
    
    f.write("QUICK START - REGRESSION:\n")
    f.write("-"*80 + "\n")
    f.write("""
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

# Load data
df = pd.read_csv('INVESTMENT_ML_REGRESSION.csv')

# Define features and target
features = ['Avg_FDI_Restriction_Index', 'FDI_Flows_Millions_USD']
target = 'Mineral_Rents_Log'  # Use log-transformed target

X = df[features]
y = df[target]

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Evaluate (use cross-validation in practice)
predictions = model.predict(X)
print(f"R² Score: {r2_score(y, predictions):.4f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y, predictions)):.4f}")
""")
    
    f.write("\n\nQUICK START - CLASSIFICATION:\n")
    f.write("-"*80 + "\n")
    f.write("""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

# Load data
df = pd.read_csv('INVESTMENT_ML_CLASSIFICATION.csv')

# Define features and target
features = ['Avg_FDI_Restriction_Index', 'FDI_Flows_Millions_USD']
target = 'Resource_Rich_Target'

X = df[features]
y = df[target]

# Train model with class weights (for imbalance)
model = RandomForestClassifier(
    n_estimators=100, 
    class_weight='balanced',
    random_state=42
)
model.fit(X, y)

# Evaluate
predictions = model.predict(X)
probabilities = model.predict_proba(X)[:, 1]

print(classification_report(y, predictions))
print(f"ROC AUC: {roc_auc_score(y, probabilities):.4f}")
""")
    
    f.write("\n\nRECOMMENDED ALGORITHMS:\n")
    f.write("-"*80 + "\n")
    f.write("✓ Random Forest - Best all-around choice\n")
    f.write("✓ Gradient Boosting (XGBoost, LightGBM) - For best performance\n")
    f.write("⚠ Linear Regression - Use scaled/log features\n")
    f.write("⚠ Neural Networks - Requires more data and tuning\n\n")
    
    f.write("IMPORTANT NOTES:\n")
    f.write("-"*80 + "\n")
    f.write("• ALWAYS use proper train/test splits (don't train and test on same data!)\n")
    f.write("• Use cross-validation for robust evaluation\n")
    f.write("• For classification, use F1-score/ROC AUC (NOT accuracy due to imbalance)\n")
    f.write("• Consider adding more features if available (time trends, lags, etc.)\n")
    f.write("• Handle time-series nature: don't use future to predict past!\n")

print(f"   ✓ Saved: QUICK_START_ML.txt")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("✅ DATASET FIXED AND READY FOR MACHINE LEARNING!")
print("="*80)

print("\nFILES CREATED:")
print("   1. INVESTMENT_ML_REGRESSION.csv - {0} rows, {1} columns".format(
    len(df_regression), len(df_regression.columns)
))
print("   2. INVESTMENT_ML_CLASSIFICATION.csv - {0} rows, {1} columns".format(
    len(df_classification), len(df_classification.columns)
))
print("   3. DATA_DICTIONARY.csv - Column explanations")
print("   4. QUICK_START_ML.txt - How to use the data")

print("\nFIXES APPLIED:")
print("   ✓ Removed data leakage (Resource_Rich, Resource_Category)")
print("   ✓ Dropped sparse columns (EITI variables)")
print("   ✓ Removed rows with missing values")
print("   ✓ Created log-transformed target for regression")
print("   ✓ Created scaled features for linear models")
print("   ✓ Created binary target for classification")
print("   ✓ Generated train/test splits")

print("\nDATA QUALITY:")
print(f"   • Clean observations: {len(df_regression):,}")
print(f"   • Countries: {df_regression['ISO3'].nunique()}")
print(f"   • Years: {df_regression['Year'].min()}-{df_regression['Year'].max()}")
print(f"   • Features: {len(valid_features)}")

print("\nNEXT STEPS:")
print("   1. Read: QUICK_START_ML.txt")
print("   2. Load: INVESTMENT_ML_REGRESSION.csv (for regression)")
print("      OR: INVESTMENT_ML_CLASSIFICATION.csv (for classification)")
print("   3. Build your ML model!")
print("   4. Remember: Use proper train/test splits and cross-validation!")

print("\n" + "="*80)
print("🚀 YOU'RE READY TO START MACHINE LEARNING!")
print("="*80 + "\n")

# %%
