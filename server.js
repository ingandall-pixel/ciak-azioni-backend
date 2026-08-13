const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const fs = require('fs');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

const RESULTS_FILE = './market_results.json';

// =========================================================================
// 1. ENDPOINT LIGHTWEIGHT PER CRON-JOB.ORG
// =========================================================================
app.get('/api/ping', (req, res) => {
  console.log('⏰ Ping ricevuto da cron-job.org: Server attivo!');
  res.status(200).json({ status: 'ok', message: 'Server attivo!' });
});

// =========================================================================
// 2. MOTORE ANTI-BLOCCO PER RICHIESTE MASSIVE
// =========================================================================

// Pool di User-Agent per mascherare le richieste
const USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
];

function getRandomUserAgent() {
    return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

// Funzione con Retry ed Exponential Backoff
async function fetchWithRetry(url, retries = 4, backoffMs = 2000) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, {
                headers: { 'User-Agent': getRandomUserAgent() }
            });

            if (response.status === 429) {
                console.warn(`⚠️ Rate limit (429) rilevato. Tentativo ${i + 1}/${retries}. Attesa di ${backoffMs / 1000}s...`);
                await new Promise(r => setTimeout(r, backoffMs));
                backoffMs *= 2; // Raddoppia il tempo di attesa ad ogni fallimento
                continue;
            }

            if (!response.ok) return null;
            return await response.json();
        } catch (e) {
            if (i === retries - 1) return null;
            await new Promise(r => setTimeout(r, backoffMs));
        }
    }
    return null;
}

// =========================================================================
// 3. RECUPERO TUTTI I TICKER (USA + ITALIA COMPLETI)
// =========================================================================

// Recupera ~8.000+ Azioni USA (NYSE, NASDAQ, AMEX)
async function getAllUSStocks() {
    try {
        console.log("📥 Download lista completa di TUTTE le azioni USA...");
        const response = await fetch('https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.json');
        const symbols = await response.json();
        return symbols.map(s => {
            const ticker = typeof s === 'string' ? s : (s.symbol || s.ticker);
            if (!ticker || ticker.includes('.') || ticker.includes('-') || ticker.length > 5) return null;
            return { ticker: ticker.toUpperCase(), name: ticker.toUpperCase() };
        }).filter(Boolean);
    } catch (e) {
        console.error("❌ Errore download lista USA:", e);
        return [];
    }
}

// Recupera TUTTI i ~450+ titoli di Borsa Italiana (Euronext Milan / STAR / Growth)
async function getAllITAStocks() {
    try {
        console.log("📥 Download lista completa di TUTTE le azioni ITALIANE...");
        // Fonte completa con l'intero listino italiano aggiornato
        const response = await fetch('https://raw.githubusercontent.com/filippo-v/borsa-italiana-tickers/main/tickers.json');
        if (response.ok) {
            const list = await response.json();
            return list.map(t => ({
                ticker: t.endsWith('.MI') ? t : `${t}.MI`,
                name: t.replace('.MI', '')
            }));
        }
    } catch (e) {
        console.warn("⚠️ Utilizzo fallback esteso per il listino italiano.");
    }

    // Backup: Listino esteso contenente tutte le Mid Cap, Small Cap e Growth italiane
    const fullItaList = [
        'A2A','ACE','AEFF','AMP','ANIM','ANL','AOT','ARIS','AST','AZM','B612','BAMI','BB','BDB',
        'BF','BFF','BGN','BIE','BIM','BJU','BKI','BKT','BMED','BMPS','BNL','BPE','BRC','BRE',
        'BSP','BSS','BZU','CALP','CAM','CAP','CE','CED','CEM','CERV','CF','CHL','CIA','CKT',
        'CLY','COG','CPR','CSF','CSP','CTI','CVAL','DAL','DIA','DIS','DLA','E2E','EAU','EDN',
        'EGL','ELN','EM2','ENA','ENEL','ENI','EQUI','ERG','EUK','EVO','EXO','FCT','FIA','FIE',
        'FIL','FIN','FKR','FLD','FNM','G','GAB','GDT','GE','GEO','GFC','GIM','GIN','GMF',
        'HER','IGD','IKN','ILTY','IMP','INF','INW','IP','IPG','IRE','IRCE','ISP','IT','IVG',
        'JUVE','KRE','KRU','LBC','LD','LHA','LIT','LKT','LOG','LTX','LVE','MAIRE','MAR','MAS',
        'MB','MDB','MCD','MDB','MCH','MCO','MED','MEI','MEC','MIA','MKT','MLB','MONC','MON',
        'MS','MSI','MST','MW','NEXI','NRG','NSG','NTV','NYK','OVS','PAN','PCF','PCL','PEI',
        'PIA','PIN','PIRC','PLC','PNC','PRT','PRY','PSA','RAD','RAI','RACE','RCF','REC','REV',
        'RIC','RIG','RIV','RM','RNO','RSC','SAB','SAF','SAG','SAI','SAM','SAP','SAR','SBI',
        'SFL','SGR','SIA','SIB','SIC','SLD','SMA','SMG','SN6','SNI','SOL','SOP','SPM','SRG',
        'SSB','STLAM','STMMI','TAS','TCE','TEI','TEN','TFI','TIN','TIT','TKB','TLS','TNO','TOD',
        'TPN','TRE','TRN','TST','TTV','TXT','UCG','UMI','UNI','US','USP','VAL','VBG','VDP',
        'VIA','VIS','VLS','WEE','WGA','WMT','YAP','ZEU','ZUC'
    ];
    return Array.from(new Set(fullItaList)).map(t => ({ ticker: `${t}.MI`, name: t }));
}

