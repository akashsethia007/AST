from time import sleep

from nselib import capital_market
import yfinance as yf
import pandas as pd
import os
import time

def update500tickers():
    print("Started updating the list of TOP 500 MCAP companies on NSE")
    eq = capital_market.equity_list()
    eq_symbol = list(eq['SYMBOL'] + '.NS')
    Market_Cap = []
    counter = 0
    for symbol in eq_symbol:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        market_cap = info.get('marketCap')
        Market_Cap.append({"Symbol": symbol, "Market_Cap": market_cap})
        counter = counter+1
        if counter/100 ==0:
            print("Here goes 100 stocks")
        time.sleep(0.01)

    print("Updated the list with MCAP, now taking only the TOP 500 companies")
    mcap_df = pd.DataFrame(Market_Cap)
    mcap_df.sort_values('Market_Cap', ascending=False, inplace=True)
    stock_list = mcap_df.head(500)
    stock_list = list(stock_list['Symbol'])
    final_list = [i.split('.', 1)[0] for i in stock_list]
    cwd = os.getcwd()
    path = '\\'.join(cwd.split('\\')[:-1]) + "\\data\\nifty500list\\stockList.csv"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file = open(path, 'w')
    for item in final_list:
        file.write(item + "\n")
    file.close()
    print("Successfully updated the file")
    return final_list
