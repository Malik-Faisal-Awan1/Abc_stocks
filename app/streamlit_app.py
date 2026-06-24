import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

import config
from src.quota_tracker import QuotaTracker
from src.data_fetcher import fetch_ohlcv, fetch_sentiment, ThrottleError, DataFetchError
from src.indicators import calculate_rsi, calculate_macd, composite_score
from src.sentiment import parse_sentiment
from src.backtester import run_backtest
import re

st.set_page_config(page_title="ABC Stocks Dashboard", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Main app background */
.stApp {
    background-color: #0A0A0B;
    background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.05) 0%, transparent 70%);
}

/* Sidebar */
[data-testid="stSidebar"] { 
    background-color: rgba(18, 18, 20, 0.7) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Metric Cards with Glassmorphism */
.metric-card, [data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.25) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.15) !important;
}

/* Modern Tab Switching */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    height: 44px;
    white-space: nowrap;
    border-radius: 8px 8px 0 0;
    padding: 0 20px;
    color: #A0AEC0 !important;
    border: none !important;
    background-color: transparent;
    transition: all 0.2s ease;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    color: #3B82F6 !important;
    background-color: rgba(59, 130, 246, 0.1) !important;
    box-shadow: inset 0 -2px 0 0 #3B82F6 !important;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    color: #E2E8F0 !important;
    background-color: rgba(255, 255, 255, 0.05);
}

