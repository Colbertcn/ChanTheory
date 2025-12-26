import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from data_fetcher import fetch_csi300_data, get_stock_name
from chan_core import ChanEngine
from visualizer import plot_chan
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DateSelector(ttk.Frame):
    def __init__(self, parent, label_text, default_date=None):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label_text)
        self.label.pack(side=tk.LEFT, padx=5)
        
        if default_date is None:
            default_date = datetime.now()
            
        # Year
        current_year = default_date.year
        self.year_var = tk.StringVar(value=str(current_year))
        self.year_cb = ttk.Combobox(self, textvariable=self.year_var, width=5, values=[str(y) for y in range(current_year-5, current_year+2)])
        self.year_cb.pack(side=tk.LEFT, padx=2)
        ttk.Label(self, text="-").pack(side=tk.LEFT)
        
        # Month
        self.month_var = tk.StringVar(value=f"{default_date.month:02d}")
        self.month_cb = ttk.Combobox(self, textvariable=self.month_var, width=3, values=[f"{m:02d}" for m in range(1, 13)])
        self.month_cb.pack(side=tk.LEFT, padx=2)
        ttk.Label(self, text="-").pack(side=tk.LEFT)
        
        # Day
        self.day_var = tk.StringVar(value=f"{default_date.day:02d}")
        self.day_cb = ttk.Combobox(self, textvariable=self.day_var, width=3, values=[f"{d:02d}" for d in range(1, 32)])
        self.day_cb.pack(side=tk.LEFT, padx=2)
        
    def get_date_str(self):
        y = self.year_var.get()
        m = self.month_var.get()
        d = self.day_var.get()
        return f"{y}-{m}-{d}"

class CustomRunnerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chan Theory Custom Data Runner")
        self.root.geometry("400x300")
        
        # 1. Period Selection
        frame_period = ttk.Frame(root, padding=10)
        frame_period.pack(fill=tk.X)
        
        ttk.Label(frame_period, text="Symbol:").pack(side=tk.LEFT, padx=5)
        self.symbol_var = tk.StringVar(value="000300")
        symbol_entry = ttk.Entry(frame_period, textvariable=self.symbol_var, width=8)
        symbol_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_period, text="K-Line Period:").pack(side=tk.LEFT, padx=5)
        self.period_var = tk.StringVar(value="30")
        period_cb = ttk.Combobox(frame_period, textvariable=self.period_var, width=10, values=["1", "5", "30", "daily"])
        period_cb.pack(side=tk.LEFT, padx=5)
        
        # 2. Start Date
        frame_start = ttk.Frame(root, padding=10)
        frame_start.pack(fill=tk.X)
        self.start_selector = DateSelector(frame_start, "Start Date:")
        self.start_selector.pack(side=tk.LEFT)
        
        # 3. End Date
        frame_end = ttk.Frame(root, padding=10)
        frame_end.pack(fill=tk.X)
        self.end_selector = DateSelector(frame_end, "End Date:  ")
        self.end_selector.pack(side=tk.LEFT)
        
        # 4. Run Button
        frame_btn = ttk.Frame(root, padding=20)
        frame_btn.pack(fill=tk.X)
        btn_run = ttk.Button(frame_btn, text="Fetch Data & Plot", command=self.run_task)
        btn_run.pack(expand=True, fill=tk.X)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(root, textvariable=self.status_var, foreground="blue").pack(side=tk.BOTTOM, pady=5)

    def run_task(self):
        symbol = self.symbol_var.get().strip()
        period = self.period_var.get()
        start_str = self.start_selector.get_date_str()
        end_str = self.end_selector.get_date_str()
        
        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol.")
            return
        
        # Validate dates
        try:
            s_dt = datetime.strptime(start_str, "%Y-%m-%d")
            e_dt = datetime.strptime(end_str, "%Y-%m-%d")
            if s_dt > e_dt:
                messagebox.showerror("Error", "Start date must be before end date.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid date.")
            return

        # Add time suffix
        start_full = f"{start_str} 00:00:00"
        end_full = f"{end_str} 23:59:59"
        
        period_display = f"{period}min" if period != 'daily' else "daily"
        self.status_var.set(f"Fetching {symbol} {period_display} data from {start_str} to {end_str}...")
        self.root.update()
        
        try:
            df = fetch_csi300_data(period=period, start_date=start_full, end_date=end_full, symbol=symbol)
            
            if df.empty:
                self.status_var.set("Error: No data fetched.")
                messagebox.showwarning("No Data", f"No data returned for {symbol} in this range.\nNote: 1-min data availability might be limited to recent history.\n\nRange: {start_str} to {end_str}")
                return
                
            self.status_var.set(f"Fetched {len(df)} records. Processing...")
            self.root.update()
            
            # Chan Engine
            engine = ChanEngine(df)
            engine.process_inclusion()
            engine.find_fenxing()
            engine.draw_bi()
            
            # Get Stock Name
            try:
                stock_name = get_stock_name(symbol)
            except:
                stock_name = None

            # Show Plot
            self.show_plot_window(df, engine, period, symbol, stock_name)
            self.status_var.set("Done.")
            
        except Exception as e:
            self.status_var.set("Error occurred.")
            messagebox.showerror("Exception", str(e))

    def show_plot_window(self, df, engine, period, stock_code, stock_name):
        top = tk.Toplevel(self.root)
        
        period_str = f"{period} Min" if period != 'daily' else "Daily"
        
        title_part = f"{stock_name} {stock_code}" if stock_name else stock_code
        top.title(f"Chan Chart - {title_part} {period_str}")
        top.geometry("1200x800")
        
        fig = plot_chan(df, engine, period=period, stock_code=stock_code, stock_name=stock_name, return_figure=True)
        
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = CustomRunnerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
