import json
import time
import yfinance as yf

MERCATO_ITA = [
    {"ticker": "ENEL.MI", "nome": "Enel"},
    {"ticker": "ISP.MI", "nome": "Intesa Sanpaolo"},
    {"ticker": "RACE.MI", "nome": "Ferrari"}
]

MERCATO_USA = [
    {"ticker": "AAPL", "nome": "Apple"},
    {"ticker": "TSLA", "nome": "Tesla"},
    {"ticker": "NVDA", "nome": "NVIDIA"}
]

def recupera_dati(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1y")
        if hist.empty:
            return None
        
        prezzo_attuale = hist['Close'].iloc[-1]
        prezzo_inizio = hist['Close'].iloc[0]
        var_percentuale = ((prezzo_attuale - prezzo_inizio) / prezzo_inizio) * 100
        
        valuta = "€" if ticker_symbol.endswith(".MI") else "$"
        return {
            "prezzo": f"{prezzo_attuale:.2f} {valuta}",
            "var_periodo": f"{'+' if var_percentuale >= 0 else ''}{var_percentuale:.1f}%"
        }
    except Exception as e:
        print(f"Errore su {ticker_symbol}: {e}")
        return None

def aggiorna_db():
    database = {"italiano": [], "americano": []}

    print("Recupero dati Mercato Italiano...")
    for item in MERCATO_ITA:
        dati = recupera_dati(item["ticker"])
        if dati:
            database["italiano"].append({
                "azione": item["nome"],
                "prezzo": dati["prezzo"],
                "var_periodo": dati["var_periodo"]
            })
        time.sleep(1)  # Pausa di 1 secondo tra le chiamate

    print("Recupero dati Mercato Americano...")
    for item in MERCATO_USA:
        dati = recupera_dati(item["ticker"])
        if dati:
            database["americano"].append({
                "azione": item["nome"],
                "prezzo": dati["prezzo"],
                "var_periodo": dati["var_periodo"]
            })
        time.sleep(1)  # Pausa di 1 secondo tra le chiamate

    with open("market_db.json", "w", encoding="utf-8") as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
        
    print("File market_db.json aggiornato!")

if __name__ == "__main__":
    aggiorna_db()
