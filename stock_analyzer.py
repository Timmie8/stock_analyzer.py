import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_signal(df):
    # 1. Grondige data-check
    if df is None or df.empty or len(df) < 21:
        return "NO DATA"
    
    # 2. Fix: Yahoo Finance Multi-index platstaan
    # Dit is de reden voor de ERRORs
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Zorg dat alle kolommen hoofdletters hebben (soms geeft Yahoo 'close' ipv 'Close')
    df.columns = [str(col).capitalize() for col in df.columns]

    try:
        # 3. Bereken Indicatoren
        # We gebruiken .squeeze() om zeker te weten dat we een Series hebben
        close_series = df['Close'].squeeze()
        volume_series = df['Volume'].squeeze()

        df['EMA9'] = ta.ema(close_series, length=9)
        df['EMA21'] = ta.ema(close_series, length=21)
        df['RSI'] = ta.rsi(close_series, length=14)
        df['AvgVol'] = ta.sma(volume_series, length=20)

        last = df.iloc[-1]

        # 4. Score Logica
        is_bullish = last['EMA9'] > last['EMA21']
        is_bearish = last['EMA9'] < last['EMA21']
        rsi_val = last['RSI']
        
        vol_filter = last['Volume'] > (last['AvgVol'] * 0.8)

        if is_bullish and rsi_val > 50 and vol_filter:
            return "STRONG BUY ✅"
        elif is_bearish and rsi_val < 50 and vol_filter:
            return "STRONG SELL ❌"
        elif is_bullish:
            return "BULLISH 📈"
        elif is_bearish:
            return "BEARISH 📉"
        else:
            return "NEUTRAL ⚪"
    except Exception as e:
        return f"CALC ERROR"

# --- Streamlit Layout ---
st.set_page_config(page_title="GPT-5 Analyzer", layout="wide")
st.title("🚀 GPT-5 Stock Scanner (Fixed Version)")

user_input = st.text_input("Enter Tickers (e.g. AAPL, NVDA, DD)", "AAPL, NVDA, DD")

if st.button("Run Market Scan"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    results = []

    for s in tickers:
        with st.spinner(f"Downloading {s}..."):
            try:
                # We downloaden een extra ruime periode om gaten in data op te vangen
                d_data = yf.download(s, period="2y", interval="1d", progress=False, auto_adjust=True)
                h_data = yf.download(s, period="1mo", interval="1h", progress=False, auto_adjust=True)

                if not d_data.empty:
                    results.append({
                        "Ticker": s,
                        "Price": f"${d_data['Close'].iloc[-1].item():.2f}",
                        "1H Signal": get_signal(h_data),
                        "Daily Signal": get_signal(d_data),
                        "RSI": f"{ta.rsi(d_data['Close'].squeeze(), length=14).iloc[-1]:.1f}"
                    })
                else:
                    results.append({"Ticker": s, "1H Signal": "NOT FOUND", "Daily Signal": "NOT FOUND", "Price": "N/A", "RSI": "N/A"})
            except Exception as e:
                st.error(f"Error with {s}: {e}")
                results.append({"Ticker": s, "1H Signal": "ERROR", "Daily Signal": "ERROR", "Price": "N/A", "RSI": "N/A"})

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)


