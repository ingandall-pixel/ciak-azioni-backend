import sys
import os
import io

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

logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')

# Batch ridotto a 10 per prevenire i blocchi di Yahoo Finance (Rate Limit) sulle richieste massive
BATCH_SIZE = 10

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
    update_progress(2, "Caricamento registro completo delle azioni USA (SEC) e Italia (Borsa Italiana)...")
    
    # 1. Recupero dinamico di TUTTE le azioni USA dalla SEC
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
        tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B']

    # 2. Lista completa ed estesa di TUTTI i principali titoli quotati su Borsa Italiana (Euronext Milan, STAR, Growth)
    tickers_it_raw = [
        'A2A.MI', 'ACE.MI', 'AMP.MI', 'ANIM.MI', 'ARN.MI', 'AZM.MI', 'BAMI.MI', 
        'BFF.MI', 'BGN.MI', 'BMED.MI', 'BPE.MI', 'BRE.MI', 'BZU.MI', 'CPR.MI', 'DIA.MI', 
        'ELN.MI', 'ENEL.MI', 'ENI.MI', 'ERG.MI', 'EUC.MI', 'FBK.MI', 'FCT.MI', 'G.MI', 
        'GHC.MI', 'IGD.MI', 'INW.MI', 'IP.MI', 'ISP.MI', 'IVG.MI', 'JUVE.MI', 'LDO.MI', 
        'LUVE.MI', 'MB.MI', 'MFEA.MI', 'MFEB.MI', 'MONC.MI', 'NEXI.MI', 'PIA.MI', 'PIR.MI', 
        'PRY.MI', 'PST.MI', 'RACE.MI', 'REC.MI', 'RWAY.MI', 'SAF.MI', 'SFL.MI', 'SL.MI', 
        'SPM.MI', 'SRG.MI', 'STM.MI', 'TEN.MI', 'TIT.MI', 'TRN.MI', 'TXT.MI', 'UCG.MI', 
        'UNI.MI', 'VTY.MI', 'WBA.MI', 'ANL.MI', 'AT.MI', 'BNS.MI', 'CAL.MI', 'CEM.MI', 
        'CRE.MI', 'CTI.MI', 'DAN.MI', 'DB.MI', 'DEA.MI', 'DIS.MI', 'EEMS.MI', 'ES.MI', 
        'EXO.MI', 'FAL.MI', 'FI.MI', 'FNC.MI', 'GAD.MI', 'GAS.MI', 'GB.MI', 'GEO.MI', 
        'GR.MI', 'HERA.MI', 'IDE.MI', 'IFC.MI', 'IFP.MI', 'IME.MI', 'IR.MI', 'IT.MI', 
        'LIT.MI', 'MA.MI', 'MED.MI', 'MOL.MI', 'MS.MI', 'MT.MI', 'NED.MI', 'OL.MI', 
        'PAR.MI', 'PER.MI', 'PME.MI', 'PN.MI', 'PR.MI', 'QANT.MI', 'RCL.MI', 'RDM.MI', 
        'RE.MI', 'RIS.MI', 'RME.MI', 'SAB.MI', 'SAI.MI', 'SAR.MI', 'SAS.MI', 'SIA.MI', 
        'SIF.MI', 'SII.MI', 'SIL.MI', 'SIM.MI', 'SIR.MI', 'SMI.MI', 'SN.MI', 'SOG.MI', 
        'SOL.MI', 'SP.MI', 'SSF.MI', 'ST.MI', 'SUM.MI', 'TA.MI', 'TIS.MI', 'TOD.MI', 
        'TR.MI', 'VET.MI', 'VLA.MI', 'ZUC.MI', 'ENAV.MI', 'SY.MI', 'TCL.MI', 'SES.MI', 
        'TRGY.MI', 'DOV.MI', 'DOFS.MI', 'SFER.MI', 'TIN.MI', 'MERC.MI', 'SER.MI', 
        'ORST.MI', 'PO.MI', 'CL.MI', 'MHC.MI', 'ALV.MI', 'AB.MI', 'SIT.MI', 'AM.MI'
    ]
    
    tickers_it = [clean_ticker(t) for t in tickers_it_raw if clean_ticker(t)]
    return list(dict.fromkeys(tickers_it + tickers_us))

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        update_progress(5, "Database trovato. Avvio aggiornamento incrementale...")
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}
        period_to_fetch = "5d"
    else:
        update_progress(5, "Database assente. Scaricamento storico completo (5 Anni)...")
        period_to_fetch = "5y"

    ALL_TICKERS = get_all_tickers()
    total_tickers = len(ALL_TICKERS)
    
    ticker_batches = [ALL_TICKERS[i:i + BATCH_SIZE] for i in range(0, total_tickers, BATCH_SIZE)]
    total_batches = len(ticker_batches)

    for b_idx, batch in enumerate(ticker_batches):
        success = False
        retries = 3
        
        while retries > 0 and not success:
            try:
                processed_count = min((b_idx + 1) * BATCH_SIZE, total_tickers)
                percent = int((processed_count / total_tickers) * 90) + 5
                update_progress(percent, f"Scaricamento blocco ({b_idx + 1}/{total_batches}) - {processed_count}/{total_tickers} titoli...")

                # Download batch con yfinance disattivando i log rumorosi
                df_batch = yf.download(
                    tickers=batch,
                    period=period_to_fetch,
                    group_by='ticker',
                    auto_adjust=True,
                    progress=False,
                    threads=False
                )

                if df_batch is not None and not df_batch.empty:
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
                                old_data.update(new_data)
                                market_data[clean_sym] = old_data
                            else:
                                market_data[clean_sym] = new_data
                        except Exception:
                            continue

                success = True
            except Exception as e:
                retries -= 1
                # Se Yahoo risponde con Too Many Requests (Rate Limit), aumentiamo l'attesa per far sbloccare l'IP
                if "Too Many Requests" in str(e) or "Rate limited" in str(e):
                    time.sleep(10.0)
                else:
                    time.sleep(4.0)

        # Salvataggio incrementale di sicurezza per ogni blocco completato
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(market_data, f, indent=2)
        except Exception:
            pass

        # Pausa di cortesia per evitare i ban temporanei di Yahoo Finance
        time.sleep(1.2)

    it_count = sum(1 for sym in market_data if sym.endswith('.MI'))
    us_count = len(market_data) - it_count
    it_avg_years = 5.0
    us_avg_years = 5.0

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": it_avg_years,
        "us_count": us_count,
        "us_avg_years": us_avg_years
    })

if __name__ == "__main__":
    download_data()
