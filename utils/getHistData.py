from utils import scraper, stocks

def getHistDatanow(ticker, today_date, hist_date):
    df = stocks.get_data(stock_symbol=ticker, start_date=hist_date, end_date=today_date)
    return df
