import akshare as ak
import pandas as pd

def test_us():
    # AAPL is Nasdaq -> 105
    try:
        print("Fetching 105.AAPL...")
        df = ak.stock_us_hist_min_em(symbol="105.AAPL")
        print(f"Rows: {len(df)}")
        print(df.head(1))
    except Exception as e:
        print(f"Error 105: {e}")

    # NVDA is Nasdaq -> 105
    # TSLA is Nasdaq -> 105
    # BABA is Nasdaq? No?
    # F (Ford) is NYSE -> 106?
    
    try:
        print("Fetching 106.F (Ford)...")
        df = ak.stock_us_hist_min_em(symbol="106.F")
        print(f"Rows: {len(df)}")
        print(df.head(1))
    except Exception as e:
        print(f"Error 106: {e}")

if __name__ == "__main__":
    test_us()
