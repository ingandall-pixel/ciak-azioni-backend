import sys
import json
import os
import pandas as pd
import numpy as np

DB_FILE = 'market_db.json'

def calculate_screening(market, period, median_markup, std_markup, sort_by, sort_order):
    if not os.path.exists(DB_FILE):
        return json.dumps([])

    with open(DB_FILE, 'r') as f:
        market_data = json.load(f)

    results = []
    
    for symbol, prices_dict in market_data.items():
        is_it = symbol.endswith('.MI')
        if market == 'it' and not is_it:
            continue
        if market == 'us' and is_it:
            continue

        if not prices_dict or len(prices_dict) < 2:
            continue

        df = pd.DataFrame(list(prices_dict.items()), columns=['Date', 'Close'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)  # Ordinamento cronologico garantito
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df.dropna(inplace=True)

        if df.empty:
            continue

        now = df.index.max()
        if period == '1d':
            start_date = now - pd.Timedelta(days=1)
        elif period == '1w':
            start_date = now - pd.Timedelta(weeks=1)
        elif period == '1m':
            start_date = now - pd.Timedelta(days=30)
        elif period == '1y':
            start_date = now - pd.Timedelta(days=365)
        else:
            start_date = now - pd.Timedelta(days=365 * 5)

        df_period = df[df.index >= start_date]
        if len(df_period) < 2:
            df_period = df

        prices = df_period['Close']
        current_price = float(prices.iloc[-1])
        start_price = float(prices.iloc[0])
        
        period_change = ((current_price - start_price) / start_price) * 100 if start_price > 0 else 0.0
        
        daily_change = 0.0
        if len(prices) >= 2:
            prev_price = float(prices.iloc[-2])
            daily_change = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0.0

        mean_val = prices.mean()
        median_val = prices.median()
        std_val = prices.std()

        median_media_ratio = (median_val / mean_val * 100) if mean_val > 0 else 0.0
        std_media_ratio = (std_val / mean_val * 100) if mean_val > 0 else 0.0

        if median_media_ratio >= float(median_markup) and std_media_ratio >= float(std_markup):
            results.append({
                "name": symbol,
                "symbol": symbol,
                "price": round(current_price, 2),
                "period_change": round(period_change, 2),
                "daily_change": round(daily_change, 2),
                "median_media_ratio": round(median_media_ratio, 2),
                "std_media_ratio": round(std_media_ratio, 2)
            })

    reverse_order = (sort_order == 'desc')
    if sort_by == 'perf':
        results.sort(key=lambda x: x['period_change'], reverse=reverse_order)
    elif sort_by == 'median':
        results.sort(key=lambda x: x['median_media_ratio'], reverse=reverse_order)
    elif sort_by == 'std':
        results.sort(key=lambda x: x['std_media_ratio'], reverse=reverse_order)

    return json.dumps(results)

if __name__ == "__main__":
    market = sys.argv[1] if len(sys.argv) > 1 else "it"
    period = sys.argv[2] if len(sys.argv) > 2 else "1y"
    median_markup = sys.argv[3] if len(sys.argv) > 3 else "0"
    std_markup = sys.argv[4] if len(sys.argv) > 4 else "0"
    sort_by = sys.argv[5] if len(sys.argv) > 5 else "perf"
    sort_order = sys.argv[6] if len(sys.argv) > 6 else "desc"

    print(calculate_screening(market, period, median_markup, std_markup, sort_by, sort_order))
