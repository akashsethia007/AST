import numpy as np
import pandas as pd
from datetime import datetime, date
from nsepy import get_history
import os
from nsepy.commons import URLFetch
from requests import Session
from functools import partial
from nsepy.constants import symbol_count, symbol_list
import io
from dateutil.relativedelta import relativedelta
from nsepy.urls import equity_symbol_list_url, index_constituents_url
from utils.getHistData import getHistDatanow
from utils.get500tickers import update500tickers
from utils.set_date import set_dates
from utils.gen_st_signal import generate_st_signal
from utils.st_calculator import st_value

cwd = os.getcwd()
today_date, hist_date = set_dates(60)
ticker_list = update500tickers()
#ticker_list = ['TEJASNET','TCS'] #Hardcoded for testing purpose
failed_to_get_data = []
successful_to_get_data = []
indicator_signals = []
st_73_signals = []
st_72_signals = []
for ticker in ticker_list:
    try:
        df = getHistDatanow(ticker,today_date, hist_date)
        df.drop_duplicates(inplace=True)
        path = '\\'.join(cwd.split('\\')[:-1])+f'\data\historicalData\{ticker}.csv'
        df.to_csv(path)
        successful_to_get_data.append(ticker)
        cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        df = df[cols]
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df['date'] = df['date'].dt.date
        st_73 = st_value(df, length=7, multiplier=3)
        path = '\\'.join(cwd.split('\\')[:-1])+f'\data\st_73_data\{ticker}.csv'
        st_73.to_csv(path)
        st73_signal, st73_value = generate_st_signal(st_73,ticker)
        st73_var = { "ticker": ticker,
                     "st73_signal": st73_signal,
                     "st73_value": st73_value
        }
        st_73_signals.append(st73_var)
        st_72 = st_value(df, length=7, multiplier=2)
        path = '\\'.join(cwd.split('\\')[:-1])+f'\data\st_72_data\{ticker}.csv'
        st_72.to_csv(path)
        st72_signal, st72_value = generate_st_signal(st_72,ticker)
        st72_var = {"ticker": ticker,
                    "st72_signal": st72_signal,
                    "st72_value": st72_value
                    }
        st_72_signals.append(st72_var)
        var = {
            "ticker": ticker,
            "st73_signal": st73_signal,
            "st73_value": st73_value,
            "st72_signal": st72_signal,
            "st72_value": st72_value
        }
        indicator_signals.append(var)

    except Exception as e:
        print(e)
        failed_to_get_data.append(ticker)
print(var)
print(indicator_signals)
path = '\\'.join(cwd.split('\\')[:-1])+f"\data\indicatorSignals\all.csv"
indicator_signals.to_csv(path)
path = '\\'.join(cwd.split('\\')[:-1])+f"\data\indicatorSignals\st73_signals.csv"
st_73_signals.to_csv(path)
path = '\\'.join(cwd.split('\\')[:-1])+f"\data\indicatorSignals\st72_signals.csv"
st_72_signals.to_csv(path)

'''
print(df.head())
print(df.columns)
df.info()
#check if there are any signals for the day by filtering var on st73 and st72 signals
#st73_gen_signals
#st72_gen_signals
#st73_gen_signals.to_csv(path)
#st72_gen_signals.to_csv(path)
'''
print(successful_to_get_data)
print(failed_to_get_data)
'''
#generate suggestion file
#phase2 - > check for the ST
#generate GTT
#phase3 - > Integrate with Kite
'''