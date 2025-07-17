from datetime import datetime
import pandas as pd
import os

global st_stocks
cwd = os.getcwd()
def gen_buy_orders(st_stocks):
    custMetadata_path = '\\'.join(cwd.split('\\')[:-1]) + f"\customers\custTxn.csv"
    custMetadata = pd.read_csv(custMetadata_path, sep=';', engine='python')
    custMetadata.reset_index(inplace=True)
    for index, row in custMetadata.iterrows():
        cnt = 0
        order_list=[]
        api_key = row['broker']
        daily_txn_limit = int(row['daily_txn_limit'])
        for a in st_stocks:
            txn_limit = int(row['txn_limit'] / a['close_price'])
            tk = a['ticker']
            if cnt < daily_txn_limit:
                order = ("curl https://api.kite.trade/orders/regular \\"
                    "-H \"X-Kite-Version: 3\" \\"
                    f"-H \"Authorization: token api_key:{api_key}\" \\"
                    f"-d \"tradingsymbol={tk}\" \\"
                    "-d \"exchange=NSE\" \\"
                    "-d \"transaction_type=BUY\" \\"
                    "-d \"order_type=MARKET\" \\"
                    f"-d \"quantity={int(round(txn_limit,0))} \" \\"
                    "-d \"product=CNC\" \\"
                    "-d \"validity=DAY\" "
                    )
                order_list.append(order)
                cnt = cnt+1
        dt = datetime.today().strftime('%Y%m%d')
        path = '\\'.join(cwd.split('\\')[:-1])+f"\\transactions\\{dt}\\{row['custid']}.csv"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            for line in order_list:
                f.write(f"{line}\n")
