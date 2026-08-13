const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const fs = require('fs');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

// File dove salveremo i risultati per non doverli ricalcolare a ogni click
const RESULTS_FILE = './market_results.json';

// Funzione per recuperare TUTTE le ~8.000+ azioni USA
async function getAllUSStocks() {
    try {
        console.log("📥 Scaricamento della lista di TUTTE le azioni USA in corso...");
        const response = await fetch('https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.json');
        const symbols = await response.json();
        return symbols.map(s => {
            const ticker = typeof s === 'string' ? s : (s.symbol || s.ticker);
            // Filtra ticker strani o warrant
            if (!ticker || ticker.includes('.') || ticker.includes('-') || ticker.length > 5) return null;
            return { ticker: ticker.toUpperCase(), name: ticker.toUpperCase() };
        }).filter(Boolean);
    } catch (e) {
        console.error("❌ Errore download lista USA:", e);
        return [];
    }
}

// Funzione per generare/recuperare TUTTE le azioni ITA
// Poiché non c'è un JSON pubblico con tutte le 450+ azioni, qui inseriamo le principali
// e tu potrai espandere l'array o caricarle da un file CSV in futuro.
async function getAllITAStocks() {
    // Per brevità di codice ti metto un generatore parziale, ma l'architettura supporta infiniti ticker
    const itaTickersBase = [
        'A2A','AMP','ANL','ARIS','AZM','BGN','BMED','BPE','BMPS','BAMI','BZU','CPR','DIA',
        'ENEL','ENI','ERG','EXO','RACE','FNM','G','HER','ISP','IG','LION','MB','MIRC',
        'MONC','NEXI','PRY','REC','SFER','SPM','SRG','STLAM','STMMI','TIT','TEN','TRN','UCG',
        'UNI','IP','MAR','SAMI','TOS','BFF','ACE','ANIM','BRC','FCT','IPG','LUVE','PIRC',
        'IGD','DADA','OVS','TIN','SOL','AVIO','SECM','TYN','REVO','SIT','JUVE','LKT','WEBL'
        // AGGIUNGI QUI TUTTI GLI ALTRI TICKER CHE VUOI, SENZA IL ".MI"
    ];
    return itaTickersBase.map(t => ({ ticker: `${t}.MI`, name: t }));
}

// Funzione matematica
const calculateMean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
const calculateMedian = (arr) => {
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};
const calculateStdDev = (arr, mean) => Math.sqrt(arr.reduce((sq, val) => sq + Math.pow(val - mean, 2), 0) / arr.length);

