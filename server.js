const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Rotta fondamentale per caricare la pagina HTML principale
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const DB_FILE = path.join(__dirname, 'market_db.json');
const PROGRESS_FILE = path.join(__dirname, 'progress.json');

// Rotta chiamata da index.html per avviare l'aggiornamento del database
app.post('/api/update-market', (req, res) => {
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify({ percent: 0, status: "Avvio in corso..." }));
    const pythonProcess = spawn('python3', ['update_db.py']);
    res.json({ success: true, message: "Aggiornamento avviato con successo." });
});

// Rotta per monitorare la percentuale di avanzamento
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

// Rotta chiamata da index.html per ottenere i risultati filtrati (con gestione errori e stderr migliorata)
app.get('/api/get-results', (req, res) => {
    const { market = 'IT', tf = '1m', mm = '0', sr = '0' } = req.query;
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
        try {
            const cleanData = dataString.trim();
            const results = JSON.parse(cleanData);
            res.json(results);
        } catch (e) {
            console.error("Errore di Parsing JSON:", e, "Dati ricevuti:", dataString);
            res.json([]);
        }
    });
});

app.listen(PORT, () => {
    console.log(`Server avviato sulla porta ${PORT}`);
});