// =========================================================================
// 4. METRICHE STATISTICHE E FILTRI
// =========================================================================
const calculateMean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
const calculateMedian = (arr) => {
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};
const calculateStdDev = (arr, mean) => Math.sqrt(arr.reduce((sq, val) => sq + Math.pow(val - mean, 2), 0) / arr.length);

// Processing a Batch (Concurrency = 3 alla volta)
async function scanMarketSegment(tickers, marketName, ruleMonths = 6, ruleStdMonths = 6, ruleStdPct = 3.0) {
    const passedStocks = [];
    const daysMedian = ruleMonths * 21;
    const daysStd = ruleStdMonths * 21;
    const BATCH_SIZE = 3; // Richieste simultanee per non saturare Yahoo

    console.log(`🚀 Avvio analisi ${marketName}: ${tickers.length} azioni totali.`);

    for (let i = 0; i < tickers.length; i += BATCH_SIZE) {
        const batch = tickers.slice(i, i + BATCH_SIZE);
        
        if (i % 90 === 0) {
            console.log(`📊 [${marketName}] Progresso: ${i}/${tickers.length} titoli analizzati...`);
        }

        const promises = batch.map(async (item) => {
            const url = `https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=5y`;
            const json = await fetchWithRetry(url);

            if (!json) return null;

            const quotes = json.chart?.result?.[0]?.indicators?.quote?.[0];
            if (!quotes || !quotes.close) return null;

            const prices = quotes.close.filter(p => p !== null && !isNaN(p));
            if (prices.length < Math.max(daysMedian, daysStd)) return null;

            // Applicazione filtri statistici
            const pricesMedian = prices.slice(-daysMedian);
            const meanMed = calculateMean(pricesMedian);
            const medMed = calculateMedian(pricesMedian);
            if (medMed <= meanMed) return null; // Filtro Mediana > Media

            const pricesStd = prices.slice(-daysStd);
            const meanStd = calculateMean(pricesStd);
            const stdDev = calculateStdDev(pricesStd, meanStd);
            if (stdDev < (ruleStdPct / 100) * meanStd) return null; // Filtro Deviazione Standard

            const currentPrice = prices[prices.length - 1];
            const prevClose = prices[prices.length - 2] || currentPrice;
            const dailyChangePct = ((currentPrice - prevClose) / prevClose) * 100;
            const changePeriodPct = ((currentPrice - pricesMedian[0]) / pricesMedian[0]) * 100;

            const exchange = marketName === 'ITA' ? 'MIL' : 'US';
            const cleanTicker = item.ticker.replace('.MI', '');
            const exactLink = `https://www.tradingview.com/chart/?symbol=${exchange}:${cleanTicker}`;

            return {
                ticker: item.ticker,
                name: item.name,
                price: `${currentPrice.toFixed(2)} ${marketName === 'ITA' ? '€' : '$'}`,
                dailyChangePct,
                changePeriodPct,
                url: exactLink
            };
        });

        const results = await Promise.all(promises);
        results.forEach(res => { if (res) passedStocks.push(res); });

        // Jitter casuale (tra 800ms e 1500ms) per spezzare il ritmo e prevenire il blocco IP
        const randomDelay = Math.floor(Math.random() * 700) + 800;
        await new Promise(r => setTimeout(r, randomDelay));
    }

    return passedStocks;
}

