import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_gpt5_score(df):
    if df is None or df.empty or len(df) < 35: # MACD heeft meer data nodig
        return "NO DATA", 0, 0
    
    # 1. Data Cleaning (Yahoo Finance Multi-index fix)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col).capitalize() for col in df.columns]

    try:
        close_series = df['Close'].squeeze()
        volume_series = df['Volume'].squeeze()

        # 2. Bereken Indicatoren
        df['EMA9'] = ta.ema(close_series, length=9)
        df['EMA21'] = ta.ema(close_series, length=21)
        df['RSI'] = ta.rsi(close_series, length=14)
        
        # MACD Berekening (12, 26, 9)
        macd = ta.macd(close_series, fast=12, slow=26, signal=9)
        df['MACD_L'] = macd['MACD_12_26_9']
        df['MACD_S'] = macd['MACDS_12_26_9']
        
        df['AvgVol'] = ta.sma(volume_series, length=20)

        last = df.iloc[-1]

        # 3. GPT-5 Score Logica
        ema_bullish = last['EMA9'] > last['EMA21']
        macd_bullish = last['MACD_L'] > last['MACD_S']
        rsi_bullish = last['RSI'] > 50
        vol_ok = last['Volume'] > (last['AvgVol'] * 0.8)

        # 4. Bepaal Score
        if ema_bullish and macd_bullish and rsi_bullish and vol_ok:
            score = "STRONG BUY ✅"
        elif not ema_bullish and not macd_bullish and not rsi_bullish and vol_ok:
            score = "STRONG SELL ❌"
        elif ema_bullish and macd_bullish:
            score = "BULLISH TREND 📈"
        elif not ema_bullish and not macd_bullish:
            score = "BEARISH TREND 📉"
        else:
            score = "NEUTRAL ⚪"
            
        return score, last['RSI'], last['MACD_L'] - last['MACD_S']
    except Exception as e:
        return "CALC ERROR", 0, 0

# --- Streamlit Dashboard Layout ---
st.set_page_config(page_title="GPT-5 MACD Analyzer", layout="wide")
st.title("📊 GPT-5 MACD & EMA Dashboard")
st.markdown("Analysis based on **EMA 9/21 Cross**, **MACD Bullish/Bearish Histogram**, and **RSI Momentum**.")

user_input = st.text_input("Enter Tickers (comma separated)", "DD, AAPL, NVDA, TSLA")

if st.button("Calculate Scores"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    results = []

    for s in tickers:
        with st.spinner(f"Analyzing {s}..."):
            try:
                # Ophalen van data
                # We gebruiken 60 dagen voor 1h om genoeg data te hebben voor MACD
                d_data = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
                h_data = yf.download(s, period="60d", interval="1h", progress=False, auto_adjust=True)

                if not d_data.empty and not h_data.empty:
                    score_h, rsi_h, macd_diff_h = get_gpt5_score(h_data)
                    score_d, rsi_d, macd_diff_d = get_gpt5_score(d_data)

                    results.append({
                        "Ticker": s,
                        "Price": f"${d_data['Close'].iloc[-1].item():.2f}",
                        "1H Signal (MACD+EMA)": score_h,
                        "Daily Signal (MACD+EMA)": score_d,
                        "RSI (Daily)": f"{rsi_d:.1f}",
                        "MACD Status": "Bullish" if macd_diff_d > 0 else "Bearish"
                    })
                else:
                    results.append({"Ticker": s, "Price": "N/A", "1H Signal (MACD+EMA)": "NOT FOUND", "Daily Signal (MACD+EMA)": "NOT FOUND", "RSI (Daily)": "N/A", "MACD Status": "N/A"})
            except Exception as e:
                results.append({"Ticker": s, "Price": "ERROR", "1H Signal (MACD+EMA)": "ERROR", "Daily Signal (MACD+EMA)": "ERROR", "RSI (Daily)": "N/A", "MACD Status": "N/A"})

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)


