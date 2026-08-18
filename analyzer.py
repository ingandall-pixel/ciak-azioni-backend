import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')

def get_price_at_delta(history_dict, sorted_dates, latest_date, days_delta):
    target_date = latest_date - timedelta(days=days_delta)
    target_str = target_date.strftime("%Y-%m-%d")
    
    # Trova la data disponibile più vicina (precedente o uguale al target)
    valid_dates = [d for d in sorted_dates if d <= target_str]
    if not valid_dates:
        return history_dict[sorted_dates[0]]
    
    closest_date = valid_dates[-1]
    return history_dict[closest_date]

def analyze_market():
    if not os.path.exists(DB_FILE):
        print(json.dumps({"error": "market_db.json non trovato."}))
        return

    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return

    results = []

    for ticker, history_dict in db.items():
        if not history_dict or not isinstance(history_dict, dict):
            continue
        
        sorted_dates = sorted(history_dict.keys())
        if len(sorted_dates) < 2:
            continue

        latest_date_str = sorted_dates[-1]
        try:
            latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
        except:
            continue

        current_price = history_dict[latest_date_str]
        
        # Estrazione prezzi passati per i vari periodi
        p_1d = get_price_at_delta(history_dict, sorted_dates, latest_date, 1)
        p_1w = get_price_at_delta(history_dict, sorted_dates, latest_date, 7)
        p_1m = get_price_at_delta(history_dict, sorted_dates, latest_date, 30)
        p_1y = get_price_at_delta(history_dict, sorted_dates, latest_date, 365)
        p_5y = get_price_at_delta(history_dict, sorted_dates, latest_date, 365 * 5)
        p_all = history_dict[sorted_dates[0]]

        def calc_ret(p_past):
            return round(((current_price - p_past) / p_past) * 100, 2) if p_past else 0

        market = "IT" if (ticker.endswith('.MI') or ticker.endswith('.AS')) else "US"

        results.append({
            "ticker": ticker,
            "market": market,
            "current_price": round(current_price, 4),
            "returns": {
                "1d": calc_ret(p_1d),
                "1w": calc_ret(p_1w),
                "1m": calc_ret(p_1m),
                "1y": calc_ret(p_1y),
                "5y": calc_ret(p_5y),
                "all": calc_ret(p_all)
            }
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    analyze_market()
