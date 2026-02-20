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

# %%
import pandas as pd
import numpy as np

# %%

# Load datasets
rq = pd.read_csv("datasets/API_RQ.EST_DS2_en_csv_v2_126996.csv", skiprows=4)
meta = pd.read_csv("datasets/Metadata_Country_API_RQ.EST_DS2_en_csv_v2_126996.csv")

# Merge on Country Code
merged = rq.merge(meta, on="Country Code", how="left")

# Inspect result
merged.head()

# %%
merged = merged[merged["Region"].notna()]
merged.head()

# %%
# Save to CSV from worldbank
merged.to_csv("RegulatoryQuality_Combined.csv", index=False)

# %% [markdown]
# ## still on worldbank

# %%


# 1. Load the datasets
# Replace filenames if yours are different
reg_file = 'RegulatoryQuality_Combined.csv'
wgi_file = 'datasets/world_governace_indicators_data.csv'

df_reg = pd.read_csv(reg_file)
df_wgi = pd.read_csv(wgi_file)

# --- STEP 1: Clean and Reshape the WGI dataset ---
# Rename '1996 [YR1996]' to '1996'
wgi_year_map = {col: col.split(' ')[0] for col in df_wgi.columns if '[' in col}
df_wgi = df_wgi.rename(columns=wgi_year_map)

# Replace '..' with NaN and convert years to numeric
year_cols_wgi = [col for col in df_wgi.columns if col.isdigit()]
for col in year_cols_wgi:
    df_wgi[col] = pd.to_numeric(df_wgi[col].replace('..', np.nan), errors='coerce')

# Melt WGI to Long Format
wgi_long = df_wgi.melt(
    id_vars=['Country Name', 'Country Code'],
    value_vars=year_cols_wgi,
    var_name='Year',
    value_name='Regulatory_Quality'
).dropna(subset=['Regulatory_Quality'])

# --- STEP 2: Clean and Reshape the World Bank Combined dataset ---
# This file contains the Region and Income Group metadata
year_cols_reg = [str(y) for y in range(1960, 2025) if str(y) in df_reg.columns]
reg_long = df_reg.melt(
    id_vars=['Country Name', 'Country Code', 'Region', 'IncomeGroup'],
    value_vars=year_cols_reg,
    var_name='Year',
    value_name='Regulatory_Quality'
).dropna(subset=['Regulatory_Quality'])

# --- STEP 3: Merge the two ---
# We use an 'outer' merge to make sure we keep countries unique to either file
# We prioritize the 'reg_long' file because it has the Region/Income metadata
combined = pd.merge(
    reg_long, 
    wgi_long, 
    on=['Country Code', 'Year'], 
    how='outer', 
    suffixes=('', '_wgi')
)

# Fill gaps: if 'Regulatory_Quality' is missing, take it from the WGI source
combined['Regulatory_Quality'] = combined['Regulatory_Quality'].fillna(combined['Regulatory_Quality_wgi'])
combined['Country Name'] = combined['Country Name'].fillna(combined['Country Name_wgi'])

# Drop redundant columns and sort
combined = combined.drop(columns=['Regulatory_Quality_wgi', 'Country Name_wgi'])
combined['Year'] = combined['Year'].astype(int)
combined = combined.sort_values(['Country Name', 'Year']).reset_index(drop=True)

# 4. Save the result
combined.to_csv('Master_Regulatory_Quality.csv', index=False)

print("Merge Complete!")
print(f"Total Rows: {len(combined)}")
print(combined.head())

# %% [markdown]
# ## combining with SRD data from IMF

# %%
# 1. Load the SRD dataset
srd_df = pd.read_csv('datasets/dataset_2025-11-10T03_51_05.279979035Z_DEFAULT_INTEGRATION_IMF.RES_SRD_1.0.0.csv')

# 2. Reshape SRD to Long Format
# Year columns are from '1973' to '2014'
year_cols = [str(y) for y in range(1973, 2015)]
id_vars = ['COUNTRY', 'INDICATOR', 'SR_CATEGORY', 'SR_TYPE']

