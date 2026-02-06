import streamlit as st
import yfinance as yf
import pandas as pd

def calculate_macd_clean(df):
    try:
        # Stap 1: Forceer de data naar een simpele lijst van prijzen
        # We negeren alle ingewikkelde kolomstructuren van Yahoo
        close_prices = df['Close'].values.flatten()
        series = pd.Series(close_prices).dropna()

        if len(series) < 35:
            return "INSUFFICIENT DATA"

        # Stap 2: Handmatige MACD berekening (geen extra libraries nodig)
        exp1 = series.ewm(span=12, adjust=False).mean()
        exp2 = series.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()

        # Stap 3: Signaal bepalen
        last_macd = macd_line.iloc[-1]
        last_sig = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_sig = signal_line.iloc[-2]

        if prev_macd <= prev_sig and last_macd > last_sig:
            return "BULLISH CROSS 🚀"
        elif prev_macd >= prev_sig and last_macd < last_sig:
            return "BEARISH CROSS 📉"
        elif last_macd > last_sig:
            return "STRONG BUY ✅"
        else:
            return "STRONG SELL ❌"
            
    except Exception as e:
        return f"DATA ERROR"

# --- Streamlit Interface ---
st.set_page_config(page_title="Ultimate MACD Fix", layout="wide")
st.title("📟 GPT-5 Pure MACD Scanner")
st.info("Deze versie berekent de MACD handmatig om fouten met externe bibliotheken te voorkomen.")

user_input = st.text_input("Enter Tickers (comma separated)", "AAPL, NVDA, TSLA, DD")

if st.button("Run Analysis"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    results = []

    for s in tickers:
        with st.spinner(f"Scanning {s}..."):
            try:
                # We halen de data op met auto_adjust=True
                # Dit zorgt voor de meest schone prijsdata
                d_data = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
                h_data = yf.download(s, period="60d", interval="1h", progress=False, auto_adjust=True)

                if not d_data.empty and not h_data.empty:
                    results.append({
                        "Ticker": s,
                        "Current Price": f"${d_data['Close'].values.flatten()[-1]:.2f}",
                        "1H MACD Score": calculate_macd_clean(h_data),
                        "Daily MACD Score": calculate_macd_clean(d_data)
                    })
                else:
                    results.append({"Ticker": s, "Current Price": "N/A", "1H MACD Score": "NOT FOUND", "Daily MACD Score": "NOT FOUND"})
            except Exception:
                results.append({"Ticker": s, "Current Price": "ERROR", "1H MACD Score": "ERROR", "Daily MACD Score": "ERROR"})

    if results:
        st.table(pd.DataFrame(results))





