import pandas as pd
import yfinance as yf

ticker = 'BOVA11.SA'
hist = yf.download(ticker, period='15d', interval='1d', auto_adjust=False, actions=True, progress=False)
print('Raw columns:', list(hist.columns))
print(hist.tail(3))

hist_adj = yf.download(ticker, period='15d', interval='1d', auto_adjust=True, actions=False, progress=False)
print('\nAdjusted tail:')
print(hist_adj.tail(3))

last_close = float(hist.tail(1)['Close'])
last_adj_close = float(hist_adj.tail(1)['Close'])
print('\nLast Close:', last_close)
print('Last Adjusted Close:', last_adj_close)
