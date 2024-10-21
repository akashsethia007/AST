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

cwd = os.getcwd()
today_date, hist_date = set_dates(60)
#ticker_list = update500tickers()
ticker_list = ['TCS','INFY','RELIANCE'] #Hardcoded for testing purpose
failed_to_get_data = []
successful_to_get_data = []
indicator_signals = {}

for ticker in ticker_list:
    try:
        df = getHistDatanow(ticker,today_date, hist_date)
        df.drop_duplicates(inplace=True)
        successful_to_get_data.append(ticker)
        cols = ['Date', 'Open Price', 'High Price', 'Low Price', 'Close Price', 'Total Traded Quantity']
        df = df[cols]
        df = df.rename(columns={'Date': 'date', 'Open Price': 'open', 'High Price': 'high', 'Close Price': 'close',
                                    'Low Price': 'low', 'Total Traded Quantity': 'volume'})
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df['date'] = df['date'].dt.date
        path = r'PycharmProjects/AST/data/historicalData/{ticker}.csv'
        df.to_csv(path)
        st_73 = st_value(df, length=7, multiplier=3)
        path = r'PycharmProjects/AST/data/historicalData/st_73_{ticker}.csv'
        st_73.to_csv(path)
        st73_signal, st73_value = generate_st_signal(st_73)
        st_72 = st_value(df, length=7, multiplier=2)
        path = r'PycharmProjects/AST/data/historicalData/st_72_{ticker}.csv'
        st72.to_csv(path)
        st72_signal, st72_value = generate_st_signal(st_72)
        print(f"Received the signal for {ticker}")
        var = {
            ticker: ticker,
            st73_signal: st73_signal,
            st73_value: st73_value,
            st72_signal: st72_signal,
            st72_value: st72_value
        }
        indicator_signals.update(var)

    except Exception as e:
        failed_to_get_data.append(ticker)
#check if there are any signals for the day by filtering var on st73 and st72 signals
#st73_gen_signals
#st72_gen_signals
#st73_gen_signals.to_csv(path)
#st72_gen_signals.to_csv(path)
print(successful_to_get_data)
print(failed_to_get_data)
#generate suggestion file
#phase2 - > check for the ST
#generate GTT
#phase3 - > Integrate with Kite
