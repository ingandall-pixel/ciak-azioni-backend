const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Rotta Home: Carica l'interfaccia
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Endpoint Pulsante "Avvia analisi" (Aggiornamento Manuale)
app.post('/api/run-analysis', (req, res) => {
    console.log("Analisi manuale avviata...");
    // Usiamo 'python3' invece di 'python' per compatibilità su ambienti Linux/Render
    const pythonProcess = spawn('python3', ['analyzer.py', 'it', '1y', '0', '0', 'perf', 'desc']);
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.json({ success: true, message: "Analisi completata con successo!" });
        } else {
            res.status(500).json({ success: false, message: "Errore durante l'esecuzione dello script Python." });
        }
    });
});

// Endpoint per il filtraggio on-demand
app.get('/api/filter-actions', (req, res) => {
    const { market, period, medianMarkup, stdMarkup, sortBy, sortOrder } = req.query;

    const pythonProcess = spawn('python3', [
        'analyzer.py', 
        market || 'it', 
        period || '1y', 
        medianMarkup || 0, 
        stdMarkup || 0, 
        sortBy || 'perf', 
        sortOrder || 'desc'
    ]);

    let dataString = '';
    pythonProcess.stdout.on('data', (data) => { dataString += data.toString(); });
    
    pythonProcess.on('close', (code) => {
        try {
            res.json(JSON.parse(dataString));
        } catch (e) {
            res.status(500).json({ error: "Errore nel calcolo dei dati." });
        }
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server attivo su porta ${PORT}`);
});
