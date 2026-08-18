import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta

DB_FILE = 'market_db.json'
PROGRESS_FILE = 'progress.json'

# Lista completa e massiccia delle principali azioni italiane (Mib + Mid Cap)
TICKERS_IT = [
    'A2A.MI', 'AMP.MI', 'ANTM.MI', 'AZM.MI', 'BAMI.MI', 'BGN.MI', 'BMED.MI', 
    'BPE.MI', 'BRY.MI', 'BZU.MI', 'CAI.MI', 'CNHI.MI', 'CPR.MI', 'DOP.MI', 
    'ENEL.MI', 'ENI.MI', 'ERG.MI', 'EXO.MI', 'G.MI', 'HER.MI', 'INW.MI', 
    'IP.MI', 'ISP.MI', 'LDO.MI', 'MB.MI', 'MONC.MI', 'NEXI.MI', 'PST.MI', 
    'PRY.MI', 'RACE.MI', 'REC.MI', 'SPM.MI', 'SRG.MI', 'STM.MI', 'TEN.MI', 
    'TIT.MI', 'TRN.MI', 'UCG.MI', 'UNI.MI', 'WBA.MI'
]

# Selezione ampia e robusta dei principali titoli americani (Tech, Finanziari, Industriali, S&P Top)
TICKERS_US = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JNJ', 'V', 
    'JPM', 'WMT', 'MA', 'XOM', 'UNH', 'HD', 'PG', 'DIS', 'BAC', 'PFE', 'NFLX', 
    'AMD', 'INTC', 'ADBE', 'CRM', 'CSCO', 'PEP', 'KO', 'T', 'VZ', 'NKE', 'PYPL'
]

ALL_TICKERS = TICKERS_IT + TICKERS_US

def update_progress(percent, status):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({"percent": percent, "status": status}, f)

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        update_progress(5, "Database trovato. Avvio aggiornamento incrementale...")
        with open(DB_FILE, 'r') as f:
            try:
                market_data = json.load(f)
            except:
                market_data = {}
        period_to_fetch = "5d" # Scarichiamo gli ultimi 5 giorni per aggiornare l'ultima candela
    else:
        update_progress(5, "Nessun Database trovato. Avvio download storico 5 ANNI...")
        period_to_fetch = "5y"

    total_tickers = len(ALL_TICKERS)
    
    for i, ticker in enumerate(ALL_TICKERS):
        try:
            # Calcolo percentuale per la barra di avanzamento (da 5% a 95%)
            percent = int(((i + 1) / total_tickers) * 90) + 5
            update_progress(percent, f"Scaricamento ({i+1}/{total_tickers}): {ticker}")

            # Download da yfinance
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period_to_fetch)
            
            if hist.empty:
                continue

            # Convertiamo le date in stringhe standard
            hist.index = hist.index.strftime('%Y-%m-%d')
            new_data = hist[['Close']].to_dict()['Close']

            if db_exists and ticker in market_data:
                # Se il db esiste, prendiamo i vecchi dati, togliamo l'ultima data registrata e uniamo le nuove
                old_data = market_data[ticker]
                if len(old_data) > 0 and period_to_fetch == "5d":
                    last_date = list(old_data.keys())[-1]
                    if last_date in old_data:
                        del old_data[last_date] # Elimino l'ultima candela per evitare duplicati/incoerenze
                
                # Unisco i vecchi dati ripuliti con le nuove candele scaricate
                old_data.update(new_data)
                market_data[ticker] = old_data
            else:
                # Se il db non esiste (o il ticker è nuovo), salvo lo storico completo
                market_data[ticker] = new_data
            
            # Salvataggio incrementale a checkpoint ogni 10 azioni per evitare crash e perdita dati
            if i % 10 == 0:
                with open(DB_FILE, 'w') as f:
                    json.dump(market_data, f)

            time.sleep(0.3) # Pausa di sicurezza per evitare il blocco (Rate Limit) di Yahoo Finance

        except Exception as e:
            err_msg = f"Errore con {ticker}: {e}"
            print(err_msg)
            # Scriviamo l'errore anche nel file di log per tracciabilità
            with open('error_log.txt', 'a') as log_f:
                log_f.write(f"{datetime.now().isoformat()} - {err_msg}\n")
            continue

    update_progress(98, "Salvataggio finale nel database...")
    
    with open(DB_FILE, 'w') as f:
        json.dump(market_data, f)
        
    update_progress(100, "Completato!")

if __name__ == "__main__":
    download_data()
