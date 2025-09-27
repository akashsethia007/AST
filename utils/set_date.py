import datetime
from datetime import datetime, timedelta

def set_dates(num_of_days):
    print(f"INFO  :: Start date set to {datetime.today().strftime('%Y-%m-%d')} and End date set to {(datetime.today() - timedelta(days=num_of_days)).strftime('%Y-%m-%d')}")
    return str(datetime.today().strftime('%Y-%m-%d')), str((datetime.today() - timedelta(days=num_of_days)).strftime('%Y-%m-%d'))