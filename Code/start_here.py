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
from utils.st73 import *
cwd = os.getcwd()

#phase 1 - > import the list of top 500 companies listed on NSE by market cap
for ticker in ['TCS']:
    df = getHistDatanow(ticker)
    #ticker_st73 = st73()
cols = ['open', 'high', 'low', 'close', 'volume']
st_df = df[cols]
print(st_df.to_string())
new_path_st = '\\'.join(cwd.split('\\')[:-1]) + "\\data\\historicalData\\" + ticker + "_st.csv"
st_df.to_csv(new_path_st)
st, upt, dt = get_supertrend(st_df)
#st73_df = df[cols]
#run ST7(2/3)
#generate suggestion file
#phase2 - > check for the ST
#generate GTT
#phase3 - > Integrate with Kite
