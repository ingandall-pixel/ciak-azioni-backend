import os
import json
from datetime import datetime, timedelta

DB_FILE = "market_db.json"

def carica_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def salva_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def aggiorna_archivio_completo():
    db = carica_db()
    oggi = datetime.now().date()
    limite_5_anni_fa = oggi - timedelta(days=5*365)
    
    # Qui integri la tua logica di recupero dati per ciascun titolo presente nel db
    for ticker, dati_azione in db.items():
        storico = dati_azione.get("istorico", []) # o la chiave che usi per le quotazioni
        
        # 1. Individua l'ultima data di quotazione presente
        if storico:
            ultima_data_str = storico[-1].get('date')
            ultima_data = datetime.strptime(ultima_data_str, '%Y-%m-%d').date()
        else:
            ultima_data = limite_5_anni_fa

        # Se siamo già aggiornati a oggi, saltiamo
        if ultima_data >= oggi:
            continue

        # 2. Scarica i giorni mancanti da ultima_data + 1 giorno fino a oggi
        # (Richiama qui la funzione di download/aggiornamento specifica del tuo script)
        nuovi_dati = scarica_dati_mancanti(ticker, ultima_data + timedelta(days=1), oggi)
        
        if nuovi_dati:
            storico.extend(nuovi_dati)
            # Ordina per data
            storico = sorted(storico, key=lambda x: x['date'])

        # 3. Regola dei 5 anni massimi (finestra mobile rigida)
        # Filtriamo mantenendo solo gli ultimi 5 anni rispetto a oggi
        storico_filtrato = [
            d for d in storico 
            if datetime.strptime(d['date'], '%Y-%m-%d').date() >= limite_5_anni_fa
        ]
        
        dati_azione["istorico"] = storico_filtrato
        db[ticker] = dati_azione

    salva_db(db)
    return db

def scarica_dati_mancanti(ticker, data_inizio, data_fine):
    # Inserisci qui la chiamata effettiva che usi per scaricare i dati da Yahoo/Investing o altra fonte
    dati_scaricati = []
    # Esempio fittizio di integrazione con il tuo scraper esistente
    return dati_scaricati

if __name__ == "__main__":
    aggiorna_archivio_completo()
