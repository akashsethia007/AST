from datetime import datetime, date
import os
from utils.getHistData import getHistDatanow
from utils.get500tickers import update500tickers
from utils.set_date import set_dates
from utils.gen_st_signal import generate_st_signal
from utils.st_calculator import st_value
from utils.genBuyOrders import gen_buy_orders
print(f"INFO :: Started the execution at {datetime.now()}")
cwd = os.getcwd()
today_date, hist_date = set_dates(45)
ticker_list = update500tickers()
print(f"INFO :: Created the list of top MCAP companies at {datetime.now()}")
#ticker_list = ['HDFCBANK'] #Hardcoded for testing purpose
failed_to_get_data = []
successful_to_get_data = []
indicator_signals = []
st_73_signals = []
st_72_signals = []
for ticker in ticker_list:
    try:
        df = getHistDatanow(ticker,today_date, hist_date)
        successful_to_get_data.append(ticker)
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
        print(f"Failed to do anything for {ticker} as the problem is {e}")
        failed_to_get_data.append(ticker)
print(f"INFO :: Done with the execution at {datetime.now()}")
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

print(f"INFO:: ST73 stocks being :: {st_73_stocks}")
print(f"INFO:: ST72 stocks being :: {st_72_stocks}")

if len(st_73_stocks) > 0:
    gen_buy_orders(st_73_stocks)
else:
    print("INFO:: No stocks in ST73 list")
if len(st_72_stocks) > 0:
    gen_buy_orders(st_72_stocks)
else:
    print("INFO:: No stocks in ST72 list")
print(successful_to_get_data)
print(failed_to_get_data)
print(f"Completed the execution at {datetime.now()}")

'''
#generate GTT
#phase3 - > Integrate with Kite
'''