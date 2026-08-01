from __future__ import annotations

import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.genBuyOrders import gen_buy_orders
from utils.gen_st_signal import generate_st_signal
from utils.get500tickers import update500tickers
from utils.getHistData import getHistDataBatch, BATCH_SIZE
from utils.set_date import set_dates
from utils.st_calculator import st_value
from utils.writeFiles import writeFiles
from utils.writeSTFiles import writeSTFiles

# ---------------------------------------------------------------------------
# Silence noisy third-party loggers
# ---------------------------------------------------------------------------
for _name in ('yfinance', 'peewee'):
    _l = logging.getLogger(_name)
    _l.disabled = True
    _l.propagate = False

# ---------------------------------------------------------------------------
# Paths — anchored to repo root, independent of working directory
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DT   = datetime.today().strftime('%Y%m%d')

PATH_ST73          = ROOT / "data" / "st"           / f"{DT}_st73.csv"
PATH_ST72          = ROOT / "data" / "st"           / f"{DT}_st72.csv"
PATH_ST73_DMA      = ROOT / "data" / "st"           / f"{DT}_st73_dma.csv"
PATH_ST72_DMA      = ROOT / "data" / "st"           / f"{DT}_st72_dma.csv"
PATH_DMA_CHANGE    = ROOT / "data" / "10dma"        / f"{DT}_10dma.csv"
PATH_500_LIST      = ROOT / "data" / "nifty500list" / f"{DT}_stockList.csv"
PATH_START_SIGNAL  = ROOT / "data" / "start"        / f"{DT}_start_signal.csv"
PATH_FINISH_SIGNAL = ROOT / "data" / "start"        / f"{DT}_finish_signal.csv"
PATH_IND_SIGNALS   = ROOT / "indicator_signals"     / f"{DT}_indicator_signals.csv"

# How many threads to use for batch processing.
# Each thread fetches a batch of BATCH_SIZE tickers in one HTTP call.
_WORKERS = 25


