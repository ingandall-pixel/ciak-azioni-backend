import os
import json
import sys
import numpy as np
from datetime import datetime, timedelta

try:
    import ijson
except ImportError:
    ijson = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')

class NanStreamReader:
    """Legge il file a blocchi sostituendo 'NaN' non valido in 'null' senza saturare la RAM."""
    def __init__(self, file_path):
        self.f = open(file_path, 'rb')
        self.leftover = b''

    def read(self, size=-1):
        if size == -1:
            data = self.f.read()
            return data.replace(b'NaN', b'null')
        
        chunk = self.f.read(size)
        if not chunk and not self.leftover:
            return b''
        
        data = self.leftover + chunk
        if len(chunk) == size:
            self.leftover = data[-3:]
            data_to_clean = data[:-3]
        else:
            self.leftover = b''
            data_to_clean = data

        return data_to_clean.replace(b'NaN', b'null')

    def close(self):
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def parse_date(d_str):
    clean_str = str(d_str).split('T')[0].split(' ')[0]
    if len(clean_str) >= 10 and clean_str.count('-') >= 2:
        return clean_str[:10]
    return None

def analyze(market, tf, median_markup, std_ratio):
    if not os.path.exists(DB_FILE):
        return []

    results = []
    days_map = {
        '1d': 2,
        '1w': 7,
        '1m': 30,
        '3m': 90,
        '6m': 180,
        '1y': 365,
        '5y': 1825,
        'max': 99999
    }
    target_days = days_map.get(tf, 90)

    # Apertura dello stream con pulizia dinamica dei NaN
    with NanStreamReader(DB_FILE) as f:
        if ijson:
            items = ijson.kvitems(f, '')
        else:
            items = json.load(f).items()

        for ticker, obj in items:
            is_it = ticker.endswith('.MI') or ticker.endswith('.AS')
            
            if market == 'IT' and not is_it:
                continue
            if market == 'US' and is_it:
                continue

            history_raw = {}
            if isinstance(obj, dict):
                history_raw = obj.get("istorico") or obj.get("storico") or obj.get("history") or obj.get("prices") or {}

            if not history_raw or not isinstance(history_raw, dict):
                continue

            history = {}
            for d_raw, val in history_raw.items():
                d_clean = parse_date(d_raw)
                if not d_clean or val is None:
                    continue

                if isinstance(val, dict):
                    close_val = val.get("close")
                    if close_val is not None:
                        history[d_clean] = float(close_val)
                elif isinstance(val, (int, float)):
                    history[d_clean] = float(val)

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
                filtered_dates = [
                    d for d in dates 
                    if datetime.strptime(d, '%Y-%m-%d') >= cutoff
                ]

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
        try:
            mm = float(sys.argv[3])
        except ValueError:
            mm = 0.0
            
        try:
            sr = float(sys.argv[4])
        except ValueError:
            sr = 0.0

        print(json.dumps(analyze(m, tf, mm, sr)), flush=True)
    else:
        print(json.dumps([]), flush=True)