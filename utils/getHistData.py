from utils import scraper, stocks
from nsepython import *

def getHistDatanow(ticker, today_date, hist_date):
    df = stocks.get_data(stock_symbol=ticker, start_date=hist_date, end_date=today_date)
    return df

'''
logging.basicConfig(level=logging.DEBUG)
def equity_history(symbol,series,start_date,end_date):
    url="https://www.nseindia.com/api/historical/cm/equity?symbol="+symbol+"&series=[%22"+series+"%22]&from="+str(start_date)+"&to="+str(end_date)+""
    payload = nsefetch(url)
    print(type(payload))
    print(payload)
    return pd.DataFrame.from_records(payload["data"])
    
start_date = "23-08-2024"
end_date = "21-10-2024"
start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y")
end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y")


symbol = "SBIN"
series = "EQ"
start_date = "08-01-2021"
end_date ="14-06-2021"
df= equity_history(symbol,series,start_date,end_date)
print(type(df))

columns_required = ["TIMESTAMP", "CH_SYMBOL", "CH_SERIES", "CH_TRADE_HIGH_PRICE",
                        "CH_TRADE_LOW_PRICE", "CH_OPENING_PRICE", "CH_CLOSING_PRICE", "CH_LAST_TRADED_PRICE",
                        "CH_PREVIOUS_CLS_PRICE", "CH_TOT_TRADED_QTY", "CH_TOT_TRADED_VAL", "CH_52WEEK_HIGH_PRICE",
                        "CH_52WEEK_LOW_PRICE","TIMESTAMP"]
result = df
result = result[columns_required]
result = result.set_axis(
        ['datetime', 'Symbol', 'Series', 'high', 'low', 'open', 'close', 'Last Price',
         'Prev Close Price', 'volume', 'Total Traded Value', '52 Week High Price',
         '52 Week Low Price','date'], axis=1)
result.set_index('datetime', inplace=True)
'''