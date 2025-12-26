import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def test_hk_01810():
    symbol = "01810"
    print(f"Testing HK stock symbol: {symbol}")
    
    # Test Min Data
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=5)
    
    start_date_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Fetching 30min data from {start_date_str} to {end_date_str}...")
    
    try:
        df = ak.stock_hk_hist_min_em(symbol=symbol, period='30', adjust="qfq", start_date=start_date_str, end_date=end_date_str)
        if df.empty:
            print("Result is empty!")
        else:
            print(f"Success! Got {len(df)} rows.")
            print(df.head())
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    test_hk_01810()
