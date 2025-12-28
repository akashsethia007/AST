from nsetools import Nse

nse=Nse()
top_highs = nse.get_52_week_high()
high_stks = []

def top52highs (tickers):
    for stocks in top_highs:
        if stocks['symbol'] in tickers:
            print(stocks['symbol'])
            print("HERE IT IS")
            print(stocks['new52WHL'])
            var = {"ticker": stocks['symbol'], "new52WHL": 1}
        else:
            var = {"ticker": stocks['symbol'], "new52WHL": 0}
    high_stks.append(var)
    return high_stks