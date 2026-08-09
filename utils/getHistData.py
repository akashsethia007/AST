from __future__ import annotations

import yfinance as yf
import pandas as pd

# Number of tickers to download in a single yfinance batch call.
# yfinance fetches all tickers in one HTTP request when given a space-separated
# string, so larger batches = fewer round-trips.  50 is a safe ceiling before
# Yahoo starts rate-limiting individual symbol resolution.
BATCH_SIZE = 50


def getHistDatanow(ticker: str, hist_date: str) -> pd.DataFrame | bool:
    """Fetch OHLCV history for a single NSE ticker from Yahoo Finance."""
    try:
        data = yf.Ticker(f"{ticker}.NS").history(start=hist_date)
        return data if not data.empty else False
    except Exception as e:
        print(f"ERROR: Failed to get history data for {ticker}: {e}")
        return False


def getHistDataBatch(tickers: list[str], hist_date: str) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV history for a batch of NSE tickers in a single HTTP call.

    Returns a dict mapping bare ticker symbol → DataFrame.
    Missing / empty tickers are omitted from the result.
    """
    ns_symbols = [f"{t}.NS" for t in tickers]
    query = ' '.join(ns_symbols)
    result: dict[str, pd.DataFrame] = {}
    try:
        raw = yf.download(
            query,
            start=hist_date,
            group_by='ticker',
            auto_adjust=True,
            progress=False,
            threads=True,       # yfinance uses its own threading internally
        )
        if raw.empty:
            return result

        # Single-ticker download has a flat MultiIndex; normalise to dict
        if len(tickers) == 1:
            result[tickers[0]] = raw
            return result

        for ticker, ns_sym in zip(tickers, ns_symbols):
            try:
                df = raw[ns_sym].dropna(how='all')
                if not df.empty:
                    result[ticker] = df
            except KeyError:
                pass
    except Exception as e:
        print(f"ERROR: Batch history download failed: {e}")
    return result
