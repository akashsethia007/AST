from datetime import datetime, timedelta


def set_dates(num_of_days):
    """Return (today_str, hist_start_str) where hist_start is num_of_days ago."""
    today = datetime.today()
    hist_start = (today - timedelta(days=num_of_days)).strftime('%Y-%m-%d')
    print(f"INFO  :: Date range: {hist_start} → {today.strftime('%Y-%m-%d')}")
    return str(today), hist_start
