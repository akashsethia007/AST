"""
Top200ST72.py — Automated Stock Screener
=========================================

Flow
----
  STEP 1 : Fetch the top UNIVERSE_SIZE NSE stocks by market capitalisation.
  STEP 2 : For each stock, backtest every ST config in ST_PARAMS on TIMEFRAME
           bars using CAPITAL_PER_TRADE rupees.  Compute win %, total P&L,
           number of trades, and % return.
  STEP 3 : Rank all (stock, ST config) pairs by % return and keep the top
           TOP_N_RESULT rows (one row per stock — the best ST config wins).
           Print + save the table.
  STEP 4 : From that top-N list, find every stock that flipped ST green
           exactly 2 bars ago on the same timeframe.  Print + save.

All user-facing settings are in the CONFIG block — nothing else needs touching.
"""

from __future__ import annotations

import logging
import sys
import subprocess

# ---------------------------------------------------------------------------
# Silence yfinance debug flood BEFORE any yfinance import
# ---------------------------------------------------------------------------
class _WarningFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.WARNING

_root = logging.getLogger()
_root.setLevel(logging.DEBUG)
_sh = logging.StreamHandler(sys.stdout)
_sh.setLevel(logging.WARNING)
_sh.addFilter(_WarningFilter())
_root.handlers = [_sh]
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pandas_ta_classic as ta
import yfinance as yf
from nselib import capital_market


# ===========================================================================
#   C O N F I G   —   only edit this block between runs
# ===========================================================================

# Timeframe for all ST calculations and the green-flip scan.
# Options: 'M' (monthly) | 'W' (weekly) | 'D' (daily) | '1h' (hourly)
# Note: Yahoo caps hourly history at ~60 days regardless of YEARS_BACK.
TIMEFRAME = 'D'

# How many years of history to use for the backtest.
YEARS_BACK = 3

# SuperTrend configurations to test. Format: (length, multiplier).
# Every stock is backtested on ALL configs; it's ranked by its best result.
ST_PARAMS = [
    (7, 2),    # ST72
    (7, 3),    # ST73
]

# How many NSE stocks to pull from market-cap ranking (universe).
UNIVERSE_SIZE = 1000

# How many top performers to keep in the final ranked list.
TOP_N_RESULT = 365

# Starting capital in ₹ used for every (stock, ST config) backtest.
# All stocks start with the same amount so results are directly comparable.
CAPITAL_PER_TRADE = 10000

# Parallel download threads and tickers-per-batch.
MAX_WORKERS = 20
BATCH_SIZE  = 50

# ===========================================================================
#   End of CONFIG
# ===========================================================================


# ---------------------------------------------------------------------------
# Derive runtime constants — do not edit below this line
# ---------------------------------------------------------------------------
_TF_META = {
    # key : (yf_interval, label, lookback_days, min_bars, scan_offset)
    'M'  : ('1mo', 'Monthly', YEARS_BACK * 365 + 60, 24, 3),
    'W'  : ('1wk', 'Weekly',  YEARS_BACK * 365 + 60, 30, 3),
    'D'  : ('1d',  'Daily',   YEARS_BACK * 365 + 30, 50, 3),
    '1h' : ('1h',  'Hourly',  59,                    50, 3),
}

if TIMEFRAME not in _TF_META:
    sys.exit(f"ERROR :: TIMEFRAME '{TIMEFRAME}' invalid. Choose from: {list(_TF_META)}")
if not ST_PARAMS:
    sys.exit("ERROR :: ST_PARAMS is empty — add at least one (length, multiplier) tuple.")

YF_INTERVAL, TF_LABEL, _LOOKBACK_DAYS, _MIN_BARS, _SCAN_OFFSET = _TF_META[TIMEFRAME]
START_DATE = (datetime.today() - timedelta(days=_LOOKBACK_DAYS)).strftime('%Y-%m-%d')

_ST_LABEL  = '+'.join(f"ST{l}{int(m)}" for l, m in ST_PARAMS)   # e.g. "ST72+ST73"
_TF_TAG    = TIMEFRAME.replace('1h', 'hourly')                    # safe for filenames
_FILE_TAG  = f"{_TF_TAG}_{_ST_LABEL.replace('+', '_')}"          # e.g. "D_ST72_ST73"