srd_long = srd_df.melt(
    id_vars=id_vars,
    value_vars=year_cols,
    var_name='Year',
    value_name='Reform_Score'
).dropna(subset=['Reform_Score'])

# 3. Simplify for the Master Dataset
# Because there are many indicators, we can take the average per country per year 
# to get an "Overall Regulatory Stance" or keep them separate.
# Here, let's create a pivot so each category is a column
srd_summary = srd_long.groupby(['COUNTRY', 'Year', 'SR_CATEGORY'])['Reform_Score'].mean().unstack().reset_index()

# 4. Standardize Country Names for Merging (using the logic from before)
def normalize_name(name):
    if not isinstance(name, str): return ""
    return name.lower().strip().replace(",", "").replace("republic of", "").strip()

srd_summary['name_clean'] = srd_summary['COUNTRY'].apply(normalize_name)

# 5. Merge with your existing Master (from previous steps)
# master = pd.read_csv('Master_Regulatory_Quality.csv') # Your WB/WGI master
# master['name_clean'] = master['Country Name'].apply(normalize_name)

# 1. Standardize names more aggressively
def robust_cleanup(name):
    import re
    if not isinstance(name, str): return ""
    name = name.lower()
    name = re.sub(r'\(.*\)', '', name) # Remove text in brackets
    name = re.sub(r'[^a-z\s]', '', name) # Remove punctuation
    replacements = {
        'democratic republic of': 'dr',
        'republic of': '',
        'united states of america': 'united states',
        'pdr': '',
        'the ': ''
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()

master['name_clean'] = master['Country Name'].apply(robust_cleanup)
srd_summary['name_clean'] = srd_summary['COUNTRY'].apply(robust_cleanup)

# 2. Use a LEFT JOIN 
# This ensures we KEEP every country from your World Bank 'Master' 
# and just attach IMF data where it exists.
final_v3 = pd.merge(
    master, 
    srd_summary.drop(columns=['COUNTRY']), 
    on=['name_clean', 'Year'], 
    how='left' 
)

# 3. Fill the gaps
# For the 90 countries not in SRD, we leave them as NaN or 0 
# rather than deleting the whole country.
print(f"Merge finished. Total countries retained: {final_v3['Country Name'].nunique()}")
# Save the dataframe to a CSV file
final_v3.to_csv('Final_Regulatory_Dataset.csv', index=False)

print("File successfully saved as 'Final_Regulatory_Dataset.csv'")


# %% [markdown]
# ## categorizing into textual and numerical for regulatory dataset

# %%
# =================================================================
# 2. REGULATORY POLICY DATASETS (WGI + IMF SRD)
# =================================================================

wgi_file = 'datasets/world_governace_indicators_data.csv'
imf_srd_file = 'datasets/dataset_2025-11-10T03_51_05.279979035Z_DEFAULT_INTEGRATION_IMF.RES_SRD_1.0.0.csv'
print("Processing Regulatory Policy Data...")

# --- A. WGI Data Processing ---
wgi_df = pd.read_csv(wgi_file)
# Melt the year columns (e.g., '1996 [YR1996]') into a long format
year_cols_wgi = [col for col in wgi_df.columns if '[' in col]
wgi_melted = wgi_df.melt(id_vars=['Country Name', 'Country Code'], 
                         value_vars=year_cols_wgi, 
                         var_name='Year_Raw', 
                         value_name='WGI_RQ_Score')

# Clean Year and Scores
wgi_melted['Year'] = wgi_melted['Year_Raw'].str.extract('(\d+)').astype(float)
wgi_melted['WGI_RQ_Score'] = pd.to_numeric(wgi_melted['WGI_RQ_Score'], errors='coerce')
wgi_numerical = wgi_melted[['Country Code', 'Year', 'WGI_RQ_Score']].rename(columns={'Country Code': 'ISO3'})

# --- B. IMF SRD Data Processing ---
imf_df = pd.read_csv(imf_srd_file)
# Years are headers from 1973 to 2014
year_cols_imf = [str(y) for y in range(1973, 2015)]
imf_melted = imf_df.melt(id_vars=['COUNTRY', 'SERIES_NAME'], 
                         value_vars=year_cols_imf, 
                         var_name='Year', 
                         value_name='IMF_SRD_Score')

imf_melted['Year'] = imf_melted['Year'].astype(float)
imf_melted['IMF_SRD_Score'] = pd.to_numeric(imf_melted['IMF_SRD_Score'], errors='coerce')
imf_numerical = imf_melted.rename(columns={'COUNTRY': 'ISO3', 'SERIES_NAME': 'Indicator_Name'})

# --- C. Final Regulatory Numerical Merge ---
# Merging WGI and IMF data on ISO3 and Year
regulatory_numerical = pd.merge(wgi_numerical, imf_numerical, on=['ISO3', 'Year'], how='outer')
regulatory_numerical.to_csv('reg_num/Regulatory_Policy_Numerical.csv', index=False)

# --- D. Regulatory Text Data (Descriptions) ---
# This extracts the definitions of the policies/indicators used in the numerical data
regulatory_text = imf_df[['SERIES_NAME', 'SR_CATEGORY', 'FULL_DESCRIPTION']].copy()
regulatory_text.rename(columns={
    'SERIES_NAME': 'Indicator', 
    'SR_CATEGORY': 'Policy_Area', 
    'FULL_DESCRIPTION': 'Definition_and_Scope'
}, inplace=True)
# Removing duplicates to have a clean reference for indicator meanings
regulatory_text = regulatory_text.drop_duplicates()
regulatory_text.to_csv('reg_num/Regulatory_Policy_Text.csv', index=False)

print("\nSuccess! The following files have been created:")
print("1. Investment_Policy_Numerical.csv - (FDI scores by sector/year)")
print("2. Investment_Policy_Text.csv      - (Legal justifications and notes for FDI)")
print("3. Regulatory_Policy_Numerical.csv - (WGI and IMF governance scores)")
print("4. Regulatory_Policy_Text.csv      - (Definitions of regulatory indicators)")

# %%
B


# %% [markdown]
# ## adding the data from transparency, CPI

# %%
def process_cpi_data(file_path):
    """Processes the Transparency International CPI Historical dataset."""
    # Skip metadata rows
    df = pd.read_excel(file_path, sheet_name="CPI Historical (internal)", skiprows=3)
    df.columns = [c.strip() for c in df.columns]
    
    # Selecting core features for the numerical dataset
    keep_cols = [
        'ISO3', 'Year', 'CPI score', 'Rank', 
        'World Bank CPIA', 'PRS International Country Risk Guide',
        'Varieties of Democracy Project', 'World Economic Forum EOS'
    ]
    # Filter only available columns
    available_cols = [c for c in keep_cols if c in df.columns]
    df_clean = df[available_cols].copy()
    
    # Standardize column names
    df_clean.rename(columns={'CPI score': 'CPI_Score', 'Rank': 'CPI_Rank'}, inplace=True)
    return df_clean



# --- Execution ---
# Paths to your uploaded files
cpi_path = 'datasets/CPI2023_Global_Results__Trends.xlsx'


# Process CPI
cpi_numerical = process_cpi_data(cpi_path)



# Save processed segments
cpi_numerical.to_csv('CPI_Numerical_Processed.csv', index=False)



print(f"Processed CPI: {cpi_numerical.shape}")



# %%
def process_dstri_data(file_path):
    """Processes the Digital Services Trade Restrictiveness Index."""
    # Using engine='python' to handle complex text fields in OBS_VALUE
    df = pd.read_csv(file_path, engine='python')
    
    # 1. Create Numerical Indicators (Binary)
    num_df = df[df['OBS_VALUE'].isin(['yes', 'no'])].copy()
    num_df['Value'] = num_df['OBS_VALUE'].map({'yes': 1, 'no': 0})
    
    # Pivot to get indicators as columns
    dstri_num = num_df.pivot_table(
        index=['REF_AREA', 'TIME_PERIOD'], 
        columns='STRI_REGULATORY_MEASURE', 
        values='Value', 
        aggfunc='first'
    ).reset_index()
    dstri_num.rename(columns={'REF_AREA': 'ISO3', 'TIME_PERIOD': 'Year'}, inplace=True)
    
    # 2. Create Text Dataset (Explanatory Notes)
    text_df = df[~df['OBS_VALUE'].isin(['yes', 'no', np.nan])].copy()
    text_df = text_df[['REF_AREA', 'TIME_PERIOD', 'STRI_REGULATORY_MEASURE', 'OBS_VALUE']]
    text_df.columns = ['ISO3', 'Year', 'Policy_Area', 'Legal_Basis_Note']
    
    return dstri_num, text_df

dstri_path = 'datasets/OECD.TAD.TPD,DSD_STRI_POLICY@DF_STRI_POLICY_DIGITAL,+all.csv'

dstri_numerical, dstri_text = process_dstri_data(dstri_path)
dstri_numerical.to_csv('DSTRI_Numerical_Processed.csv', index=False)
dstri_text.to_csv('DSTRI_Text_Notes.csv', index=False)
print(f"Processed DSTRI Numerical: {dstri_numerical.shape}")
print(f"Processed DSTRI Text: {dstri_text.shape}")

# %%

# %% [markdown]
# ## integrating with existing data

# %%


# 1. Load your three files
# These are your 'clean' datasets ready for merging
df_reg = pd.read_csv('Final_Regulatory_Dataset.csv')
df_cpi = pd.read_csv('CPI_Numerical_Processed.csv')
df_dstri = pd.read_csv('DSTRI_Numerical_Processed.csv')

# 2. Standardize data types for 'Year' and 'Country Code'
# This ensures the merge finds matches correctly
for df in [df_reg, df_cpi, df_dstri]:
    df['Year'] = df['Year'].astype(int)
    # Ensure no hidden spaces in the country codes
    if 'Country Code' in df.columns:
        df['Country Code'] = df['Country Code'].str.strip()
    if 'ISO3' in df.columns:
        df['ISO3'] = df['ISO3'].str.strip()

# 3. Step-by-Step Integration (Left Join)
# We start with the Regulatory dataset and 'attach' the others to it
print("Integrating CPI data...")
master_df = pd.merge(
    df_reg, 
    df_cpi, 
    left_on=['Country Code', 'Year'], 
    right_on=['ISO3', 'Year'], 
    how='left'
)

# Remove redundant ISO3 column after merge
if 'ISO3' in master_df.columns:
    master_df.drop(columns=['ISO3'], inplace=True)

print("Integrating DSTRI data...")
master_df = pd.merge(
    master_df,
    df_dstri,
    left_on=['Country Code', 'Year'],
    right_on=['ISO3', 'Year'],
    how='left'
)

# Final cleanup
if 'ISO3' in master_df.columns:
    master_df.drop(columns=['ISO3'], inplace=True)

# 4. Save the final Master Dataset
master_df.to_csv('Master_Integrated_Dataset.csv', index=False)

print("-" * 30)
print("SUCCESS: Master Integrated Dataset created.")
print(f"Total Rows: {master_df.shape[0]}")
print(f"Total Columns: {master_df.shape[1]}")
master_df.head()

# %%

# %% [markdown]
# ## processing resource governance index data

# %%


# --- 1. Load the RGI File ---
# We skip the first row based on the file structure analysis
rgi_file = 'datasets/2021_Resource_Governance_Index_scores_workbook_English.xlsx'
rgi_raw = pd.read_excel(rgi_file, sheet_name='2021_RGI_scores ', skiprows=1)

# --- 2. Transpose and Clean ---
# We want the 'Element name' to become our headers
# Transpose the dataframe, setting the indicators as columns
rgi_t = rgi_raw.set_index('Element name').T
rgi_t = rgi_t.reset_index()

# Rename the 'index' column to 'Country_Sector'
rgi_t.rename(columns={'index': 'Country_Sector'}, inplace=True)

# Filter out metadata rows (like 'Number', 'Element Info')
# We only want rows that correspond to countries (which were originally columns)
# The first few rows of the transposed dataframe will be metadata we don't need
valid_countries = rgi_t[rgi_t['Country_Sector'].str.contains(r'\(', na=False)].copy()

# Extract Country Name
# Split "Azerbaijan (oil and gas)" into "Azerbaijan"
valid_countries['Country Name'] = valid_countries['Country_Sector'].apply(lambda x: x.split('(')[0].strip())

# Select Key Indicators
# We'll take the headline index and key components
indicators = ['Resource Governance Index', 'Value realization', 'Revenue management', 'Enabling environment']
# Note: Column names in the CSV might vary slightly (e.g., caps), so we select carefully
# Based on your file preview: 'Resource Governance Index' exists. Let's just grab that for now.
target_cols = ['Country Name', 'Resource Governance Index']
rgi_final = valid_countries[target_cols].copy()

# Convert scores to numeric (coercing non-numeric values like '.' to NaN)
rgi_final['Resource Governance Index'] = pd.to_numeric(rgi_final['Resource Governance Index'], errors='coerce')

# Aggregate duplicates (e.g., Colombia Mining + Colombia Oil & Gas) -> Mean Score
rgi_grouped = rgi_final.groupby('Country Name')['Resource Governance Index'].mean().reset_index()
rgi_grouped['Year'] = 2021  # Assign to 2021

# --- 3. Integrate with Master Dataset ---
# Load Master File
master_df = pd.read_csv('Master_Integrated_Dataset.csv')

# Merge
# We use 'left' join to keep existing master data safe
master_updated = pd.merge(
    master_df,
    rgi_grouped,
    on=['Country Name', 'Year'],
    how='left'
)

# --- 4. Save Updated Master File ---
master_updated.to_csv('Master_Integrated_Dataset_v2.csv', index=False)

print("RGI Data Integrated Successfully!")
print(f"New shape: {master_updated.shape}")
print("Sample of Countries with RGI Data:")
print(master_updated[master_updated['Resource Governance Index'].notnull()][['Country Name', 'Year', 'Resource Governance Index']].head())

# %%

# %% [markdown]
# ## HANDLING CRYPTIC CODES FROM THE DSTRI DATASET

# %%
# import pandas as pd

# 1. Load the Master Dataset you created in the previous step
# (Ensure this matches your actual file name)
master_df = pd.read_csv('Master_Integrated_Dataset_v2.csv')

def process_dstri_indices(df):
    """
    Takes the raw 'cryptic' DSTRI columns (e.g., 10_1_1, 6_1_1fix)
    and aggregates them into 5 meaningful policy area scores.
    """
    # Create lists of columns for each policy area based on prefixes
    infra_cols = [c for c in df.columns if str(c).startswith('6_')]
    electronic_cols = [c for c in df.columns if str(c).startswith('7_')]
    payment_cols = [c for c in df.columns if str(c).startswith('8_')]
    ipr_cols = [c for c in df.columns if str(c).startswith('9_')]
    other_cols = [c for c in df.columns if str(c).startswith('10_')]

    # Calculate unweighted averages (indices range 0-1)
    # A higher score = More restrictive regulation
    if infra_cols:
        df['DSTRI_Infrastructure_Score'] = df[infra_cols].mean(axis=1)
    if electronic_cols:
        df['DSTRI_Electronic_Trans_Score'] = df[electronic_cols].mean(axis=1)
    if payment_cols:
        df['DSTRI_Payment_Systems_Score'] = df[payment_cols].mean(axis=1)
    if ipr_cols:
        df['DSTRI_Intellectual_Property_Score'] = df[ipr_cols].mean(axis=1)
    if other_cols:
        df['DSTRI_Other_Barriers_Score'] = df[other_cols].mean(axis=1)
    
    # Calculate a composite 'Digital Openness' score (proxy for total DSTRI)
    # We take the mean of all relevant columns found
    all_dstri_cols = infra_cols + electronic_cols + payment_cols + ipr_cols + other_cols
    if all_dstri_cols:
        df['DSTRI_Composite_Score'] = df[all_dstri_cols].mean(axis=1)
        
        # Drop the granular 'cryptic' columns to clean up the dataset
        df.drop(columns=all_dstri_cols, inplace=True)
        print(f"Aggregated {len(all_dstri_cols)} granular DSTRI columns into 6 composite scores.")
        
    return df

# 2. Run the processing
final_df = process_dstri_indices(master_df)

# 3. Save the final "Analysis-Ready" dataset
final_df.to_csv('Final_Analysis_Ready_Dataset.csv', index=False)

# 4. Check the results
print("Columns in Final Dataset:")
print(final_df.columns.tolist())
print("\nSample Data:")
print(final_df[['Country Name', 'Year', 'DSTRI_Composite_Score', 'CPI_Score']].head())

# %%

# %% [markdown]
# ## DROPPING RGI COLUMN DUE TO DATA SPARSITY

# %%


# 1. Load your dataset
df = pd.read_csv('Final_Analysis_Ready_Dataset.csv')

# 2. List of columns to drop 
# We remove RGI because it only has 17 rows and will break your regression
cols_to_drop = ['Resource Governance Index', 'name_clean']

# Drop columns only if they exist to avoid errors
df_clean = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

# 3. Save the cleaner version
df_clean.to_csv('Regulatory_Dataset_Clean.csv', index=False)

print("✅ Column 'Resource Governance Index' has been dropped.")
print(f"✅ New file saved as: 'Regulatory_Dataset_Clean.csv'")
print(f"Remaining columns: {df_clean.columns.tolist()}")

# %%

# %% [markdown]
# ## CLUSTERING DATASET BY CONTINENT/COUNTRY

# %%
import pandas as pd

# Load the clean dataset
df = pd.read_csv('Regulatory_Dataset_Clean.csv')

# --- 1. Statistical Clustering (Group Means) ---
# We calculate the average Regulatory Quality and CPI Score for each Region and Income Group
cluster_analysis = df.groupby(['Region', 'IncomeGroup'])[['Regulatory_Quality', 'CPI_Score']].mean().reset_index()

# Sort by Regulatory Quality to see the "Clustered" ranking
cluster_analysis = cluster_analysis.sort_values(by='Regulatory_Quality', ascending=False)

print("--- Regional & Income Clusters (Averages) ---")
print(cluster_analysis)

# --- 2. Data Imputation (Optional but Recommended) ---
# If a country is missing a value for a specific year, a common 'cluster' technique 
# is to fill that gap with the average of its Region/Income group.
df['Regulatory_Quality_Filled'] = df.groupby(['Region', 'IncomeGroup'])['Regulatory_Quality'].transform(lambda x: x.fillna(x.mean()))

# --- 3. Preparing for Regression (Dummy Variables) ---
# To use these clusters in a model, you convert them into 'Dummy Variables'
# This tells the model: "This data point belongs to the Africa cluster"
df_with_dummies = pd.get_dummies(df, columns=['Region', 'IncomeGroup'], drop_first=True)

# Save this version for your actual modeling
df_with_dummies.to_csv('Regulatory_Dataset_Clustered.csv', index=False)

print("\n✅ Analysis Complete!")
print("✅ Saved 'Regulatory_Dataset_Clustered.csv' with Region/Income indicators for your model.")

# %%

# %% [markdown]
# ## ANALYSIS WITH THE SATELITE MODEL

# %%
import pandas as pd

# 1. Load your clustered dataset
df = pd.read_csv('Regulatory_Dataset_Clustered.csv')

# 2. Define your "Predictor" groups
# These names must match your CSV column headers exactly
baseline_vars = ['Regulatory_Quality', 'Region_Sub-Saharan Africa', 'IncomeGroup_Low income']
special_vars = ['CPI_Score', 'World Bank CPIA', 'DSTRI_Composite_Score', 'Varieties of Democracy Project']

# Combine into one list for the analysis
all_vars = [v for v in (baseline_vars + special_vars) if v in df.columns]

# 3. Create the summary table
summary = df[all_vars].describe().transpose()

# 4. Add a column for "Missingness" (Fixed the typo here!)
summary['Missing %'] = (df[all_vars].isnull().sum() / len(df)) * 100

# 5. Save this as your "Table 1" for your paper
summary.to_csv('Paper_Table1_Descriptive_Stats.csv')

print("--- DESCRIPTIVE STATISTICS FOR SUPERVISOR ---")
print(summary[['count', 'mean', 'std', 'Missing %']])

# %%
