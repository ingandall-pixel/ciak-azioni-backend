const express = require('express');
const cors = require('cors');
const cron = require('node-cron');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

// Lista automatica e predefinita di azioni italiane e USA
const STOCKS_DATABASE = {
    ITA: [
        { ticker: 'ENEL.MI', name: 'Enel' },
        { ticker: 'ENI.MI', name: 'Eni' },
        { ticker: 'ISP.MI', name: 'Intesa Sanpaolo' },
        { ticker: 'UCG.MI', name: 'UniCredit' },
        { ticker: 'STLAM.MI', name: 'Stellantis' },
        { ticker: 'G.MI', name: 'Generali' },
        { ticker: 'RACE.MI', name: 'Ferrari' },
        { ticker: 'PRY.MI', name: 'Prysmian' },
        { ticker: 'TEN.MI', name: 'Tenaris' },
        { ticker: 'MB.MI', name: 'Mediobanca' },
        { ticker: 'BAMI.MI', name: 'Banco BPM' },
        { ticker: 'SRG.MI', name: 'Snam' },
        { ticker: 'TRN.MI', name: 'Terna' },
        { ticker: 'REC.MI', name: 'Recordati' },
        { ticker: 'MONC.MI', name: 'Moncler' }
    ],
    USA: [
        { ticker: 'AAPL', name: 'Apple' },
        { ticker: 'MSFT', name: 'Microsoft' },
        { ticker: 'NVDA', name: 'Nvidia' },
        { ticker: 'GOOGL', name: 'Alphabet' },
        { ticker: 'AMZN', name: 'Amazon' },
        { ticker: 'META', name: 'Meta' },
        { ticker: 'TSLA', name: 'Tesla' },
        { ticker: 'AMD', name: 'AMD' },
        { ticker: 'NFLX', name: 'Netflix' },
        { ticker: 'JPM', name: 'JPMorgan' },
        { ticker: 'BAC', name: 'Bank of America' },
        { ticker: 'DIS', name: 'Disney' },
        { ticker: 'INTC', name: 'Intel' },
        { ticker: 'PYPL', name: 'PayPal' },
        { ticker: 'V', name: 'Visa' }
    ]
};

// Variabile in memoria per i risultati
let cachedData = { 
    ITA: [], 
    USA: [], 
    lastUpdate: 'Nessuna analisi effettuata', 
    isScanning: false 
};

// Funzione di attesa per evitare il blocco di Yahoo Finance
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' }});
            if (response.status === 429) { await sleep(5000); continue; }
            if (!response.ok) return null;
            return await response.json();
        } catch (e) { if (i === retries - 1) return null; }
    }
    return null;
}

async function scanMarketSegment(tickers) {
    const passed = [];
    for (const item of tickers) {
        console.log(`Analizzando automaticamente ${item.ticker}...`);
        const json = await fetchWithRetry(`https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=6mo`);
        
        if (json?.chart?.result?.[0]?.indicators?.quote?.[0]?.close) {
            passed.push({ ticker: item.ticker, name: item.name }); 
        }
        await sleep(2000); // 2 secondi di pausa automatica per sicurezza
    }
    return passed;
}

async function runFullAnalysis() {
    if (cachedData.isScanning) return;
    
    cachedData.isScanning = true;
    console.log("🚀 Inizio scansione automatica del mercato...");

    try {
        const resITA = await scanMarketSegment(STOCKS_DATABASE.ITA);
        const resUSA = await scanMarketSegment(STOCKS_DATABASE.USA);
        
        cachedData = { 
            ITA: resITA, 
            USA: resUSA, 
            lastUpdate: new Date().toLocaleString('it-IT'), 
            isScanning: false 
        };
        console.log("✅ Scansione automatica completata con successo!");
    } catch (e) {
        console.error("❌ Errore durante la scansione:", e);
        cachedData.isScanning = false;
    }
}

// Avvio automatico programmato ogni giorno alle 05:00
cron.schedule('0 5 * * *', runFullAnalysis);

// ROTTE DEL SERVER
app.get('/', (req, res) => {
    res.send('<h1>Server Ciak Azioni attivo!</h1><p>Visualizza i dati su <a href="/api/market-analysis">/api/market-analysis</a> oppure avvia la scansione manuale su <a href="/api/force-start">/api/force-start</a>.</p>');
});

app.get('/api/market-analysis', (req, res) => {
    res.json(cachedData);
});

app.get('/api/force-start', (req, res) => {
    runFullAnalysis();
    res.send("🚀 Scansione avviata automaticamente in background.");
});

app.listen(PORT, () => console.log(`Server attivo sulla porta ${PORT}`));
