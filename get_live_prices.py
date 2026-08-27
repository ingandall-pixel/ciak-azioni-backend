import sys
import json
import logging
import yfinance as yf

# Silenzia i log e warning su stderr di yfinance
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

if len(sys.argv) > 1:
    raw_tickers = sys.argv[1].split(',')
    # Rimuove l'eventuale '$' e pulisce gli spazi
    clean_tickers = [t.replace('$', '').strip() for t in raw_tickers if t.strip()]
    
    prezzi = {}
    if clean_tickers:
        try:
            tickers_obj = yf.Tickers(' '.join(clean_tickers))
            for ticker in clean_tickers:
                try:
                    price = tickers_obj.tickers[ticker].fast_info.last_price
                    if price is not None:
                        prezzi[ticker] = round(price, 2)
                except Exception:
                    continue
        except Exception:
            pass

    print(json.dumps(prezzi))
else:
    print(json.dumps({}))