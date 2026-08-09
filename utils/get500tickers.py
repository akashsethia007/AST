from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pandas as pd
import yfinance as yf
from nselib import capital_market

DT = datetime.today().strftime('%Y%m%d')
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "nifty500list"

# Number of symbols to query in a single yfinance batch call
_BATCH_SIZE = 100


def _fetch_mcaps_batch(symbols: list[str]) -> list[dict]:
    """Fetch market caps for a batch of symbols using yf.Tickers (single HTTP session)."""
    results = []
    try:
        tickers_obj = yf.Tickers(' '.join(symbols))
        for sym in symbols:
            try:
                mcap = tickers_obj.tickers[sym].info.get('marketCap')
                results.append({"Symbol": sym, "Market_Cap": mcap})
            except Exception:
                results.append({"Symbol": sym, "Market_Cap": None})
    except Exception as e:
        print(f"ERROR :: Batch mcap fetch failed: {e}")
        # Fall back: return Nones so we don't lose the symbols entirely
        results = [{"Symbol": s, "Market_Cap": None} for s in symbols]
    return results


def update500tickers() -> list[str]:
    print("INFO  :: Started updating the list of TOP 500 MCAP companies on NSE")

    eq = capital_market.equity_list()
    eq_symbols = list(eq['SYMBOL'] + '.NS')
    print(f"INFO  :: Total NSE stocks fetched: {len(eq_symbols)}")

    # Batch all symbols — far fewer HTTP round-trips than one-by-one
    market_caps = []
    total_batches = (len(eq_symbols) + _BATCH_SIZE - 1) // _BATCH_SIZE
    for batch_num, start in enumerate(range(0, len(eq_symbols), _BATCH_SIZE), start=1):
        batch = eq_symbols[start: start + _BATCH_SIZE]
        market_caps.extend(_fetch_mcaps_batch(batch))
        if batch_num % 5 == 0 or batch_num == total_batches:
            pct = round(batch_num * 100 / total_batches, 1)
            print(f"INFO  :: {pct}% of market-cap batches done ({batch_num}/{total_batches})")

    print("INFO  :: 100% done — sorting by market cap, keeping top 600")

    mcap_df = pd.DataFrame(market_caps)
    mcap_df.sort_values('Market_Cap', ascending=False, inplace=True)

    # Strip ".NS" suffix for consistency with the rest of the pipeline
    top_symbols = mcap_df.head(600)['Symbol'].str.split('.').str[0].tolist()

    out_path = DATA_DIR / f"{DT}_stockList.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({'Stock_Symbols': top_symbols}).to_csv(out_path, index=False)
    print(f"INFO  :: Stock list saved to {out_path}")

    return top_symbols