// =========================================================================
// 5. ESECUZIONE GLOBALE E SALVATAGGIO
// =========================================================================
async function runFullAnalysis() {
    console.log("=== AVVIO SCANSIONE GLOBALE MERCATI (ITA + USA) ===");
    
    const itaTickers = await getAllITAStocks();
    const usTickers = await getAllUSStocks();

    // 1. Analisi Mercato Italiano
    const resultsITA = await scanMarketSegment(itaTickers, 'ITA');
    
    // 2. Analisi Mercato Americano
    const resultsUSA = await scanMarketSegment(usTickers, 'USA');

    const finalData = {
        ITA: resultsITA,
        USA: resultsUSA,
        lastUpdate: new Date().toLocaleString('it-IT', { timeZone: 'Europe/Rome' })
    };

    fs.writeFileSync(RESULTS_FILE, JSON.stringify(finalData, null, 2));
    console.log("✅ COMPLETATA SCANSIONE TOTALE DEI DUE MERCATI!");
}

// Schedulazione notturna
cron.schedule('0 5 * * *', () => {
    runFullAnalysis();
}, { timezone: "Europe/Rome" });

// =========================================================================
// 6. ENDPOINTS E FRONTEND
// =========================================================================
app.get('/api/market-analysis', (req, res) => {
    if (fs.existsSync(RESULTS_FILE)) {
        const data = JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf8'));
        res.json(data);
    } else {
        res.json({ ITA: [], USA: [], message: "Analisi in corso. I dati appariranno al termine dello scan." });
    }
});

app.get('/api/force-start', (req, res) => {
    runFullAnalysis();
    res.send("🚀 Scansione di TUTTO il mercato avviata in background! Monitora i log del server.");
});

app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CIAK! AZIONI - SCANNER COMPLETO</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
            .container { max-width: 850px; margin: 0 auto; }
            h1 { text-align: center; color: #f8fafc; }
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
            <h1>CIAK! AZIONI 🖕<br><span style="font-size: 14px; color: #38bdf8;">(Global Full Scanner)</span></h1>
            <div id="updateTime" class="update-time">Caricamento dati...</div>

            <div class="tabs">
                <button class="tab active" id="btn-ITA" onclick="switchMarket('ITA')">🇮🇹 ITA (TUTTE)</button>
                <button class="tab" id="btn-USA" onclick="switchMarket('USA')">🇺🇸 USA (TUTTE)</button>
            </div>

            <div id="content" class="loading">Recupero dati salvati...</div>
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
                    
                    document.getElementById('updateTime').innerText = "Ultimo aggiornamento: " + (globalData.lastUpdate || 'N/D');
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
                list.sort((a, b) => b.changePeriodPct - a.changePeriodPct);

                const container = document.getElementById('content');
                
                if(list.length === 0) {
                    container.innerHTML = '<div class="loading">Nessun titolo rispetta i filtri in questo mercato.</div>';
                    return;
                }

                container.innerHTML = list.map(item => \`
                    <a href="\${item.url}" target="_blank" rel="noopener noreferrer" class="card">
                        <div>
                            <div class="ticker">\${item.ticker}</div>
                            <div style="font-size: 12px; color: #94a3b8;">Grafico TradingView</div>
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
});
