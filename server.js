const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const mongoose = require('mongoose');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI;

// Connessione MongoDB
mongoose.connect(MONGO_URI)
    .then(() => console.log('✅ Connesso a MongoDB Atlas'))
    .catch(err => console.error('❌ Errore di connessione a MongoDB:', err));

const MarketData = mongoose.model('MarketData', new mongoose.Schema({
    key: { type: String, unique: true, default: 'global_analysis' },
    ITA: Array,
    USA: Array,
    lastUpdate: String,
    isScanning: Boolean
}));

// =========================================================================
// MOTORE ANTI-BLOCCO
// =========================================================================
async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36' }});
            if (response.status === 429) { await new Promise(r => setTimeout(r, 2000 * (i + 1))); continue; }
            if (!response.ok) return null;
            return await response.json();
        } catch (e) { if (i === retries - 1) return null; }
    }
    return null;
}

// =========================================================================
// LOGICA DI SELEZIONE
// =========================================================================
const calculateMean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
const calculateMedian = (arr) => { const s = [...arr].sort((a, b) => a - b); const m = Math.floor(s.length / 2); return s.length % 2 !== 0 ? s[m] : (s[m-1] + s[m]) / 2; };
const calculateStdDev = (arr, mean) => Math.sqrt(arr.reduce((sq, val) => sq + Math.pow(val - mean, 2), 0) / arr.length);

async function scanMarketSegment(tickers, marketName, ruleMonths = 6, ruleStdMonths = 6, ruleStdPct = 3.0) {
    const passed = [];
    const BATCH_SIZE = 5;
    const daysMed = ruleMonths * 21;
    const daysStd = ruleStdMonths * 21;

    for (let i = 0; i < tickers.length; i += BATCH_SIZE) {
        const batch = tickers.slice(i, i + BATCH_SIZE);
        const promises = batch.map(async (item) => {
            const json = await fetchWithRetry(`https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=5y`);
            if (!json?.chart?.result?.[0]?.indicators?.quote?.[0]?.close) return null;
            const prices = json.chart.result[0].indicators.quote[0].close.filter(p => p !== null && !isNaN(p));
            if (prices.length < Math.max(daysMed, daysStd)) return null;

            const pMed = prices.slice(-daysMed);
            if (calculateMedian(pMed) <= calculateMean(pMed)) return null;

            const pStd = prices.slice(-daysStd);
            if (calculateStdDev(pStd, calculateMean(pStd)) < (ruleStdPct / 100) * calculateMean(pStd)) return null;

            const cur = prices[prices.length - 1];
            return { 
                ticker: item.ticker, 
                name: item.name, 
                price: `${cur.toFixed(2)} ${marketName === 'ITA' ? '€' : '$'}`, 
                changePeriodPct: ((cur - pMed[0]) / pMed[0]) * 100, 
                dailyChangePct: ((cur - (prices[prices.length-2] || cur)) / (prices[prices.length-2] || cur)) * 100, 
                url: `https://www.tradingview.com/chart/?symbol=${marketName === 'ITA' ? 'MIL' : 'US'}:${item.ticker.replace('.MI', '')}` 
            };
        });
        const res = await Promise.all(promises);
        res.forEach(r => { if (r) passed.push(r); });
        await new Promise(r => setTimeout(r, 600));
    }
    return passed;
}

// =========================================================================
// FUNZIONI DATI (Inserisci qui la tua lista completa)
// =========================================================================
async function getAllITAStocks() {
    return [
        { ticker: 'ENEL.MI', name: 'Enel' },
        { ticker: 'ENI.MI', name: 'Eni' },
        { ticker: 'ISP.MI', name: 'Intesa Sanpaolo' },
        { ticker: 'STLAM.MI', name: 'Stellantis' }
        // Aggiungi qui gli altri titoli...
    ];
}

async function getAllUSStocks() {
    return [
        { ticker: 'AAPL', name: 'Apple' },
        { ticker: 'MSFT', name: 'Microsoft' },
        { ticker: 'TSLA', name: 'Tesla' },
        { ticker: 'NVDA', name: 'Nvidia' }
        // Aggiungi qui gli altri titoli...
    ];
}

// =========================================================================
// ESECUZIONE
// =========================================================================
async function runFullAnalysis() {
    try {
        const db = await MarketData.findOne({ key: 'global_analysis' });
        if (db?.isScanning) {
            console.log("⚠️ Una scansione risulta già attiva.");
            return;
        }

        await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: true }, { upsert: true });

        console.log("🚀 Inizio scansione mercati...");
        const ita = await getAllITAStocks();
        const us = await getAllUSStocks();
        
        const resITA = await scanMarketSegment(ita, 'ITA');
        const resUSA = await scanMarketSegment(us, 'USA');
        
        await MarketData.findOneAndUpdate(
            { key: 'global_analysis' }, 
            { ITA: resITA, USA: resUSA, lastUpdate: new Date().toLocaleString('it-IT', { timeZone: 'Europe/Rome' }), isScanning: false }, 
            { upsert: true }
        );
        console.log("✅ Scansione completata!");
    } catch (e) {
        console.error("❌ Errore critico:", e);
        await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: false }, { upsert: true });
    }
}

cron.schedule('0 5 * * *', runFullAnalysis, { timezone: "Europe/Rome" });

// =========================================================================
// ENDPOINTS
// =========================================================================
app.get('/api/market-analysis', async (req, res) => {
    try {
        const data = await MarketData.findOne({ key: 'global_analysis' });
        if (data && (data.ITA?.length > 0 || data.USA?.length > 0)) {
            res.json({ ITA: data.ITA, USA: data.USA, lastUpdate: data.lastUpdate });
        } else {
            res.json({ ITA: [], USA: [], message: "Analisi in corso." });
        }
    } catch (e) {
        res.status(500).json({ ITA: [], USA: [], message: "Errore database." });
    }
});

app.get('/api/unlock', async (req, res) => {
    await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: false }, { upsert: true });
    res.send("🔓 Server sbloccato.");
});

app.get('/api/force-start', (req, res) => {
    runFullAnalysis();
    res.send("🚀 Scansione avviata.");
});

app.listen(PORT, () => console.log(`Server attivo sulla porta ${PORT}`));
