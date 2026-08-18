import yfinance as yf
import pandas as pd
import json
import os
import time

DB_FILE = 'market_db.json'
PROGRESS_FILE = 'progress.json'

def update_progress(percent, status):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({"percent": percent, "status": status}, f)

def get_all_tickers():
    update_progress(2, "Raccolta lista completa titoli (Italia + USA)...")
    
    # Mercato Italiano Principale
    tickers_it = [
        'A2A.MI', 'AMP.MI', 'AZM.MI', 'BPE.MI', 'BMED.MI', 'BAMI.MI', 'CPR.MI', 
        'CNHI.MI', 'DIA.MI', 'ENEL.MI', 'ENI.MI', 'ERG.MI', 'RACE.MI', 'G.MI', 
        'HER.MI', 'ISP.MI', 'INW.MI', 'LDO.MI', 'MB.MI', 'MONC.MI', 'NEXI.MI', 
        'PST.MI', 'PRY.MI', 'SPM.MI', 'SRG.MI', 'STM.MI', 'TEN.MI', 'TRN.MI', 
        'TIT.MI', 'UCG.MI', 'UNI.MI', 'EXO.MI', 'IP.MI', 'REC.MI'
    ]
    
    # Mercato Americano (S&P 500 dinamico da Wikipedia)
    try:
        url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url_sp500)[0]
        tickers_us = table['Symbol'].tolist()
        tickers_us = [ticker.replace('.', '-') for ticker in tickers_us]
    except Exception as e:
        print(f"Fallback lista US attivato causa errore: {e}")
        tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'NFLX', 'AMD', 'INTC']

    return tickers_it + tickers_us

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        try:
            with open(DB_FILE, 'r') as f:
                market_data = json.load(f)
        except:
            market_data = {}

    ALL_TICKERS = get_all_tickers()
    total_tickers = len(ALL_TICKERS)
    period_to_fetch = "5d" if db_exists and len(market_data) > 0 else "5y"

    update_progress(5, f"Inizio elaborazione di {total_tickers} azioni...")

    for i, ticker in enumerate(ALL_TICKERS):
        try:
            percent = int(((i + 1) / total_tickers) * 92) + 5
            update_progress(percent, f"Scaricamento ({i+1}/{total_tickers}): {ticker}")

            stock = yf.Ticker(ticker)
            hist = stock.history(period=period_to_fetch)
            
            if hist.empty:
                continue

            hist.index = hist.index.strftime('%Y-%m-%d')
            new_data = hist[['Close']].to_dict()['Close']

            if db_exists and ticker in market_data:
                old_data = market_data[ticker]
                if len(old_data) > 0 and period_to_fetch == "5d":
                    last_date = list(old_data.keys())[-1]
                    if last_date in old_data:
                        del old_data[last_date] # Rimuove l'ultima candela per aggiornarla
                old_data.update(new_data)
                market_data[ticker] = old_data
            else:
                market_data[ticker] = new_data
            
            # Salvataggio incrementale a checkpoint ogni 10 azioni per evitare perdita dati in caso di crash
            if i % 10 == 0:
                with open(DB_FILE, 'w') as f:
                    json.dump(market_data, f)

            time.sleep(0.15) # Pausa di sicurezza anti-ban

        except Exception as e:
            print(f"Errore critico su {ticker}: {e}")
            continue

    update_progress(99, "Salvataggio finale database in corso...")
    with open(DB_FILE, 'w') as f:
        json.dump(market_data, f)
        
    update_progress(100, "Completato!")

if __name__ == "__main__":
    download_data()
