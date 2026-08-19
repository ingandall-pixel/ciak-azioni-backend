import os
import json
import time
import sys
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')

def update_progress(percent, status, extra_data=None):
    data = {"percent": percent, "status": status}
    if extra_data:
        data.update(extra_data)
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass

def fetch_yahoo_chart(ticker, range_str="5y"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "range": range_str,
        "interval": "1d",
        "events": "div,split"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None
        data = response.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return None
        
        res = result[0]
        timestamps = res.get("timestamp", [])
        quotes = res.get("indicators", {}).get("quote", [{}])[0]
        closes = quotes.get("close", [])
        
        history = {}
        for ts, close in zip(timestamps, closes):
            if ts and close is not None:
                date_str = pd.to_datetime(ts, unit='s').strftime('%Y-%m-%d')
                history[date_str] = float(close)
        return history
    except Exception:
        return None

def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception:
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

def get_nasdaq100_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/NASDAQ-100"
        tables = pd.read_html(url)
        for df in tables:
            for col in ['Ticker', 'Symbol']:
                if col in df.columns:
                    return df[col].tolist()
    except Exception:
        return []

def download_data():
    market_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}

    update_progress(5, "Recupero elenchi completi dai mercati...")
    
    us_tickers_raw = list(set(get_sp500_tickers() + get_nasdaq100_tickers()))
    
    # Elenco pulito e corretto con ENEL.MI e i principali titoli italiani
    tickers_it = [
        'ENEL.MI', 'ISP.MI', 'UCG.MI', 'ENI.MI', 'G.MI', 'RACE.MI', 'STLAM.MI', 'STM.MI', 
        'TRN.MI', 'SRG.MI', 'PRY.MI', 'MONC.MI', 'MB.MI', 'LDO.MI', 'SPM.MI', 'NEXI.MI', 
        'REC.MI', 'HER.MI', 'A2A.MI', 'IG.MI', 'BAMI.MI', 'BPER.MI', 'BMPS.MI', 'AZM.MI', 
        'FINECO.MI', 'PST.MI', 'EXOR.AS', 'UNIS.MI', 'IP.MI', 'INW.MI', 'CPR.MI', 'DANIELI.MI'
    ]

    all_tickers = [(t, 'IT') for t in tickers_it] + [(t, 'US') for t in us_tickers_raw]
    total = len(all_tickers)

    for idx, (sym, market) in enumerate(all_tickers):
        percent = int((idx / total) * 90) + 5
        if idx % 10 == 0:
            update_progress(percent, f"Scaricamento {sym} ({idx}/{total})...")
        
        fetched_history = fetch_yahoo_chart(sym, range_str="5y")
        
        if fetched_history and len(fetched_history) >= 2:
            if sym in market_data:
                combined = market_data[sym]
                combined.update(fetched_history)
                sorted_dates = sorted(combined.keys())
                
                max_days = 1300
                if len(sorted_dates) > max_days:
                    sorted_dates = sorted_dates[-max_days:]
                
                market_data[sym] = {d: combined[d] for d in sorted_dates}
            else:
                sorted_dates = sorted(fetched_history.keys())
                market_data[sym] = {d: fetched_history[d] for d in sorted_dates}
        
        time.sleep(0.3)

    it_years_list, us_years_list = [], []
    for sym, hist in market_data.items():
        if not hist:
            continue
        dates = sorted(hist.keys())
        if len(dates) >= 2:
            try:
                years = (datetime.strptime(dates[-1], '%Y-%m-%d') - datetime.strptime(dates[0], '%Y-%m-%d')).days / 365.25
                if sym in tickers_it or sym.endswith('.MI') or sym.endswith('.AS'):
                    it_years_list.append(years)
                else:
                    us_years_list.append(years)
            except Exception:
                pass

    it_count = sum(1 for sym in market_data if sym in tickers_it or sym.endswith('.MI') or sym.endswith('.AS'))
    us_count = len(market_data) - it_count
    
    it_avg_years = round(sum(it_years_list) / len(it_years_list), 1) if it_years_list else 0.0
    us_avg_years = round(sum(us_years_list) / len(us_years_list), 1) if us_years_list else 0.0

    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, indent=2)
    except Exception:
        pass

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": it_avg_years,
        "us_count": us_count,
        "us_avg_years": us_avg_years
    })

def analyze(market, tf, median_markup, std_ratio):
    if not os.path.exists(DB_FILE):
        return []

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    days_map = {'1d': 2, '1w': 7, '1m': 30, '1y': 365, '5y': 1825, 'max': 99999}
    target_days = days_map.get(tf, 30)

    for ticker, history in data.items():
        is_it = ticker.endswith('.MI') or ticker.endswith('.AS')
        if (market == 'IT' and not is_it) or (market == 'US' and is_it):
            continue

        dates = sorted(history.keys())
        if len(dates) < 2:
            continue

        latest_date_str = dates[-1]
        latest_dt = datetime.strptime(latest_date_str, '%Y-%m-%d')
        
        if tf == 'max':
            filtered_dates = dates
        else:
            cutoff = latest_dt - timedelta(days=target_days)
            filtered_dates = [d for d in dates if datetime.strptime(d, '%Y-%m-%d') >= cutoff]

        if len(filtered_dates) < 2:
            continue

        prices = [history[d] for d in filtered_dates]
        np_prices = np.array(prices)

        mean_val = np.mean(np_prices)
        median_val = np.median(np_prices)
        std_val = np.std(np_prices)

        if mean_val == 0:
            continue

        med_markup_pct = ((median_val - mean_val) / mean_val) * 100.0
        std_ratio_pct = (std_val / mean_val) * 100.0

        if med_markup_pct >= median_markup and std_ratio_pct >= std_ratio:
            # Prende l'effettivo prezzo corrente (ultimo giorno disponibile)
            curr_price = history[dates[-1]]
            prev_price = history[filtered_dates[0]]
            var_period = ((curr_price - prev_price) / prev_price) * 100.0

            all_prices = [history[d] for d in dates]
            daily_var = 0.0
            if len(all_prices) >= 2:
                daily_var = ((all_prices[-1] - all_prices[-2]) / all_prices[-2]) * 100.0

            sparkline = prices[-30:] if len(prices) >= 30 else prices

            results.append({
                "ticker": ticker,
                "price": round(curr_price, 2),
                "var_period": round(var_period, 2),
                "var_daily": round(daily_var, 2),
                "med_mean_ratio": round(med_markup_pct, 2),
                "std_mean_ratio": round(std_ratio_pct, 2),
                "sparkline": sparkline
            })

    return results

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'download':
        download_data()
    elif len(sys.argv) > 4:
        m = sys.argv[1]
        tf = sys.argv[2]
        mm = float(sys.argv[3])
        sr = float(sys.argv[4])
        print(json.dumps(analyze(m, tf, mm, sr)))
    else:
        download_data()