const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const DB_FILE = path.join(__dirname, 'market_db.json');

// Middleware per leggere il formato JSON e servire i file statici dalla cartella public
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 1. Rotta per l'aggiornamento incrementale (collegata a "Avvia analisi di mercato")
app.post('/api/update-market', (req, res) => {
    if (!fs.existsSync(DB_FILE)) {
        return res.status(404).json({ status: "error", message: "Database non trovato." });
    }

    try {
        // Qui puoi inserire o richiamare la logica di aggiornamento delle candele
        // (es. leggendo market_db.json e aggiornando i dati)
        
        res.json({ status: "success", message: "Analisi di mercato e aggiornamento incrementale completati con successo!" });
    } catch (error) {
        res.status(500).json({ status: "error", message: "Errore durante l'aggiornamento del mercato." });
    }
});

// 2. Rotta per restituire i risultati filtrati (collegata a "Restituisci risultati")
app.post('/api/get-results', (req, res) => {
    const { timeframe, median, std } = req.body;

    if (!fs.existsSync(DB_FILE)) {
        return res.json([]);
    }

    try {
        const rawData = fs.readFileSync(DB_FILE, 'utf8');
        const dbData = JSON.parse(rawData);

        let risultatiFiltrati = [];

        for (const [ticker, data] of Object.entries(dbData)) {
            // Genera il link diretto a Investing.com per il ticker
            const investingUrl = `https://www.investing.com/search/?q=${ticker}`;

            risultatiFiltrati.push({
                ticker: ticker,
                url: investingUrl,
                prezzo: data.prezzo || 0.0,
                trend_img: data.trend_img || "",
                perf1: data.perf1 || 0.0,
                perf2: data.perf2 || 0.0,
                perf3: data.perf3 || 0.0,
                perf4: data.perf4 || 0.0
            });
        }

        res.json(risultatiFiltrati);
    } catch (error) {
        console.error("Errore nella lettura del database:", error);
        res.status(500).json([]);
    }
});

// Avvio del server
app.listen(PORT, () => {
    console.log(`Server CIAK!-AZIONI in ascolto sulla porta ${PORT}`);
});