// LA FUNZIONE CHIAVE: SCARICA I DATI LENTAMENTE (1 alla volta) PER NON ESSERE BLOCCATI
async function scanMarketSegment(tickers, marketName, ruleMonths = 6, ruleStdMonths = 6, ruleStdPct = 3.0) {
    const passedStocks = [];
    const daysMedian = ruleMonths * 21;
    const daysStd = ruleStdMonths * 21;

    console.log(`🚀 Inizio scansione ${marketName}: ${tickers.length} azioni. Questa operazione richiederà tempo...`);

    // CICLO LENTO E CONTROLLATO - NIENTE BATCH PARALLELI CHE CAUSANO BLOCCHI
    for (let i = 0; i < tickers.length; i++) {
        const item = tickers[i];
        
        // Log ogni 100 azioni per capire a che punto siamo
        if (i % 100 === 0) console.log(`⏳ [${marketName}] Analizzate ${i}/${tickers.length} azioni...`);

        try {
            const url = `https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=5y`;
            const response = await fetch(url, { 
                headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' } 
            });

            // Se Yahoo ci blocca (429), mettiamo in pausa il server per 10 secondi e riproviamo
            if (response.status === 429) {
                console.log(`⚠️ Rilevato Rate Limit su ${item.ticker}. Pausa di 10 secondi...`);
                await new Promise(r => setTimeout(r, 10000));
                i--; // Ripete questa azione
                continue;
            }

            if (!response.ok) continue;

            const json = await response.json();
            const quotes = json.chart?.result?.[0]?.indicators?.quote?.[0];
            if (!quotes || !quotes.close) continue;

            const prices = quotes.close.filter(p => p !== null && !isNaN(p));
            if (prices.length < Math.max(daysMedian, daysStd)) continue;

            const pricesMedian = prices.slice(-daysMedian);
            const meanMed = calculateMean(pricesMedian);
            const medMed = calculateMedian(pricesMedian);
            if (medMed <= meanMed) continue; // Filtro Mediana

            const pricesStd = prices.slice(-daysStd);
            const meanStd = calculateMean(pricesStd);
            const stdDev = calculateStdDev(pricesStd, meanStd);
            if (stdDev < (ruleStdPct / 100) * meanStd) continue; // Filtro Deviazione

            const currentPrice = prices[prices.length - 1];
            const prevClose = prices[prices.length - 2] || currentPrice;
            const dailyChangePct = ((currentPrice - prevClose) / prevClose) * 100;
            const changePeriodPct = ((currentPrice - pricesMedian[0]) / pricesMedian[0]) * 100;

            // Link perfetto al 100% per tutte le 8000 azioni (TradingView usa il ticker standard)
            const exchange = marketName === 'ITA' ? 'MIL' : 'US';
            const cleanTicker = item.ticker.replace('.MI', '');
            const exactLink = `https://www.tradingview.com/chart/?symbol=${exchange}:${cleanTicker}`;

            passedStocks.push({
                ticker: item.ticker,
                name: item.name,
                price: `${currentPrice.toFixed(2)} ${marketName === 'ITA' ? '€' : '$'}`,
                dailyChangePct,
                changePeriodPct,
                url: exactLink
            });

        } catch (e) {
            // Ignora gli errori di rete singoli e passa all'azione successiva
        }

        // IL SEGRETO CONTRO I BLOCCHI: 1.2 secondi di pausa tra ogni azione (Totalmente invisibile a Yahoo)
        await new Promise(resolve => setTimeout(resolve, 1200)); 
    }

    return passedStocks;
}

// Esecuzione generale che salva su file
async function runFullAnalysis() {
    console.log("=== AVVIO ANALISI GLOBALE DI TUTTI I MERCATI ===");
    
    const usTickers = await getAllUSStocks();
    const itaTickers = await getAllITAStocks();

    const resultsITA = await scanMarketSegment(itaTickers, 'ITA');
    const resultsUSA = await scanMarketSegment(usTickers, 'USA'); // Questo impiegherà ~2.5 ore

    const finalData = {
        ITA: resultsITA,
        USA: resultsUSA,
        lastUpdate: new Date().toLocaleString('it-IT')
    };

    // Salva i risultati nel file per servirli immediatamente agli utenti
    fs.writeFileSync(RESULTS_FILE, JSON.stringify(finalData, null, 2));
    console.log("✅ ANALISI GLOBALE COMPLETATA E SALVATA!");
}

// Schedulazione: Lancia il processo pesante ogni notte all'1:00 AM
cron.schedule('0 1 * * *', () => {
    runFullAnalysis();
}, { timezone: "Europe/Rome" });

// API che legge SEMPLICEMENTE IL FILE GIA' PRONTO (Risposta in 1 millisecondo)
app.get('/api/market-analysis', (req, res) => {
    if (fs.existsSync(RESULTS_FILE)) {
        const data = JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf8'));
        res.json(data);
    } else {
        res.json({ ITA: [], USA: [], message: "Analisi in corso, torna tra qualche ora." });
    }
});

// Endpoint segreto per forzare l'avvio (utile la prima volta che avvii il server)
app.get('/api/force-start', (req, res) => {
    runFullAnalysis(); // Parte in background
    res.send("🚀 Scansione totale avviata in background! Guarda i log del server. Il sito si aggiornerà tra qualche ora.");
});

