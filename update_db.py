import os
import json
import time
import urllib.request
import pandas as pd
import io
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')

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
    update_progress(2, "Caricamento registro globale azioni USA e Italia...")
    
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
        tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

    # Ticker ufficiali e reali di Borsa Italiana supportati da Stooq (solo codici brevi)
    tickers_it = [
        'enel.it', 'eni.it', 'isp.it', 'ucg.it', 'stm.it', 'g.it', 
        'race.it', 'stla.it', 'ldo.it', 'snam.it', 'trn.it', 
        'ig.it', 'rec.it', 'inwit.it', 'bper.it', 'bmps.it', 
        'dia.it', 'mon.it', 'nexi.it', 'pry.it', 'unipol.it', 
        'pst.it', 'erg.it', 'a2a.it', 'hera.it', 'cpr.it', 'fbk.it', 
        'bami.it', 'bff.it', 'bmed.it', 'ip.it', 'spm.it', 
        'srg.it', 'ten.it', 'tit.it', 'enav.it', 'sfer.it', 
        'exo.it', 'amp.it', 'anim.it', 'azm.it', 'bre.it', 
        'fct.it', 'mb.it', 'pia.it', 'sfl.it', 'pirc.it', 
        'igd.it', 'luve.it', 'pi.it', 'pir.it', 'saf.it', 'sl.it', 
        'txt.it', 'uni.it', 'vty.it', 'anl.it', 'aal.it', 'aeffe.it', 
        'alg.it', 'am.it', 'ascopiave.it', 'bpc.it', 'bri.it', 
        'br.it', 'cval.it', 'ctic.it', 'dea.it', 'dis.it', 'elica.it', 
        'ema.it', 'espr.it', 'fidia.it', 'fnc.it', 'gedi.it', 'geox.it', 
        'gr.it', 'ie.it', 'maire.it', 'mondadori.it', 'mutuionline.it', 
        'ovs.it', 'poligrafici.it', 'rcs.it', 'reply.it', 'safilo.it', 
        'sol.it', 'tamburi.it', 'tiscali.it', 'trevi.it', 'valsoia.it', 
        'netweek.it', 'esautomotion.it', 'giglio.it', 'indelb.it', 'wiit.it', 
        'cofide.it', 'falck.it', 'servitalia.it', 'illimity.it', 'dovalue.it', 
        'orsero.it', 'sesa.it', 'sanlorenzo.it', 'digitalbros.it', 'cy4gate.it', 
        'eurotech.it', 'itway.it', 'openjobmetis.it', 'sabaf.it', 'saras.it', 
        'seriindustrial.it', 'tessellis.it', 'avio.it', 'bancaifis.it', 
        'bancagenerali.it', 'bancaprofilo.it', 'beghelli.it', 'brioschi.it', 
        'carraro.it', 'cattolica.it', 'credem.it', 'datalogic.it', 'ferretti.it', 
        'gabetti.it', 'immsi.it', 'interpump.it', 'italmobiliare.it', 'mediobanca.it', 
        'monrif.it', 'pininfarina.it', 'piaggio.it', 'portobello.it', 'prima.it', 
        'snai.it', 'tas.it', 'buzzi.it', 'datalogic.it', 'delonghi.it'
    ]
    
    cleaned = [t.lower().strip() for t in tickers_it]
    return list(dict.fromkeys(cleaned)), list(dict.fromkeys(tickers_us))

def download_stooq_data(symbol):
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('utf-8')
            if 'Exceeded' in content or '<html' in content.lower():
                return None
            df = pd.read_csv(io.StringIO(content))
            if 'Date' in df.columns and 'Close' in df.columns:
                df = df.dropna(subset=['Close'])
                df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                df = df.dropna(subset=['Close'])
                if not df.empty:
                    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
                    return dict(zip(df['Date'], df['Close']))
    except Exception:
        pass
    return None

def download_data():
    market_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}

    tickers_it, tickers_us = get_all_tickers()
    all_tickers = [(t, 'it') for t in tickers_it] + [(t, 'us') for t in tickers_us]
    total = len(all_tickers)

    for idx, (ticker, market_type) in enumerate(all_tickers):
        percent = int((idx / total) * 90) + 5
        if idx % 50 == 0:
            update_progress(percent, f"Scaricamento ({idx}/{total}) in corso...")

        s_symbol = ticker if market_type == 'it' else f"{ticker}.us"

        history = download_stooq_data(s_symbol)
        if history:
            clean_key = ticker.upper().replace('.IT', '.MI') if market_type == 'it' else ticker.upper()
            market_data[clean_key] = history
        
        time.sleep(0.15)

    it_years_list = []
    us_years_list = []

    for sym, hist in market_data.items():
        if not hist:
            continue
        dates = sorted(hist.keys())
        if len(dates) >= 2:
            try:
                d_start = datetime.strptime(dates[0], '%Y-%m-%d')
                d_end = datetime.strptime(dates[-1], '%Y-%m-%d')
                years = (d_end - d_start).days / 365.25
                if sym.endswith('.MI'):
                    it_years_list.append(years)
                else:
                    us_years_list.append(years)
            except Exception:
                pass

    it_count = sum(1 for sym in market_data if sym.endswith('.MI'))
    us_count = len(market_data) - it_count
    
    it_avg_years = round(sum(it_years_list) / len(it_years_list), 1) if it_years_list else 0.0
    us_avg_years = round(sum(us_years_list) / len(us_years_list), 1) if us_years_list else 0.0

    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, indent=2)
    except Exception:
        pass

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": it_avg_years,
        "us_count": us_count,
        "us_avg_years": us_avg_years
    })

if __name__ == "__main__":
    download_data()