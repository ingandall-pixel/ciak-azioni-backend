const express = require('express');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 1. Rotta per avviare l'analisi di mercato (collegata a "Avvia analisi di mercato")
app.post('/api/update-market', (req, res) => {
    // Esegue lo script Python "analyzer.py download" in background
    const pyProcess = spawn('python', [path.join(__dirname, 'analyzer.py'), 'download']);

    pyProcess.on('error', (err) => {
        console.error("Errore nell'avvio del processo Python:", err);
    });

    res.json({ status: "success", message: "Analisi di mercato e aggiornamento dati avviati sul server!" });
});

// 2. Rotta per verificare lo stato dell'avanzamento (legge progress.json)
app.get('/api/progress', (req, res) => {
    const progressFile = path.join(__dirname, 'progress.json');
    if (fs.existsSync(progressFile)) {
        try {
            const data = fs.readFileSync(progressFile, 'utf8');
            res.json(JSON.parse(data));
        } catch (e) {
            res.json({ percent: 0, status: "Lettura in corso..." });
        }
    } else {
        res.json({ percent: 0, status: "In attesa di avvio..." });
    }
});

// 3. Rotta per restituire i risultati filtrati (collegata a "Restituisci risultati")
app.post('/api/get-results', (req, res) => {
    const { market = 'IT', timeframe = '1m', median = 50, std = 10 } = req.body;

    // Esegue analyzer.py passando i parametri di filtro
    const pyProcess = spawn('python', [
        path.join(__dirname, 'analyzer.py'),
        market,
        timeframe,
        median.toString(),
        std.toString()
    ]);

    let dataString = '';
    let errorString = '';

    pyProcess.stdout.on('data', (chunk) => {
        dataString += chunk;
    });

    pyProcess.stderr.on('data', (chunk) => {
        errorString += chunk;
    });

    pyProcess.on('close', (code) => {
        if (code !== 0) {
            console.error(`Errore in analyzer.py: ${errorString}`);
            return res.status(500).json([]);
        }

        try {
            const results = JSON.parse(dataString);
            
            // Mappa i risultati aggiungendo il link dinamico a Investing.com per ciascun ticker
            const formattedResults = results.map(item => ({
                ticker: item.ticker,
                url: `https://www.investing.com/search/?q=${item.ticker}`,
                prezzo: item.price,
                trend_img: "", // Può essere integrato con la generazione sparkline grafica
                perf1: item.var_period,
                perf2: item.var_daily,
                perf3: item.med_mean_ratio,
                perf4: item.std_mean_ratio
            }));

            res.json(formattedResults);
        } catch (e) {
            console.error("Errore nel parsing dell'output JSON:", e, dataString);
            res.status(500).json([]);
        }
    });
});

// Avvio del server
app.listen(PORT, () => {
    console.log(`Server CIAK!-AZIONI attivo sulla porta ${PORT}`);
});