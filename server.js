const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const DB_FILE = path.join(__dirname, 'market_db.json');
const PROGRESS_FILE = path.join(__dirname, 'progress.json');

app.post('/api/update-market', (req, res) => {
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify({ percent: 0, status: "Avvio in corso..." }));
    const pythonProcess = spawn('python3', ['update_db.py']);
    
    pythonProcess.stderr.on('data', (data) => {
        console.error("Errore update_db stderr:", data.toString());
    });

    res.json({ success: true, message: "Aggiornamento avviato con successo." });
});

app.get('/api/progress', (req, res) => {
    if (fs.existsSync(PROGRESS_FILE)) {
        try {
            const data = fs.readFileSync(PROGRESS_FILE, 'utf8');
            res.json(JSON.parse(data));
        } catch (e) {
            res.json({ percent: 0, status: "Lettura progresso..." });
        }
    } else {
        res.json({ percent: 0, status: "In attesa..." });
    }
});

// Rotta risultati: legge esattamente i valori inseriti dall'utente (default '0')
app.get('/api/get-results', (req, res) => {
    const { market = 'ALL', tf = '1m', mm = '0', sr = '0' } = req.query;
    
    // Ordine parametri: market, tf, mm, sr
    const pythonProcess = spawn('python3', ['analyzer.py', market, tf, mm, sr]);
    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorString += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (errorString) {
            console.error("Errore Python stderr:", errorString);
        }

        const cleanData = dataString.trim();
        if (!cleanData) {
            console.warn("Nessun dato ricevuto da analyzer.py (output vuoto).");
            return res.json([]);
        }

        try {
            const results = JSON.parse(cleanData);
            res.json(results);
        } catch (e) {
            console.error("Errore di Parsing JSON:", e, "Dati ricevuti:", dataString);
            res.json([]);
        }
    });
});

app.get('/api/live-prices', async (req, res) => {
    const { tickers = '' } = req.query;
    if (!tickers) return res.json({});

    const allTickers = tickers.split(',').map(t => t.trim()).filter(Boolean);
    const prezziLive = {};

    const fetchTicker = async (ticker) => {
        try {
            const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(ticker)}?interval=1d&range=1d`;
            const response = await fetch(url, { 
                headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' } 
            });
            
            if (response.ok) {
                const data = await response.json();
                const meta = data.chart?.result?.[0]?.meta;
                const price = meta?.regularMarketPrice ?? meta?.chartPreviousClose;
                
                if (price !== undefined && price !== null) {
                    prezziLive[ticker] = price;
                }
            }
        } catch (e) {
            // Ignora eventuali errori su singoli ticker
        }
    };

    // Esegue le richieste a lotti da 15 in parallelo per gestire centinaia di azioni senza blocchi IP
    const batchSize = 15;
    for (let i = 0; i < allTickers.length; i += batchSize) {
        const batch = allTickers.slice(i, i + batchSize);
        await Promise.allSettled(batch.map(ticker => fetchTicker(ticker)));
    }

    res.json(prezziLive);
});

app.listen(PORT, () => {
    console.log(`Server avviato sulla porta ${PORT}`);
});