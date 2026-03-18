import pandas_ta_classic as ta
#pip install pandas-ta-classic

def st_value(df, length, multiplier):
    st = ta.supertrend(high=df['High'], low=df['Low'], close=df['Close'], length=length, multiplier=multiplier)
    return st.tail(2)
