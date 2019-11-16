import bs4 as bs
import requests
import yfinance as yf
import datetime

# Get share codes from Wikipedia
resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
soup = bs.BeautifulSoup(resp.text, 'lxml')
table = soup.find('table', {'class': 'wikitable sortable'})
tickers = []
for row in table.findAll('tr')[1:]:
    ticker = row.findAll('td')[0].text
    tickers.append(ticker)

# Download data using yahoo fincance
tickers = [s.replace('\n', '') for s in tickers]
print(tickers)
start = datetime.datetime(2019,1,1)
end = datetime.datetime(2019,7,17)
data = yf.download(tickers, start=start, end=end)
print(data)
