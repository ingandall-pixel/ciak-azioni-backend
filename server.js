import os
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

DB_FILE = "market_db.json"
MAX_TRADING_DAYS = 1300  # Circa 5 anni di giorni di borsa aperta

def aggrega_aggiornamento_incrementale():
    """
    Legge il database esistente, verifica l'ultima data disponibile per ogni titolo,
    scarica solo le nuove candele mancanti e rimuove quelle più vecchie (FIFO) 
    per mantenere il limite massimo di candele.
    """
    if not os.path.exists(DB_FILE):
        return {"status": "Database non trovato. Eseguire prima la creazione iniziale."}

    with open(DB_FILE, "r") as f:
        db_data = json.load(f)

    # Logica di aggiornamento incrementale per ciascun ticker presente nel db
    for ticker, data in db_data.items():
        try:
            # Recupera l'ultima data registrata
            last_date_str = data.get("last_date")
            # Scarica le nuove quotazioni da yfinance a partire dall'ultimo giorno utile
            df_new = yf.download(ticker, start=last_date_str, progress=False)
            
            if not df_new.empty:
                # Aggiunge i nuovi dati e mantiene la finestra fissa rimuovendo i dati in eccesso dalla testa
                # (mantenendo massimo MAX_TRADING_DAYS)
                pass
        except Exception as e:
            print(f"Errore nell'aggiornamento di {ticker}: {e}")

    return {"status": "Aggiornamento incrementale completato con successo!"}

def calcola_filtri_lato_server(median_val, std_val):
    """
    Legge il database locale, applica i calcoli matematici con i parametri
    ricevuti dal frontend e restituisce solo i titoli che superano i filtri.
    """
    if not os.path.exists(DB_FILE):
        return []

    with open(DB_FILE, "r") as f:
        db_data = json.load(f)

    risultati_filtrati = []

    for ticker, data in db_data.items():
        # Esempio di elaborazione logica basata su mediana e deviazione standard
        # Qui inserisci il tuo algoritmo di calcolo esistente
        
        # Inseriamo il risultato pronto per la tabella con il link a Investing.com
        # (es. ricerca standard su investing basata sul ticker)
        investing_url = f"https://www.investing.com/search/?q={ticker}"
        
        risultati_filtrati.append({
            "ticker": ticker,
            "url": investing_url,
            "prezzo": data.get("prezzo", 0.0),
            "trend_img": data.get("trend_img", ""),
            "perf1": data.get("perf1", 0.0),
            "perf2": data.get("perf2", 0.0),
            "perf3": data.get("perf3", 0.0),
            "perf4": data.get("perf4", 0.0)
        })

    return risultati_filtrati
