import datetime

def set_dates():
    print("Setting up the dates for this execution")
    date_now = datetime.date.today()
    years_to_add = date_now.year - 1
    today_date = date_now.strftime('%Y-%m-%d')
    hist_date = date_now.replace(year=years_to_add).strftime('%Y-%m-%d')
    print(f"Start date set to {today_date} and end date set to {hist_date}")
    return today_date, hist_date