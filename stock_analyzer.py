import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_indicators(df, is_1h=False):
    try:
        # Data opschonen
        close_prices = df['Close'].values.flatten()
        high_prices = df['High'].values.flatten()
        low_prices = df['Low'].values.flatten()
        
        if len(close_prices) < 35:
            return "DATA TE KORT", 0

        # --- MACD ---
        series = pd.Series(close_prices)
        exp1 = series.ewm(span=12, adjust=False).mean()
        exp2 = series.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        
        last_macd = macd_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        macd_stijgend = last_macd > prev_macd

        # --- STOCHASTIC (14, 3, 3) ---
        low_14 = pd.Series(low_prices).rolling(window=14).min()
        high_14 = pd.Series(high_prices).rolling(window=14).max()
        
        # %K berekening
        k_raw = 100 * ((pd.Series(close_prices) - low_14) / (high_14 - low_14 + 0.00001))
        k_line = k_raw.rolling(window=3).mean()
        
        curr_k = round(float(k_line.iloc[-1]), 2)
        prev_k = round(float(k_line.iloc[-2]), 2)

        # Logica: %K > 80 en stijgend
        stoch_is_hot = (curr_k > 80) and (curr_k > prev_k)

        if is_1h:
            if stoch_is_hot:
                return "STRONG BUY ✅", curr_k
            elif curr_k < 20:
                return "OVERSOLD ❌", curr_k
            else:
                return "NEUTRAAL ⚪", curr_k
        else:
            # Daily Trend
            macd_bull = last_macd > (macd_line.ewm(span=9).mean().iloc[-1])
            return "BULLISH 📈" if macd_bull else "BEARISH 📉", curr_k
            
    except Exception as e:
        return "ERROR", 0

# --- Streamlit UI ---
st.set_page_config(page_title="GPT-5 Stoch Tracker", layout="wide")
st.title("🚀 GPT-5 Momentum Scanner")

tickers_input = st.text_input("Voer tickers in:", "LUMN, AAPL, NVDA, TSLA, DD")

if st.button("Scan Markt"):
    tickers = [t.strip().upper() for t in tickers_input.split(',')]
    data_list = []

    for s in tickers:
        try:
            d_data = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
            h_data = yf.download(s, period="60d", interval="1h", progress=False, auto_adjust=True)

            if not d_data.empty and not h_data.empty:
                score_1h, k_val_1h = calculate_indicators(h_data, is_1h=True)
                score_d, _ = calculate_indicators(d_data, is_1h=False)

                data_list.append({
                    "Ticker": s,
                    "Prijs": round(d_data['Close'].iloc[-1], 2),
                    "1H Signaal": score_1h,
                    "Stoch %K (1H)": k_val_1h,
                    "Dag Trend": score_d
                })
        except:
            continue

    if data_list:
        df = pd.DataFrame(data_list)
        
        # Styling toevoegen: Kleur de Stoch kolom als aan de eisen voldaan wordt
        def highlight_stoch(val):
            color = 'background-color: #00ff00; color: black' if val > 80 else ''
            return color

        st.table(df) # We gebruiken st.table voor maximale zichtbaarheid van alle kolommen







