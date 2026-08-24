import os
import json
import time
import requests
import yfinance as yf
import logging
from datetime import datetime, timedelta

# Silenzia i messaggi di errore di yfinance per tenere il terminale pulito
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

DB_FILE = "market_db.json"
PROGRESS_FILE = "progress.json"
TEMP_DIR = "temp_db"

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

def ottieni_tutti_i_ticker_dinamici():
    ticker_dinamici = []
    app_headers = {'User-Agent': 'MarketAnalyzerApp/1.0 (admin@marketanalyzer.com)'}

    print("--- FASE 1: Scansione Mercato USA (Server SEC) ---")
    try:
        res_us = requests.get("https://www.sec.gov/files/company_tickers.json", headers=app_headers, timeout=15)
        if res_us.status_code == 200:
            for key, value in res_us.json().items():
                t = value.get('ticker')
                if t and len(t) <= 5 and '.' not in t:
                    ticker_dinamici.append(t)
            print(f"✅ Estratti {len(ticker_dinamici)} ticker validi dall'America.")
    except Exception as e:
        print(f"❌ Errore connessione USA: {e}")

    print("--- FASE 2: Scansione Mercato Italiano (Scanner TradingView) ---")
    try:
        tv_url = "https://scanner.tradingview.com/italy/scan"
        payload = {"columns": ["name"], "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr"]}]}
        res_it = requests.post(tv_url, json=payload, headers=app_headers, timeout=15)
        if res_it.status_code == 200:
            it_count = 0
            for item in res_it.json().get("data", []):
                ticker_name = item.get("d", [""])[0]
                if ticker_name:
                    ticker_dinamici.append(f"{ticker_name}.MI")
                    it_count += 1
            print(f"✅ Estratte in tempo reale {it_count} azioni Italiane (Listino completo e aggiornato).")
    except Exception as e:
        print(f"❌ Errore critico API Italia: {e}")

    return list(set(ticker_dinamici))

def scarica_dati_yfinance(ticker, data_inizio=None):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=data_inizio.strftime('%Y-%m-%d')) if data_inizio else stock.history(period="5y")
        if df.empty: return {}
            
        return {indice.strftime('%Y-%m-%d'): {"close": float(riga['Close'])} for indice, riga in df.iterrows()}
    except Exception:
        return {}

def aggiorna_archivio_completo():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    print("\nConnessione ai server in corso per il recupero dei listini globali...")
    update_progress(2, "Connessione ai server per estrazione ticker...")
    
    tutti_i_ticker = ottieni_tutti_i_ticker_dinamici()
    total = len(tutti_i_ticker)
    
    if total == 0:
        print("Nessun ticker trovato dai server.")
        return
        
    print(f"\nInizio download dati per {total} azioni (Modalità Risparmio RAM).")
    oggi = datetime.now().date()
    limite_5_anni_fa = oggi - timedelta(days=5*365)
    
    it_count, us_count, it_years, us_years = 0, 0, 0.0, 0.0

    for idx, ticker in enumerate(tutti_i_ticker):
        percent = int((idx / total) * 90) + 5
        if idx % 20 == 0:
            update_progress(percent, f"Scansione in corso: {ticker} ({idx + 1}/{total})")

        file_ticker = os.path.join(TEMP_DIR, f"{ticker}.json")
        dati_azione = {"istorico": {}, "years": 0.0}
        
        # Se il file esiste già e contiene dati recenti, saltalo istantaneamente per velocità
        if os.path.exists(file_ticker):
            try:
                with open(file_ticker, 'r', encoding='utf-8') as tf:
                    dati_azione = json.load(tf)
                
                storico_esistente = dati_azione.get("istorico", {})
                if storico_esistente:
                    date_presenti = [datetime.strptime(str(d).split('T')[0], '%Y-%m-%d').date() for d in storico_esistente.keys()]
                    if date_presenti and max(date_presenti) >= (oggi - timedelta(days=1)):
                        anni = dati_azione.get("years", 0.0)
                        if ticker.endswith('.MI'):
                            it_count += 1; it_years += anni
                        else:
                            us_count += 1; us_years += anni
                        continue
            except Exception:
                pass
        
        storico_esistente = dati_azione.get("istorico", {})
        date_presenti = [datetime.strptime(str(d).split('T')[0], '%Y-%m-%d').date() for d in storico_esistente.keys()] if storico_esistente else []
        
        nuovi_dati = {}
        if date_presenti:
            ultima_data = max(date_presenti)
            if ultima_data < (oggi - timedelta(days=1)):
                nuovi_dati = scarica_dati_yfinance(ticker, data_inizio=ultima_data + timedelta(days=1))
        else:
            nuovi_dati = scarica_dati_yfinance(ticker)

        storico_aggiornato = {**storico_esistente, **nuovi_dati}

        storico_filtrato = {}
        date_valide = []
        for d_str, val in storico_aggiornato.items():
            try:
                d_obj = datetime.strptime(str(d_str).split('T')[0], '%Y-%m-%d').date()
                if d_obj >= limite_5_anni_fa:
                    storico_filtrato[d_str] = val
                    date_valide.append(d_obj)
            except Exception:
                pass

        if not storico_filtrato:
            if os.path.exists(file_ticker): os.remove(file_ticker)
            continue

        anni = round(max(0.1, (max(date_valide) - min(date_valide)).days / 365.0), 1) if date_valide else 0.0
        
        with open(file_ticker, 'w', encoding='utf-8') as tf:
            json.dump({"istorico": storico_filtrato, "years": anni}, tf)
            
        if ticker.endswith('.MI'):
            it_count += 1; it_years += anni
        else:
            us_count += 1; us_years += anni

        time.sleep(0.15) 

    # FASE FINALE: Unisce tutti i file in uno solo scrivendo direttamente su disco
    print("\nAssemblaggio del database finale in corso... (Questo richiede pochi secondi)")
    update_progress(96, "Assemblaggio del database finale in corso...")
    
    with open(DB_FILE, 'w', encoding='utf-8') as f_out:
        f_out.write("{\n")
        files = [f for f in os.listdir(TEMP_DIR) if f.endswith('.json')]
        count_files = len(files)
        
        for i, filename in enumerate(files):
            ticker_name = filename.replace('.json', '')
            with open(os.path.join(TEMP_DIR, filename), 'r', encoding='utf-8') as tf:
                f_out.write(f'"{ticker_name}": {tf.read()}')
                if i < count_files - 1:
                    f_out.write(",\n")
        f_out.write("\n}")

    it_avg = round(it_years / it_count, 1) if it_count > 0 else 0.0
    us_avg = round(us_years / us_count, 1) if us_count > 0 else 0.0

    update_progress(100, "Scansione globale completata!", {
        "it_count": it_count, "it_avg_years": it_avg,
        "us_count": us_count, "us_avg_years": us_avg
    })
    
    print("\n[100%] Operazione completata con successo! Architettura a basso consumo RAM riuscita.")

if __name__ == "__main__":
    aggiorna_archivio_completo()