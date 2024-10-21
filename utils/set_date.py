import datetime
from datetime import datetime, timedelta

def set_dates(num_of_days):
    print(f"Start date set to {datetime.today().strftime('%Y-%m-%d')} and end date set to {(datetime.today() - timedelta(days=num_of_days)).strftime('%Y-%m-%d')}")
    return datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d').date(), datetime.strptime((datetime.today() - timedelta(days=num_of_days)).strftime('%Y-%m-%d'), '%Y-%m-%d').date()