import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

st.title("📈 주식 상세 정보 페이지")

# --- 사용자 입력 ---
ticker_input = st.text_input("종목 티커 입력 (예: 005930.KS)", value="005930.KS")
history_days = st.slider("차트 기간(일)", min_value=1, max_value=30, value=7)

# --- 데이터 가져오기 ---
@st.cache_data(ttl=10)
def fetch_stock_data(ticker, days=7):
    t = yf.Ticker(ticker)
    info = {}
    try:
        fi = t.fast_info
        info['현재가'] = fi.last_price
        info['전일종가'] = fi.previous_close
        info['시가'] = fi.open
        info['고가'] = fi.day_high
        info['저가'] = fi.day_low
        info['거래량'] = fi.volume
        info['시가총액'] = fi.market_cap
    except:
        info = {}
    # 최근 가격 차트 데이터
    start_date = datetime.utcnow() - timedelta(days=days)
    hist = t.history(start=start_date)
    hist = hist.reset_index()
    return info, hist

info, hist = fetch_stock_data(ticker_input, history_days)

# --- 상세 정보 출력 ---
if info:
    st.subheader(f"{ticker_input} 상세 정보")
    col1, col2, col3 = st.columns(3)
    col1.metric("현재가", f"{info.get('현재가', 'N/A')}")
    col1.metric("전일종가", f"{info.get('전일종가', 'N/A')}")
    col2.metric("시가", f"{info.get('시가', 'N/A')}")
    col2.metric("고가", f"{info.get('고가', 'N/A')}")
    col3.metric("저가", f"{info.get('저가', 'N/A')}")
    col3.metric("거래량", f"{info.get('거래량', 'N/A')}")
    st.markdown(f"**시가총액:** {info.get('시가총액', 'N/A')}")
else:
    st.error("데이터를 불러올 수 없습니다. 티커를 확인하세요.")

# --- 가격 차트 ---
if not hist.empty:
    st.subheader(f"{ticker_input} 최근 {history_days}일 가격 차트")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Close'], mode='lines', name='종가'))
    fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Open'], mode='lines', name='시가', line=dict(dash='dash')))
    fig.update_layout(margin=dict(l=20,r=20,t=30,b=20), xaxis_title="날짜", yaxis_title="가격", height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("차트용 데이터가 없습니다.")

st.caption("데이터 출처: Yahoo Finance (실시간 데이터는 약간 지연될 수 있음)")
