import sys
import os
import json
import time
import logging
import warnings
import urllib.request
import yfinance as yf
from datetime import datetime

# Silenzia gli errori di sistema e i log di yfinance
sys.stderr.flush()
devnull = open(os.devnull, 'w')
os.dup2(devnull.fileno(), sys.stderr.fileno())
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')

# Batch ridotto per evitare il ban dell'IP da Yahoo
BATCH_SIZE = 8

def update_progress(percent, status, extra_data=None):
    data = {"percent": percent, "status": status}
    if extra_data: data.update(extra_data)
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except: pass

def get_all_tickers():
    update_progress(2, "Recupero lista completa mercati (USA + Italia)...")
    
    # Lista USA dinamica dalla SEC
    tickers_us = []
    try:
        url = 'https://www.sec.gov/files/company_tickers.json'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            tickers_us = [item['ticker'].replace('.', '-') for item in data.values()]
    except:
        tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'NVDA']

    # Per l'Italia: carichiamo i panieri completi da una fonte affidabile (Wikipedia/Borsa Italiana)
    # Poiché non possiamo fare web scraping complesso qui, aggiungiamo i prefissi 
    # di tutti i mercati italiani (Euronext Milan, STAR, EGM)
    # Nota: se hai un file 'tickers_it.txt' con i 500 titoli, caricalo qui.
    # Se non lo hai, usiamo una lista di espansione automatica.
    
    # ESEMPIO: Se vuoi 500 titoli, crea un file 'tickers_it.txt' nella cartella 
    # e decommenta le righe sotto:
    try:
        with open(os.path.join(BASE_DIR, 'tickers_it.txt'), 'r') as f:
            tickers_it = [line.strip() for line in f.readlines()]
    except:
        # Fallback se il file manca: una lista molto più ampia
        tickers_it = ['A2A.MI', 'ENEL.MI', 'ENI.MI', 'ISP.MI', 'UCG.MI', 'STLA.MI', 'PRY.MI', 'RACE.MI', 'TLIT.MI'] # ecc...
    
    return list(set(tickers_it + tickers_us))

def download_data():
    market_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: market_data = json.load(f)
    
    tickers = get_all_tickers()
    
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i+BATCH_SIZE]
        try:
            # Download con yfinance, gestendo le eccezioni
            data = yf.download(batch, period="2y", group_by='ticker', progress=False)
            
            for ticker in batch:
                try:
                    # Estrazione sicura
                    if len(batch) > 1:
                        df = data[ticker]
                    else:
                        df = data
                    
                    if not df.empty and 'Close' in df:
                        series = df['Close'].dropna()
                        market_data[ticker] = series.apply(lambda x: float(x)).to_dict()
                except:
                    continue # Se il ticker fallisce, passa al prossimo senza crashare
                    
            update_progress(int((i/len(tickers))*100), f"Elaborazione: {i}/{len(tickers)}")
            time.sleep(2) # Pausa anti-ban
            
        except Exception as e:
            if 'Too Many Requests' in str(e):
                time.sleep(30) # Pausa lunga se Yahoo ci blocca
            continue

    with open(DB_FILE, 'w') as f:
        json.dump(market_data, f)
    update_progress(100, "Completato!")

if __name__ == "__main__":
    download_data()S
