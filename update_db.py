import json
import os
import time
import urllib.request
from datetime import datetime

DB_FILE = 'market_db.json'
PROGRESS_FILE = 'progress.json'

# Elenco completo dei titoli target
TICKERS_IT = [
    'A2A.MI', 'AMP.MI', 'AZM.MI', 'BAMI.MI', 'BGN.MI', 'BMED.MI', 'BPE.MI', 
    'CPR.MI', 'DIA.MI', 'ENEL.MI', 'ENI.MI', 'ERG.MI', 'FBK.MI', 'G.MI', 
    'INW.MI', 'ISP.MI', 'JUVE.MI', 'LDO.MI', 'MB.MI', 'MONC.MI', 'NEXI.MI', 
    'PRY.MI', 'PST.MI', 'RACE.MI', 'REC.MI', 'SPM.MI', 'SRG.MI', 'STM.MI', 
    'TEN.MI', 'TIT.MI', 'TRN.MI', 'UCG.MI', 'UNI.MI'
]

TICKERS_US = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 
    'JNJ', 'V', 'JPM', 'WMT', 'AMD', 'NFLX', 'DIS', 'BAC', 'PFE', 'KO'
]

def update_progress(percent, status, extra_data=None):
    data = {"percent": percent, "status": status}
    if extra_data:
        data.update(extra_data)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)

def fetch_yahoo_chart(ticker, range_period="5y"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_period}&interval=1d"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            result = res_data['chart']['result'][0]
            timestamps = result.get('timestamp', [])
            closes = result['indicators']['quote'][0].get('close', [])
            
            price_dict = {}
            for ts, close in zip(timestamps, closes):
                if close is not None:
                    date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    price_dict[date_str] = round(close, 2)
            return price_dict
    except Exception:
        return None

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        try:
            with open(DB_FILE, 'r') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}
        range_period = "5d"
        update_progress(5, "Aggiornamento incrementale...")
    else:
        range_period = "5y"  # Copre perfettamente 1D, 1W, 1M, 1Y e 5Y
        update_progress(5, "Scaricamento storico (5 Anni)...")

    all_tickers = TICKERS_IT + TICKERS_US
    total = len(all_tickers)

    for idx, ticker in enumerate(all_tickers):
        percent = int(((idx + 1) / total) * 90) + 5
        update_progress(percent, f"Scaricamento {ticker} ({idx+1}/{total})...")
        
        prices = fetch_yahoo_chart(ticker, range_period)
        if prices:
            if ticker in market_data and db_exists:
                market_data[ticker].update(prices)
            else:
                market_data[ticker] = prices
                
            with open(DB_FILE, 'w') as f:
                json.dump(market_data, f)
        
        time.sleep(0.2)

    it_count = sum(1 for t in market_data if t in TICKERS_IT)
    us_count = sum(1 for t in market_data if t in TICKERS_US)

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": 5.0,
        "us_count": us_count,
        "us_avg_years": 5.0
    })

if __name__ == "__main__":
    download_data()
