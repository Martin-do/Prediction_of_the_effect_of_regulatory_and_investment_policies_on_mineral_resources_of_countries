import pandas as pd

def main():
    print("Generating Global_Commodity_Prices.csv...")
    # Historical Brent Crude annual averages (approximate from World Bank Pink Sheet)
    years = list(range(1990, 2026))
    prices = [23.73, 20.00, 19.32, 16.97, 15.82, 17.02, 20.67, 19.09, 12.72, 17.97, 
              28.50, 24.44, 25.02, 28.83, 38.27, 54.38, 65.14, 72.39, 97.26, 61.67,
              79.50, 111.26, 111.67, 108.66, 98.95, 52.39, 43.73, 54.19, 71.31, 64.28,
              41.84, 70.89, 100.93, 82.49, 80.00, 80.00] # Using 80 for 2024/2025 estimate
    
    # Pad if years list and prices list differ
    if len(prices) < len(years):
        prices.extend([prices[-1]] * (len(years) - len(prices)))
        
    df = pd.DataFrame({'Year': years, 'Oil_Price_Global_USD': prices})
    
    output_file = 'Global_Commodity_Prices.csv'
    df.to_csv(output_file, index=False)
    print(f"Saved {len(df)} rows to {output_file}")

if __name__ == "__main__":
    main()
