from nsetools import Nse

nse=Nse()
top_highs = nse.get_52_week_high()
high_stks = {}

def top52highs (tickers):
    for stocks in top_highs:
        if stocks['symbol'] in tickers:
            high_stks[stocks['symbol']] = 1
    print(high_stks)
    return high_stks