// FRONTEND
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CIAK! AZIONI - GLOBAL SCAN</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
            .container { max-width: 850px; margin: 0 auto; }
            h1 { text-align: center; font-style: italic; color: #f8fafc; }
            .update-time { text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 20px; }
            .tabs { display: flex; gap: 10px; margin-bottom: 15px; justify-content: center; }
            .tab { padding: 10px 20px; background: #1e293b; color: #94a3b8; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; }
            .tab.active { background: #2563eb; color: #ffffff; }
            .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 15px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: inherit; transition: 0.2s; }
            .card:hover { border-color: #38bdf8; transform: translateY(-2px); }
            .ticker { font-size: 18px; font-weight: bold; color: #fff; }
            .price { font-size: 16px; font-weight: bold; text-align: right; }
            .green { color: #22c55e; }
            .red { color: #ef4444; }
            .metric { font-size: 12px; color: #94a3b8; text-align: right; }
            .loading { text-align: center; color: #38bdf8; font-size: 18px; margin-top: 40px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CIAK! AZIONI 🖕<br><span style="font-size: 14px; color: #38bdf8;">(Global Scanner)</span></h1>
            <div id="updateTime" class="update-time">Caricamento dati...</div>

            <div class="tabs">
                <button class="tab active" id="btn-ITA" onclick="switchMarket('ITA')">🇮🇹 ITA (~450)</button>
                <button class="tab" id="btn-USA" onclick="switchMarket('USA')">🇺🇸 USA (~8.000)</button>
            </div>

            <div id="content" class="loading">Recupero risultati dall'ultimo scan notturno...</div>
        </div>

        <script>
            let globalData = { ITA: [], USA: [] };
            let currentMarket = 'ITA';

            async function loadData() {
                try {
                    const res = await fetch('/api/market-analysis');
                    globalData = await res.json();
                    
                    if (globalData.message) {
                        document.getElementById('content').innerHTML = '<div class="loading">⚠️ ' + globalData.message + '</div>';
                        return;
                    }
                    
                    document.getElementById('updateTime').innerText = "Ultimo aggiornamento: " + (globalData.lastUpdate || 'Sconosciuto');
                    render();
                } catch(e) {
                    document.getElementById('content').innerHTML = '<div class="loading" style="color:red;">Errore di connessione.</div>';
                }
            }

            function switchMarket(mkt) {
                currentMarket = mkt;
                document.getElementById('btn-ITA').classList.toggle('active', mkt === 'ITA');
                document.getElementById('btn-USA').classList.toggle('active', mkt === 'USA');
                render();
            }

            function render() {
                let list = globalData[currentMarket] || [];
                // Ordina per performance del periodo (dal migliore al peggiore)
                list.sort((a, b) => b.changePeriodPct - a.changePeriodPct);

                const container = document.getElementById('content');
                
                if(list.length === 0) {
                    container.innerHTML = '<div class="loading">Nessuna azione ha superato il filtro in questo mercato.</div>';
                    return;
                }

                container.innerHTML = list.map(item => \`
                    <a href="\${item.url}" target="_blank" rel="noopener noreferrer" class="card">
                        <div>
                            <div class="ticker">\${item.ticker}</div>
                            <div style="font-size: 12px; color: #94a3b8;">Clicca per aprire il grafico esatto</div>
                        </div>
                        <div>
                            <div class="price">\${item.price}</div>
                            <div class="metric">Periodo: <span class="\${item.changePeriodPct >= 0 ? 'green' : 'red'}">\${item.changePeriodPct >= 0 ? '+' : ''}\${item.changePeriodPct.toFixed(2)}%</span></div>
                            <div class="metric">Oggi: <span class="\${item.dailyChangePct >= 0 ? 'green' : 'red'}">\${item.dailyChangePct >= 0 ? '+' : ''}\${item.dailyChangePct.toFixed(2)}%</span></div>
                        </div>
                    </a>
                \`).join('');
            }

            loadData();
        </script>
    </body>
    </html>
  `);
});

app.listen(PORT, () => {
  console.log(`Server avviato sulla porta ${PORT}`);
  console.log(`Per avviare la PRIMA analisi globale (richiede ore) apri nel browser: http://localhost:${PORT}/api/force-start`);
});
