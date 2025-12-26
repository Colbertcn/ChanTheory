import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import threading

# Global cache for stock names
_stock_names_cache = {}
_cache_lock = threading.Lock()

def detect_market(symbol):
    """
    Detect market type based on symbol.
    Returns: 'A', 'HK', 'US', 'INDEX'
    """
    symbol = str(symbol).strip().upper()
    
    known_indices = ['000300', '000001', '399001', '000905', '000016', '399006'] 
    
    if symbol.endswith('.HK'):
        return 'HK', symbol[:-3]
    if symbol.endswith('.US'):
        return 'US', symbol[:-3]
        
    if symbol in known_indices:
        return 'INDEX', symbol
        
    if len(symbol) == 5 and symbol.isdigit():
        return 'HK', symbol
        
    if any(c.isalpha() for c in symbol) and not (symbol.startswith('SH') or symbol.startswith('SZ') or symbol.startswith('BJ')):
        return 'US', symbol
        
    return 'A', symbol

def get_stock_name(symbol):
    """
    Get stock name. Tries to fetch from AkShare if not in cache.
    """
    symbol = str(symbol).strip().upper()
    
    with _cache_lock:
        if symbol in _stock_names_cache:
            return _stock_names_cache[symbol]
    
    market, clean_symbol = detect_market(symbol)
    name = symbol # Default to symbol
    
    try:
        if market == 'A':
            # Try specific A-share lookup first (fast)
            try:
                # stock_individual_info_em is fast but might not work for all
                # But stock_zh_a_spot_em is heavy.
                # Let's try individual info first?
                # Actually stock_individual_info_em returns a dataframe with fields.
                # It requires symbol like "600519".
                df = ak.stock_individual_info_em(symbol=clean_symbol)
                # Field: 股票简称
                if not df.empty:
                    # df structure: item, value
                    name_row = df[df['item'] == '股票简称']
                    if not name_row.empty:
                        name = name_row['value'].values[0]
            except:
                pass
                
        elif market == 'HK':
            # HK spot is relatively small (~3000 rows)
            # We can cache the whole list once?
            # Or just return symbol for now if it's too slow.
            # Let's try to fetch spot once.
            global _hk_list_cache
            if '_hk_list_cache' not in globals():
                print("Fetching HK stock list for names...")
                _hk_list_cache = ak.stock_hk_spot_em()
            
            # _hk_list_cache columns: 序号, 代码, 名称, ...
            # Code is 5 digits usually.
            row = _hk_list_cache[_hk_list_cache['代码'] == clean_symbol]
            if not row.empty:
                name = row['名称'].values[0]
                
        elif market == 'US':
            # US list is huge. Maybe just use symbol.
            # Or try stock_us_spot_em()
            pass
            
    except Exception as e:
        print(f"Error fetching name for {symbol}: {e}")
        
    with _cache_lock:
        _stock_names_cache[symbol] = name
        
    return name

def fetch_csi300_data(period='15', days=60, start_date=None, end_date=None, symbol='000300'):
    """
    Fetch market data using AkShare.
    """
    # Calculate start date if not provided
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=int(days * 1.5)) 
        start_date_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        start_date_str = start_date
        
    # Prepare end_date string if provided
    end_date_str = end_date if end_date else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Clean symbol
    symbol = str(symbol).strip()

    print(f"Fetching data for {symbol} from AkShare (Start: {start_date_str}, End: {end_date_str})...")
    
    try:
        market, clean_symbol = detect_market(symbol)
        df = pd.DataFrame()
        
        # --- HK Market ---
        if market == 'HK':
            print(f"Detected HK Stock: {clean_symbol}")
            if period in ['1', '5', '15', '30', '60']:
                df = ak.stock_hk_hist_min_em(symbol=clean_symbol, period=period, adjust="qfq", start_date=start_date_str, end_date=end_date_str)
            elif period == 'daily':
                s_d = start_date_str.split(' ')[0].replace('-', '')
                e_d = end_date_str.split(' ')[0].replace('-', '')
                df = ak.stock_hk_hist(symbol=clean_symbol, period="daily", start_date=s_d, end_date=e_d, adjust="qfq")
        
        # --- US Market ---
        elif market == 'US':
            print(f"Detected US Stock: {clean_symbol}")
            
            if period == 'daily':
                prefixes = ["105.", "106.", "107."]
                s_d = start_date_str.split(' ')[0].replace('-', '')
                e_d = end_date_str.split(' ')[0].replace('-', '')
                
                for prefix in prefixes:
                    try:
                        code = f"{prefix}{clean_symbol}"
                        print(f"Trying {code}...")
                        df = ak.stock_us_hist(symbol=code, period="daily", start_date=s_d, end_date=e_d, adjust="qfq")
                        if not df.empty:
                            break
                    except:
                        continue
            else:
                prefixes = ["105.", "106.", "107."]
                for prefix in prefixes:
                    try:
                        code = f"{prefix}{clean_symbol}"
                        print(f"Trying {code}...")
                        df = ak.stock_us_hist_min_em(symbol=code, start_date=start_date_str, end_date=end_date_str)
                        if not df.empty:
                            break
                    except:
                        continue
                
                if not df.empty and period != '1':
                    print(f"Resampling US 1-min data to {period}-min...")
                    df['时间'] = pd.to_datetime(df['时间'])
                    df.set_index('时间', inplace=True)
                    freq_map = {'5': '5min', '15': '15min', '30': '30min', '60': '60min'}
                    freq = freq_map.get(period, '1min')
                    df_resampled = df.resample(freq).agg({
                        '开盘': 'first', '最高': 'max', '最低': 'min', '收盘': 'last', '成交量': 'sum'
                    })
                    df = df_resampled.dropna().reset_index()
        
        # --- A-Share Market / Index ---
        else: # market == 'A' or 'INDEX'
            if period in ['1', '5', '15', '30', '60']:
                if market == 'INDEX':
                    df = ak.index_zh_a_hist_min_em(symbol=clean_symbol, period=period, start_date=start_date_str, end_date=end_date_str)
                else:
                    df = ak.stock_zh_a_hist_min_em(symbol=clean_symbol, period=period, start_date=start_date_str, end_date=end_date_str, adjust='qfq')
            elif period == 'daily':
                s_d = start_date_str.split(' ')[0].replace('-', '')
                e_d = end_date_str.split(' ')[0].replace('-', '')
                if market == 'INDEX':
                    df = ak.index_zh_a_hist(symbol=clean_symbol, period="daily", start_date=s_d, end_date=e_d)
                else:
                    df = ak.stock_zh_a_hist(symbol=clean_symbol, period="daily", start_date=s_d, end_date=e_d, adjust="qfq")
            else:
                 print(f"Unsupported period: {period}")
                 return pd.DataFrame()

        if df is not None and not df.empty:
             print(f"AkShare returned shape: {df.shape}")
        
        if df.empty:
            print(f"Warning: AkShare returned empty DataFrame for start_date={start_date_str}")
            return pd.DataFrame()
            
        rename_map = {
            '时间': 'datetime', '日期': 'datetime',
            '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'
        }
        df = df.rename(columns=rename_map)
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        
        cols_to_check = ['open', 'high', 'low', 'close']
        for col in cols_to_check:
            mask_zero = (df[col] <= 0)
            if mask_zero.any():
                print(f"Warning: Found {mask_zero.sum()} rows with {col} <= 0. Fixing by using Close value...")
                df.loc[mask_zero, col] = df.loc[mask_zero, 'close']

        df = df.sort_values('datetime').reset_index(drop=True)
        return df
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_csi300_data()
    print(df.head())
