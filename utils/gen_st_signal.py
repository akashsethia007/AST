def generate_st_signal(df, ticker):
    """Return (signal, current_st_value) for the last two rows of a SuperTrend df.

    Signal is 1 when SuperTrend value fell AND direction flipped to bullish (1).
    """
    last_two = df.tail(2)
    prev_st, prev_dir = float(last_two.iloc[0, 0]), int(last_two.iloc[0, 1])
    curr_st, curr_dir = float(last_two.iloc[1, 0]), int(last_two.iloc[1, 1])

    signal = 1 if (prev_st > curr_st and prev_dir < curr_dir and curr_dir == 1) else 0
    return signal, round(curr_st, 1)
