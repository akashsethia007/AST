from utils import scraper
from utils import stocks
import datetime
import os

def getHistDatanow(ticker):
    print("Setting up the dates for this execution")
    date_now = datetime.date.today()
    years_to_add = date_now.year - 1
    today_date = date_now.strftime('%Y-%m-%d')
    hist_date = date_now.replace(year=years_to_add).strftime('%Y-%m-%d')

    print(f"Start date set to {today_date} and end date set to {hist_date}")
    cwd = os.getcwd()
    new_path = '\\'.join(cwd.split('\\')[:-1]) + "\\data\\historicalData\\" + ticker + ".csv"
    df = stocks.get_data(stock_symbol=ticker, start_date=hist_date, end_date=today_date)
    return df