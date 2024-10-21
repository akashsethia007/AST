import datetime
from datetime import datetime, timedelta

def set_dates(num_of_days):
    print("Setting up the dates for this execution")
    today_date = datetime.today().strftime('%Y-%m-%d')
    hist_date = (datetime.today() - timedelta(days=num_of_days)).strftime('%Y-%m-%d')
    print(f"Start date set to {today_date} and end date set to {hist_date}")
    return today_date, hist_date