import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_signal(df):
    # Controleer of data echt gevuld is
    if df is None or df.empty or len(df) < 21:
        return "NO DATA"
    
    # Zorg dat we alleen de 'Close' kolom gebruiken zonder Multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['AvgVol'] = ta.sma(df['Volume'], length=20)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    bull_cross = (prev['EMA9'] <= prev['EMA21']) and (last['EMA9'] > last['EMA21'])
    bear_cross = (prev['EMA9'] >= prev['EMA21']) and (last['EMA9'] < last['EMA21'])
    vol_filter = last['Volume'] > last['AvgVol']

    if bull_cross and last['RSI'] > 50 and vol_filter:
        return "STRONG BUY ✅"
    elif bear_cross and last['RSI'] < 50 and vol_filter:
        return "STRONG SELL ❌"
    else:
        return "NEUTRAL ⚪"

st.title("GPT-5 Stock Analyzer")
user_input = st.text_input("Enter Symbols", "AAPL, NVDA, TSLA")

if st.button("Start Scan"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    final_results = []

    for s in tickers:
        try:
            # Download met extra stabiliteit
            d1 = yf.download(s, period="1y", interval="1d", progress=False)
            h1 = yf.download(s, period="1mo", interval="1h", progress=False)
            
            final_results.append({
                "Symbol": s,
                "1H Signal": get_signal(h1),
                "Daily Signal": get_signal(d1)
            })
        except:
            final_results.append({"Symbol": s, "1H Signal": "ERROR", "Daily Signal": "ERROR"})

    st.table(pd.DataFrame(final_results))

