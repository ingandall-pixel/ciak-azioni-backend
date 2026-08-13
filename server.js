const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const mongoose = require('mongoose');
const fs = require('fs'); // Necessario per leggere il file JSON

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI;

mongoose.connect(MONGO_URI).catch(err => console.error(err));

const MarketData = mongoose.model('MarketData', new mongoose.Schema({
    key: { type: String, unique: true, default: 'global_analysis' },
    ITA: Array, USA: Array, lastUpdate: String, isScanning: Boolean
}));

// Funzione di utilità per attendere (anti-blocco)
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' }});
            if (response.status === 429) { await sleep(5000 * (i + 1)); continue; }
            if (!response.ok) return null;
            return await response.json();
        } catch (e) { await sleep(2000); }
    }
    return null;
}

async function scanMarketSegment(tickers, marketName) {
    const passed = [];
    // Processiamo 1 alla volta con pausa variabile per non bloccare
    for (const item of tickers) {
        console.log(`Analizzando ${item.ticker}...`);
        const json = await fetchWithRetry(`https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=6mo`);
        
        if (json?.chart?.result?.[0]?.indicators?.quote?.[0]?.close) {
            const prices = json.chart.result[0].indicators.quote[0].close.filter(p => p !== null && !isNaN(p));
            // Qui puoi rimettere la tua logica di calcolo (median, stddev)
            // ... (inserisci qui la tua logica if) ...
            passed.push({ ticker: item.ticker, name: item.name }); // Esempio
        }
        
        await sleep(2000); // PAUSA DI 2 SECONDI TRA OGNI AZIONE (Cruciale!)
    }
    return passed;
}

async function runFullAnalysis() {
    const db = await MarketData.findOne({ key: 'global_analysis' });
    if (db?.isScanning) return;

    await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: true }, { upsert: true });

    try {
        // Carichiamo le liste dal file JSON esterno
        const rawData = fs.readFileSync('./stocks.json');
        const stocks = JSON.parse(rawData);

        const resITA = await scanMarketSegment(stocks.ITA, 'ITA');
        const resUSA = await scanMarketSegment(stocks.USA, 'USA');
        
        await MarketData.findOneAndUpdate(
            { key: 'global_analysis' }, 
            { ITA: resITA, USA: resUSA, lastUpdate: new Date().toLocaleString(), isScanning: false }, 
            { upsert: true }
        );
    } catch (e) {
        console.error(e);
        await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: false }, { upsert: true });
    }
}

cron.schedule('0 5 * * *', runFullAnalysis);
app.get('/api/force-start', (req, res) => { runFullAnalysis(); res.send("Avviato"); });
app.listen(PORT);
