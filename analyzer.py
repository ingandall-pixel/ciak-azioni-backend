import os
import json
import sys
import numpy as np
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')

def analyze(market, tf, median_markup, std_ratio):
    if not os.path.exists(DB_FILE):
        return []

    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []

    results = []
    days_map = {'1d': 2, '1w': 7, '1m': 30, '1y': 365, '5y': 1825, 'max': 99999}
    target_days = days_map.get(tf, 30)

    for ticker, obj in data.items():
        is_it = ticker.endswith('.MI') or ticker.endswith('.AS')
        
        if market == 'IT' and not is_it:
            continue
        if market == 'US' and is_it:
            continue

        # Estrae l'istorico generato da update_db.py
        history_raw = obj.get("istorico", {}) if isinstance(obj, dict) else {}
        if not history_raw:
            continue

        # Normalizza i prezzi gestendo la struttura {"close": valore}
        history = {}
        for d_str, val in history_raw.items():
            if len(d_str) == 10 and d_str.count('-') == 2:
                if isinstance(val, dict) and "close" in val:
                    history[d_str] = float(val["close"])
                elif isinstance(val, (int, float)):
                    history[d_str] = float(val)

        dates = sorted(history.keys())
        if len(dates) < 2:
            continue

        latest_date_str = dates[-1]
        try:
            latest_dt = datetime.strptime(latest_date_str, '%Y-%m-%d')
        except Exception:
            continue
        
        if tf == 'max':
            filtered_dates = dates
        else:
            cutoff = latest_dt - timedelta(days=target_days)
            filtered_dates = []
            for d in dates:
                try:
                    if datetime.strptime(d, '%Y-%m-%d') >= cutoff:
                        filtered_dates.append(d)
                except Exception:
                    pass

        if len(filtered_dates) < 2:
            continue

        prices = [history[d] for d in filtered_dates]
        np_prices = np.array(prices)

        mean_val = np.mean(np_prices)
        median_val = np.median(np_prices)
        std_val = np.std(np_prices)

        if mean_val == 0:
            continue

        med_markup_pct = ((median_val - mean_val) / mean_val) * 100.0
        std_ratio_pct = (std_val / mean_val) * 100.0

        if med_markup_pct >= median_markup and std_ratio_pct >= std_ratio:
            curr_price = history[dates[-1]]
            prev_price = history[filtered_dates[0]]
            var_period = ((curr_price - prev_price) / prev_price) * 100.0

            all_prices = [history[d] for d in dates]
            daily_var = 0.0
            if len(all_prices) >= 2:
                daily_var = ((all_prices[-1] - all_prices[-2]) / all_prices[-2]) * 100.0

            sparkline = prices[-30:] if len(prices) >= 30 else prices

            results.append({
                "ticker": ticker,
                "price": round(curr_price, 2),
                "var_period": round(var_period, 2),
                "var_daily": round(daily_var, 2),
                "med_mean_ratio": round(med_markup_pct, 2),
                "std_mean_ratio": round(std_ratio_pct, 2),
                "sparkline": sparkline
            })

    return results

if __name__ == "__main__":
    if len(sys.argv) > 4:
        m = sys.argv[1]
        tf = sys.argv[2]
        mm = float(sys.argv[3])
        sr = float(sys.argv[4])
        print(json.dumps(analyze(m, tf, mm, sr)))
    else:
        print(json.dumps([]))