import sys
import json
import pandas as pd
import numpy as np

def calculate_screening(market, period, median_markup, std_markup, sort_by, sort_order):
    # Dati simulati di esempio (nella versione finale leggeranno dal database CSV/JSON)
    # Ogni elemento contiene le informazioni per la riga della tabella:
    # Nome, Link Investing, Prezzo, Variazione Periodo, Variazione Giornaliera, Mediana/Media, DevStd/Media, ecc.
    
    mock_data = [
        {
            "name": "Enel",
            "symbol": "ENEL.MI",
            "investing_url": "https://www.investing.com/equities/enel",
            "price": 6.85,
            "period_change": 2.45,
            "daily_change": -0.32,
            "median_media_ratio": 5.2,
            "std_media_ratio": 12.4
        },
        {
            "name": "Intesa Sanpaolo",
            "symbol": "ISP.MI",
            "investing_url": "https://www.investing.com/equities/intesa-sanpaolo",
            "price": 3.42,
            "period_change": 4.10,
            "daily_change": 1.15,
            "median_media_ratio": 3.8,
            "std_media_ratio": 15.1
        },
        {
            "name": "Apple",
            "symbol": "AAPL",
            "investing_url": "https://www.investing.com/equities/apple-computer-inc",
            "price": 225.50,
            "period_change": -1.20,
            "daily_change": 0.85,
            "median_media_ratio": 6.1,
            "std_media_ratio": 18.3
        }
    ]

    # Filtro in base ai parametri passati dalle rotelline iOS e dai periodi
    filtered_results = []
    for item in mock_data:
        # Applichiamo i filtri basati sui markup percentuali richiesti
        if item["median_media_ratio"] >= float(median_markup) and item["std_media_ratio"] >= float(std_markup):
            filtered_results.append(item)

    # Ordinamento dinamico in base alla scelta dell'utente
    reverse_order = (sort_order == 'desc')
    if sort_by == 'perf':
        filtered_results.sort(key=lambda x: x['period_change'], reverse=reverse_order)
    elif sort_by == 'median':
        filtered_results.sort(key=lambda x: x['median_media_ratio'], reverse=reverse_order)
    elif sort_by == 'std':
        filtered_results.sort(key=lambda x: x['std_media_ratio'], reverse=reverse_order)

    return json.dumps(filtered_results)

if __name__ == "__main__":
    market = sys.argv[1] if len(sys.argv) > 1 else "it"
    period = sys.argv[2] if len(sys.argv) > 2 else "1y"
    median_markup = sys.argv[3] if len(sys.argv) > 3 else "0"
    std_markup = sys.argv[4] if len(sys.argv) > 4 else "0"
    sort_by = sys.argv[5] if len(sys.argv) > 5 else "perf"
    sort_order = sys.argv[6] if len(sys.argv) > 6 else "desc"

    output_json = calculate_screening(market, period, median_markup, std_markup, sort_by, sort_order)
    print(output_json)
