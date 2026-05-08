import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import os

st.set_page_config(page_title="GrokStock Analyst", layout="wide")
st.title("🚀 GrokStock Analyst v1.1")
st.caption("Your on-demand stock research agent • Buy/Sell ideas • Screening • Deep dives")

# ====================== WATCHLIST (Improved) ======================
WATCHLIST_FILE = "watchlist.json"
if os.path.exists(WATCHLIST_FILE):
    with open(WATCHLIST_FILE, "r") as f:
        watchlist = json.load(f)
else:
    watchlist = ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "BABA", "TSM", "JPM", "SPY", "QQQ"]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = watchlist

st.sidebar.header("📋 Your Watchlist")

# Show current watchlist with scroll
st.sidebar.write("**Current watchlist** (" + str(len(st.session_state.watchlist)) + " stocks):")
st.sidebar.markdown("\n".join([f"• {t}" for t in st.session_state.watchlist]))

new_ticker = st.sidebar.text_input("Add ticker (e.g. AAPL)", "")
if st.sidebar.button("➕ Add"):
    if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker.upper())
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(st.session_state.watchlist, f)
        st.sidebar.success(f"✅ Added {new_ticker.upper()}")

if st.session_state.watchlist:
    remove_ticker = st.sidebar.selectbox("Remove ticker", st.session_state.watchlist)
    if st.sidebar.button("🗑️ Remove"):
        st.session_state.watchlist.remove(remove_ticker)
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(st.session_state.watchlist, f)
        st.sidebar.success(f"✅ Removed {remove_ticker}")

# ====================== TABS ======================
tab1, tab2, tab3 = st.tabs(["🔍 Screener", "📊 Deep Dive", "💡 Buy/Sell Ideas"])

def calculate_rsi(data, periods=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=periods).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ====================== TAB 1: SCREENER (unchanged - already good) ======================
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
                if hist.empty: continue

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
            st.dataframe(df, use_container_width=True, height=600)
            st.success("✅ Screening complete!")
        else:
            st.warning("No data returned.")

# ====================== TAB 2: DEEP DIVE (Much Improved) ======================
with tab2:
    st.subheader("📊 Deep-Dive Analysis")
    ticker_input = st.text_input("Enter ticker for full analysis", "AAPL").upper().strip()

    if st.button("Analyze", type="primary"):
        with st.spinner("Fetching fundamentals, chart, news..."):
            stock = yf.Ticker(ticker_input)
            info = stock.info
            hist = stock.history(period="1y")
            news = stock.news[:5]

            if hist.empty:
                st.error("No data found for this ticker.")
            else:
                # Chart
                fig = go.Figure(data=[go.Candlestick(x=hist.index,
                    open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'])])
                fig.update_layout(title=f"{ticker_input} - 1 Year Price", height=500)
                st.plotly_chart(fig, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Fundamentals")
                    st.write("**Company**:", info.get('longName', 'N/A'))
                    st.write("**Sector**:", info.get('sector', 'N/A'))
                    st.write("**Market Cap**:", f"${info.get('marketCap',0)/1e9:.1f}B")
                    st.write("**P/E (fwd)**:", info.get('forwardPE', 'N/A'))
                    st.write("**EPS (ttm)**:", info.get('trailingEps', 'N/A'))
                    st.write("**Beta**:", info.get('beta', 'N/A'))

                with col2:
                    st.subheader("Technicals")
                    latest = hist.iloc[-1]
                    rsi_val = calculate_rsi(hist['Close']).iloc[-1]
                    st.write("**Current Price**:", f"${latest['Close']:.2f}")
                    st.write("**RSI (14)**:", round(rsi_val, 1))
                    st.write("**Avg Daily Vol**:", f"{hist['Volume'].mean()/1e6:.1f}M shares")
                    st.write("**52w High / Low**:", f"${info.get('fiftyTwoWeekHigh', 'N/A')} / ${info.get('fiftyTwoWeekLow', 'N/A')}")

                # Simple Verdict
                score = 0
                if (info.get('forwardPE', 999) < 25): score += 30
                if (30 < rsi_val < 70): score += 30
                if (latest['Close'] > hist['Close'].rolling(50).mean().iloc[-1]): score += 40
                verdict = "🟢 Strong Buy Idea" if score >= 80 else "🟡 Watch / Potential Buy" if score >= 50 else "🔴 Avoid or Sell"
                st.markdown(f"### Agent Verdict: **{verdict}** (Score: {score}/100)")

                # News
                st.subheader("Latest News")
                for article in news:
                    st.markdown(f"• [{article['title']}]({article.get('link', '#')})")

# ====================== TAB 3: BUY/SELL IDEAS ======================
with tab3:
    st.subheader("💡 Buy/Sell Idea Generator")
    if st.button("Generate Fresh Ideas from Watchlist", type="primary"):
        ideas = []
        for ticker in st.session_state.watchlist:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="6mo")
                if hist.empty: continue
                rsi = calculate_rsi(hist['Close']).iloc[-1]
                pe = info.get('forwardPE') or 999
                above_ma = hist['Close'].iloc[-1] > hist['Close'].rolling(50).mean().iloc[-1]
                score = (30 if pe < 22 else 0) + (30 if 30 < rsi < 70 else 0) + (40 if above_ma else 0)
                rec = "BUY" if score >= 70 else "SELL" if score <= 30 else "HOLD"
                ideas.append({"Ticker": ticker, "Price": round(hist['Close'].iloc[-1],2), "Score": score, "Rec": rec})
            except:
                continue
        if ideas:
            df = pd.DataFrame(ideas).sort_values("Score", ascending=False)
            st.dataframe(df, use_container_width=True)
            st.success("Ideas generated!")
        else:
            st.warning("No ideas generated.")

st.sidebar.info("✅ Data from yfinance • Auto-saves watchlist")
st.caption("Not financial advice • Educational use only")
