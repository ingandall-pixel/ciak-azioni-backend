const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const mongoose = require('mongoose');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI;

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

// MOTORE ANTI-BLOCCO: Aumentato il timeout di sicurezza
async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, { 
                headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36' }
            });
            if (response.status === 429) { 
                await new Promise(r => setTimeout(r, 5000 * (i + 1))); // Attesa più lunga se bloccati
                continue; 
            }
            if (!response.ok) return null;
            return await response.json();
        } catch (e) { if (i === retries - 1) return null; }
    }
    return null;
}

const calculateMean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
const calculateMedian = (arr) => { const s = [...arr].sort((a, b) => a - b); const m = Math.floor(s.length / 2); return s.length % 2 !== 0 ? s[m] : (s[m-1] + s[m]) / 2; };
const calculateStdDev = (arr, mean) => Math.sqrt(arr.reduce((sq, val) => sq + Math.pow(val - mean, 2), 0) / arr.length);

// LOGICA SCANSIONE: BATCH_SIZE ridotto a 3 per massima sicurezza
async function scanMarketSegment(tickers, marketName, ruleMonths = 6, ruleStdMonths = 6, ruleStdPct = 3.0) {
    const passed = [];
    const BATCH_SIZE = 3; 
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
                ticker: item.ticker, name: item.name, price: `${cur.toFixed(2)} ${marketName === 'ITA' ? '€' : '$'}`, 
                changePeriodPct: ((cur - pMed[0]) / pMed[0]) * 100, 
                dailyChangePct: ((cur - (prices[prices.length-2] || cur)) / (prices[prices.length-2] || cur)) * 100, 
                url: `https://www.tradingview.com/chart/?symbol=${marketName === 'ITA' ? 'MIL' : 'US'}:${item.ticker.replace('.MI', '')}` 
            };
        });
        const res = await Promise.all(promises);
        res.forEach(r => { if (r) passed.push(r); });
        await new Promise(r => setTimeout(r, 1500)); // Pausa più lunga tra i batch per non farsi bannare
    }
    return passed;
}

// LISTA OTTIMIZZATA (FTSE MIB + Top USA)
async function getAllITAStocks() {
    return [
        { ticker: 'ENEL.MI', name: 'Enel' }, { ticker: 'ENI.MI', name: 'Eni' }, { ticker: 'ISP.MI', name: 'Intesa Sanpaolo' },
        { ticker: 'STLAM.MI', name: 'Stellantis' }, { ticker: 'G.MI', name: 'Generali' }, { ticker: 'UNIC.MI', name: 'UniCredit' },
        { ticker: 'AZM.MI', name: 'Azimut' }, { ticker: 'BAMI.MI', name: 'Banco BPM' }, { ticker: 'BMPS.MI', name: 'MPS' },
        { ticker: 'TEN.MI', name: 'Tenaris' }, { ticker: 'PRY.MI', name: 'Prysmian' }, { ticker: 'STM.MI', name: 'STMicro' },
        { ticker: 'RACE.MI', name: 'Ferrari' }, { ticker: 'MONC.MI', name: 'Moncler' }, { ticker: 'REC.MI', name: 'Recordati' }
    ];
}

async function getAllUSStocks() {
    return [
        { ticker: 'AAPL', name: 'Apple' }, { ticker: 'MSFT', name: 'Microsoft' }, { ticker: 'NVDA', name: 'Nvidia' },
        { ticker: 'GOOGL', name: 'Alphabet' }, { ticker: 'AMZN', name: 'Amazon' }, { ticker: 'META', name: 'Meta' },
        { ticker: 'TSLA', name: 'Tesla' }, { ticker: 'AMD', name: 'AMD' }, { ticker: 'NFLX', name: 'Netflix' },
        { ticker: 'JPM', name: 'JPMorgan' }, { ticker: 'BAC', name: 'Bank of America' }, { ticker: 'DIS', name: 'Disney' }
    ];
}

async function runFullAnalysis() {
    const db = await MarketData.findOne({ key: 'global_analysis' });
    if (db?.isScanning) return; // Protezione da esecuzione multipla

    await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: true }, { upsert: true });

    try {
        const ita = await getAllITAStocks();
        const us = await getAllUSStocks();
        const resITA = await scanMarketSegment(ita, 'ITA');
        const resUSA = await scanMarketSegment(us, 'USA');
        
        await MarketData.findOneAndUpdate(
            { key: 'global_analysis' }, 
            { ITA: resITA, USA: resUSA, lastUpdate: new Date().toLocaleString('it-IT', { timeZone: 'Europe/Rome' }), isScanning: false }, 
            { upsert: true }
        );
    } catch (e) {
        await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: false }, { upsert: true });
    }
}

cron.schedule('0 5 * * *', runFullAnalysis, { timezone: "Europe/Rome" });

app.get('/api/market-analysis', async (req, res) => {
    const data = await MarketData.findOne({ key: 'global_analysis' });
    res.json(data || { ITA: [], USA: [], message: "In attesa..." });
});

app.get('/api/unlock', async (req, res) => {
    await MarketData.findOneAndUpdate({ key: 'global_analysis' }, { isScanning: false }, { upsert: true });
    res.send("Sbloccato.");
});

app.get('/api/force-start', (req, res) => {
    runFullAnalysis();
    res.send("Avviato.");
});

app.listen(PORT, () => console.log(`Server attivo su porta ${PORT}`));
