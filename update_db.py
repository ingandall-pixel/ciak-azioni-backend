import json
import time
import yfinance as yf

# === TUTTE LE PRINCIPALI AZIONI ITALIANE (FTSE MIB) ===
MERCATO_ITA = [
    {"ticker": "A2A.MI", "nome": "A2A"},
    {"ticker": "AMP.MI", "nome": "Amplifon"},
    {"ticker": "AZM.MI", "nome": "Azimut Holding"},
    {"ticker": "BAMI.MI", "nome": "Banco BPM"},
    {"ticker": "BPE.MI", "nome": "BPER Banca"},
    {"ticker": "BC.MI", "nome": "Brunello Cucinelli"},
    {"ticker": "BZU.MI", "nome": "Buzzi Unicem"},
    {"ticker": "CPR.MI", "nome": "Campari"},
    {"ticker": "DIA.MI", "nome": "Diasorin"},
    {"ticker": "ENEL.MI", "nome": "Enel"},
    {"ticker": "ENI.MI", "nome": "Eni"},
    {"ticker": "ERG.MI", "nome": "ERG"},
    {"ticker": "RACE.MI", "nome": "Ferrari"},
    {"ticker": "FBK.MI", "nome": "FinecoBank"},
    {"ticker": "G.MI", "nome": "Generali"},
    {"ticker": "HER.MI", "nome": "Hera"},
    {"ticker": "ISP.MI", "nome": "Intesa Sanpaolo"},
    {"ticker": "INW.MI", "nome": "INWIT"},
    {"ticker": "IP.MI", "nome": "Interpump Group"},
    {"ticker": "IG.MI", "nome": "Italgas"},
    {"ticker": "LDO.MI", "nome": "Leonardo"},
    {"ticker": "MB.MI", "nome": "Mediobanca"},
    {"ticker": "MONC.MI", "nome": "Moncler"},
    {"ticker": "NEXI.MI", "nome": "Nexi"},
    {"ticker": "PIRC.MI", "nome": "Pirelli & C"},
    {"ticker": "PST.MI", "nome": "Poste Italiane"},
    {"ticker": "PRY.MI", "nome": "Prysmian"},
    {"ticker": "REC.MI", "nome": "Recordati"},
    {"ticker": "SPM.MI", "nome": "Saipem"},
    {"ticker": "SRG.MI", "nome": "Snam"},
    {"ticker": "STLAM.MI", "nome": "Stellantis"},
    {"ticker": "STMMI.MI", "nome": "STMicroelectronics"},
    {"ticker": "TIT.MI", "nome": "Telecom Italia"},
    {"ticker": "TEN.MI", "nome": "Tenaris"},
    {"ticker": "TRN.MI", "nome": "Terna"},
    {"ticker": "UCG.MI", "nome": "UniCredit"},
    {"ticker": "UNI.MI", "nome": "Unipol"}
]

# === TUTTE LE PRINCIPALI AZIONI AMERICANE (BIG TECH & S&P 500) ===
MERCATO_USA = [
    {"ticker": "AAPL", "nome": "Apple"},
    {"ticker": "MSFT", "nome": "Microsoft"},
    {"ticker": "GOOGL", "nome": "Alphabet (Google)"},
    {"ticker": "AMZN", "nome": "Amazon"},
    {"ticker": "TSLA", "nome": "Tesla"},
    {"ticker": "META", "nome": "Meta Platforms (Facebook)"},
    {"ticker": "NVDA", "nome": "NVIDIA"},
    {"ticker": "NFLX", "nome": "Netflix"},
    {"ticker": "JPM", "nome": "JPMorgan Chase"},
    {"ticker": "V", "nome": "Visa"},
    {"ticker": "MA", "nome": "Mastercard"},
    {"ticker": "JNJ", "nome": "Johnson & Johnson"},
    {"ticker": "WMT", "nome": "Walmart"},
    {"ticker": "PG", "nome": "Procter & Gamble"},
    {"ticker": "DIS", "nome": "Walt Disney"},
    {"ticker": "HD", "nome": "Home Depot"},
    {"ticker": "BAC", "nome": "Bank of America"},
    {"ticker": "XOM", "nome": "Exxon Mobil"},
    {"ticker": "CVX", "nome": "Chevron"},
    {"ticker": "KO", "nome": "Coca-Cola"},
    {"ticker": "PEP", "nome": "PepsiCo"},
    {"ticker": "MCD", "nome": "McDonald's"},
    {"ticker": "CSCO", "nome": "Cisco Systems"},
    {"ticker": "INTC", "nome": "Intel"},
    {"ticker": "AMD", "nome": "Advanced Micro Devices"},
    {"ticker": "PFE", "nome": "Pfizer"},
    {"ticker": "NKE", "nome": "Nike"}
]

def recupera_dati(ticker_symbol):
    """Scarica i dati da Yahoo Finance e calcola prezzo e variazione."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1y")
        
        if hist.empty:
            print(f"Nessun dato trovato per {ticker_symbol}")
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

    print(f"Inizio recupero dati Mercato Italiano ({len(MERCATO_ITA)} azioni)...")
    for item in MERCATO_ITA:
        dati = recupera_dati(item["ticker"])
        if dati:
            database["italiano"].append({
                "azione": item["nome"],
                "prezzo": dati["prezzo"],
                "var_periodo": dati["var_periodo"]
            })
        print(f"-> Caricato {item['nome']}. Attesa 1 secondo...")
        time.sleep(1)  # LA PAUSA CRUCIALE DI 1 SECONDO PER NON FARSI BLOCCARE

    print(f"\nInizio recupero dati Mercato Americano ({len(MERCATO_USA)} azioni)...")
    for item in MERCATO_USA:
        dati = recupera_dati(item["ticker"])
        if dati:
            database["americano"].append({
                "azione": item["nome"],
                "prezzo": dati["prezzo"],
                "var_periodo": dati["var_periodo"]
            })
        print(f"-> Caricato {item['nome']}. Attesa 1 secondo...")
        time.sleep(1)  # LA PAUSA CRUCIALE DI 1 SECONDO PER NON FARSI BLOCCARE

    # Salva tutto nel JSON
    with open("market_db.json", "w", encoding="utf-8") as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
        
    print("\n✅ File market_db.json aggiornato con successo con TUTTE le azioni!")

if __name__ == "__main__":
    aggiorna_db()
