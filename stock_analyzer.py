import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

# We behouden je get_signal functie precies zoals hij was
def get_signal(df):
    if df is None or len(df) < 21:
        return "INSUFFICIENT DATA"
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

# NIEUWE Streamlit Dashboard Functie
def run_streamlit_dashboard():
    st.title("GPT-5 Stock Analyzer")
    
    # Gebruik st.text_input in plaats van de standaard input()
    user_input = st.text_input("Enter stock symbols (e.g., NVDA, AAPL, DD)", "AAPL, NVDA")
    
    if st.button("Run Analysis"):
        tickers = [t.strip().upper() for t in user_input.split(',')]
        results = []

        for symbol in tickers:
            with st.spinner(f"Analyzing {symbol}..."):
                try:
                    # threads=False voorkomt dat Streamlit vastloopt
                    data_1h = yf.download(symbol, interval="1h", period="1mo", progress=False, threads=False)
                    data_1d = yf.download(symbol, interval="1d", period="1y", progress=False, threads=False)

                    score_1h = get_signal(data_1h)
                    score_1d = get_signal(data_1d)

                    results.append({
                        "Symbol": symbol,
                        "1H Signal": score_1h,
                        "Daily Signal": score_1d
                    })
                except Exception as e:
                    results.append({"Symbol": symbol, "1H Signal": "ERROR", "Daily Signal": "ERROR"})

        # Toon resultaten in een mooie tabel
        if results:
            df_results = pd.DataFrame(results)
            st.table(df_results)

if __name__ == "__main__":
    run_streamlit_dashboard()
