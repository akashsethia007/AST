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
#from utils.st73 import *
cwd = os.getcwd()

#phase 1 - > import the list of top 500 companies listed on NSE by market cap

failed_to_get_data = []
successful_to_get_data = []
for ticker in ['TCS']:
    try:
        print(f"Starting the process for {ticker}")
        df = getHistDatanow(ticker)
        successful_to_get_data.append[ticker]
        cols = ['Date', 'Open Price', 'High Price', 'Low Price', 'Close Price', 'Total Traded Quantity']
        df = df[cols]
        df = df.rename(columns={'Date': 'date', 'Open Price': 'open', 'High Price': 'high', 'Close Price': 'close',
                                    'Low Price': 'low', 'Total Traded Quantity': 'volume'})
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df['date'] = df['date'].dt.date
        df.drop_duplicates(inplace=True)
        supertrend_value = st_value(df, length=7, multiplier=3)

    except Exception as e:
        failed_to_get_data.append[ticker]
        print(f"ERROR: {e}")

#generate suggestion file
#phase2 - > check for the ST
#generate GTT
#phase3 - > Integrate with Kite
