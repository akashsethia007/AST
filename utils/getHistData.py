import os
from utils import scraper, stocks
from nsepython import *

def equity_history(ticker,start_date,end_date):
    url="https://www.nseindia.com/api/historical/cm/equity?symbol="+ticker+"&series=[%22"+"EQ"+"%22]&from="+str(start_date)+"&to="+str(end_date)+""
    try:
        payload = nsefetch(url)
        df = pd.DataFrame.from_records(payload["data"])
    except Exception as e:
        print(f"ERROR for {ticker} being :: {str(e)}")
    return pd.DataFrame.from_records(payload["data"])

def format_dataframe_result(result):
    columns_required = ["TIMESTAMP", "CH_SYMBOL", "CH_SERIES", "CH_TRADE_HIGH_PRICE",
                        "CH_TRADE_LOW_PRICE", "CH_OPENING_PRICE", "CH_CLOSING_PRICE", "CH_LAST_TRADED_PRICE",
                        "CH_PREVIOUS_CLS_PRICE", "CH_TOT_TRADED_QTY", "CH_TOT_TRADED_VAL", "CH_52WEEK_HIGH_PRICE",
                        "CH_52WEEK_LOW_PRICE", "TIMESTAMP"]
    result = result[columns_required]
    result = result.set_axis(
        ['datetime', 'Symbol', 'Series', 'high', 'low', 'open', 'close', 'Last Price',
         'Prev Close Price', 'volume', 'Total Traded Value', '52 Week High Price',
         '52 Week Low Price','date'], axis=1)
    result.set_index('datetime', inplace=True)
    result.sort_index(inplace=True)
    return result
def getHistDatanow(ticker, today_date, hist_date):
    # df = stocks.get_data(stock_symbol=ticker, start_date=hist_date, end_date=today_date)
    df = equity_history(ticker, str(hist_date), str(today_date))
    df.drop_duplicates(inplace=True)
    df = format_dataframe_result(df)
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    df['date'] = df['date'].dt.date
    result = df

    return result

'''
cwd=os.getcwd()
df = getHistDatanow('INFY','22-10-2024','02-09-2024')
path = '\\'.join(cwd.split('\\')[:-1]) + f"\\data\\nifty500list\\updated.csv"
os.makedirs(os.path.dirname(path), exist_ok=True)
df.to_csv(path)
'''

'''
logging.basicConfig(level=logging.DEBUG)
today_date set to 2024-10-23 and 
hist_date set to 2024-08-24

symbol = "SBIN"
series = "EQ"
start_date = "08-01-2021"
end_date ="14-06-2021"

result = df
result = result[columns_required]
'''