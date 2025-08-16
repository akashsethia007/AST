import os
import time
from datetime import datetime
import subprocess
import sys
#subprocess.run([sys.executable, "-m", "pip", "freeze"])
from utils.genBuyOrders import gen_buy_orders
from utils.gen_st_signal import generate_st_signal
from utils.get500tickers import update500tickers
from utils.getHistData import getHistDatanow
from utils.set_date import set_dates
from utils.st_calculator import st_value
from utils.writeSTFiles import writeSTFiles
import logging

logger = logging.getLogger('yfinance')
logger.disabled = True
logger.propagate = False
peewee_logger = logging.getLogger('peewee')

peewee_logger.disabled = True
peewee_logger.setLevel(logging.WARNING)
peewee_logger.handlers = []

print(f"INFO :: Started the execution at {datetime.now()}")

today_date, hist_date = set_dates(400)
ticker_list = update500tickers()
print(f"INFO :: Created the list of top MCAP companies at {datetime.now()}")
#ticker_list = ['HDFCBANK'] #Hardcoded for testing purpose
indicator_signals = []
st_73_signals = []
st_72_signals = []
counter = 0
print(f"INFO :: Starting Indicator calculations at {datetime.now()}")
for ticker in ticker_list:
    counter = counter + 1
    if counter % 125 == 0:
        print(f"INFO :: {round(counter * 100 / len(ticker_list), 2)}% done.")
    time.sleep(0.01)
    try:
        df = getHistDatanow(ticker, hist_date)
        close_price = list(df.tail(1).iloc[0])[3]
        df['200DMA'] = df['Close'].rolling(window=200).mean()
        DMA_200 = round(list(df.tail(1).iloc[0])[7], 2)
        try:
            st_73 = st_value(df, length=7, multiplier=3)
            st73_signal, st73_value = generate_st_signal(st_73, ticker)
        except Exception as e:
            print(f"ERROR :: Failed to get SuperTrend 73 value for {ticker}")
            st73_signal, st73_value = -1, -1
        try:
            st_72 = st_value(df, length=7, multiplier=2)
            st72_signal, st72_value = generate_st_signal(st_72, ticker)
        except Exception as e:
            print(f"ERROR:: Failed to get SuperTrend 72 value for {ticker}")
            st72_signal, st72_value = -1, -1

        var = {
            "ticker": ticker,
            "st73_signal": st73_signal,
            "st73_value": st73_value,
            "st72_signal": st72_signal,
            "st72_value": st72_value,
            "close_price": round(close_price,2),
            "DMA_200": round(DMA_200,2)
        }
        indicator_signals.append(var)
    except Exception as e:
        print(f"ERROR :: Failed to get Historical data for {ticker} as the problem is {e}")
print(f"INFO :: Done with the execution at {datetime.now()}")
st_73_stocks = []
st_73_dma_stocks = []
st_72_stocks = []
st_72_dma_stocks = []
for i in indicator_signals:
    if i['st73_signal'] == 1:
        var = {
            "ticker": i['ticker'],
            "close_price": i['close_price'],
            "st73_value" : i['st73_value'],
            "DMA_200": i["DMA_200"]
        }
        st_73_stocks.append(var)
    if i['st72_signal'] == 1:
        var = {
            "ticker": i['ticker'],
            "close_price": i['close_price'],
            "st72_value": i['st72_value'],
            "DMA_200": i["DMA_200"]
        }
        st_72_stocks.append(var)
    if i['st73_signal'] == 1 and i['close_price'] > i['DMA_200']:
        var = {
            "ticker": i['ticker'],
            "close_price": i['close_price'],
            "st73_value": i['st73_value'],
            "DMA_200": i["DMA_200"]
        }
        st_73_dma_stocks.append(var)
    if i['st72_signal'] == 1 and i['close_price'] > i['DMA_200']:
        var = {
            "ticker": i['ticker'],
            "close_price": i['close_price'],
            "st72_value": i['st72_value'],
            "DMA_200": i["DMA_200"]
        }
        st_72_dma_stocks.append(var)

print(f"INFO :: ST73 stocks being :: {st_73_stocks}")
print(f"INFO :: ST73 with 200 DMA :: {st_73_dma_stocks}")
print(f"INFO :: ST72 stocks being :: {st_72_stocks}")
print(f"INFO :: ST72 with 200 DMA :: {st_72_dma_stocks}")
cwd = os.getcwd()
dt = datetime.today().strftime('%Y%m%d')
path_indicator_signals = '\\'.join(cwd.split('\\')[:-1]) + f"\\indicator_signals\\{dt}_indicator_signals.csv"
path73 = '\\'.join(cwd.split('\\')[:-1]) + f"\\data\\st\\{dt}_st73.csv"
path72 = '\\'.join(cwd.split('\\')[:-1]) + f"\\data\\st\\{dt}_st72.csv"
path73dma = '\\'.join(cwd.split('\\')[:-1]) + f"\\data\\st\\{dt}_st73_dma.csv"
path72dma = '\\'.join(cwd.split('\\')[:-1]) + f"\\data\\st\\{dt}_st72_dma.csv"

writeSTFiles(path_indicator_signals, indicator_signals)
if len(st_73_stocks) > 0:
    print("INFO :: Writing the ST73 file")
    writeSTFiles(path73, st_73_stocks)
    if len(st_73_dma_stocks) > 0:
        writeSTFiles(path73dma, st_73_dma_stocks)
    print("INFO :: Generating buy orders for ST73")
    gen_buy_orders(st_73_stocks)
else:
    print("INFO :: No stocks in ST73 list")

if len(st_72_stocks) > 0:
    print("INFO :: Writing the ST72 file")
    writeSTFiles(path72, st_72_stocks)
    if len(st_72_dma_stocks) > 0:
        writeSTFiles(path72dma, st_72_dma_stocks)
    print("INFO :: Generating buy orders for ST72")
    gen_buy_orders(st_72_stocks)
else:
    print("INFO :: No stocks in ST72 list")

print(f"INFO :: Completed the execution at {datetime.now()}")

'''
#generate GTT
#phase3 - > Integrate with Kite
phase4 -> update gtt
'''
