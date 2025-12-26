import pandas as pd
from data_fetcher import fetch_csi300_data

def debug_fetch():
    # Fetch 1-min data for a problematic date (e.g., Dec 18, 2025)
    # Start/End date needs to include the trading hours.
    start_date = "2025-12-18 09:00:00"
    end_date = "2025-12-18 16:00:00"
    
    print(f"Fetching 1-min data for {start_date} to {end_date}...")
    df = fetch_csi300_data(period='1', start_date=start_date, end_date=end_date)
    
    if df.empty:
        print("DF is empty!")
        return
        
    print(f"Fetched {len(df)} rows.")
    print("Description:")
    print(df.describe())
    
    print("\nCheck for zeros:")
    for col in ['open', 'high', 'low', 'close']:
        zeros = df[df[col] <= 0]
        if not zeros.empty:
            print(f"Found {len(zeros)} rows with {col} <= 0")
            print(zeros.head())
        else:
            print(f"No {col} <= 0")

if __name__ == "__main__":
    debug_fetch()
