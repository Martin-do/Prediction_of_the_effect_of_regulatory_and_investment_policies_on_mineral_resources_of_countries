import requests
import pandas as pd
import json

def fetch_eiti_data():
    print("Fetching EITI Summary Data...")
    url = "https://eiti.org/api/v2.0/summary_data"
    all_records = []
    
    while url:
        print(f"Fetching: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data:
                print("Unexpected API response structure.")
                break
                
            for entry in data['data']:
                try:
                    # Extract Year from Label or use year_end
                    label = entry.get('label', '')
                    year = None
                    if ':' in label:
                        parts = label.split(':')
                        if len(parts) > 1:
                            year = parts[-1].strip()
                    
                    if not year:
                        year = entry.get('year_end', '')[:4] if entry.get('year_end') else None

                    # Revenue Extraction
                    revenue_local = entry.get('revenue_government_sum', 0)
                    currency = entry.get('currency', '')
                    rate = entry.get('currency_rate', 0)
                    
                    # Convert to float safely
                    try:
                        revenue_local = float(revenue_local) if revenue_local else 0.0
                        rate = float(rate) if rate else 0.0
                    except (ValueError, TypeError):
                        revenue_local = 0.0
                        rate = 0.0

                    # Calculate USD
                    revenue_usd = 0.0
                    if rate > 0:
                        revenue_usd = revenue_local / rate
                    
                    record = {
                        'Country Name': entry.get('country.label'),
                        'Country Code': entry.get('country.iso3'),
                        'Year': year,
                        'Total_Revenue_Local': revenue_local,
                        'Currency': currency,
                        'Exchange_Rate': rate,
                        'Total_Revenue_USD': revenue_usd
                    }
                    all_records.append(record)
                except Exception as e:
                    print(f"Error processing entry: {e}")
                    continue
            
            # Pagination
            if 'next' in data and data['next']:
                url = data['next']['href']
            else:
                url = None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            break

    if all_records:
        df = pd.DataFrame(all_records)
        print(f"Fetched {len(df)} total records.")
        return df
    else:
        return None

def main():
    eiti_df = fetch_eiti_data()
    
    if eiti_df is not None:
        # Save to CSV
        output_file = 'EITI_Governance_Dataset.csv'
        eiti_df.to_csv(output_file, index=False)
        print(f"Dataset saved to {output_file}")
        
        # Display first few rows
        print(eiti_df.head())
        print("\nColumns:", eiti_df.columns.tolist())
    else:
        print("Failed to create EITI dataset.")

if __name__ == "__main__":
    main()
