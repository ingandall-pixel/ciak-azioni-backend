import sys
import os
import io

# Silenziamo lo stderr a livello OS prima di caricare yfinance
# per evitare che gli avvisi innocui vengano scambiati per errori da server.js
sys.stderr.flush()
devnull = open(os.devnull, 'w')
os.dup2(devnull.fileno(), sys.stderr.fileno())

import json
import time
import logging
import warnings
import urllib.request
import pandas as pd
import yfinance as yf
from datetime import datetime

# Disattivazione log interni yfinance
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

# Definizione dei percorsi assoluti sicuri per salvare il file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')

BATCH_SIZE = 50  # Scarica 50 titoli alla volta in un'unica richiesta per evitare blocchi IP

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
    update_progress(2, "Caricamento registro completo delle azioni (Italia e USA)...")
    
    # 1. Recupero lista azioni USA dal registro SEC / S&P 500
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
        # Fallback S&P 500 se SEC non risponde
        try:
            url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            req = urllib.request.Request(url_sp500, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                sp500_df = pd.read_html(io.StringIO(html))[0]
                tickers_us = [clean_ticker(t).replace('.', '-') for t in sp500_df['Symbol'].tolist()]
        except Exception:
            tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B']

    # 2. Lista completa Azioni Mercato Italiano (FTSE MIB, Mid Cap, Small Cap)
    tickers_it_raw = [
        'A2A.MI', 'ACE.MI', 'AMP.MI', 'ANIM.MI', 'ARN.MI', 'AZM.MI', 'BAMI.MI', 
        'BFF.MI', 'BGN.MI', 'BMED.MI', 'BPE.MI', 'BRE.MI', 'BZU.MI', 'CPR.MI', 'DIA.MI', 
        'ELN.MI', 'ENEL.MI', 'ENI.MI', 'ERG.MI', 'EUC.MI', 'FBK.MI', 'FCT.MI', 'G.MI', 
        'GHC.MI', 'IGD.MI', 'INW.MI', 'IP.MI', 'ISP.MI', 'IVG.MI', 'JUVE.MI', 'LDO.MI', 
        'LUVE.MI', 'MB.MI', 'MFEA.MI', 'MFEB.MI', 'MONC.MI', 'NEXI.MI', 'PIA.MI', 'PIR.MI', 
        'PRY.MI', 'PST.MI', 'RACE.MI', 'REC.MI', 'RWAY.MI', 'SAF.MI', 'SFL.MI', 'SL.MI', 
        'SPM.MI', 'SRG.MI', 'STM.MI', 'TEN.MI', 'TIT.MI', 'TRN.MI', 'TXT.MI', 'UCG.MI', 
        'UNI.MI', 'VTY.MI', 'WBA.MI'
    ]
    
    tickers_it = [clean_ticker(t) for t in tickers_it_raw if clean_ticker(t)]
    
    # Rimuoviamo eventuali duplicati
    return list(dict.fromkeys(tickers_it + tickers_us))

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        update_progress(5, "Database trovato. Aggiornamento incrementale...")
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}
        period_to_fetch = "5d"
    else:
        update_progress(5, "Database assente. Scaricamento completo (5 Anni)...")
        period_to_fetch = "5y"  # Per coprire 1D, 1W, 1M, 1Y e 5Y

    ALL_TICKERS = get_all_tickers()
    total_tickers = len(ALL_TICKERS)
    
    # Dividiamo i ticker in blocchi (batch) da 50
    ticker_batches = [ALL_TICKERS[i:i + BATCH_SIZE] for i in range(0, total_tickers, BATCH_SIZE)]
    total_batches = len(ticker_batches)

    for b_idx, batch in enumerate(ticker_batches):
        try:
            processed_count = min((b_idx + 1) * BATCH_SIZE, total_tickers)
            percent = int((processed_count / total_tickers) * 90) + 5
            update_progress(percent, f"Scaricamento blocco ({b_idx + 1}/{total_batches}) - {processed_count}/{total_tickers} titoli...")

            # DOWNLOAD IN BATCH: 1 sola chiamata per 50 titoli insieme!
            df_batch = yf.download(
                tickers=batch,
                period=period_to_fetch,
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=True
            )

            if df_batch is None or df_batch.empty:
                time.sleep(1.0)
                continue

            for ticker in batch:
                clean_sym = clean_ticker(ticker)
                try:
                    if len(batch) == 1:
                        series = df_batch['Close'] if 'Close' in df_batch else None
                    else:
                        series = df_batch[clean_sym]['Close'] if clean_sym in df_batch and 'Close' in df_batch[clean_sym] else None

                    if series is None or series.dropna().empty:
                        continue

                    series = series.dropna()
                    series.index = series.index.strftime('%Y-%m-%d')
                    new_data = series.to_dict()

                    if db_exists and clean_sym in market_data:
                        old_data = market_data[clean_sym]
                        if len(old_data) > 0 and period_to_fetch == "5d":
                            last_date = list(old_data.keys())[-1]
                            if last_date in old_data:
                                del old_data[last_date]
                        old_data.update(new_data)
                        market_data[clean_sym] = old_data
                    else:
                        market_data[clean_sym] = new_data
                except Exception:
                    continue

            # SALVATAGGIO IMMEDIATO AD OGNI BLOCCO: crea e popola subito market_db.json
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(market_data, f, indent=2)

            time.sleep(1.0)  # Pausa precauzionale tra i blocchi per rispettare Yahoo

        except Exception:
            time.sleep(2.0)
            continue

    # Statistiche finali
    it_count = sum(1 for sym in market_data if sym.endswith('.MI'))
    us_count = len(market_data) - it_count

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": 5.0,
        "us_count": us_count,
        "us_avg_years": 5.0
    })

if __name__ == "__main__":
    download_data()
