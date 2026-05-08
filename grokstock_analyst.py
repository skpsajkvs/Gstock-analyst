import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import os

st.set_page_config(page_title="GrokStock Analyst", layout="wide")
st.title("🚀 GrokStock Analyst v1.0")
st.caption("Your on-demand stock research agent • Buy/Sell ideas • Screening • Deep dives")

# ====================== WATCHLIST ======================
WATCHLIST_FILE = "watchlist.json"
if os.path.exists(WATCHLIST_FILE):
    with open(WATCHLIST_FILE, "r") as f:
        watchlist = json.load(f)
else:
    watchlist = ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "BABA", "TSM", "JPM", "SPY", "QQQ"]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = watchlist

st.sidebar.header("📋 Your Watchlist")

new_ticker = st.sidebar.text_input("Add ticker (e.g. AAPL)", "")
if st.sidebar.button("➕ Add"):
    if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker.upper())
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(st.session_state.watchlist, f)

if st.session_state.watchlist:
    remove_ticker = st.sidebar.selectbox("Remove ticker", st.session_state.watchlist)
    if st.sidebar.button("🗑️ Remove"):
        st.session_state.watchlist.remove(remove_ticker)
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(st.session_state.watchlist, f)

# ====================== TABS ======================
tab1, tab2, tab3 = st.tabs(["🔍 Screener", "📊 Deep Dive", "💡 Buy/Sell Ideas"])

# Simple RSI function (no pandas_ta needed)
def calculate_rsi(data, periods=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ====================== TAB 1: SCREENER ======================
with tab1:
    st.subheader("Dynamic Opportunity Screener")
    col1, col2 = st.columns(2)
    with col1:
        max_pe = st.slider("Max P/E Ratio", 5, 100, 30)
    with col2:
        min_volume_m = st.slider("Min Avg Daily Volume (millions)", 1, 100, 5)

    if st.button("🚀 Run Screen on Watchlist", type="primary"):
        results = []
        for ticker in st.session_state.watchlist:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="3mo")
                if hist.empty:
                    continue

                current_price = hist['Close'].iloc[-1]
                pe = info.get('forwardPE') or info.get('trailingPE') or 999
                avg_volume = hist['Volume'].mean() / 1_000_000
                rsi = calculate_rsi(hist['Close']).iloc[-1]

                score = 0
                if pe < max_pe: score += 40
                if avg_volume > min_volume_m: score += 30
                if 30 < rsi < 70: score += 30

                results.append({
                    "Ticker": ticker,
                    "Price": round(current_price, 2),
                    "P/E": round(pe, 1),
                    "RSI": round(rsi, 1),
                    "Avg Vol (M)": round(avg_volume, 1),
                    "Score": score
                })
            except:
                continue

        if results:
            df = pd.DataFrame(results).sort_values("Score", ascending=False)
            st.dataframe(df, use_container_width=True)
            st.success("✅ Screening complete!")
        else:
            st.warning("No data found. Check your internet or tickers.")

# ====================== TAB 2: DEEP DIVE ======================
with tab2:
    st.subheader("Deep-Dive Analysis")
    ticker_input = st.text_input("Enter ticker", "AAPL").upper()

    if st.button("Analyze", type="primary"):
        with st.spinner("Fetching data..."):
            stock = yf.Ticker(ticker_input)
            info = stock.info
            hist = stock.history(period="1y")

            if not hist.empty:
                # Chart
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close']
                )])
                fig.update_layout(title=f"{ticker_input} - 1 Year", height=500)
                st.plotly_chart(fig, use_container_width=True)

                # Info
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Company**:", info.get('longName', 'N/A'))
                    st.write("**Sector**:", info.get('sector', 'N/A'))
                    st.write("**Market Cap**:", f"${info.get('marketCap', 0)/1e9:.1f}B")
                with col2:
                    st.write("**Current Price**:", f"${hist['Close'].iloc[-1]:.2f}")
                    st.write("**P/E**:", info.get('forwardPE') or info.get('trailingPE', 'N/A'))
                    st.write("**52w High/Low**:", f"${info.get('fiftyTwoWeekHigh', 'N/A')} / ${info.get('fiftyTwoWeekLow', 'N/A')}")

# ====================== TAB 3: BUY/SELL IDEAS ======================
with tab3:
    st.subheader("Buy/Sell Idea Generator")
    if st.button("Generate Ideas for Watchlist", type="primary"):
        st.info("Scanning your watchlist... (this may take 10-20 seconds)")
        # Similar logic as screener - you can expand this later

st.sidebar.info("✅ Using free yfinance data • Works on iPad")
st.caption("Not financial advice • For research only")
