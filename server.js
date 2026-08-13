const express = require('express');
const cors = require('cors');
const cron = require('node-cron');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

// Variabile in memoria (al posto del database)
let cachedData = { ITA: [], USA: [], lastUpdate: 'Nessuna analisi effettuata', isScanning: false };

async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' }});
            if (response.status === 429) { await new Promise(r => setTimeout(r, 2000)); continue; }
            if (!response.ok) return null;
            return await response.json();
        } catch (e) { if (i === retries - 1) return null; }
    }
    return null;
}

// (Inserisci qui le tue funzioni scanMarketSegment, getAllITAStocks, getAllUSStocks come prima)
// ...

async function runFullAnalysis() {
    if (cachedData.isScanning) return;
    
    cachedData.isScanning = true;
    console.log("🚀 Inizio scansione...");

    try {
        // Supponendo tu abbia le funzioni definite sotto
        const resITA = await scanMarketSegment(await getAllITAStocks(), 'ITA');
        const resUSA = await scanMarketSegment(await getAllUSStocks(), 'USA');
        
        cachedData = { 
            ITA: resITA, 
            USA: resUSA, 
            lastUpdate: new Date().toLocaleString('it-IT'), 
            isScanning: false 
        };
        console.log("✅ Scansione completata!");
    } catch (e) {
        console.error("❌ Errore:", e);
        cachedData.isScanning = false;
    }
}

cron.schedule('0 5 * * *', runFullAnalysis);

app.get('/api/market-analysis', (req, res) => {
    res.json(cachedData);
});

app.get('/api/force-start', (req, res) => {
    runFullAnalysis();
    res.send("🚀 Scansione avviata.");
});

app.listen(PORT, () => console.log(`Server attivo su porta ${PORT}`));
