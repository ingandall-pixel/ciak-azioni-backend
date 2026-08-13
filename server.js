const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

// Variabile in memoria (al posto del database)
let cachedData = { 
    ITA: [], 
    USA: [], 
    lastUpdate: 'Nessuna analisi effettuata', 
    isScanning: false 
};

// Funzione di attesa per evitare il ban di Yahoo Finance
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

async function scanMarketSegment(tickers, marketName) {
    const passed = [];
    for (const item of tickers) {
        console.log(`Analizzando ${item.ticker}...`);
        const json = await fetchWithRetry(`https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=6mo`);
        
        if (json?.chart?.result?.[0]?.indicators?.quote?.[0]?.close) {
            // Qui va la tua logica di analisi
            passed.push({ ticker: item.ticker, name: item.name }); 
        }
        await sleep(2000); // 2 secondi di pausa tra un'azione e l'altra
    }
    return passed;
}

async function runFullAnalysis() {
    if (cachedData.isScanning) return;
    
    cachedData.isScanning = true;
    console.log("🚀 Inizio scansione...");

    try {
        // Legge la lista titoli dal file stocks.json
        const rawData = fs.readFileSync(path.join(__dirname, 'stocks.json'));
        const stocks = JSON.parse(rawData);

        const resITA = await scanMarketSegment(stocks.ITA, 'ITA');
        const resUSA = await scanMarketSegment(stocks.USA, 'USA');
        
        cachedData = { 
            ITA: resITA, 
            USA: resUSA, 
            lastUpdate: new Date().toLocaleString('it-IT'), 
            isScanning: false 
        };
        console.log("✅ Scansione completata!");
    } catch (e) {
        console.error("❌ Errore durante la scansione:", e);
        cachedData.isScanning = false;
    }
}

// Analisi automatica ogni giorno alle 05:00
cron.schedule('0 5 * * *', runFullAnalysis);

// ROTTE
app.get('/', (req, res) => {
    res.send('<h1>Server Ciak Azioni attivo!</h1><p>Vai su <a href="/api/market-analysis">/api/market-analysis</a> per vedere i dati o su <a href="/api/force-start">/api/force-start</a> per avviare la scansione.</p>');
});

app.get('/api/market-analysis', (req, res) => {
    res.json(cachedData);
});

app.get('/api/force-start', (req, res) => {
    runFullAnalysis();
    res.send("🚀 Scansione avviata in background. Controlla i log su Render.");
});

app.listen(PORT, () => console.log(`Server attivo su porta ${PORT}`));
