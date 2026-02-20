import requests
import pandas as pd
import time

def fetch_world_bank_data(indicator_code, indicator_name):
    print(f"Fetching {indicator_name} ({indicator_code})...")
    url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page=20000&date=1990:2025"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if len(data) < 2:
            print("No data found or unexpected format.")
            return None
        
        records = []
        for entry in data[1]:
            record = {
                'Country Name': entry['country']['value'],
                'Country Code': entry['countryiso3code'],
                'Year': entry['date'],
                indicator_name: entry['value']
            }
            records.append(record)
            
        df = pd.DataFrame(records)
        print(f"Fetched {len(df)} records.")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    # Indicator: Mineral rents (% of GDP) - NY.GDP.MINR.RT.ZS
    mineral_rents_df = fetch_world_bank_data('NY.GDP.MINR.RT.ZS', 'Mineral_Rents_Percent_GDP')
    
    # Indicator: Total natural resources rents (% of GDP) - NY.GDP.TOTL.RT.ZS
    # total_rents_df = fetch_world_bank_data('NY.GDP.TOTL.RT.ZS', 'Total_Natural_Resources_Rents_Percent_GDP')
    
    if mineral_rents_df is not None:
        # Save to CSV
        output_file = 'Mineral_Resources_Dataset.csv'
        mineral_rents_df.to_csv(output_file, index=False)
        print(f"Dataset saved to {output_file}")
        
        # Display first few rows
        print(mineral_rents_df.head())
    else:
        print("Failed to create dataset.")

if __name__ == "__main__":
    main()
