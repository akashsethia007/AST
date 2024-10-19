import numpy as np
import pandas as pd
import pandas_ta as ta

def st_value(df, length, multiplier):
    st = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=7, multiplier=3)
    return list(round(st.tail(1).iloc[:,0],1))[0]
