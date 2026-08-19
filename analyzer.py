import numpy as np
from datetime import datetime, timedelta

def calcola_statistiche_periodo(storico, arco_temporale):
    """
    Calcola Mediana/Media e Dev.Std/Media filtrando i dati in base all'arco temporale scelto:
    '1m' (1 Mese), '3m' (3 Mesi), '6m' (6 Mesi), '1y' (1 Anno), '5y' (5 Anni)
    """
    if not storico:
        return 0.0, 0.0

    oggi = datetime.now().date()
    
    # Determinazione della data di inizio in base all'arco temporale
    if arco_temporale == '1m':
        data_inizio = oggi - timedelta(days=30)
    elif arco_temporale == '3m':
        data_inizio = oggi - timedelta(days=90)
    elif arco_temporale == '6m':
        data_inizio = oggi - timedelta(days=180)
    elif arco_temporale == '1y':
        data_inizio = oggi - timedelta(days=365)
    elif arco_temporale == '5y':
        data_inizio = oggi - timedelta(days=5*365)
    else:
        data_inizio = oggi - timedelta(days=365) # Default 1 Anno

    # Filtriamo lo storico per l'intervallo temporale richiesto
    storico_filtrato = [
        d for d in storico 
        if datetime.strptime(d['date'], '%Y-%m-%d').date() >= data_inizio
    ]

    if not storico_filtrato:
        return 0.0, 0.0

    # Estraiamo i prezzi o i ritorni giornalieri (usiamo i prezzi di chiusura o variazioni secondo la tua logica)
    prezzi = [float(d['close']) for d in storico_filtrato if 'close' in d]
    
    if len(prezzi) < 2:
        return 0.0, 0.0

    media = np.mean(prezzi)
    mediana = np.median(prezzi)
    dev_std = np.std(prezzi)

    # Rapporti percentuali richiesti
    pct_mediana_media = (mediana / media) * 100 if media != 0 else 0.0
    pct_dev_media = (dev_std / media) * 100 if media != 0 else 0.0

    return round(pct_mediana_media, 2), round(pct_dev_media, 2)