ROOT        = Path(__file__).resolve().parents[1]
DT          = datetime.today().strftime('%Y%m%d')
RESULTS_DIR = ROOT / "results"
DATED_DIR   = ROOT / "data" / "top200"
RESULTS_DIR.mkdir(exist_ok=True)
DATED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_BACKTEST_LATEST = RESULTS_DIR / f"{_FILE_TAG}_backtest.csv"
OUTPUT_BACKTEST_DATED  = DATED_DIR   / f"{DT}_{_FILE_TAG}_backtest.csv"
OUTPUT_GREEN_LATEST    = RESULTS_DIR / f"{_FILE_TAG}_green_2bars.csv"
OUTPUT_GREEN_DATED     = DATED_DIR   / f"{DT}_{_FILE_TAG}_green_2bars.csv"


# ---------------------------------------------------------------------------
# Utility: timestamp string
# ---------------------------------------------------------------------------
def _ts() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ---------------------------------------------------------------------------
# Utility: progress printer (fires at 0 %, 10 %, 20 % … 100 %)
# ---------------------------------------------------------------------------
class _Progress:
    def __init__(self, total: int, label: str):
        self.total = total
        self.done  = 0
        self.label = label
        self._last = -1
        self._tick(0)

    def _tick(self, pct: int):
        print(f"  [{self.label}] {pct:>3}%")
        self._last = pct

    def update(self, n: int = 1):
        self.done += n
        bucket = int(self.done * 100 / self.total) // 10 * 10
        if bucket > self._last:
            self._tick(bucket)
        if self.done >= self.total and self._last < 100:
            self._tick(100)


# ===========================================================================
#   STEP 1 — Build universe: top UNIVERSE_SIZE stocks by market cap
# ===========================================================================
def step1_get_universe(n: int) -> list[str]:
    print(f"\n{'─'*60}")
    print(f"  STEP 1 — Universe: top {n} NSE stocks by market cap")
    print(f"  Started  : {_ts()}")
    print(f"{'─'*60}")

    eq = capital_market.equity_list()
    all_symbols = list(eq['SYMBOL'] + '.NS')
    total = len(all_symbols)
    print(f"  {total} NSE symbols found — fetching market caps in batches of 100")

    mcaps: list[dict] = []
    prog = _Progress(total, "mcap fetch")

    for start in range(0, total, 100):
        batch = all_symbols[start: start + 100]
        try:
            tobj = yf.Tickers(' '.join(batch))
            for sym in batch:
                try:
                    mcaps.append({"Symbol": sym,
                                  "Market_Cap": tobj.tickers[sym].info.get('marketCap')})
                except Exception:
                    mcaps.append({"Symbol": sym, "Market_Cap": None})
        except Exception as e:
            print(f"  WARN :: batch failed: {e}")
            mcaps.extend({"Symbol": s, "Market_Cap": None} for s in batch)
        prog.update(len(batch))

    df = pd.DataFrame(mcaps).dropna(subset=['Market_Cap'])
    df.sort_values('Market_Cap', ascending=False, inplace=True)
    universe = df.head(n)['Symbol'].str.split('.').str[0].tolist()
    print(f"  → {len(universe)} tickers selected")
    print(f"  Finished : {_ts()}\n")
    return universe


# ===========================================================================
#   STEP 2 — Backtest each stock on every ST config
# ===========================================================================

