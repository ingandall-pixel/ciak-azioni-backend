import yfinance as yf
import pandas as pd
import json
import os
import time
import io
import urllib.request
from datetime import datetime

DB_FILE = 'market_db.json'
PROGRESS_FILE = 'progress.json'
LOG_FILE = 'error_log.txt'
BATCH_SIZE = 50 

def update_progress(percent, status, extra_data=None):
    data = {"percent": percent, "status": status}
    if extra_data:
        data.update(extra_data)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)

def log_error(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def clean_ticker(symbol):
    if not symbol:
        return ""
    return str(symbol).replace('$', '').strip()

def get_all_tickers():
    update_progress(2, "Caricamento elenchi completi USA ed Italia...")
    tickers_us = []
    
    # 1. MERCATO USA COMPLETO (SEC Registro Ufficiale con User-Agent conforme)
    try:
        req = urllib.request.Request(
            'https://www.sec.gov/files/company_tickers.json',
            headers={'User-Agent': 'FinancialAppUser admin@financialapp.com'}
        )
        with urllib.request.urlopen(req) as response:
            sec_data = json.loads(response.read().decode())
            for item in sec_data.values():
                symbol = clean_ticker(item['ticker']).replace('.', '-')
                if symbol:
                    tickers_us.append(symbol)
    except Exception as e:
        log_error(f"Errore recupero SEC USA: {e}")

    # Fallback Wikipedia S&P 500 se SEC fallisce
    if not tickers_us:
        try:
            url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            req = urllib.request.Request(
                url_sp500,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                sp500_df = pd.read_html(io.StringIO(html))[0]
                tickers_us = [clean_ticker(t).replace('.', '-') for t in sp500_df['Symbol'].tolist()]
        except Exception as e:
            log_error(f"Errore recupero Wikipedia S&P500: {e}")
            tickers_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

    # 2. MERCATO ITALIA (Titoli principali Borsa Italiana / FTSE MIB / MidCap / Star)
    tickers_it_raw = [
        'A2A.MI', 'ACE.MI', 'AMP.MI', 'ANIM.MI', 'ARN.MI', 'AZM.MI', 'B3.MI', 'BAMI.MI', 
        'BFF.MI', 'BGN.MI', 'BMED.MI', 'BPE.MI', 'BRE.MI', 'BZU.MI', 'CPR.MI', 'DIA.MI', 
        'ELN.MI', 'ENEL.MI', 'ENI.MI', 'ERG.MI', 'EUC.MI', 'FBK.MI', 'FCT.MI', 'G.MI', 
        'GHC.MI', 'IGD.MI', 'INW.MI', 'IP.MI', 'ISP.MI', 'IVG.MI', 'JUVE.MI', 'LDO.MI', 
        'LUVE.MI', 'MB.MI', 'MFEA.MI', 'MFEB.MI', 'MONC.MI', 'NEXI.MI', 'PIA.MI', 'PIR.MI', 
        'PRY.MI', 'PST.MI', 'RACE.MI', 'REC.MI', 'RWAY.MI', 'SAF.MI', 'SFL.MI', 'SL.MI', 
        'SPM.MI', 'SRG.MI', 'STM.MI', 'TEN.MI', 'TIT.MI', 'TRN.MI', 'TXT.MI', 'UCG.MI', 
        'UNI.MI', 'VTY.MI', 'WBA.MI'
    ]

    tickers_it = [clean_ticker(t) for t in tickers_it_raw if clean_ticker(t)]
    return list(dict.fromkeys(tickers_it + tickers_us))

def download_data():
    db_exists = os.path.exists(DB_FILE)
    market_data = {}

    if db_exists:
        update_progress(5, "Database trovato. Aggiornamento incrementale...")
        try:
            with open(DB_FILE, 'r') as f:
                market_data = json.load(f)
        except Exception as e:
            log_error(f"Errore lettura DB esistente: {e}")
            market_data = {}
        period_to_fetch = "5d"
    else:
        update_progress(5, "Database assente. Scaricamento completo...")
        period_to_fetch = "5y"

    ALL_TICKERS = get_all_tickers()
    total_tickers = len(ALL_TICKERS)
    
    if total_tickers == 0:
        log_error("Nessun ticker disponibile per il download.")
        update_progress(100, "Errore: Lista ticker vuota")
        return

    ticker_batches = [ALL_TICKERS[i:i + BATCH_SIZE] for i in range(0, total_tickers, BATCH_SIZE)]
    total_batches = len(ticker_batches)

    for b_idx, batch in enumerate(ticker_batches):
        try:
            processed_count = min((b_idx + 1) * BATCH_SIZE, total_tickers)
            percent = int((processed_count / total_tickers) * 90) + 5
            update_progress(percent, f"Scaricamento blocco ({b_idx + 1}/{total_batches}) - {processed_count}/{total_tickers} titoli...")

            df_batch = yf.download(
                tickers=batch,
                period=period_to_fetch,
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=True
            )

            if df_batch is None or df_batch.empty:
                continue

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
                        if len(old_data) > 0 and period_to_fetch == "5d":
                            last_date = list(old_data.keys())[-1]
                            if last_date in old_data:
                                del old_data[last_date]
                        old_data.update(new_data)
                        market_data[clean_sym] = old_data
                    else:
                        market_data[clean_sym] = new_data
                except Exception as e_tick:
                    log_error(f"Errore estrazione ticker {clean_sym}: {e_tick}")
                    continue

            with open(DB_FILE, 'w') as f:
                json.dump(market_data, f)

            time.sleep(0.5)

        except Exception as e:
            err_msg = f"Errore blocco {b_idx + 1}: {e}"
            print(err_msg)
            log_error(err_msg)
            time.sleep(1.0)
            continue

    # Statistiche finali per il pop-up report
    it_count = 0
    us_count = 0
    it_years = []
    us_years = []

    for sym, prices in market_data.items():
        if not prices or len(prices) < 2:
            continue
        sorted_dates = sorted(prices.keys())
        d_start = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        d_end = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        diff_years = max((d_end - d_start).days / 365.25, 0.01)

        if sym.endswith('.MI'):
            it_count += 1
            it_years.append(diff_years)
        else:
            us_count += 1
            us_years.append(diff_years)

    it_avg_years = round(sum(it_years) / len(it_years), 1) if it_years else 0.0
    us_avg_years = round(sum(us_years) / len(us_years), 1) if us_years else 0.0

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": it_avg_years,
        "us_count": us_count,
        "us_avg_years": us_avg_years
    })

if __name__ == "__main__":
    download_data()
