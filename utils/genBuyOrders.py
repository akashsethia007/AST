from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.writeFiles import writeFiles

_CUSTOMERS_PATH = Path(__file__).resolve().parents[1] / "customers" / "custTxn.csv"


def gen_buy_orders(st_stocks):
    """Generate Zerodha Kite curl buy-order commands for each customer."""
    cust_txn = pd.read_csv(_CUSTOMERS_PATH, sep=';', engine='python')
    dt = datetime.today().strftime('%Y%m%d')
    out_dir = Path(__file__).resolve().parents[1] / "transactions" / dt

    for _, row in cust_txn.iterrows():
        api_key = row['broker']
        daily_limit = int(row['daily_txn_limit'])
        order_list = []

        for stock in st_stocks[:daily_limit]:
            qty = int(round(row['txn_limit'] / stock['close_price'], 0))
            tk = stock['ticker']
            order = (
                f"curl https://api.kite.trade/orders/regular \\\n"
                f"  -H \"X-Kite-Version: 3\" \\\n"
                f"  -H \"Authorization: token api_key:{api_key}\" \\\n"
                f"  -d \"tradingsymbol={tk}\" \\\n"
                f"  -d \"exchange=NSE\" \\\n"
                f"  -d \"transaction_type=BUY\" \\\n"
                f"  -d \"order_type=MARKET\" \\\n"
                f"  -d \"quantity={qty}\" \\\n"
                f"  -d \"product=CNC\" \\\n"
                f"  -d \"validity=DAY\""
            )
            order_list.append(order)

        path = out_dir / f"{row['custid']}.csv"
        writeFiles(str(path), order_list)
