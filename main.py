# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Streamlit page config
st.set_page_config(page_title="KR Stocks Live", layout="wide")

st.title("🇰🇷 실시간(에 가깝게) 국내 주식 시세 대시보드")
st.caption("예: 삼성전자 005930.KS, NAVER 035420.KQ — 티커 끝에 .KS(코스피)/.KQ(코스닥) 붙이기")

# --- Sidebar: watchlist & settings ---
st.sidebar.header("설정")
default_watch = "005930.KS,035420.KQ,000660.KS"  # 예시: 삼성전자, NAVER, SK하이닉스
watch_input = st.sidebar.text_area("감시할 종목 (콤마로 구분)", value=default_watch, height=80)
tickers = [t.strip().upper() for t in watch_input.split(",") if t.strip()]

refresh_seconds = st.sidebar.number_input("자동갱신(초)", min_value=5, max_value=3600, value=15, step=5)
show_chart = st.sidebar.checkbox("차트 표시", value=True)
history_minutes = st.sidebar.number_input("차트 기간(분)", min_value=1, max_value=1440, value=60, step=1)

# force a refresh widget (useful when running locally)
if st.sidebar.button("즉시 새로고침"):
    st.experimental_rerun()

# helper: fetch current quote and intraday history
@st.cache_data(ttl=10)
def fetch_ticker_data(ticker, period_minutes=60):
    """
    Returns: dict { 'info': series current info, 'hist': DataFrame intraday }
    Uses yfinance to fetch latest quote and intraday 1m data (best-effort).
    """
    try:
        t = yf.Ticker(ticker)
        # get current info via fast_info or history
        fast = {}
        try:
            fi = t.fast_info
            fast['last_price'] = fi.last_price
            fast['open'] = fi.open
            fast['previous_close'] = fi.previous_close
        except Exception:
            # fallback: last close from history
            hist = t.history(period="2d", interval="1m")
            if not hist.empty:
                fast['last_price'] = hist['Close'].iloc[-1]
                fast['open'] = hist['Open'].iloc[-1]
                fast['previous_close'] = hist['Close'].iloc[-2] if len(hist) > 1 else hist['Close'].iloc[-1]
            else:
                fast = {'last_price': None, 'open': None, 'previous_close': None}

        # intraday history: try 1m interval for the requested window
        period = max(1, int(period_minutes))
        start = datetime.utcnow() - timedelta(minutes=period)
        hist = t.history(start=start, interval="1m", actions=False)
        hist = hist.reset_index()
        # normalize timestamps to local (optional) - keep as-is for simplicity
        return {'info': fast, 'hist': hist}
    except Exception as e:
        return {'info': {}, 'hist': pd.DataFrame()}

# layout: top summary table
cols = st.columns([2, 3])
with cols[0]:
    st.subheader("감시 목록")
    if not tickers:
        st.info("사이드바에 종목 티커를 입력하세요. 예: 005930.KS")
    else:
        rows = []
        for tk in tickers:
            data = fetch_ticker_data(tk, period_minutes=history_minutes)
            info = data['info']
            last = info.get('last_price', None)
            prev = info.get('previous_close', None)
            change = None
            pct = None
            if last is not None and prev is not None and prev != 0:
                change = last - prev
                pct = (change / prev) * 100
            rows.append({
                "Ticker": tk,
                "현재가": last if last is not None else "N/A",
                "전일종가": prev if prev is not None else "N/A",
                "변동": f"{change:.2f}" if change is not None else "N/A",
                "변동률(%)": f"{pct:.2f}%" if pct is not None else "N/A"
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

with cols[1]:
    st.subheader("요약")
    if tickers:
        # show the top mover by absolute change
        df_numeric = df[df["현재가"] != "N/A"].copy()
        if not df_numeric.empty:
            df_numeric["현재가"] = pd.to_numeric(df_numeric["현재가"])
            df_numeric["전일종가"] = pd.to_numeric(df_numeric["전일종가"])
            df_numeric["abs_change"] = (df_numeric["현재가"] - df_numeric["전일종가"]).abs()
            top = df_numeric.sort_values("abs_change", ascending=False).iloc[0]
            st.markdown(f"**가장 큰 변동:** {top['Ticker']} — 현재가 **{top['현재가']:.2f}** (전일 **{top['전일종가']:.2f}**)")
        else:
            st.write("현재 데이터 없음")

# show charts for each ticker
if show_chart and tickers:
    st.subheader("종목별 차트 (마지막 {}분)".format(history_minutes))
    for tk in tickers:
        data = fetch_ticker_data(tk, period_minutes=history_minutes)
        hist = data['hist']
        if hist.empty:
            st.write(f"{tk}의 차트 데이터가 없습니다.")
            continue

        st.markdown(f"**{tk}**")
        # Plotly line chart of Close
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist['Datetime'] if 'Datetime' in hist.columns else hist['Date'],
                                 y=hist['Close'],
                                 mode='lines',
                                 name='Close'))
        fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=250, xaxis_title=None, yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

# footer: auto-refresh
st.write("---")
st.caption(f"데이터 소스: Yahoo Finance via yfinance (표시된 가격은 실시간에 가깝지만 데이터 정책에 따라 지연될 수 있음).")
# auto-refresh using experimental function
st_autorefresh = st.experimental_singleton(lambda: None)  # placeholder to avoid lint issues
# Use Streamlit built-in autorefresh
count = st.experimental_get_query_params().get("refresh_count", [0])
st.experimental_set_query_params(refresh_count=int(count[0]) + 1 if count else 1)
# JavaScript-based refresh: simple meta refresh via HTML
st.markdown(f"""
<meta http-equiv="refresh" content="{refresh_seconds}">
""", unsafe_allow_html=True)
