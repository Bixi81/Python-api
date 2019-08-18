import yfinance as yf
import datetime

stocks = ["VOW3.DE", "SAP.DE"]
start = datetime.datetime(2000,1,1)
end = datetime.datetime(2019,7,17)
data = yf.download(stocks, start=start, end=end)
print(data)
