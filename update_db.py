import os
import json
import time
import urllib.request
import pandas as pd
import io
from datetime import datetime

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

def clean_ticker(symbol):
    if not symbol:
        return ""
    return str(symbol).replace('$', '').strip()

def get_all_tickers():
    update_progress(2, "Caricamento registro completo delle azioni USA (SEC) e Italia...")
    
    tickers_us = []
    try:
        url_sec = 'https://www.sec.gov/files/company_tickers.json'
        req = urllib.request.Request(
            url_sec,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            sec_data = json.loads(response.read().decode('utf-8'))
            tickers_us = [clean_ticker(item['ticker']).replace('.', '-') for item in sec_data.values()]
    except Exception:
        tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

    raw_it = [
        'a2a', 'ace', 'amp', 'anim', 'arn', 'azm', 'bami', 'bff', 'bgn', 'bmed', 
        'bpe', 'bre', 'bzu', 'cpr', 'dia', 'eln', 'enel', 'eni', 'erg', 'euc', 
        'fbk', 'fct', 'g', 'ghc', 'igd', 'inw', 'ip', 'isp', 'ivg', 'juve', 
        'ldo', 'luve', 'mb', 'mfea', 'mfeb', 'monc', 'nexi', 'pia', 'pir', 'pry', 
        'pst', 'race', 'rec', 'rway', 'saf', 'sfl', 'sl', 'spm', 'srg', 'stm', 
        'ten', 'tit', 'trn', 'txt', 'ucg', 'uni', 'vty', 'wba', 'enav', 'sfer', 
        'exo', 'hera', 'anl', 'aal', 'aeffe', 'alg', 'am', 'ascopiave', 'bantes', 
        'ber', 'bif', 'bmps', 'bnl', 'bpc', 'bri', 'br', 'cval', 'ctic', 'dada', 
        'dea', 'dis', 'elica', 'ema', 'espr', 'fidia', 'fnc', 'gedi', 'geox', 
        'gr', 'ie', 'italcementi', 'maire', 'mondadori', 'mutuionline', 'ovs', 
        'pirelli', 'poligrafici', 'rcs', 'reply', 'safilo', 'saras', 'sol', 
        'tamburi', 'tiscali', 'tks', 'trevi', 'unipolsai', 'stellantis', 'ferrari', 
        'leonardo', 'generali', 'unicredit', 'intesasanpaolo', 'snam', 'terna', 
        'italgas', 'recordati', 'inwit', 'bper', 'mps', 'diasorin', 'asm', 
        'avio', 'banca ifis', 'banca generali', 'banca pop sondrio', 'bem', 'beghelli', 
        'buonardi', 'carraro', 'cattolica', 'cematal', 'circuito', 'credem', "d'amico", 
        'digital bros', 'dovalue', 'esprinet', 'eurizon', 'falck renew', 'ferretti', 
        'fidia', 'fiordi', 'franchetti', 'gamenet', 'giglio', 'illimity', 
        'interpump', 'italmobiliare', 'la doria', 'lventure', 'marzotto', 
        'mondadori', 'monrif', 'orsero', 'ovs', 'pininfarina', 
        'piaggio', 'portobello', 'prima', 'reno de medici', 'safe bag', 'sesa', 'seri industrial', 
        'snai', 'sol', 'tamburi', 'tas', 'tiscali', 'trevi', 'unipol', 'valsoia', 
        'netweek', 'esautomotion', 'giglio group', 'illimity', 'indel b', 'wiit', 
        'centrale del latte', 'cofide', 'esprinet', 'falck', 'servizi italia', 'tecnoprint'
    ]
    
    cleaned = []
    for t in raw_it:
        t = t.lower().strip()
        if t.endswith('.mi'):
            t = t[:-3] + '.it'
        elif not t.endswith('.it'):
            t = t + '.it'
        cleaned.append(t)
    tickers_it = list(dict.fromkeys(cleaned))

    return tickers_it, list(dict.fromkeys(tickers_us))

def download_stooq_data(symbol):
    if '.' in symbol:
        stooq_symbol = symbol.lower()
    else:
        stooq_symbol = f"{symbol.lower()}.us"
        
    url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            df = pd.read_csv(io.StringIO(response.read().decode('utf-8')))
            if 'Date' in df.columns and 'Close' in df.columns:
                df = df.dropna(subset=['Close'])
                df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                df = df.dropna(subset=['Close'])
                if not df.empty:
                    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
                    return dict(zip(df['Date'], df['Close']))
    except Exception:
        pass
    return None

def download_data():
    market_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}

    tickers_it, tickers_us = get_all_tickers()
    all_tickers = [(t, 'it') for t in tickers_it] + [(t, 'us') for t in tickers_us]
    total = len(all_tickers)

    for idx, (ticker, market_type) in enumerate(all_tickers):
        percent = int((idx / total) * 90) + 5
        if idx % 100 == 0:
            update_progress(percent, f"Scaricamento ({idx}/{total}) tramite Stooq...")

        if market_type == 'it':
            s_symbol = ticker if ticker.endswith('.it') else f"{ticker}.it"
        else:
            s_symbol = f"{ticker.lower()}.us"

        history = download_stooq_data(s_symbol)
        if history:
            if market_type == 'it':
                clean_key = ticker.upper().replace('.IT', '.MI')
            else:
                clean_key = ticker.upper()
            market_data[clean_key] = history
        
        time.sleep(0.01)

    it_years_list = []
    us_years_list = []

    for sym, hist in market_data.items():
        if not hist:
            continue
        dates = sorted(hist.keys())
        if len(dates) >= 2:
            try:
                d_start = datetime.strptime(dates[0], '%Y-%m-%d')
                d_end = datetime.strptime(dates[-1], '%Y-%m-%d')
                years = (d_end - d_start).days / 365.25
                if sym.endswith('.MI'):
                    it_years_list.append(years)
                else:
                    us_years_list.append(years)
            except Exception:
                pass

    it_count = sum(1 for sym in market_data if sym.endswith('.MI'))
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

if __name__ == "__main__":
    download_data()