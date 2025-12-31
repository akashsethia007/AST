from nsepython import *
import yfinance as yf

def getHistDatanow(ticker,hist_date):
    data = pd.DataFrame
    try:
        ticker = ticker+".NS"
        ticker = yf.Ticker(ticker)
        data = ticker.history(start=hist_date)
        time.sleep(0.02)

    except Exception as e:
        print(f"ERROR: Failed to get the history data for {ticker} as {str(e)}")
        data=False
    return data
