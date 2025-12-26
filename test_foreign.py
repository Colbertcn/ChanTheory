import akshare as ak
import pandas as pd

def test_fetch():
    print("Testing HK Min (00700)...")
    try:
        df_hk = ak.stock_hk_hist_min_em(symbol="00700", period="30")
        print(f"HK Data: {len(df_hk)} rows")
        print(df_hk.head(1))
    except Exception as e:
        print(f"HK Error: {e}")

    print("\nTesting US Min (AAPL)...")
    try:
        # Try just AAPL
        df_us = ak.stock_us_hist_min_em(symbol="105.AAPL", period="30") # Eastmoney often uses 105. for Nasdaq, 106. for NYSE? Or AkShare helps?
        # Let's try standard AAPL first? No, AkShare usually matches EM symbol.
        # Actually akshare might handle "AAPL" directly if we are lucky, or we need to find the code.
        # Let's try '105.AAPL' (Nasdaq) or just 'AAPL'.
        # Actually let's try to find symbol code for AAPL.
        pass
    except Exception as e:
        pass
        
    try:
        # Common convention in AkShare for US might be just the ticker for some funcs, but EM usually needs prefix.
        # Let's try '105.AAPL' which is common for EM.
        print("Trying '105.AAPL'...")
        df_us = ak.stock_us_hist_min_em(symbol="105.AAPL", period="30")
        print(f"US Data (105.AAPL): {len(df_us)} rows")
        print(df_us.head(1))
    except Exception as e:
        print(f"US Error (105.AAPL): {e}")

    try:
        # Try 'AAPL'
        print("Trying 'AAPL'...")
        df_us = ak.stock_us_hist_min_em(symbol="AAPL", period="30")
        print(f"US Data (AAPL): {len(df_us)} rows")
        print(df_us.head(1))
    except Exception as e:
        print(f"US Error (AAPL): {e}")

if __name__ == "__main__":
    test_fetch()
