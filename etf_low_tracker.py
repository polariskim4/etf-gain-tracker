import yfinance as yf
import pandas as pd
import pytz
import requests
import os
from datetime import datetime, timedelta

# GitHub Secrets 환경변수
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TICKERS = [
    "TQQQ", "SOXL", "SPXL", "UPRO", "TECL", "FAS", "FNGU", "TNA", "KORU", "NUGT",
    "YINN", "UDOW", "LABU", "NAIL", "DFEN", "DPST", "ERX", "URTY", "EDC", "CURE",
    "BRZU", "EURL", "INDL", "DRN", "DUSL", "UTSL", "MEXX", "TPOR", "PILL", "BITU", "ETHT"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def get_status_icon(recovery_pct):
    """1년 저점 대비 상승률 기준으로 아이콘 표시 (기준은 변경 가능)"""
    if recovery_pct <= 15.0: return "🔥 적극매수"
    elif recovery_pct <= 40.0: return "🟢 매수"
    else: return "🟡 진입"

def fetch_and_send_data():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    # 각 기간별 시작 날짜 계산
    date_3y = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
    date_2y = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
    date_1y = (datetime.now() - timedelta(days=1*365)).strftime('%Y-%m-%d')
    
    results = []
    for ticker in TICKERS:
        try:
            etf = yf.Ticker(ticker)
            # 최대 3년치 데이터를 가져옴
            hist = etf.history(start=date_3y)
            if hist.empty: continue
            
            current_price = hist['Close'].iloc[-1]

            # 1년, 2년, 3년 내 최저점 찾기
            low_1y = hist[hist.index >= date_1y]['Low'].min()
            low_2y = hist[hist.index >= date_2y]['Low'].min()
            low_3y = hist['Low'].min()

            # 저점 대비 상승률 계산
            rec_1y = ((current_price - low_1y) / low_1y) * 100
            rec_2y = ((current_price - low_2y) / low_2y) * 100
            rec_3y = ((current_price - low_3y) / low_3y) * 100
            
            results.append({
                "ETF": ticker,
                "현재가": round(current_price, 2),
                "1년": round(rec_1y, 1),
                "2년": round(rec_2y, 1),
                "3년": round(rec_3y, 1),
                "전략": get_status_icon(rec_1y) # 1년 기준 아이콘
            })
        except: continue

    if results:
        # 1년 상승률이 낮은 순서(바닥권)로 정렬
        df = pd.DataFrame(results).sort_values(by="1년", ascending=True)
        
        msg = f"<b>📊 ETF 기간별 저점 대비 상승률 리포트</b>\n"
        msg += f"기준: {current_ny_time} (NYT)\n\n"
        
        for _, row in df.iterrows():
            msg += f"<b>{row['ETF']}</b> (현재 ${row['현재가']}) {row['전략']}\n"
            msg += f"└ 1년저점 대비: <b>+{row['1년']}%</b>\n"
            msg += f"└ 2년저점 대비: +{row['2년']}%\n"
            msg += f"└ 3년저점 대비: +{row['3년']}%\n\n"
        
        send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send_data()