def _download_batch(tickers: list[str]) -> dict[str, pd.DataFrame]:
    """Download OHLCV for a batch of tickers.

    Tries a single bulk yf.download first (fast). Any tickers that come back
    empty fall back to individual yf.Ticker().history() calls so nothing is
    silently dropped due to yfinance MultiIndex alignment quirks.
    """
    ns = [f"{t}.NS" for t in tickers]
    out: dict[str, pd.DataFrame] = {}

    # ── Bulk attempt ──────────────────────────────────────────────────────
    try:
        raw = yf.download(
            ' '.join(ns),
            start=START_DATE,
            interval=YF_INTERVAL,
            group_by='ticker',
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if not raw.empty:
            if len(tickers) == 1:
                out[tickers[0]] = raw
            else:
                for ticker, ns_sym in zip(tickers, ns):
                    try:
                        df = raw[ns_sym].dropna(how='all')
                        if not df.empty:
                            out[ticker] = df
                    except KeyError:
                        pass   # will be retried below
    except Exception:
        pass   # full batch failed — retry all individually below

    # ── Per-ticker fallback for anything the bulk call missed ─────────────
    missed = [t for t in tickers if t not in out]
    for ticker in missed:
        try:
            df = yf.Ticker(f"{ticker}.NS").history(
                start=START_DATE, interval=YF_INTERVAL
            )
            if df is not None and not df.empty:
                out[ticker] = df
        except Exception:
            pass

    return out


def _compute_st(df: pd.DataFrame, length: int, multiplier: float):
    """Return (val_series, dir_series) or (None, None)."""
    st = ta.supertrend(
        high=df['High'], low=df['Low'], close=df['Close'],
        length=length, multiplier=multiplier,
    )
    if st is None or st.empty:
        return None, None
    try:
        vc = [c for c in st.columns if c.startswith('SUPERT_') and 'd' not in c][0]
        dc = [c for c in st.columns if c.startswith('SUPERTd_')][0]
        return st[vc], st[dc]
    except IndexError:
        return None, None


def _backtest_one_config(ticker: str, df: pd.DataFrame,
                         length: int, multiplier: float) -> dict | None:
    """
    Backtest ST(length, multiplier) on df.

    Returns a dict with:
      ticker, st_config, total_pnl, pct_return,
      total_trades, winning_trades, win_pct, final_capital
    """
    if len(df) < _MIN_BARS:
        return None
    try:
        st_val, st_dir = _compute_st(df, length, multiplier)
        if st_val is None:
            return None

        work = df.copy()
        work['_v'] = st_val.values
        work['_d'] = st_dir.values
        work.dropna(subset=['_v', '_d'], inplace=True)
        if len(work) < 2:
            return None

        capital     = float(CAPITAL_PER_TRADE)
        shares      = 0
        entry_price = 0.0
        trades: list[float] = []
        in_pos      = False

        for i in range(1, len(work)):
            p_dir = int(work['_d'].iloc[i - 1])
            c_dir = int(work['_d'].iloc[i])
            price = float(work['Close'].iloc[i])

            # BUY — ST flips bullish
            if not in_pos and p_dir == -1 and c_dir == 1:
                shares = int(capital / price)
                if shares == 0:
                    continue
                entry_price = price
                capital    -= shares * price
                in_pos      = True

            # SELL — ST flips bearish
            elif in_pos and p_dir == 1 and c_dir == -1:
                proceeds = shares * price
                trades.append(round(proceeds - shares * entry_price, 2))
                capital += proceeds
                shares   = 0
                in_pos   = False

        # Close any open position at the last bar
        if in_pos and shares > 0:
            last_price = float(work['Close'].iloc[-1])
            proceeds   = shares * last_price
            trades.append(round(proceeds - shares * entry_price, 2))
            capital += proceeds

        n_trades   = len(trades)
        n_wins     = sum(1 for p in trades if p > 0)
        total_pnl  = round(capital - CAPITAL_PER_TRADE, 2)

        return {
            "ticker":         ticker,
            "st_config":      f"ST{length}{int(multiplier)}",
            "capital_used":   CAPITAL_PER_TRADE,
            "total_pnl":      total_pnl,
            "pct_return":     round(total_pnl / CAPITAL_PER_TRADE * 100, 2),
            "total_trades":   n_trades,
            "winning_trades": n_wins,
            "win_pct":        round(n_wins * 100 / n_trades, 1) if n_trades else 0.0,
            "final_capital":  round(capital, 2),
        }
    except Exception as e:
        print(f"  ERROR :: backtest failed for {ticker} ST{length}{multiplier}: {e}")
        return None


def _backtest_ticker(ticker: str, df: pd.DataFrame) -> list[dict]:
    """Run all ST_PARAMS configs for one ticker."""
    return [r for length, mult in ST_PARAMS
            for r in [_backtest_one_config(ticker, df, length, mult)]
            if r is not None]


def step2_run_backtest(universe: list[str]) -> list[dict]:
    batches = [universe[i: i + BATCH_SIZE] for i in range(0, len(universe), BATCH_SIZE)]
    total   = len(universe)

    print(f"{'─'*60}")
    print(f"  STEP 2 — Download {TF_LABEL} OHLCV  ({START_DATE} → today)")
    print(f"  Started  : {_ts()}")
    print(f"           {total} tickers  |  {len(batches)} batches × {BATCH_SIZE}  |  {MAX_WORKERS} workers")
    print(f"{'─'*60}")
    dl_prog = _Progress(total, "download")

    print(f"\n  STEP 2 (cont.) — Backtest {_ST_LABEL} on {TF_LABEL} bars")
    print(f"           {len(ST_PARAMS)} ST config(s) × {total} stocks  "
          f"= up to {len(ST_PARAMS) * total} simulations")
    bt_prog = _Progress(total, "backtest")

    all_rows: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fmap = {pool.submit(_download_batch, b): b for b in batches}
        for future in as_completed(fmap):
            batch    = fmap[future]
            hist_map = future.result()
            dl_prog.update(len(batch))

            for ticker in batch:
                df = hist_map.get(ticker)
                if df is not None:
                    all_rows.extend(_backtest_ticker(ticker, df))
                bt_prog.update(1)

    print()
    print(f"  {len(all_rows)} backtest results from {len(set(r['ticker'] for r in all_rows))} unique tickers")
    print(f"  Finished : {_ts()}\n")
    return all_rows


# ===========================================================================
#   STEP 3 — Rank and keep top TOP_N_RESULT stocks
# ===========================================================================
def step3_rank(all_rows: list[dict]) -> pd.DataFrame:
    print(f"{'─'*60}")
    print(f"  STEP 3 — Rank by % return, keep top {TOP_N_RESULT}")
    print(f"  Started  : {_ts()}")
    print(f"{'─'*60}")

    df = pd.DataFrame(all_rows)
    # Per ticker: keep the ST config that gave the highest % return
    best = (
        df.sort_values('pct_return', ascending=False)
          .drop_duplicates(subset='ticker', keep='first')
          .sort_values('pct_return', ascending=False)
    )

    # Prefer profitable stocks — only include losers if there aren't enough winners
    profitable = best[best['pct_return'] > 0]
    if len(profitable) >= TOP_N_RESULT:
        top = profitable.head(TOP_N_RESULT)
    else:
        print(f"  NOTE :: Only {len(profitable)} profitable stocks found "
              f"(needed {TOP_N_RESULT}) — showing all profitable + top losers")
        top = best.head(TOP_N_RESULT)

    top = top.reset_index(drop=True)
    top.index += 1

    pd.set_option('display.max_rows', TOP_N_RESULT)
    pd.set_option('display.float_format', '{:,.2f}'.format)
    print(f"\n  Top {len(top)} stocks  [{TF_LABEL} | {_ST_LABEL}]")
    print(f"  Columns: rank | ticker | best ST config | capital ₹{CAPITAL_PER_TRADE:,} | "
          f"total P&L | % return | trades | wins | win %\n")
    print(top.to_string())

    top.to_csv(OUTPUT_BACKTEST_LATEST, index_label='rank')
    top.to_csv(OUTPUT_BACKTEST_DATED,  index_label='rank')
    print(f"\n  Saved → {OUTPUT_BACKTEST_LATEST}")
    print(f"  Saved → {OUTPUT_BACKTEST_DATED}")
    print(f"  Finished : {_ts()}\n")
    return top


# ===========================================================================
#   STEP 4 — Green-flip scan: which of the top-N turned ST green 2 bars ago?
# ===========================================================================
def _check_green_flip(ticker: str) -> list[dict]:
    """
    For each ST config, check whether the ticker's SuperTrend flipped bullish
    exactly 2 bars ago (i.e. bar at iloc[-3]) on the configured timeframe.

    Bar positions:
      iloc[-1] = latest bar       (may still be live / incomplete intraday)
      iloc[-2] = 1 bar ago        (last fully closed bar)
      iloc[-3] = 2 bars ago       ← this is the flip candidate
    """
    scan_days  = max(90, _LOOKBACK_DAYS // 8)
    hist_start = (datetime.today() - timedelta(days=scan_days)).strftime('%Y-%m-%d')
    hits: list[dict] = []
    try:
        df = yf.Ticker(f"{ticker}.NS").history(start=hist_start, interval=YF_INTERVAL)
        if df is None or len(df) < _SCAN_OFFSET + 2:
            return hits

        for length, mult in ST_PARAMS:
            st_val, st_dir = _compute_st(df, length, mult)
            if st_val is None:
                continue

            dirs = st_dir.dropna()
            vals = st_val.dropna()
            if len(dirs) < _SCAN_OFFSET + 1:
                continue

            # iloc[-3] is the flip candle; iloc[-4] must have been bearish
            flip_dir   = int(dirs.iloc[-_SCAN_OFFSET])
            before_dir = int(dirs.iloc[-_SCAN_OFFSET - 1])

            if before_dir == -1 and flip_dir == 1:
                flip_ts = dirs.index[-_SCAN_OFFSET]
                hits.append({
                    "ticker":      ticker,
                    "st_config":   f"ST{length}{int(mult)}",
                    "flip_date":   flip_ts.strftime('%Y-%m-%d %H:%M'
                                                    if TIMEFRAME == '1h'
                                                    else '%Y-%m-%d'),
                    "close_price": round(float(df['Close'].iloc[-2]), 2),
                    "st_value":    round(float(vals.iloc[-2]), 2),
                })
    except Exception as e:
        print(f"  ERROR :: green-check failed for {ticker}: {e}")
    return hits


def step4_find_green(top_tickers: list[str], top_df: pd.DataFrame) -> pd.DataFrame | None:
    total = len(top_tickers)
    print(f"{'─'*60}")
    print(f"  STEP 4 — ST green flip scan  (2 {TF_LABEL.lower()} bars ago)")
    print(f"  Started  : {_ts()}")
    print(f"           Checking {total} stocks × {len(ST_PARAMS)} ST config(s)")
    print(f"{'─'*60}")
    prog = _Progress(total, "green scan")
    hits: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fmap = {pool.submit(_check_green_flip, tk): tk for tk in top_tickers}
        for future in as_completed(fmap):
            hits.extend(future.result())
            prog.update(1)

    if not hits:
        print(f"\n  No ST green flips found 2 {TF_LABEL.lower()} bars ago.")
        print(f"  Finished : {_ts()}\n")
        return None

    gdf = (
        pd.DataFrame(hits)
          .sort_values(['ticker', 'st_config'])
          .reset_index(drop=True)
    )
    gdf.index += 1

    # Join total_pnl and pct_return from the backtest results
    pnl_cols = top_df[['ticker', 'total_pnl', 'pct_return']].drop_duplicates('ticker')
    gdf = gdf.merge(pnl_cols, on='ticker', how='left')

    print(f"\n  {len(gdf)} signal(s) found — ST flipped GREEN 2 {TF_LABEL.lower()} bars ago\n")
    print(gdf.to_string())

    gdf.to_csv(OUTPUT_GREEN_LATEST, index_label='rank')
    gdf.to_csv(OUTPUT_GREEN_DATED,  index_label='rank')
    print(f"\n  Saved → {OUTPUT_GREEN_LATEST}")
    print(f"  Saved → {OUTPUT_GREEN_DATED}")
    print(f"  Finished : {_ts()}\n")
    return gdf


# ===========================================================================
#   Entry point
# ===========================================================================
def main():
    print(f"\n{'═'*60}")
    print(f"  NSE SuperTrend Stock Screener")
    print(f"{'═'*60}")
    print(f"  Timeframe      : {TIMEFRAME}  ({TF_LABEL} — {YF_INTERVAL})")
    print(f"  ST configs     : {[f'ST{l}{int(m)}' for l, m in ST_PARAMS]}")
    print(f"  Backtest range : {START_DATE} → today  ({YEARS_BACK} yr)")
    print(f"  Universe       : top {UNIVERSE_SIZE} NSE stocks by market cap")
    print(f"  Capital/trade  : ₹{CAPITAL_PER_TRADE:,}")
    print(f"  Result size    : top {TOP_N_RESULT} stocks")
    print(f"  Run date       : {DT}")
    print(f"{'═'*60}\n")

    t0 = datetime.now()
    print(f"  Script started : {_ts()}\n")

    # ── Step 1: Universe ──────────────────────────────────────────────────
    universe = step1_get_universe(UNIVERSE_SIZE)

    # ── Step 2: Backtest ──────────────────────────────────────────────────
    all_rows = step2_run_backtest(universe)
    if not all_rows:
        sys.exit("ERROR :: No backtest results — check internet connection.")

    # ── Step 3: Rank ──────────────────────────────────────────────────────
    top_df = step3_rank(all_rows)

    # ── Step 4: Green-flip scan ───────────────────────────────────────────
    step4_find_green(top_df['ticker'].tolist(), top_df)

    elapsed = round((datetime.now() - t0).total_seconds() / 60, 1)
    print(f"{'═'*60}")
    print(f"  Script finished : {_ts()}")
    print(f"  Total elapsed   : {elapsed} min")
    print(f"{'═'*60}\n")

# ---------------------------------------------------------------------------
# Git helper
# ---------------------------------------------------------------------------
def git_activity():
    print("INFO  :: Pushing changes to git")
    subprocess.run(["git", "add", "."],                              cwd=str(ROOT), check=False)
    subprocess.run(["git", "commit", "-m", f"Data update {DT}"],     cwd=str(ROOT), check=False)
    subprocess.run(["git", "push"],                                  cwd=str(ROOT), check=False)

if __name__ == "__main__":
    main()
    git_activity()
