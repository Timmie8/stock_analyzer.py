import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_macd_signal(df):
    # 1. Basis check
    if df is None or df.empty or len(df) < 35:
        return "INSUFFICIENT DATA"
    
    try:
        # 2. DATA FIX: Forceer de data naar een simpele lijst van getallen
        # We halen de 'Close' kolom op en dwingen deze naar een Series zonder gedoe
        if isinstance(df.columns, pd.MultiIndex):
            close_data = df['Close'].iloc[:, 0] # Pak de eerste kolom van de Close multi-index
        else:
            close_data = df['Close']
            
        # Maak er een schone series van
        close_series = pd.Series(close_data.values.flatten(), name="close").dropna()

        # 3. Bereken MACD (12, 26, 9)
        macd = ta.macd(close_series, fast=12, slow=26, signal=9)
        
        # Pak de juiste kolomnamen uit de resultaat-tabel van pandas_ta
        macd_line = macd['MACD_12_26_9']
        signal_line = macd['MACDS_12_26_9']

        last_macd = macd_line.iloc[-1]
        last_sig = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_sig = signal_line.iloc[-2]

        # 4. Logica
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
            
    except Exception as e:
        # Toon de echte foutmelding in de console voor debugging
        print(f"Error detail: {e}")
        return "CALC ERROR"

# --- Streamlit Layout ---
st.set_page_config(page_title="MACD Fix Dashboard", layout="wide")
st.title("📟 Fixed MACD Momentum Scanner")

user_input = st.text_input("Enter Tickers (e.g. DD, AAPL, NVDA)", "DD, AAPL, NVDA")

if st.button("Analyze MACD"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    results = []

    for s in tickers:
        with st.spinner(f"Fetching {s}..."):
            try:
                # auto_adjust=True is cruciaal voor schone prijzen
                d_data = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
                h_data = yf.download(s, period="60d", interval="1h", progress=False, auto_adjust=True)

                if not d_data.empty and not h_data.empty:
                    results.append({
                        "Ticker": s,
                        "Price": f"${d_data['Close'].iloc[-1].item():.2f}",
                        "1H MACD Score": get_macd_signal(h_data),
                        "Daily MACD Score": get_macd_signal(d_data)
                    })
                else:
                    results.append({"Ticker": s, "Price": "N/A", "1H MACD Score": "NOT FOUND", "Daily MACD Score": "NOT FOUND"})
            except Exception as e:
                results.append({"Ticker": s, "Price": "ERROR", "1H MACD Score": "ERROR", "Daily MACD Score": "ERROR"})

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)




