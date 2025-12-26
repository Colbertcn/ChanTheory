import akshare as ak
print("Searching for HK/US stock functions in akshare...")
for attr in dir(ak):
    if "hk" in attr and "hist" in attr:
        print(attr)
    if "us" in attr and "hist" in attr:
        print(attr)
