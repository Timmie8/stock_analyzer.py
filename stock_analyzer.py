import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_indicators(df, is_1h=False):
    try:
        # Data Cleaning
        close_prices = df['Close'].values.flatten()
        high_prices = df['High'].values.flatten()
        low_prices = df['Low'].values.flatten()
        
        if len(close_prices) < 35:
            return "INSUFFICIENT DATA", 0

        # --- MACD (Voor Trend) ---
        series = pd.Series(close_prices)
        exp1 = series.ewm(span=12, adjust=False).mean()
        exp2 = series.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        last_macd = macd_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        macd_bullish = last_macd > signal_line.iloc[-1]
        macd_stijgend = last_macd > prev_macd

        # --- STOCHASTIC (14, 3, 3) ---
        low_14 = pd.Series(low_prices).rolling(window=14).min()
        high_14 = pd.Series(high_prices).rolling(window=14).max()
        
        # %K Basis (zonder deling door nul fouten)
        k_raw = 100 * ((pd.Series(close_prices) - low_14) / (high_14 - low_14 + 0.00001))
        # %K 3-period smoothing
        k_line = k_raw.rolling(window=3).mean()
        
        curr_k = k_line.iloc[-1]
        prev_k = k_line.iloc[-2]

        # --- JOUW SPECIFIEKE LOGICA ---
        # 1H criteria: %K > 80 en stijgend
        stoch_buy = (curr_k > 80) and (curr_k > prev_k)

        if is_1h:
            if stoch_buy:
                # Als Stoch super sterk is, geven we de BUY, 
                # we gebruiken MACD alleen als extra bevestiging in de tekst
                status = "STRONG BUY ✅" if macd_stijgend else "MOMENTUM BUY 🚀"
                return status, round(curr_k, 2)
            elif curr_k < 20 and curr_k < prev_k:
                return "STRONG SELL ❌", round(curr_k, 2)
            else:
                return "NEUTRAL ⚪", round(curr_k, 2)
        else:
            # Daily blijft op de hoofdtrend (MACD)
            return "BULLISH 📈" if macd_bullish else "BEARISH 📉", round(curr_k, 2)
            
    except Exception as e:
        return f"ERROR", 0

# --- Streamlit Interface ---
st.set_page_config(page_title="GPT-5 Precise Scanner", layout="wide")
st.title("📈 GPT-5 Precise Momentum Tracker")

user_input = st.text_input("Tickers (bijv. LUMN, AAPL, NVDA, DD)", "LUMN, AAPL, NVDA, DD")

if st.button("Analyseer Momentum"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    results = []

    for s in tickers:
        with st.spinner(f"Scannen van {s}..."):
            try:
                # Ophalen data (auto_adjust=True voor zuivere prijzen)
                d_data = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
                h_data = yf.download(s, period="60d", interval="1h", progress=False, auto_adjust=True)

                if not d_data.empty and not h_data.empty:
                    score_1h, k_1h = calculate_indicators(h_data, is_1h=True)
                    score_d, _ = calculate_indicators(d_data, is_1h=False)

                    results.append({
                        "Ticker": s,
                        "Prijs": f"${d_data['Close'].values.flatten()[-1]:.2f}",
                        "1H Score (Stoch Focus)": score_1h,
                        "1H Stoch %K": k_1h,
                        "Daily Trend (MACD)": score_d
                    })
            except:
                results.append({"Ticker": s, "1H Score (Stoch Focus)": "ERR"})

    if results:
        # Tabel weergeven
        st.dataframe(pd.DataFrame(results), use_container_width=True)






