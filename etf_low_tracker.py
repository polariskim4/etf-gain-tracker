import yfinance as yf
import pandas as pd
import pytz
import requests
import os
from datetime import datetime

# GitHub Secrets에서 정보 가져오기
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
    """전저점 대비 상승률이 낮을수록 '적극매수' 표시"""
    if recovery_pct <= 15.0:
        return "🔥 적극매수"
    elif recovery_pct <= 40.0:
        return "🟢 매수"
    else:
        return "🟡 진입"

def fetch_and_send_low_data():
    ny_tz = pytz.timezone('America/New_York')
    current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    results = []
    for ticker in TICKERS:
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period="max")
            if hist.empty: continue
            
            # 역대 최저가(ATL) 및 현재가 추출
            atl = hist['Close'].min()
            current_price = hist['Close'].iloc[-1]
            
            # 전저점 대비 상승률(Recovery) 계산
            recovery = ((current_price - atl) / atl) * 100
            
            results.append({
                "ETF": ticker, 
                "전저점": round(atl, 2), 
                "현재가": round(current_price, 2), 
                "상승률": round(recovery, 2), 
                "전략": get_status_icon(recovery)
            })
        except: continue

    if results:
        # 상승률이 낮은 순(바닥에 가까운 순)으로 정렬
        df = pd.DataFrame(results).sort_values(by="상승률", ascending=True)
        
        msg = f"<b>📉 레버리지 ETF 전저점 대비 상승률 리포트</b>\n"
        msg += f"기준: {current_ny_time} (NYT)\n"
        msg += f"(상승률이 낮을수록 바닥권입니다)\n\n"
        
        for _, row in df.iterrows():
            msg += f"<b>{row['ETF']}</b> : +{row['상승률']}% {row['전략']}\n"
            msg += f"└ 현재: ${row['현재가']} / 전저점: ${row['전저점']}\n\n"
        
        send_telegram_message(msg)

if __name__ == "__main__":
    fetch_and_send_low_data()
