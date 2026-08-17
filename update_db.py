import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta

DB_FILE = 'market_db.json'
PROGRESS_FILE = 'progress.json'

# Lista rappresentativa (per evitare ban, usiamo i principali titoli MIB e una selezione ampia USA)
TICKERS_IT = ['ENEL.MI', 'ISP.MI', 'UCG.MI', 'ENI.MI', 'RACE.MI', 'STM.MI', 'TIT.MI', 'TRN.MI', 'PRY.MI', 'G.MI']
TICKERS_US = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JNJ', 'V', 'JPM', 'WMT']
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
            market_data = json.load(f)
        period_to_fetch = "5d" # Scarichiamo gli ultimi 5 giorni per sicurezza
    else:
        update_progress(5, "Nessun Database trovato. Avvio download 5 ANNI...")
        period_to_fetch = "5y"

    total_tickers = len(ALL_TICKERS)
    
    for i, ticker in enumerate(ALL_TICKERS):
        try:
            # Calcolo percentuale per la barra
            percent = int(((i + 1) / total_tickers) * 90) + 5
            update_progress(percent, f"Scaricamento: {ticker}")

            # Download da yfinance
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period_to_fetch)
            
            if hist.empty:
                continue

            # Convertiamo le date in stringhe
            hist.index = hist.index.strftime('%Y-%m-%d')
            new_data = hist[['Close']].to_dict()['Close']

            if db_exists and ticker in market_data:
                # Se il db esiste, prendiamo i vecchi dati, togliamo l'ultima data registrata e uniamo le nuove
                old_data = market_data[ticker]
                if len(old_data) > 0:
                    last_date = list(old_data.keys())[-1]
                    del old_data[last_date] # Elimino l'ultima candela
                
                # Unisco i vecchi dati ripuliti con le nuove candele scaricate
                old_data.update(new_data)
                market_data[ticker] = old_data
            else:
                # Se il db non esiste (o il ticker è nuovo), salvo i 5 anni completi
                market_data[ticker] = new_data
                
            time.sleep(0.5) # Pausa vitale per non farsi bloccare da Yahoo Finance

        except Exception as e:
            print(f"Errore con {ticker}: {e}")
            continue

    update_progress(98, "Salvataggio nel database...")
    
    with open(DB_FILE, 'w') as f:
        json.dump(market_data, f)
        
    update_progress(100, "Completato!")

if __name__ == "__main__":
    download_data()
