import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')

def analyze_market(market_filter="IT", timeframe="1m", min_median=50.0, min_std=10.0):
    if not os.path.exists(DB_FILE):
        print(json.dumps([]))
        return

    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            market_data = json.load(f)
    except Exception:
        print(json.dumps([]))
        return

    # Mappa i giorni in base al timeframe scelto
    tf_days = {
        "1w": 7,
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "ytd": (datetime.now() - datetime(datetime.now().year, 1, 1)).days
    }
    days_back = tf_days.get(timeframe, 30)

    results = []
    cutoff_date = datetime.now() - timedelta(days=days_back)

    for ticker, history in market_data.items():
        # Filtro per mercato (IT vs US)
        is_it = ticker.endswith('.MI') or ticker.endswith('.AS')
        if market_filter == "IT" and not is_it:
            continue
        if market_filter == "US" and is_it:
            continue

        if not history or len(history) < 2:
            continue

        dates = sorted(history.keys())
        prices = [history[d] for d in dates]
        
        # Prezzo corrente (ultimo disponibile)
        current_price = prices[-1]
        
        # Variazione giornaliera (ultimo rispetto al precedente)
        var_daily = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) >= 2 else 0.0

        # Filtra le date per il timeframe selezionato per calcolare le performance del periodo
        filtered_prices = []
        for d_str, price in history.items():
            try:
                dt = datetime.strptime(d_str, '%Y-%m-%d')
                if dt >= cutoff_date:
                    filtered_prices.append(price)
            except Exception:
                continue

        if len(filtered_prices) < 2:
            filtered_prices = prices[-min(len(prices), days_back):]

        # Variazione del periodo
        start_period_price = filtered_prices[0]
        var_period = ((current_price - start_period_price) / start_period_price) * 100

        # Calcoli statistici su base storica / periodo
        arr = np.array(filtered_prices)
        mean_val = np.mean(arr)
        median_val = np.median(arr)
        std_val = np.std(arr)

        if mean_val == 0:
            continue

        # Rapporti percentuali richiesti
        med_mean_ratio = (median_val / mean_val) * 100
        std_mean_ratio = (std_val / mean_val) * 100

        # Applicazione dei filtri come LIMITI MINIMI INFERIORI (>=)
        if med_mean_ratio >= min_median and std_mean_ratio >= min_std:
            results.append({
                "ticker": ticker,
                "price": round(current_price, 2),
                "var_period": round(var_period, 2),
                "var_daily": round(var_daily, 2),
                "med_mean_ratio": round(med_mean_ratio, 2),
                "std_mean_ratio": round(std_mean_ratio, 2)
            })

    print(json.dumps(results))

if __name__ == "__main__":
    # Parametri passati da riga di comando: [market, timeframe, min_median, min_std]
    m_filter = sys.argv[1] if len(sys.argv) > 1 else "IT"
    t_frame = sys.argv[2] if len(sys.argv) > 2 else "1m"
    m_med = float(sys.argv[3]) if len(sys.argv) > 3 else 50.0
    m_std = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0

    if m_filter == "download":
        # Gestito eventualmente da altri flussi o script
        pass
    else:
        analyze_market(m_filter, t_frame, m_med, m_std)
