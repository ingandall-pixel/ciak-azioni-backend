import os
import json
import time
import requests
import pandas as pd
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

def fetch_yahoo_chart(ticker, range_str="5y"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "range": range_str,
        "interval": "1d",
        "events": "div,split"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None
        data = response.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return None
        
        res = result[0]
        timestamps = res.get("timestamp", [])
        quotes = res.get("indicators", {}).get("quote", [{}])[0]
        closes = quotes.get("close", [])
        
        history = {}
        for ts, close in zip(timestamps, closes):
            if ts and close is not None:
                date_str = pd.to_datetime(ts, unit='s').strftime('%Y-%m-%d')
                history[date_str] = float(close)
        return history
    except Exception:
        return None

def download_data():
    market_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}

    # Mercato USA completo (S&P 500 & NASDAQ 100 integrati)
    tickers_us = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'JNJ',
        'XOM', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV', 'PEP',
        'KO', 'AVGO', 'COST', 'TMO', 'MCD', 'CSCO', 'ABT', 'WMT', 'ACN', 'DHR',
        'LIN', 'DIS', 'NKE', 'ADBE', 'VZ', 'TXN', 'PM', 'NEE', 'RTX', 'QCOM',
        'AMGN', 'HON', 'IBM', 'INTC', 'SBUX', 'CAT', 'GE', 'DE', 'LOW', 'SPGI',
        'AMD', 'LMT', 'PLD', 'ISRG', 'BKNG', 'GILD', 'ADI', 'C', 'MDLZ', 'TJX',
        'ZTS', 'MU', 'LRCX', 'PANW', 'SNPS', 'CDNS', 'SO', 'DUK', 'CL', 'ITW',
        'BSX', 'PGR', 'CI', 'MO', 'BDX', 'EQIX', 'CB', 'SLB', 'SHW',
        'ETN', 'ICE', 'CME', 'NSC', 'CSX', 'HUM', 'WM', 'FCX', 'USB', 'PNC',
        'TGT', 'NOC', 'GD', 'CLX', 'AON', 'IT', 'EMR', 'EOG', 'PSX', 'VLO',
        'PYPL', 'NFLX', 'INTU', 'AMAT', 'BK', 'BLK', 'AXP', 'BA', 'MMM', 'CHTR',
        'PLTR', 'UBER', 'ABNB', 'SNOW', 'CRWD', 'DDOG', 'NET', 'TEAM', 'SHOP', 'SQ',
        'COIN', 'ROKU', 'ZM', 'DOCU', 'PTON', 'TWLO', 'MRNA', 'BNTX', 'PFE', 'LLY',
        'TMUS', 'T', 'CMCSA', 'PARA', 'WBD', 'FOXA', 'EA', 'TTWO', 'RBLX', 'DKNG',
        'WYNN', 'LVS', 'MGM', 'MAR', 'HLT', 'DAL', 'UAL', 'AAL', 'LUV', 'GM',
        'F', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'SNAP', 'PINS', 'SPOT', 'HOOD',
        'ORCL', 'CRM', 'NOW', 'REGN', 'VRTX', 'FISV', 'ADSK', 'MNST', 'O', 'KDP',
        'AZN', 'NVO', 'ASML', 'SHEL', 'TTE', 'BP', 'BHP', 'RY', 'TD', 'HDB',
        'SNY', 'GSK', 'MELI', 'PDD', 'JD', 'BIDU', 'BABA', 'TSM', 'NICE',
        'A', 'AAP', 'ABAC', 'ABCB', 'ACGL', 'ACM', 'ADC', 'ADM', 'ADP', 'AEE',
        'AEP', 'AES', 'AFL', 'AIG', 'AIZ', 'AJG', 'AKAM', 'ALB', 'ALGN', 'ALK',
        'ALL', 'ALLE', 'AMCR', 'AME', 'AMP', 'AMT', 'ANET', 'ANSS', 'AOS', 'APA',
        'APD', 'APH', 'APTV', 'ARE', 'ATO', 'AVB', 'AVY', 'AWK', 'AXON', 'AZO',
        'BAC', 'BALL', 'BAX', 'BBY', 'BEN', 'BF-B', 'BG', 'BIIB', 'BIO', 'BKR',
        'BLDR', 'BMY', 'BR', 'BRO', 'BWA', 'BX', 'BXP', 'CAG', 'CAH', 'CARR',
        'CBOE', 'CBRE', 'CCI', 'CCL', 'CDW', 'CE', 'CEG', 'CF', 'CFG', 'CHD',
        'CHRW', 'CINF', 'CMA', 'CMG', 'CMI', 'CMS', 'CNC', 'CNP', 'COF', 'COO',
        'COP', 'COR', 'CPAY', 'CPB', 'CPRT', 'CPT', 'CRL', 'CSX', 'CTAS', 'CTLT',
        'CTRA', 'CTSH', 'CTVA', 'CVS', 'CZR', 'D', 'DAY', 'DD', 'DECK', 'DFS',
        'DG', 'DGX', 'DHI', 'DLR', 'DLTR', 'DOV', 'DOW', 'DPZ', 'DRI', 'DTE',
        'DVA', 'DVN', 'EA', 'EBAY', 'ECL', 'ED', 'EFX', 'EG', 'EIX', 'EL',
        'ELV', 'EMN', 'ENPH', 'EPAM', 'EQR', 'ERIE', 'ES', 'ESS', 'ETR', 'EVRG',
        'EW', 'EXC', 'EXPD', 'EXPE', 'EXR', 'FANG', 'FAST', 'FDS', 'FDX', 'FE',
        'FFIV', 'FI', 'FITB', 'FLT', 'FMC', 'FOX', 'FRT', 'FSLR', 'FTNT', 'FTV',
        'GDDY', 'GEHC', 'GEN', 'GPC', 'GIS', 'GL', 'GLW', 'GNRC', 'GPN', 'GRMN',
        'GS', 'GWW', 'HAL', 'HAS', 'HBAN', 'HCA', 'HES', 'HIG', 'HII', 'HOLX',
        'HPE', 'HPQ', 'HRL', 'HSIC', 'HST', 'HSY', 'HUBB', 'HWM', 'IDXX', 'IEX',
        'IFF', 'ILMN', 'INCY', 'INVH', 'IPG', 'IQV', 'IR', 'IRM', 'IVZ', 'J',
        'JBHT', 'JBL', 'JCI', 'JKHY', 'JNPR', 'K', 'KEY', 'KEYS', 'KHC', 'KIM',
        'KLAC', 'KMB', 'KMI', 'KMX', 'KR', 'KVUE', 'L', 'LDOS', 'LEN', 'LH',
        'LHX', 'LKQ', 'LLY', 'LNT', 'LULU', 'LW', 'LYB', 'LYV', 'MAA', 'MAS',
        'MCHP', 'MCK', 'MDT', 'MET', 'MHK', 'MKC', 'MKTX', 'MLM', 'MMC', 'MOH',
        'MOS', 'MPC', 'MPWR', 'MRSH', 'MS', 'MSCI', 'MSI', 'MTB', 'MTCH', 'MTD',
        'NCLH', 'NDAQ', 'NDSN', 'NEM', 'NI', 'NLOK', 'NOC', 'NRG', 'NTAP', 'NTRS',
        'NUE', 'NVR', 'NXPI', 'ODFL', 'OGN', 'OKE', 'OMC', 'ON', 'ORLY', 'OTIS',
        'OXY', 'PAYC', 'PAYX', 'PCAR', 'PCG', 'PEAK', 'PEG', 'PFG', 'PGR', 'PH',
        'PHM', 'PKG', 'PNR', 'PNW', 'PODD', 'POOL', 'PPG', 'PPL', 'PRU', 'PSA',
        'PTC', 'PWR', 'QRVO', 'RCL', 'REG', 'RF', 'RHI', 'RJF', 'RL', 'RMD',
        'ROK', 'ROL', 'ROP', 'ROST', 'RSG', 'RVTY', 'SBAC', 'SCHW', 'SEDG', 'SEE',
        'SJM', 'SNA', 'SO', 'SRE', 'STE', 'STLD', 'STT', 'STX', 'STZ', 'SWK',
        'SWKS', 'SYF', 'SYK', 'SYY', 'TAP', 'TDG', 'TDY', 'TECH', 'TEL', 'TER',
        'TFC', 'TFX', 'TSCO', 'TSN', 'TT', 'TXT', 'TYL', 'UA', 'UAA', 'UDR',
        'UHS', 'ULTA', 'UNP', 'UPS', 'URI', 'VLO', 'VLTO', 'VMC', 'VRSK', 'VRSN',
        'VST', 'VTR', 'VTRS', 'WAB', 'WAT', 'WBA', 'WDC', 'WEC', 'WELL', 'WFC',
        'WMB', 'WRB', 'WST', 'WTW', 'WY', 'XEL', 'XYL', 'YUM', 'ZBH', 'ZBRA',
        'ZION'
    ]

    # Mercato Italiano reale esteso
    tickers_it = [
        'A2A.MI', 'AMP.MI', 'AZM.MI', 'BAMI.MI', 'BMED.MI', 'BMPS.MI', 'BPER.MI',
        'ENEL.MI', 'ENI.MI', 'ERG.MI', 'EXOR.AS', 'G.MI', 'HER.MI', 'ISP.MI',
        'LDO.MI', 'MB.MI', 'MONC.MI', 'NEXI.MI', 'PST.MI', 'PRY.MI', 'RACE.MI',
        'SRG.MI', 'STLAM.MI', 'STM.MI', 'TEN.MI', 'TIT.MI', 'TRN.MI', 'UCG.MI',
        'UNI.MI', 'CPR.MI', 'REC.MI', 'SAIPEM.MI', 'AEF.MI', 'ARN.MI', 'ANIM.MI',
        'ASC.MI', 'AVIO.MI', 'BFF.MI', 'BZU.MI', 'CEM.MI', 'DEA.MI', 'ELC.MI',
        'ENAV.MI', 'FCT.MI', 'FILA.MI', 'GEO.MI', 'GVS.MI', 'IG.MI', 'IGD.MI',
        'ILL.MI', 'INW.MI', 'IP.MI', 'ITM.MI', 'IVG.MI', 'JUVE.MI', 'LUVE.MI',
        'MAIRE.MI', 'MOL.MI', 'OVS.MI', 'SAB.MI', 'SFER.MI', 'SOL.MI', 'TIP.MI',
        'WIIT.MI', 'PRT.MI', 'DANIELI.MI', 'ESPRINET.MI', 'GEFRAN.MI', 'KME.MI',
        'MARR.MI', 'MUTUIONLINE.MI', 'PIAGGIO.MI', 'RECORDATI.MI', 'TAMBURI.MI',
        'VALSOIA.MI', 'SESA.MI', 'MONDADORI.MI', 'WEBUILD.MI', 'BREMBO.MI',
        'BUZZI.MI', 'CIR.MI', 'INTERPUMP.MI', 'ITALMOBILIA.MI'
    ]

    tickers_it = list(dict.fromkeys(tickers_it))
    tickers_us = list(dict.fromkeys(tickers_us))

    all_tickers = [(t, 'IT') for t in tickers_it] + [(t, 'US') for t in tickers_us]
    total = len(all_tickers)

    for idx, (sym, market) in enumerate(all_tickers):
        percent = int((idx / total) * 90) + 5
        if idx % 10 == 0:
            update_progress(percent, f"Scaricamento {sym} ({idx}/{total})...")
        
        fetched_history = fetch_yahoo_chart(sym, range_str="5y")
        
        if fetched_history and len(fetched_history) >= 2:
            if sym in market_data:
                combined = market_data[sym]
                combined.update(fetched_history)
                sorted_dates = sorted(combined.keys())
                
                max_days = 1300
                if len(sorted_dates) > max_days:
                    sorted_dates = sorted_dates[-max_days:]
                
                market_data[sym] = {d: combined[d] for d in sorted_dates}
            else:
                sorted_dates = sorted(fetched_history.keys())
                market_data[sym] = {d: fetched_history[d] for d in sorted_dates}
        
        time.sleep(1.2)

    it_years_list, us_years_list = [], []
    for sym, hist in market_data.items():
        if not hist:
            continue
        dates = sorted(hist.keys())
        if len(dates) >= 2:
            try:
                years = (datetime.strptime(dates[-1], '%Y-%m-%d') - datetime.strptime(dates[0], '%Y-%m-%d')).days / 365.25
                if sym in tickers_it or sym.endswith('.MI') or sym.endswith('.AS'):
                    it_years_list.append(years)
                else:
                    us_years_list.append(years)
            except Exception:
                pass

    it_count = sum(1 for sym in market_data if sym in tickers_it or sym.endswith('.MI') or sym.endswith('.AS'))
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
