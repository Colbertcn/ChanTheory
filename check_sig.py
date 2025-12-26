import akshare as ak
import inspect

print("HK Min Args:", inspect.signature(ak.stock_hk_hist_min_em))
print("US Min Args:", inspect.signature(ak.stock_us_hist_min_em))
