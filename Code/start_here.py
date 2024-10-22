import pandas as pd
from datetime import datetime, date
import os
from utils.getHistData import getHistDatanow
from utils.get500tickers import update500tickers
from utils.set_date import set_dates
from utils.gen_st_signal import generate_st_signal
from utils.st_calculator import st_value
from utils.genBuyOrders import gen_buy_orders

print(f"Started the execution at {datetime.now()}")
cwd = os.getcwd()
today_date, hist_date = set_dates(60)
ticker_list = update500tickers()
#ticker_list = ['POLYMED'] #Hardcoded for testing purpose
failed_to_get_data = []
successful_to_get_data = []
indicator_signals = []
st_73_signals = []
st_72_signals = []
for ticker in ticker_list:
    try:
        df = getHistDatanow(ticker,today_date, hist_date)
        successful_to_get_data.append(ticker)
        df.drop_duplicates(inplace=True)
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df['date'] = df['date'].dt.date
        close_price = list(df.tail(1).iloc[0])[6]
        st_73 = st_value(df, length=7, multiplier=3)
        st73_signal, st73_value = generate_st_signal(st_73,ticker)
        st_72 = st_value(df, length=7, multiplier=2)
        st72_signal, st72_value = generate_st_signal(st_72,ticker)
        var = {
            "ticker": ticker,
            "st73_signal": st73_signal,
            "st73_value": st73_value,
            "st72_signal": st72_signal,
            "st72_value": st72_value,
            "close_price": close_price
        }
        indicator_signals.append(var)

    except Exception as e:
        print(e)
        failed_to_get_data.append(ticker)
st_73_stocks = []
st_72_stocks = []
for i in indicator_signals:
    if i['st73_signal'] == 1:
        var = {
            "ticker": i['ticker'],
            "close_price": i['close_price']
        }
        st_73_stocks.append(var)
    if i['st72_signal'] == 1:
        var = {
            "ticker": i['ticker'],
            "close_price": i['close_price']
        }
        st_72_stocks.append(var)
        #st_72_stocks.append({f"{i['ticker']: i['close_price']}"})
print(f"ST73 stocks being :: {st_73_stocks}")
print(f"ST72 stocks being :: {st_72_stocks}")
#send the list of stocks in st73 and st72 each over mail
#send the list of stocks in st73 and st72 each over WA

if len(st_73_stocks) > 0:
    gen_buy_orders(st_73_stocks)
else:
    print("No stocks in ST73 list")
if len(st_72_stocks) > 0:
    print("generating orders for st72")
    gen_buy_orders(st_72_stocks)
else:
    print("No stocks in ST72 list")
#for each customer generate buy signal
#for each customer generate GTT for each buy signal
'''
path = '\\'.join(cwd.split('\\')[:-1])+f"\data\indicatorSignals\all.csv"
indicator_signals.to_csv(path)
path = '\\'.join(cwd.split('\\')[:-1])+f"\data\indicatorSignals\st73_signals.csv"
st_73_signals.to_csv(path)
path = '\\'.join(cwd.split('\\')[:-1])+f"\data\indicatorSignals\st72_signals.csv"
st_72_signals.to_csv(path)
print(df.head())
print(df.columns)
df.info()
'''
print(successful_to_get_data)
print(failed_to_get_data)
print(f"Completed the execution at {datetime.now()}")
'''
#generate GTT
#phase3 - > Integrate with Kite
'''