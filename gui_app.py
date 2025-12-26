import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

from data_fetcher import fetch_csi300_data, get_stock_name
from chan_core import ChanEngine
from visualizer import plot_chan

class ChanVisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chan Theory Visualizer - Realtime Stock Data")
        self.root.geometry("1200x800")
        
        # Data Cache (Thread-safe dict usually okay for simple puts/gets in Python GIL)
        # Key: (symbol, period), Value: DataFrame
        self.data_cache = {} 
        self.name_cache = {} # Key: symbol, Value: str
        self.loading_status = {} # Key: (symbol, period), Value: 'loading', 'done', 'error'
        
        # Current State
        self.current_symbol = '000300'
        self.current_period = '1'
        self.current_days = 1
        
        # Define Presets
        self.presets = [
            ("1 Min / 1 Day", '1', 1),
            ("1 Min / 5 Days", '1', 5),
            ("5 Min / 5 Days", '5', 5),
            ("5 Min / 15 Days", '5', 15),
            ("30 Min / 5 Days", '30', 5),
            ("30 Min / 15 Days", '30', 15),
            ("Daily / 60 Days", 'daily', 60)
        ]
        
        # UI Setup
        self.setup_ui()
        
        # Initial Load
        # Don't load anything initially
        # self.start_background_loader()

    # REMOVED start_background_loader method
    # def start_background_loader(self): ...

    def fetch_data_task(self, period, days, symbol):
        key = (symbol, period)
        try:
            print(f"[Background] Fetching {symbol} {period} data (last {days} days)...")
            
            # Fetch name if not cached (best effort)
            if symbol not in self.name_cache:
                try:
                    if symbol == '000300':
                        name = "沪深300"
                    else:
                        name = get_stock_name(symbol)
                    self.name_cache[symbol] = name
                    print(f"[Background] Got name for {symbol}: {name}")
                except Exception as e:
                    print(f"[Background] Failed to get name for {symbol}: {e}")
            
            df = fetch_csi300_data(period=period, days=days, symbol=symbol)
            if not df.empty:
                self.data_cache[key] = df
                self.loading_status[key] = 'done'
                print(f"[Background] {symbol} {period} data ready.")
                
                # Auto-refresh UI if this is the requested one?
                # Thread-safe UI update using after()
                
                # To be user friendly:
                self.root.after(0, lambda: self.check_and_update_plot(period, symbol))
                
            else:
                self.loading_status[key] = 'error'
        except Exception as e:
            print(f"[Background] Error fetching {symbol} {period}: {e}")
            self.loading_status[key] = 'error'

    def check_and_update_plot(self, period, symbol):
        # This is called in main thread
        # If we want to auto-show, we can. But which 'days' setting?
        # Maybe we should store "pending_request" = (period, days, symbol)
        # If matches, show it.
        if hasattr(self, 'pending_request') and self.pending_request is not None:
            req_period, req_days, req_symbol = self.pending_request
            if req_period == period and req_symbol == symbol:
                self.current_period = period
                self.current_days = req_days
                self.current_symbol = symbol
                self.update_plot()
                self.status_label.config(text=f"Showing: {symbol} {period} period, last {self.current_days} days")
                # Removed messagebox as per user request
                # messagebox.showinfo("Data Ready", f"{period} data is ready!")
                self.pending_request = None

    def setup_ui(self):
        # Top Toolbar
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Stock Code Input
        ttk.Label(toolbar, text="Symbol:").pack(side=tk.LEFT, padx=5)
        self.symbol_var = tk.StringVar(value='000300')
        self.symbol_entry = ttk.Entry(toolbar, textvariable=self.symbol_var, width=8)
        self.symbol_entry.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        ttk.Label(toolbar, text="Select Scenario:").pack(side=tk.LEFT, padx=5)
        
        # Create Buttons for each preset
        for label, period, days in self.presets:
            btn = ttk.Button(
                toolbar, 
                text=label, 
                command=lambda p=period, d=days: self.on_preset_click(p, d)
            )
            btn.pack(side=tk.LEFT, padx=5)
            
        # Status Label
        self.status_label = ttk.Label(toolbar, text="Data loading in background...", foreground="blue")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main Plot Area
        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas = None

    def on_preset_click(self, period, days):
        symbol = self.symbol_var.get().strip()
        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol.")
            return
            
        key = (symbol, period)
        
        # Check cache first
        if key in self.data_cache:
            self.current_period = period
            self.current_days = days
            self.current_symbol = symbol
            self.update_plot()
            self.status_label.config(text=f"Showing: {symbol} {period} period, last {days} days")
            return
            
        # Check loading status
        status = self.loading_status.get(key, 'unknown')
        if status == 'loading':
            messagebox.showinfo("Please Wait", "Data is still loading. Please try this option again later.\n\n后台数据正在加载中，请稍后再试。")
            return
            
        # Not loaded and not loading (e.g. error or not started)
        # Launch load immediately
        self.loading_status[key] = 'loading'
        self.status_label.config(text=f"Fetching {symbol} {period} data...")
        self.pending_request = (period, days, symbol) # Store intent
        
        # Start a thread to fetch this specific data
        # Fetch just enough? Or consistent amount?
        # Let's fetch the requested amount to be safe, or stick to the max logic if we want consistent cache.
        # But user said "Avoid initial massive data... fetch after selection".
        # So we fetch what is requested. But to avoid re-fetching if they switch 5->15 days, maybe fetch max(days, 15)?
        days_to_fetch = max(days, 15) if period != 'daily' else max(days, 60)
        
        # We need to pass the updated task to thread
        t = threading.Thread(target=self.fetch_data_task, args=(period, days_to_fetch, symbol))
        t.daemon = True
        t.start()
        
        # Show message that we started
        messagebox.showinfo("Fetching Data", f"Fetching {symbol} {period} min data... Please wait a moment.\n\n正在获取数据，请稍候。")

    def update_plot(self):
        # Clear existing canvas
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            plt.close('all') 
        
        key = (self.current_symbol, self.current_period)
        df_full = self.data_cache.get(key)
        if df_full is None or df_full.empty:
            return

        # Slice data
        last_date = df_full['datetime'].max()
        start_date = last_date - timedelta(days=self.current_days)
        
        # Reset index is crucial here!
        # When we slice, we must reset index so that ChanEngine sees 0, 1, 2...
        # and mpf.plot also plots 0, 1, 2... matching the engine's indices.
        df_display = df_full[df_full['datetime'] > start_date].copy().reset_index(drop=True)
        
        if df_display.empty:
            df_display = df_full.tail(100).reset_index(drop=True) 
        
        # Run Engine
        engine = ChanEngine(df_display)
        engine.process_inclusion()
        engine.find_fenxing()
        engine.draw_bi()
        
        # Plot
        # For daily, period label might need adjustment if visualizer expects '15' etc.
        # visualizer uses period string for title.
        display_period = self.current_period
        if self.current_period == 'daily':
            display_period = 'Daily'
            
        stock_name = self.name_cache.get(self.current_symbol)
            
        fig = plot_chan(df_display, engine, period=display_period, stock_code=self.current_symbol, stock_name=stock_name, return_figure=True)
        
        # Embed
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def main_gui():
    root = tk.Tk()
    app = ChanVisApp(root)
    root.mainloop()

if __name__ == "__main__":
    main_gui()
