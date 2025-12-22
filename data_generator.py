import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =================================================================================================
# 数据生成器 (Data Generator)
#
# 用于生成符合沪深300指数特征的虚构K线数据。
# 支持自定义时间范围和生成天数。
# 默认生成15分钟级别的K线数据。
# =================================================================================================

def generate_csi300_data(start_date='2023-01-01', days=60):
    """
    生成虚构的沪深300 15分钟K线数据。
    Generates fictional CSI 300 15-minute K-line data.
    
    参数:
        start_date (str): 起始日期，格式 'YYYY-MM-DD'
        days (int): 生成的交易日数量
        
    返回:
        pd.DataFrame: 包含 datetime, open, high, low, close, volume 的DataFrame
    """
    np.random.seed(42)  # 固定随机种子，保证结果可复现 / For reproducibility
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    data_list = []
    
    current_price = 4000.0  # 沪深300初始点位 / Starting price for CSI 300
    
    for i in range(days):
        current_date = start_dt + timedelta(days=i)
        
        # Skip weekends / 跳过周末
        if current_date.weekday() >= 5:
            continue
            
        # Trading hours: 9:30-11:30, 13:00-15:00 / 交易时间段
        morning_start = current_date.replace(hour=9, minute=30)
        morning_end = current_date.replace(hour=11, minute=30)
        afternoon_start = current_date.replace(hour=13, minute=0)
        afternoon_end = current_date.replace(hour=15, minute=0)
        
        timestamps = []
        curr = morning_start
        while curr < morning_end:
            timestamps.append(curr)
            curr += timedelta(minutes=15)
            
        curr = afternoon_start
        while curr < afternoon_end:
            timestamps.append(curr)
            curr += timedelta(minutes=15)
            
        for ts in timestamps:
            # Simulate price movement (15 min volatility is higher than 1 min)
            # 模拟价格变动：15分钟的波动率比1分钟大，这里放大波动
            # Scaling volatility by approx sqrt(15) ~ 4
            change = np.random.normal(0, 6.0) 
            open_price = current_price
            close_price = current_price + change
            
            # High and Low derived from Open and Close with some volatility
            # 基于开收盘价增加随机波动生成最高/最低价
            high_price = max(open_price, close_price) + abs(np.random.normal(0, 2.0))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, 2.0))
            
            # 模拟成交量
            volume = int(np.random.exponential(150000)) # Higher volume for 15min
            
            data_list.append({
                'datetime': ts,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
            
            current_price = close_price

    df = pd.DataFrame(data_list)
    return df

if __name__ == "__main__":
    df = generate_csi300_data()
    print(df.head())
    print(f"Total records: {len(df)}")
    df.to_csv('csi300_15min_fictional.csv', index=False)
