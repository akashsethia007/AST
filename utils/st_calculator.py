import numpy as np
import pandas as pd
import pandas_ta as ta

def st_value(df, length, multiplier):
    st = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=length, multiplier=multiplier)
    return st.tail(2)
