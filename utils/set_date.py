import datetime
from datetime import datetime, timedelta

def set_dates(num_of_days):
    print(f"Start date set to {datetime.today().strftime('%d-%m-%Y')} and end date set to {(datetime.today() - timedelta(days=num_of_days)).strftime('%d-%m-%Y')}")
    #return datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d').date(), datetime.strptime((datetime.today() - timedelta(days=num_of_days)).strftime('%Y-%m-%d'), '%Y-%m-%d').date()
    return str(datetime.today().strftime('%d-%m-%Y')), str((datetime.today() - timedelta(days=num_of_days)).strftime('%d-%m-%Y'))