/* Badges */
.badge-mock  { background: rgba(16, 185, 129, 0.2); color: #10B981; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-live  { background: rgba(59, 130, 246, 0.2); color: #3B82F6; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(59, 130, 246, 0.3); }

/* Remove blockquote border for markdown alerts */
.stMarkdown blockquote {
    border-left-color: rgba(255, 255, 255, 0.1) !important;
    color: #A0AEC0 !important;
}
</style>
""", unsafe_allow_html=True)

CHART_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", family="Inter, sans-serif"),
    xaxis=dict(showgrid=False, zeroline=False, linecolor="#2D3748", tickfont=dict(color="#A0AEC0")),
    yaxis=dict(showgrid=False, zeroline=False, linecolor="#2D3748", tickfont=dict(color="#A0AEC0")),
)

_LEGEND_DARK = dict(bgcolor="rgba(14,17,23,0.7)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1)

C_BULLISH  = "#10B981"   # vivid emerald
C_BEARISH  = "#F43F5E"   # vivid rose
C_NEUTRAL  = "#F59E0B"   # amber
C_ACCENT   = "#3B82F6"   # electric blue
C_ANOMALY  = "#F97316"   # orange
C_TEXT     = "#E2E8F0"   # soft white
C_MUTED    = "#718096"   # slate grey
C_CARD     = "rgba(30, 41, 59, 0.4)" # glassmorphism slate
C_BG       = "#0A0A0B"   # deep almost black

def _validate_ticker(raw_input: str) -> tuple[bool, str]:
    ticker = raw_input.strip().upper()
    if not ticker:
        return False, "Please enter a ticker symbol."
    if len(ticker) > 5:
        return False, f"'{ticker}' is too long. Ticker symbols are 1–5 characters."
    if not re.match(r'^[A-Z]+$', ticker):
        return False, f"'{ticker}' contains invalid characters. Use letters only (e.g. AAPL)."
    return True, ticker  # Return cleaned ticker on success

if "quota_tracker" not in st.session_state:
    st.session_state["quota_tracker"] = QuotaTracker()
if "ticker" not in st.session_state:
    st.session_state["ticker"] = ""
if "last_fetch_timestamp" not in st.session_state:
    st.session_state["last_fetch_timestamp"] = None
if "current_data" not in st.session_state:
    st.session_state["current_data"] = None
if "current_sentiment" not in st.session_state:
    st.session_state["current_sentiment"] = None

@st.cache_data(ttl=config.CACHE_TTL_STANDARD)
def cached_fetch_ohlcv(ticker: str) -> pd.DataFrame:
    # Does not catch exceptions, lets them propagate
    return fetch_ohlcv(ticker)

@st.cache_data(ttl=config.CACHE_TTL_SENTIMENT)
def cached_fetch_sentiment(ticker: str) -> dict:
    return fetch_sentiment(ticker)

# 3. Sidebar
with st.sidebar:
    st.title("ABC Stocks Dashboard")
    
    if config.USE_MOCK:
        st.sidebar.success("🧪 MOCK MODE")
    else:
        st.sidebar.success("🟢 LIVE MODE")
        
    st.metric("Session Calls", st.session_state["quota_tracker"].session_total())
    
    if st.session_state["last_fetch_timestamp"]:
        st.caption(f"Last updated: {st.session_state['last_fetch_timestamp']}")

with st.form("ticker_form"):
    raw_ticker = st.text_input("Ticker Symbol", placeholder="e.g. AAPL", value=st.session_state["ticker"])
    submitted = st.form_submit_button("Analyse")

if submitted:
    is_valid, result = _validate_ticker(raw_ticker)
    if not is_valid:
        st.error(result)
        st.stop()
    ticker = result  # Cleaned, uppercase ticker
    st.session_state["ticker"] = ticker

    with st.spinner(f"Fetching data for {ticker}..."):
        if not config.USE_MOCK:
            st.session_state["quota_tracker"].record_call()
            st.session_state["quota_tracker"].record_call()

        try:
            ohlcv = cached_fetch_ohlcv(st.session_state["ticker"])
            sentiment_raw = cached_fetch_sentiment(st.session_state["ticker"])
            
            st.session_state["current_data"] = ohlcv
            st.session_state["current_sentiment"] = sentiment_raw
            st.session_state["last_fetch_timestamp"] = datetime.now()
            
        except ThrottleError:
            st.warning("Request throttled. Retrying in 1 second...")
            # Phase 1 spec: UI shows warning, no auto-retry complex loop needed unless requested
        except DataFetchError:
            st.error("Data provider returned an unexpected response. Using cached data if available.")
        except Exception as e:
            st.error("Data provider returned an unexpected response. Using cached data if available.")

if st.session_state["current_data"] is None and not submitted:
    st.info("Enter a ticker symbol and click Analyse to fetch data.")

if st.session_state["current_data"] is not None:
    df = st.session_state["current_data"]
    sent_raw = st.session_state["current_sentiment"]

    rsi = calculate_rsi(df["close"])
    macd_line, signal_line, hist = calculate_macd(df["close"])
    comp_score = composite_score(rsi, macd_line, signal_line)
    
    # Parse sentiment
    parsed_sent = parse_sentiment(sent_raw.get("sentiment", {}), sent_raw.get("news", []))

    tab1, tab2 = st.tabs(["Analysis", "Backtesting"])
    
    with tab1:
        st.subheader(f"Analysis for {st.session_state['ticker']}")
        
        fetch_time = st.session_state.get("last_fetch_timestamp")
        age_str = ""
        if fetch_time:
            age_seconds = (datetime.now() - fetch_time).seconds
            age_str = f"{age_seconds // 60}m {age_seconds % 60}s ago"
            st.caption(f"Data fetched {age_str} · Refreshes hourly")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**Price (OHLCV)**")
            fig1 = go.Figure(data=[go.Candlestick(x=df.index,
                            open=df['open'], high=df['high'],
                            low=df['low'], close=df['close'])])
            fig1.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
            st.plotly_chart(fig1, use_container_width=True)
    
        with col2:
            st.markdown("**RSI (14)**")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=rsi.index, y=rsi.values, name="RSI"))
            fig2.add_hline(y=70, line_dash="dash", line_color="red")
            fig2.add_hline(y=30, line_dash="dash", line_color="green")
            fig2.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
            st.plotly_chart(fig2, use_container_width=True)
    
        with col3:
            st.markdown("**MACD**")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=macd_line.index, y=macd_line.values, name="MACD"))
            fig3.add_trace(go.Scatter(x=signal_line.index, y=signal_line.values, name="Signal"))
            fig3.add_trace(go.Bar(x=hist.index, y=hist.values, name="Histogram"))
            fig3.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
            st.plotly_chart(fig3, use_container_width=True)
    
        with col4:
            st.markdown("**Composite Score**")
            st.write(f"Upward Momentum Confidence: {comp_score['score_pct']}%")
            st.progress(int(comp_score['score_pct']))
            st.write(f"Direction: **{comp_score['direction']}**")
            st.write(f"RSI Component: {comp_score['rsi_component']} | MACD Component: {comp_score['macd_component']}")
            st.caption("⚠️ " + comp_score['disclaimer'])
            
            st.markdown("---")
            st.markdown("**Market Sentiment**")
            if parsed_sent["is_valid"]:
                st.write(f"Sentiment: **{parsed_sent['label']}**")
                st.write(f"Bullish: {parsed_sent['bullish_pct']}% | Bearish: {parsed_sent['bearish_pct']}%")
                if parsed_sent["article_count"] == 0:
                    st.caption(
                        "Warning: Sentiment score is based on historical data -- "
                        "no recent articles found for this ticker this week. "
                        "Treat with lower confidence."
                    )
                else:
                    st.caption(f"Based on {parsed_sent['article_count']} articles this week")
                st.caption("Info: " + parsed_sent['attribution'])
            else:
                st.write("Sentiment data unavailable.")

    with tab2:
        st.subheader(f"Backtesting for {st.session_state['ticker']}")
        if fetch_time and age_str:
            st.caption(f"Data fetched {age_str} · Refreshes hourly")
            
        ohlcv_df = st.session_state["current_data"]
        backtest_result = run_backtest(ohlcv_df, st.session_state["ticker"])

        col_bt1, col_bt2, col_bt3 = st.columns(3)
        with col_bt1:
            accuracy = backtest_result["accuracy_pct"]
            if accuracy is not None:
                delta = round(accuracy - 50.0, 1)
                delta_str = f"{'+' if delta >= 0 else ''}{delta}% vs random"
                st.metric("Signal Accuracy", f"{accuracy}%", delta=delta_str)
            else:
                st.metric("Signal Accuracy", "N/A", help="No directional signals generated")
        with col_bt2:
            st.metric("Total Signals", backtest_result["total_signals"])
        with col_bt3:
            st.metric("Final Equity", f"${backtest_result['final_equity']:.2f}")

        st.write(f"Hits: {backtest_result['hits']}, Misses: {backtest_result['misses']}, Neutral: {backtest_result['neutral_days']}")

        eq_curve = backtest_result["equity_curve"]
        fig_eq = go.Figure()
        
        line_color = "#2ecc71" if backtest_result["final_equity"] >= 100 else "#e74c3c"
        
        if not eq_curve.empty:
            fig_eq.add_trace(go.Scatter(
                x=eq_curve.index,
                y=eq_curve.values,
                mode="lines",
                line=dict(color=line_color, width=2),
                name="Portfolio Value"
            ))
            
        fig_eq.add_hline(
            y=100,
            line_dash="dash",
            line_color="gray",
            annotation_text="Starting $100",
            annotation_position="bottom right"
        )
        fig_eq.update_layout(
            title="Hypothetical $100 Portfolio — Signal Replay",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
            height=350,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_eq, use_container_width=True)

        st.warning(
            "⚠️ **Illustration only.** This shows what would have happened if every signal "
            "was followed over the past 90 days. Past signal performance does not indicate "
            "future results. No real money is involved. This is a historical analysis tool, "
            "not a trading system."
        )

        col_dist1, col_dist2 = st.columns(2)
        with col_dist1:
            st.markdown("**Signal Distribution**")
            log_df = backtest_result["signal_log"]
            if not log_df.empty:
                bullish_count = len(log_df[log_df["signal"] == "Bullish"])
                bearish_count = len(log_df[log_df["signal"] == "Bearish"])
                neutral_count = backtest_result["neutral_days"]
                fig_pie = go.Figure(data=[go.Pie(
                    labels=["Bullish", "Bearish", "Neutral"],
                    values=[bullish_count, bearish_count, neutral_count],
                    hole=0.4,
                    textinfo="label+percent",
                    textposition="outside",
                    marker=dict(colors=["#2ecc71", "#e74c3c", "#95a5a6"])
                )])
                fig_pie.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                    height=300,
                    margin=dict(t=20, b=60, l=20, r=20)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("No signals generated.")

        with col_dist2:
            st.markdown("**Monthly Hit vs Miss**")
            if not log_df.empty:
                log_df_copy = log_df.copy()
                log_df_copy["month"] = pd.to_datetime(log_df_copy["date"]).dt.strftime("%Y-%m")
                grouped = log_df_copy[log_df_copy["hit_miss"].isin(["Hit", "Miss"])].groupby(["month", "hit_miss"]).size().unstack(fill_value=0)
                
                fig_bar = go.Figure()
                if "Hit" in grouped.columns:
                    fig_bar.add_trace(go.Bar(x=grouped.index, y=grouped["Hit"], name="Hit", marker_color="green"))
                if "Miss" in grouped.columns:
                    fig_bar.add_trace(go.Bar(x=grouped.index, y=grouped["Miss"], name="Miss", marker_color="red"))
                fig_bar.update_layout(barmode="group", margin=dict(l=0, r=0, t=30, b=0), height=300)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.write("No signals generated.")

        with st.expander("View Signal Log"):
            if not log_df.empty:
                st.dataframe(log_df[["date", "signal", "hit_miss", "close_T", "close_T1", "equity_after"]])
            else:
                st.write("No signal data.")
        st.info("Info: **ABC_Stocks")
