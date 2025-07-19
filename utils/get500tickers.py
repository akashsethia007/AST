import time
from nselib import capital_market
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
dt = datetime.today().strftime('%Y%m%d')

def update500tickers():
    print("INFO :: Started updating the list of TOP 500 MCAP companies on NSE")
    eq = capital_market.equity_list()
    eq_symbol = list(eq['SYMBOL'] + '.NS')
    print(f"INFO :: Total stocks being :: {len(eq_symbol)}")
    Market_Cap = []
    counter = 0
    for symbol in eq_symbol:
        time.sleep(0.01)
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            market_cap = info.get('marketCap')
            Market_Cap.append({"Symbol": symbol, "Market_Cap": market_cap})
        except Exception as e:
            print(f"get500tickers couldnt get the data for {symbol}")
        counter = counter + 1
        if counter%200 == 0:
            print(f"INFO :: {round(counter*100/len(eq_symbol),2)} % done ")

    print(f"INFO :: 100 % done ")
    print("INFO :: Updated the list with MCAP, now taking only the TOP 500 companies")
    mcap_df = pd.DataFrame(Market_Cap)
    mcap_df.sort_values('Market_Cap', ascending=False, inplace=True)
    stock_list = mcap_df.head(500)
    stock_list = list(stock_list['Symbol'])
    final_list = [i.split('.', 1)[0] for i in stock_list]
    cwd = os.getcwd()
    path = '\\'.join(cwd.split('\\')[:-1]) + f"\\data\\nifty500list\\{dt}_stockList.csv"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file = open(path, 'w')
    for item in final_list:
        file.write(item + "\n")
    file.close()
    print("INFO :: Successfully updated the file")
    return final_list
