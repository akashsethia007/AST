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
from utils import scraper
from utils import stocks
import datetime
date_now = datetime.date.today()
years_to_add = date_now.year - 1

today_date = date_now.strftime('%Y-%m-%d')
hist_date = date_now.replace(year=years_to_add).strftime('%Y-%m-%d')

df = stocks.get_data(stock_symbol="RELIANCE", start_date=hist_date, end_date=today_date)
print(df.to_string())

#phase 1 - > import the list of top 500 companies listed on NSE by market cap
#import the historical data for 1year
#run ST7(2/3)
#generate suggestion file
#phase2 - > check for the ST
#generate GTT
#phase3 - > Integrate with Kite
