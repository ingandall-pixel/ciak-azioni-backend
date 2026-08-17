import sys
import json
import pandas as pd
import numpy as np

# Funzione di calcolo e filtraggio on-demand
def process_market_data(market_type, period, median_markup, std_markup, sort_by, sort_order):
    # Qui andrà la logica che legge il database (JSON/CSV) dei mercati (italiano o americano)
    # Per ora impostiamo la struttura dati di risposta coerente con i requisiti.
    
    results = []
    # Esempio di elaborazione basata sul periodo (1G, 1S, 1M, 1A, 5A, Max)
    # Applicazione delle formule:
    # 1. Mediana >= Media * (1 + median_markup / 100)
    # 2. (Dev.Std / Media) >= (1 + std_markup / 100)
    
    # Ogni riga conterrà:
    # - Nome azione + link Investing.com (con l'icona)
    # - Sparkline (immagine andamento)
    # - Quotazione attuale
    # - Variazione % periodo (verde/rosso)
    # - Variazione % giornaliera (verde/rosso)
    
    return json.dumps(results)

if __name__ == "__main__":
    # Parametri passati da Node.js
    market = sys.argv[1] if len(sys.argv) > 1 else "it"
    period = sys.argv[2] if len(sys.argv) > 2 else "1y"
    med_markup = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    std_markup = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    sort_criterion = sys.argv[5] if len(sys.argv) > 5 else "perf"
    order_dir = sys.argv[6] if len(sys.argv) > 6 else "desc"
    
    output = process_market_data(market, period, med_markup, std_markup, sort_criterion, order_dir)
    print(output)
