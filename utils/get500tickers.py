from nselib import capital_market
import yfinance as yf
import pandas as pd
import os

def update500tickers():
    print("Started updating the list of TOP 500 MCAP companies on NSE")
    NSE_Equity = capital_market.equity_list()
    NSE_Equity_Symbol = list(NSE_Equity['SYMBOL'] + '.NS')
    Market_Cap = []
    for symbol in NSE_Equity_Symbol:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        market_cap = info.get('marketCap')
        Market_Cap.append({"Symbol" : symbol, "Market_Cap":market_cap})

    print("Updated the list with MCAP, now takin gonly the TOP 500 companies")
    Market_Cap_df = pd.DataFrame(Market_Cap)
    Market_Cap_df.sort_values('Market_Cap', ascending=False, inplace=True)
    stock_list = Market_Cap_df.head(500)
    stock_list = list(stock_list['Symbol'])
    final_list = [i.split('.', 1)[0] for i in stock_list]
    cwd = os.getcwd()
    path = '\\'.join(cwd.split('\\')[:-1]) + "\\data\\stockList.csv"
    file = open(path, 'w')
    for item in final_list:
        file.write(item + "\n")
    file.close()
    return final_list
test = update500tickers()
