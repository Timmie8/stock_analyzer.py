import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_macd_signal(df):
    if df is None or df.empty or len(df) < 35:
        return "NO DATA"
    
    # Data Cleaning (Flatten multi-index)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col).capitalize() for col in df.columns]

    try:
        close_series = df['Close'].squeeze()
        
        # Bereken MACD (12, 26, 9)
        macd = ta.macd(close_series, fast=12, slow=26, signal=9)
        macd_line = macd['MACD_12_26_9']
        signal_line = macd['MACDS_12_26_9']

        last_macd = macd_line.iloc[-1]
        last_sig = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_sig = signal_line.iloc[-2]

        # Logica bepalen
        is_bullish = last_macd > last_sig
        cross_up = (prev_macd <= prev_sig) and (last_macd > last_sig)
        cross_down = (prev_macd >= prev_sig) and (last_macd < last_sig)

        if cross_up:
            return "BULLISH CROSS 🚀"
        elif cross_down:
            return "BEARISH CROSS 📉"
        elif is_bullish:
            return "STRONG BUY ✅"
        else:
            return "STRONG SELL ❌"
            
    except Exception:
        return "CALC ERROR"

# --- Streamlit Layout ---
st.set_page_config(page_title="MACD Only Analyzer", layout="wide")
st.title("📟 Pure MACD Momentum Scanner")
st.markdown("This dashboard focuses exclusively on **MACD Line vs Signal Line** for both timeframes.")

user_input = st.text_input("Enter Tickers (comma separated)", "AAPL, NVDA, DD, TSLA")

if st.button("Analyze MACD"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    results = []

    for s in tickers:
        with st.spinner(f"Fetching {s}..."):
            try:
                # Ophalen van data
                d_data = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
                h_data = yf.download(s, period="60d", interval="1h", progress=False, auto_adjust=True)

                if not d_data.empty and not h_data.empty:
                    results.append({
                        "Ticker": s,
                        "Current Price": f"${d_data['Close'].iloc[-1].item():.2f}",
                        "1H MACD Score": get_macd_signal(h_data),
                        "Daily MACD Score": get_macd_signal(d_data)
                    })
                else:
                    results.append({"Ticker": s, "Current Price": "N/A", "1H MACD Score": "NOT FOUND", "Daily MACD Score": "NOT FOUND"})
            except Exception:
                results.append({"Ticker": s, "Current Price": "ERROR", "1H MACD Score": "ERROR", "Daily MACD Score": "ERROR"})

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)



