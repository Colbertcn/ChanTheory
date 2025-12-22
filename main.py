from data_fetcher import fetch_csi300_data
from chan_core import ChanEngine
from visualizer import plot_chan

# =================================================================================================
# 主程序入口 (Main Entry Point)
#
# 协调数据获取、缠论计算核心、可视化绘图三个模块。
# 流程：
# 1. 获取数据 (Fetch Data)
# 2. 初始化引擎 (Init Engine)
# 3. 包含处理 (Inclusion Process)
# 4. 寻找分型 (Find FenXing)
# 5. 画笔 (Draw Bi)
# 6. 可视化 (Visualize)
# =================================================================================================

def main():
    periods = ['1', '5', '30']
    
    for period in periods:
        print(f"\n{'='*50}")
        print(f"Processing {period}-minute data... / 正在处理 {period} 分钟数据...")
        print(f"{'='*50}")
        
        # Determine days based on period
        days_map = {
            '1': 1,
            '5': 5,
            '30': 30
        }
        days = days_map.get(period, 15) # Default to 15 if not found
        
        print(f"Fetching real-time data ({period} min, last {days} days)... / 正在获取实时数据...")
        # Fetch data for the specified period
        df = fetch_csi300_data(period=period, days=days)
        
        if df.empty:
            print(f"Error: No data fetched for {period} min. Skipping.")
            continue

        print(f"Data fetched: {len(df)} records")
        print(f"Latest data point: {df.iloc[-1]['datetime']}")
        
        print(f"Initializing Chan Engine ({period} min)... / 初始化缠论引擎...")
        engine = ChanEngine(df)
        
        print("Step 1: Processing Inclusion... / 步骤1：K线包含处理...")
        engine.process_inclusion()
        print(f"Standard K-lines: {len(engine.standard_klines)}")
        
        print("Step 2: Finding Fenxing... / 步骤2：识别顶底分型...")
        engine.find_fenxing()
        print(f"Fenxings found: {len(engine.fenxings)}")
        
        print("Step 3: Drawing Bi... / 步骤3：绘制笔（严格5K原则）...")
        engine.draw_bi()
        print(f"Bis found: {len(engine.bis)}")
        
        # Debug print some Bis
        if engine.bis:
            print("Sample Bis / 笔样本预览:")
            for i, bi in enumerate(engine.bis[:3]):
                print(f"Bi {i}: {bi}")
        
        print(f"Visualizing {period} min data...")
        plot_chan(df, engine, period=period)
        
    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()
