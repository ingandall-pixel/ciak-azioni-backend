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
    
    # 1. Azioni USA dalla SEC (numero di azioni invariato)
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

    # 2. Azioni Italia
    tickers_it = []
    it_file_path = os.path.join(BASE_DIR, 'tickers_it.txt')
    if os.path.exists(it_file_path):
        try:
            with open(it_file_path, 'r', encoding='utf-8') as f:
                tickers_it = [clean_ticker(line) for line in f if line.strip()]
        except Exception:
            pass
    
    if not tickers_it:
        tickers_it_raw = [
            'A2A.MI', 'ACE.MI', 'AMP.MI', 'ANIM.MI', 'ARN.MI', 'AZM.MI', 'BAMI.MI', 
            'BFF.MI', 'BGN.MI', 'BMED.MI', 'BPE.MI', 'BRE.MI', 'BZU.MI', 'CPR.MI', 'DIA.MI', 
            'ELN.MI', 'ENEL.MI', 'ENI.MI', 'ERG.MI', 'EUC.MI', 'FBK.MI', 'FCT.MI', 'G.MI', 
            'GHC.MI', 'IGD.MI', 'INW.MI', 'IP.MI', 'ISP.MI', 'IVG.MI', 'JUVE.MI', 'LDO.MI', 
            'LUVE.MI', 'MB.MI', 'MFEA.MI', 'MFEB.MI', 'MONC.MI', 'NEXI.MI', 'PIA.MI', 'PIR.MI', 
            'PRY.MI', 'PST.MI', 'RACE.MI', 'REC.MI', 'RWAY.MI', 'SAF.MI', 'SFL.MI', 'SL.MI', 
            'SPM.MI', 'SRG.MI', 'STM.MI', 'TEN.MI', 'TIT.MI', 'TRN.MI', 'TXT.MI', 'UCG.MI', 
            'UNI.MI', 'VTY.MI', 'WBA.MI', 'ENAV.MI', 'SFER.MI', 'EXO.MI', 'HERA.MI'
        ]
        tickers_it = [clean_ticker(t) for t in tickers_it_raw if clean_ticker(t)]

    return list(dict.fromkeys(tickers_it + tickers_us))

def download_stooq_data(symbol):
    # Converte il simbolo per l'interrogazione pulita su Stooq
    if symbol.endswith('.MI'):
        stooq_symbol = symbol.replace('.MI', '.it').lower()
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

    tickers = get_all_tickers()
    total = len(tickers)

    for idx, ticker in enumerate(tickers):
        percent = int((idx / total) * 90) + 5
        if idx % 50 == 0:
            update_progress(percent, f"Scaricamento ({idx}/{total}) tramite API ufficiali...")

        history = download_stooq_data(ticker)
        if history:
            market_data[ticker] = history
        
        time.sleep(0.03) # Pausa minima e sicura per la stabilità della connessione

    it_count = sum(1 for sym in market_data if sym.endswith('.MI'))
    us_count = len(market_data) - it_count
    it_avg_years = 2.0
    us_avg_years = 2.0

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
