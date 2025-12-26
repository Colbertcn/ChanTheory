import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from data_fetcher import fetch_csi300_data
from chan_core import ChanEngine
from visualizer import plot_chan

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ")
        return user_input.strip() or default
    else:
        return input(f"{prompt}: ").strip()

def parse_date(date_str, year):
    """Parse MM-DD string to YYYY-MM-DD HH:MM:SS string"""
    try:
        # Assuming MM-DD format
        month, day = map(int, date_str.split('-'))
        dt = datetime(year, month, day)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        print("Invalid date format. Please use MM-DD.")
        return None

def main():
    print("="*50)
    print("Chan Theory Custom Data Runner")
    print("="*50)
    
    # 1. Period
    while True:
        period = get_input("Enter period (1, 5, 30)", "30")
        if period in ['1', '5', '30']:
            break
        print("Invalid period. Allowed: 1, 5, 30")
        
    # 2. Year (Default to current year)
    current_year = datetime.now().year
    year_input = get_input("Enter Year", str(current_year))
    try:
        year = int(year_input)
    except:
        year = current_year
        
    # 3. Start Date
    while True:
        start_input = get_input("Enter Start Date (MM-DD)")
        start_date_str = parse_date(start_input, year)
        if start_date_str:
            break
            
    # 4. End Date
    while True:
        end_input = get_input("Enter End Date (MM-DD)", datetime.now().strftime('%m-%d'))
        end_date_str = parse_date(end_input, year)
        if end_date_str:
            # Set end time to end of day
            end_date_str = end_date_str.replace("00:00:00", "23:59:59")
            break

    print(f"\nFetching {period} min data from {start_date_str} to {end_date_str}...")
    
    # Fetch Data
    df = fetch_csi300_data(period=period, start_date=start_date_str, end_date=end_date_str)
    
    if df.empty:
        print("Error: No data fetched. Please check your dates and try again.")
        input("Press Enter to exit...")
        return

    print(f"Data fetched: {len(df)} records")
    
    # Process
    print("Processing Chan Theory logic...")
    engine = ChanEngine(df)
    engine.process_inclusion()
    engine.find_fenxing()
    engine.draw_bi()
    
    # Plot
    print("Plotting...")
    # Using plot_chan with return_figure=False to save file, or we can use True and plt.show()
    # Since this is a standalone script, let's use plt.show()
    fig = plot_chan(df, engine, period=period, return_figure=True)
    
    # Show plot
    plt.show()
    
    print("Done.")

if __name__ == "__main__":
    main()
