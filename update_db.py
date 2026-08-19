import os
import json
import time
from datetime import datetime, timedelta

# Importiamo la funzione di download da analyzer se disponibile
try:
    from analyzer import download_data
except ImportError:
    download_data = None

DB_FILE = "market_db.json"
PROGRESS_FILE = "progress.json"

def update_progress(percent, status, extra_data=None):
    data = {"percent": percent, "status": status}
    if extra_data:
        data.update(extra_data)
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass

def carica_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def salva_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def aggiorna_archivio_completo():
    db = carica_db()
    
    # Se il database è vuoto o non esiste, avviamo direttamente il download massivo
    if not db or len(db) == 0:
        print("Archivio vuoto o inesistente. Avvio del download completo dei mercati...")
        if download_data:
            download_data()
            return carica_db()
        else:
            print("Errore: Impossibile trovare la funzione di download in analyzer.py")
            return db

    oggi = datetime.now().date()
    limite_5_anni_fa = oggi - timedelta(days=5*365)
    
    items = list(db.items())
    total = len(items)
    
    print(f"Avvio aggiornamento per {total} titoli presenti nell'archivio...")

    for idx, (ticker, dati_azione) in enumerate(items):
        percent = int((idx / total) * 90) + 5
        status_msg = f"Aggiornamento {ticker} ({idx + 1}/{total})..."
        
        if idx % 5 == 0:
            update_progress(percent, status_msg)
            print(f"[{percent}%] {status_msg}")

        storico = dati_azione.get("istorico", dati_azione if isinstance(dati_azione, dict) else [])
        
        if isinstance(storico, dict):
            storico_filtrato = {d: p for d, p in storico.items() if datetime.strptime(d, '%Y-%m-%d').date() >= limite_5_anni_fa}
            db[ticker] = storico_filtrato
        elif isinstance(storico, list):
            storico_filtrato = [
                d for d in storico 
                if isinstance(d, dict) and 'date' in d and datetime.strptime(d['date'], '%Y-%m-%d').date() >= limite_5_anni_fa
            ]
            dati_azione["istorico"] = storico_filtrato
            db[ticker] = dati_azione

        time.sleep(0.1)

    salva_db(db)
    update_progress(100, "Aggiornamento completato con successo!")
    print("[100%] Aggiornamento dell'archivio completato con successo!")
    return db

if __name__ == "__main__":
    aggiorna_archivio_completo()