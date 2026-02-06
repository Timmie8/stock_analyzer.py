import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_signal(df):
    # 1. Controleer op data
    if df is None or df.empty or len(df) < 21:
        return "NO DATA"
    
    # 2. Fix voor Yahoo Finance Multi-index kolommen
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 3. Bereken Indicatoren
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['AvgVol'] = ta.sma(df['Volume'], length=20)

    # Pak de allerlaatste waarde
    last = df.iloc[-1]

    # 4. Trend Logica (in plaats van alleen Crossover)
    # Zo zie je of het aandeel NU in een koop-zone zit
    is_bullish_trend = last['EMA9'] > last['EMA21']
    is_bearish_trend = last['EMA9'] < last['EMA21']
    rsi_bullish = last['RSI'] > 50
    rsi_bearish = last['RSI'] < 50
    vol_filter = last['Volume'] > (last['AvgVol'] * 0.8) # Iets soepeler voor live data

    if is_bullish_trend and rsi_bullish and vol_filter:
        return "STRONG BUY ✅"
    elif is_bearish_trend and rsi_bearish and vol_filter:
        return "STRONG SELL ❌"
    elif is_bullish_trend:
        return "BULLISH WAIT 🟢"
    elif is_bearish_trend:
        return "BEARISH WAIT 🔴"
    else:
        return "NEUTRAL ⚪"

# --- Streamlit Interface ---
st.set_page_config(page_title="GPT-5 Trader", layout="wide")
st.title("📈 GPT-5 Multi-Timeframe Analyzer")

user_input = st.text_input("Enter Ticker Symbols (comma separated)", "AAPL, NVDA, TSLA, MSFT, DD")

if st.button("Start Market Scan"):
    tickers = [t.strip().upper() for t in user_input.split(',')]
    final_results = []

    for s in tickers:
        with st.spinner(f"Fetching {s}..."):
            try:
                # Download data (auto_adjust zorgt voor schone Close prijzen)
                d1 = yf.download(s, period="1y", interval="1d", progress=False, auto_adjust=True)
                h1 = yf.download(s, period="1mo", interval="1h", progress=False, auto_adjust=True)
                
                if not d1.empty and not h1.empty:
                    final_results.append({
                        "Symbol": s,
                        "Price": f"${d1['Close'].iloc[-1]:.2f}",
                        "1H Signal": get_signal(h1),
                        "Daily Signal": get_signal(d1),
                        "RSI (D)": f"{ta.rsi(d1['Close'], length=14).iloc[-1]:.1f}"
                    })
                else:
                    final_results.append({"Symbol": s, "1H Signal": "NOT FOUND", "Daily Signal": "NOT FOUND"})
            except Exception as e:
                final_results.append({"Symbol": s, "1H Signal": "ERROR", "Daily Signal": "ERROR"})

    # Resultaten tonen
    if final_results:
        st.table(pd.DataFrame(final_results))

