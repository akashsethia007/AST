import numpy as np
import pandas as pd
from datetime import datetime,date
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
from utils.gen_signal import generate_signal

cwd = os.getcwd()
today_date, hist_date = set_dates()
#phase 1 - > import the list of top 500 companies listed on NSE by market cap
ticker_list = update500tickers()
failed_to_get_data = []
successful_to_get_data = []

for ticker in ticker_list:
    try:
        df = getHistDatanow(ticker,today_date, hist_date)

        successful_to_get_data.append(ticker)
        cols = ['Date', 'Open Price', 'High Price', 'Low Price', 'Close Price', 'Total Traded Quantity']
        df = df[cols]
        df = df.rename(columns={'Date': 'date', 'Open Price': 'open', 'High Price': 'high', 'Close Price': 'close',
                                    'Low Price': 'low', 'Total Traded Quantity': 'volume'})
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df['date'] = df['date'].dt.date
        df.drop_duplicates(inplace=True)
        supertrend_value = st_value(df, length=7, multiplier=3)
        #gen_signal = generate_signal(ticker, supertrend_value)

    except Exception as e:
        failed_to_get_data.append(ticker)

print(successful_to_get_data)
print(failed_to_get_data)
#generate suggestion file
#phase2 - > check for the ST
#generate GTT
#phase3 - > Integrate with Kite
