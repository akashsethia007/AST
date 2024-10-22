import pandas as pd
def generate_st_signal(df, ticker):
    signal = 0
    df = df.tail(2)
    prev_day_values = list(df.iloc[0])
    current_day_values = list(df.tail(1).iloc[0])
    prev_st_value = float(prev_day_values[0])
    prev_day_signal = int(prev_day_values[1])
    curr_st_value = float(current_day_values[0])
    curr_day_signal = int(current_day_values[1])
    if float(prev_st_value) > float(curr_st_value) and float(prev_day_signal) < float(curr_day_signal) and int(curr_day_signal) == 1:
        signal = 1
    else:
        signal = 0
    return signal, round(curr_st_value,1)
