import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')

def analyze_market():
    if not os.path.exists(DB_FILE):
        print(json.dumps({"error": "market_db.json non trovato. Eseguire prima l'aggiornamento del database."}))
        return

    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Errore nella lettura del database: {str(e)}"}))
        return

    results = []

    for ticker, history_dict in db.items():
        if not history_dict or not isinstance(history_dict, dict):
            continue
        
        # Ordina le date in modo cronologico
        sorted_dates = sorted(history_dict.keys())
        if len(sorted_dates) < 2:
            continue

        closes = [history_dict[d] for d in sorted_dates]
        start_price = closes[0]
        end_price = closes[-1]
        total_return = ((end_price - start_price) / start_price) * 100 if start_price else 0
        
        max_price = max(closes)
        min_price = min(closes)
        
        market = "IT" if (ticker.endswith('.MI') or ticker.endswith('.AS')) else "US"

        results.append({
            "ticker": ticker,
            "market": market,
            "start_price": round(start_price, 4),
            "current_price": round(end_price, 4),
            "total_return_pct": round(total_return, 2),
            "max_price": round(max_price, 4),
            "min_price": round(min_price, 4),
            "data_points": len(closes)
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    analyze_market()