# ---------------------------------------------------------------------------
# Per-batch worker
# ---------------------------------------------------------------------------
def _process_batch(batch: list[str], hist_date: str) -> list[dict]:
    """Download history for `batch` tickers and compute all indicators.

    Returns a list of result dicts (one per successfully processed ticker).
    """
    hist_map = getHistDataBatch(batch, hist_date)
    results = []

    for ticker in batch:
        df = hist_map.get(ticker)
        if df is None or len(df) < 200:
            continue
        try:
            close = df['Close']

            # Compute rolling series once — reuse for both last and second-to-last
            rolling_10  = close.rolling(10).mean()
            rolling_200 = close.rolling(200).mean()

            close_price      = round(float(close.iloc[-1]), 2)
            prev_close_price = float(close.iloc[-2])
            dma_10           = round(float(rolling_10.iloc[-1]), 2)
            prev_dma_10      = round(float(rolling_10.iloc[-2]), 2)
            dma_200          = round(float(rolling_200.iloc[-1]), 2)

            dma_change = 1 if (prev_close_price < prev_dma_10 and close_price > dma_10) else 0

            try:
                st73_signal, st73_val = generate_st_signal(
                    st_value(df, length=7, multiplier=3), ticker)
            except Exception:
                st73_signal, st73_val = -1, -1

            try:
                st72_signal, st72_val = generate_st_signal(
                    st_value(df, length=7, multiplier=2), ticker)
            except Exception:
                st72_signal, st72_val = -1, -1

            results.append({
                "ticker":       ticker,
                "st73_signal":  st73_signal,
                "st73_value":   st73_val,
                "st72_signal":  st72_signal,
                "st72_value":   st72_val,
                "close_price":  close_price,
                "DMA_200":      dma_200,
                "DMA10":        dma_10,
                "10DMA_change": dma_change,
            })
        except Exception as e:
            print(f"ERROR :: Indicator calculation failed for {ticker}: {e}")

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"INFO  :: Execution started at {datetime.now()}")
    writeFiles(str(PATH_START_SIGNAL), str(datetime.now()))

    _today, hist_date = set_dates(400)

    # --- Load or build the stock universe ---
    if PATH_500_LIST.is_file():
        print(f"INFO  :: Stock list already compiled for {DT}")
        ticker_list = pd.read_csv(PATH_500_LIST)['Stock_Symbols'].tolist()
    else:
        print(f"INFO  :: Building stock list for {DT}")
        ticker_list = update500tickers()
    print(f"INFO  :: {len(ticker_list)} tickers loaded at {datetime.now()}")

    # --- Split tickers into batches ---
    batches = [ticker_list[i: i + BATCH_SIZE]
               for i in range(0, len(ticker_list), BATCH_SIZE)]
    total_tickers = len(ticker_list)
    print(f"INFO  :: Starting indicator calculations — "
          f"{len(batches)} batches × {BATCH_SIZE} tickers, {_WORKERS} workers — "
          f"at {datetime.now()}")

    # --- Parallel batch processing ---
    indicator_signals: list[dict] = []
    completed_tickers = 0

    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        future_to_batch = {
            pool.submit(_process_batch, batch, hist_date): batch
            for batch in batches
        }
        for future in as_completed(future_to_batch):
            batch_results = future.result()
            indicator_signals.extend(batch_results)
            completed_tickers += len(future_to_batch[future])
            if completed_tickers % 150 == 0 or completed_tickers >= total_tickers:
                pct = round(completed_tickers * 100 / total_tickers, 1)
                print(f"INFO  :: {pct}% done ({completed_tickers}/{total_tickers})")

    print(f"INFO  :: Calculations done at {datetime.now()} "
          f"— {len(indicator_signals)}/{total_tickers} successful")

    # --- Filter into signal buckets ---
    st_73_stocks, st_73_dma_stocks = [], []
    st_72_stocks, st_72_dma_stocks = [], []
    dma_change_stocks = []

    for sig in indicator_signals:
        base = {
            "ticker":      sig['ticker'],
            "close_price": sig['close_price'],
            "DMA_200":     sig['DMA_200'],
            "DMA_10":      sig['DMA10'],
            "datee":       DT,
        }
        above_200 = sig['close_price'] > sig['DMA_200']

        if sig['st73_signal'] == 1:
            entry = {**base, "st73_value": sig['st73_value']}
            st_73_stocks.append(entry)
            if above_200:
                st_73_dma_stocks.append(entry)

        if sig['st72_signal'] == 1:
            entry = {**base, "st72_value": sig['st72_value']}
            st_72_stocks.append(entry)
            if above_200:
                st_72_dma_stocks.append(entry)

        if sig['10DMA_change'] == 1:
            dma_change_stocks.append({
                **base,
                "st73_value": sig['st73_value'],
                "st72_value": sig['st72_value'],
            })

    print(f"INFO  :: ST73 stocks          : {[s['ticker'] for s in st_73_stocks]}")
    print(f"INFO  :: ST73 + above 200 DMA : {[s['ticker'] for s in st_73_dma_stocks]}")
    print(f"INFO  :: ST72 stocks          : {[s['ticker'] for s in st_72_stocks]}")
    print(f"INFO  :: ST72 + above 200 DMA : {[s['ticker'] for s in st_72_dma_stocks]}")
    print(f"INFO  :: 10 DMA crossover     : {[s['ticker'] for s in dma_change_stocks]}")

    # --- Persist results ---
    try:
        writeSTFiles(str(PATH_IND_SIGNALS), indicator_signals)
    except Exception as e:
        print(f"ERROR :: Could not write indicator signals: {e}")

    if st_73_stocks:
        writeSTFiles(str(PATH_ST73), st_73_stocks)
        if st_73_dma_stocks:
            writeSTFiles(str(PATH_ST73_DMA), st_73_dma_stocks)
        print("INFO  :: Generating buy orders for ST73")
        gen_buy_orders(st_73_stocks)
    else:
        print("INFO  :: No ST73 signals today")

    if st_72_stocks:
        writeSTFiles(str(PATH_ST72), st_72_stocks)
        if st_72_dma_stocks:
            writeSTFiles(str(PATH_ST72_DMA), st_72_dma_stocks)
        print("INFO  :: Generating buy orders for ST72")
        gen_buy_orders(st_72_stocks)
    else:
        print("INFO  :: No ST72 signals today")

    if dma_change_stocks:
        writeSTFiles(str(PATH_DMA_CHANGE), dma_change_stocks)
    else:
        print("INFO  :: No 10 DMA crossovers today")

    writeFiles(str(PATH_FINISH_SIGNAL), str(datetime.now()))
    print(f"INFO  :: Execution finished at {datetime.now()}")


# ---------------------------------------------------------------------------
# Git helper
# ---------------------------------------------------------------------------
def git_activity():
    print("INFO  :: Pushing changes to git")
    subprocess.run(["git", "add", "."],                              cwd=str(ROOT), check=False)
    subprocess.run(["git", "commit", "-m", f"Data update {DT}"],     cwd=str(ROOT), check=False)
    subprocess.run(["git", "push"],                                  cwd=str(ROOT), check=False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if PATH_FINISH_SIGNAL.is_file():
        print(f"INFO  :: Already completed execution for {DT}")
    else:
        main()
        git_activity()
