import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="KR Stocks Live", layout="wide")
st.title("🇰🇷 국내 주식 실시간 감시 대시보드")

# --- 사이드바 설정 ---
st.sidebar.header("설정")
default_watch = "005930.KS,035420.KQ,000660.KS"  # 삼성전자, NAVER, SK하이닉스
watch_input = st.sidebar.text_area("감시할 종목 (콤마로 구분)", value=default_watch)
tickers = [t.strip().upper() for t in watch_input.split(",") if t.strip()]

refresh_seconds = st.sidebar.number_input("자동 새로고침(초)", min_value=5, max_value=3600, value=15, step=5)
st.sidebar.button("즉시 새로고침", on_click=lambda: st.experimental_rerun())

# --- 데이터 가져오기 ---
@st.cache_data(ttl=10)
def fetch_ticker_data(tickers):
    rows = []
    for tk in tickers:
        try:
            t = yf.Ticker(tk)
            info = t.fast_info
            last = info.last_price
            prev = info.previous_close
            change = last - prev
            pct = (change / prev) * 100 if prev != 0 else None
            rows.append({
                "종목": tk,
                "현재가": last,
                "전일종가": prev,
                "변동": round(change, 2),
                "변동률(%)": round(pct, 2) if pct is not None else None
            })
        except Exception as e:
            rows.append({
                "종목": tk,
                "현재가": "N/A",
                "전일종가": "N/A",
                "변동": "N/A",
                "변동률(%)": "N/A"
            })
    return pd.DataFrame(rows)

df = fetch_ticker_data(tickers)

# --- 테이블 출력 ---
st.subheader("주식 감시 목록")
st.dataframe(df, use_container_width=True)

# --- 자동 새로고침 ---
st.markdown(f"<meta http-equiv='refresh' content='{refresh_seconds}'>", unsafe_allow_html=True)

st.caption("데이터 출처: Yahoo Finance (실시간 데이터에 약간의 지연 가능)")
