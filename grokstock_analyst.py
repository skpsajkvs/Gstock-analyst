import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pandas_ta as ta
import json
import os

st.set_page_config(page_title="GrokStock Analyst", layout="wide")
st.title("🚀 GrokStock Analyst v1.0")
st.caption("Your on-demand stock research agent • Buy/Sell ideas • Screening • Deep dives")

# Watchlist
WATCHLIST_FILE = "watchlist.json"
if os.path.exists(WATCHLIST_FILE):
    with open(WATCHLIST_FILE, "r") as f:
        watchlist = json.load(f)
else:
    watchlist = ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "BABA", "TSM", "JPM", "SPY", "QQQ"]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = watchlist

st.sidebar.header("📋 Watchlist")
new_ticker = st.sidebar.text_input("Add ticker", "")
if st.sidebar.button("Add"):
    if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker.upper())

remove_ticker = st.sidebar.selectbox("Remove", st.session_state.watchlist)
if st.sidebar.button("Remove"):
    st.session_state.watchlist.remove(remove_ticker)

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Screener", "📊 Deep Dive", "💡 Buy/Sell Ideas", "📈 Options"])

with tab1:
    st.subheader("Dynamic Screener")
    if st.button("Run Screen on Watchlist", type="primary"):
        results = []
        for ticker in st.session_state.watchlist:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="3mo")
                if hist.empty: continue
                rsi = ta.rsi(hist['Close']).iloc[-1] if not hist.empty else 50
                pe = info.get('forwardPE') or info.get('trailingPE') or 999
                score = 100 if pe < 25 and 30 < rsi < 70 else 60
                results.append({"Ticker": ticker, "Price": round(hist['Close'].iloc[-1],2), "P/E": round(pe,1), "RSI": round(rsi,1), "Score": score})
            except:
                continue
        if results:
            df = pd.DataFrame(results).sort_values("Score", ascending=False)
            st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("Deep Dive")
    ticker = st.text_input("Enter Ticker", "AAPL")
    if st.button("Analyze", type="primary"):
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period="1y")
        info = stock.info
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig.update_layout(title=f"{ticker.upper()} Price", height=500)
        st.plotly_chart(fig, use_container_width=True)
        st.write("**Company:**", info.get('longName'))
        st.write("**Price:**", round(hist['Close'].iloc[-1], 2))
        st.write("**Market Cap:**", f"${info.get('marketCap',0)/1e9:.1f}B")

with tab3:
    st.subheader("Buy/Sell Ideas")
    if st.button("Generate Ideas", type="primary"):
        st.write("Scanning watchlist... (results will appear here)")

with tab4:
    st.subheader("Options")
    opt_ticker = st.text_input("Ticker", "AAPL")
    if st.button("Show Options"):
        st.write("Options data loading...")

st.sidebar.info("Data from yfinance • Educational use only")
