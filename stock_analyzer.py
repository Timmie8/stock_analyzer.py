import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_indicators(df, is_1h=False):
    try:
        # Data Cleaning: Pak de prijzen en zorg dat het een schone lijst is
        close_prices = df['Close'].values.flatten()
        high_prices = df['High'].values.flatten()
        low_prices = df['Low'].values.flatten()
        series = pd.Series(close_prices).dropna()

        if len(series) < 35:
            return "INSUFFICIENT DATA", None

        # --- MACD BEREKENING ---
        exp1 = series.ewm(span=12, adjust=False).mean()
        exp2 = series.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()

        last_macd = macd_line.iloc[-1]
        last_sig = signal_line.iloc[-1]
        macd_bullish = last_macd > last_sig

        # --- STOCHASTIC BEREKENING (14, 3, 3) ---
        # Alleen nodig voor de 1H chart volgens jouw verzoek
        stoch_signal = True # Default op True voor Daily (daar telt alleen MACD)
        k_val = 0

        if is_1h:
            low_14 = pd.Series(low_prices).rolling(window=14).min()
            high_14 = pd.Series(high_prices).rolling(window=14).max()
            
            # %K Basis
            k_raw = 100 * ((pd.Series(close_prices) - low_14) / (high_14 - low_14))
            # %K 3-period smoothing
            k_line = k_raw.rolling(window=3).mean()
            
            curr_k = k_line.iloc[-1]
            prev_k = k_line.iloc[-2]
            
            # Jouw criteria: Boven 80 EN stijgend
            stoch_signal = (curr_k > 80) and (curr_k > prev_k)
            k_val = round(curr_k, 2)

        # --- FINALE SCORE BEPALING ---
        if macd_bullish and stoch_signal:
            return "STRONG BUY ✅", k_val
        elif not macd_bullish:
            return "STRONG SELL ❌", k_val
        else:
            return "NEUTRAL ⚪ (MACD OK, STOCH NO)", k_val
            
    except Exception as e:
        return f"ERROR", 0

# --- Streamlit Interface ---
st.set_page_config(page_title="GPT-5 Stoch/MACD Scanner", layout="wide")
st.title("📟 GPT-5 Advanced Scanner")
st.info("Logica: MACD Bullish + 1H Stoch %K > 80 & Stijgend")

user_input = st.text_input("Voer Tickers in (bijv. AAPL, NVDA, TSLA, DD)", "AAPL, NVDA, DD")

if st.button("Start Analyse"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    results = []

    for s in tickers:
        with st.spinner(f"Bezig met {s}..."):
            try:
                # Data ophalen
                d_data = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
                h_data = yf.download(s, period="60d", interval="1h", progress=False, auto_adjust=True)

                if not d_data.empty and not h_data.empty:
                    score_h, k_h = calculate_indicators(h_data, is_1h=True)
                    score_d, _ = calculate_indicators(d_data, is_1h=False)

                    results.append({
                        "Ticker": s,
                        "Prijs": f"${d_data['Close'].values.flatten()[-1]:.2f}",
                        "1H Score (MACD+Stoch)": score_h,
                        "1H Stoch K": k_h,
                        "Daily Score (MACD)": score_d
                    })
                else:
                    results.append({"Ticker": s, "Prijs": "N/A", "1H Score (MACD+Stoch)": "GEEN DATA", "1H Stoch K": 0, "Daily Score (MACD)": "GEEN DATA"})
            except Exception:
                results.append({"Ticker": s, "Prijs": "ERR", "1H Score (MACD+Stoch)": "ERR", "1H Stoch K": 0, "Daily Score (MACD)": "ERR"})

    if results:
        st.table(pd.DataFrame(results))





