import os
import json
import time
import requests
import yfinance as yf
import logging
from datetime import datetime, timedelta

# Disabilita log non necessari per il terminale
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

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
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salva_db(data):
    # Salvataggio compatto per azzerare l'uso di RAM ed evitare l'errore 'Terminated'
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f)

def ottieni_tutti_i_ticker():
    ticker_dinamici = []
    headers = {'User-Agent': 'MarketAnalyzer/1.0'}

    try:
        res_us = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=15)
        if res_us.status_code == 200:
            for value in res_us.json().values():
                t = value.get('ticker')
                if t and len(t) <= 5 and '.' not in t:
                    ticker_dinamici.append(t)
    except Exception:
        pass

    try:
        tv_url = "https://scanner.tradingview.com/italy/scan"
        payload = {"columns": ["name"], "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr"]}]}
        res_it = requests.post(tv_url, json=payload, headers=headers, timeout=15)
        if res_it.status_code == 200:
            for item in res_it.json().get("data", []):
                name = item.get("d", [""])[0]
                if name:
                    ticker_dinamici.append(f"{name}.MI")
    except Exception:
        pass

    return list(set(ticker_dinamici))

def scarica_dati(ticker, data_inizio=None):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=data_inizio.strftime('%Y-%m-%d')) if data_inizio else stock.history(period="5y")
        if df.empty: return {}
        return {idx.strftime('%Y-%m-%d'): {"close": float(row['Close'])} for idx, row in df.iterrows()}
    except Exception:
        return {}

def aggiorna_archivio_completo():
    db = carica_db()
    tutti_i_ticker = ottieni_tutti_i_ticker()
    
    # Se per qualsiasi motivo la scansione di rete fallisce, usa i ticker già presenti nel DB
    if not tutti_i_ticker:
        tutti_i_ticker = list(db.keys())

    total = len(tutti_i_ticker)
    if total == 0:
        return db

    oggi = datetime.now().date()
    limite_5_anni = oggi - timedelta(days=5*365)

    for idx, ticker in enumerate(tutti_i_ticker):
        percent = int((idx / total) * 90) + 5
        if idx % 10 == 0:
            update_progress(percent, f"Scansione {ticker} ({idx + 1}/{total})...")

        dati_esistenti = db.get(ticker, {})
        storico_esistente = dati_esistenti.get("istorico", {}) if isinstance(dati_esistenti, dict) else {}

        date_presenti = []
        for d in storico_esistente.keys():
            try:
                date_presenti.append(datetime.strptime(str(d).split('T')[0], '%Y-%m-%d').date())
            except Exception:
                continue

        nuovi_dati = {}
        if date_presenti:
            ultima_data = max(date_presenti)
            if ultima_data < (oggi - timedelta(days=1)):
                nuovi_dati = scarica_dati(ticker, data_inizio=ultima_data + timedelta(days=1))
        else:
            nuovi_dati = scarica_dati(ticker)

        storico_completo = {**storico_esistente, **nuovi_dati}
        
        storico_filtrato = {}
        date_valide = []
        for d_str, val in storico_completo.items():
            try:
                d_obj = datetime.strptime(str(d_str).split('T')[0], '%Y-%m-%d').date()
                if d_obj >= limite_5_anni:
                    storico_filtrato[d_str] = val
                    date_valide.append(d_obj)
            except Exception:
                continue

        if not storico_filtrato:
            continue

        anni = round(max(0.1, (max(date_valide) - min(date_valide)).days / 365.0), 1) if date_valide else 3.0

        db[ticker] = {
            "istorico": storico_filtrato,
            "years": anni
        }

        # Salvataggio incrementale ogni 50 azioni senza sovraccaricare il disco
        if idx % 50 == 0:
            salva_db(db)

        time.sleep(0.05)

    salva_db(db)
    update_progress(100, "Aggiornamento completato con successo!")
    return db

if __name__ == "__main__":
    aggiorna_archivio_completo()