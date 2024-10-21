def generate_st_signal(df, ticker):
    print(f'generating signal for {ticker}')
    signal = 0
    df = df.tail(2)
    prev_day_values = list(df.iloc[0])
    current_day_values = list(df.tail(1))
    prev_st_value = prev_day_values[0]
    prev_day_signal = prev_day_values[1]
    curr_st_value = current_day_values[0]
    curr_day_signal = current_day_values[1]
    if prev_st_value > curr_st_value & prev_day_signal < curr_day_signal & curr_day_signal == 1:
        signal = 1
    else:
        signal = 0
    return signal,curr_st_value
