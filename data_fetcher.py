import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def fetch_csi300_data(period='15', days=60):
    """
    Fetch CSI 300 index data using AkShare.
    
    Args:
        period (str): '1', '5', '15', '30', '60'
        days (int): Number of days to look back for start date (approximate)
        
    Returns:
        pd.DataFrame: Columns [datetime, open, high, low, close, volume]
    """
    # Calculate start date
    # Multiply by 1.5 to account for weekends/holidays roughly
    start_dt = datetime.now() - timedelta(days=int(days * 1.5)) 
    # Use YYYY-MM-DD HH:MM:SS format as per docstring seen in help
    start_date_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Fetching CSI 300 data from AkShare (Start: {start_date_str})...")
    
    try:
        # 000300 is the code for CSI 300 on Shanghai Exchange
        df = ak.index_zh_a_hist_min_em(symbol="000300", period=period, start_date=start_date_str)
        print(f"AkShare returned type: {type(df)}")
        if df is not None:
             print(f"AkShare returned shape: {df.shape}")
             print(f"Columns: {df.columns}")
        
        if df.empty:
            print(f"Warning: AkShare returned empty DataFrame for start_date={start_date_str}")
            return pd.DataFrame()
            
        # Rename columns to match the project standard
        # '时间', '开盘', '收盘', '最高', '最低', '成交量'
        rename_map = {
            '时间': 'datetime',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume'
        }
        df = df.rename(columns=rename_map)
        
        # Select only necessary columns
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        
        # Convert datetime string to datetime object if needed
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Sort by datetime just in case
        df = df.sort_values('datetime').reset_index(drop=True)
        
        return df
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_csi300_data()
    print(df.head())
    print(df.tail())
    print(f"Total records: {len(df)}")
