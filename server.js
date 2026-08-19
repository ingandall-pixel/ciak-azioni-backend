const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const DB_FILE = path.join(__dirname, 'market_db.json');
const PROGRESS_FILE = path.join(__dirname, 'progress.json');

// Endpoint per avviare il download/aggiornamento dell'archivio
app.get('/api/update', (req, res) => {
    // Resetta il file di progresso
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify({ percent: 0, status: "Avvio in corso..." }));
    
    const pythonProcess = spawn('python', ['update_db.py']);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    res.json({ success: true, message: "Aggiornamento avviato con successo." });
});

// Endpoint per controllare lo stato di avanzamento
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

// Endpoint per analizzare i dati filtrati per mercato e parametri
app.get('/api/analyze', (req, res) => {
    const { market = 'IT', tf = '1m', mm = '0', sr = '0' } = req.query;

    const pythonProcess = spawn('python', ['analyzer.py', market, tf, mm, sr]);
    let dataString = '';

    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        try {
            const results = JSON.parse(dataString);
            res.json(results);
        } catch (e) {
            res.json([]);
        }
    });
});

// Endpoint per statistiche generali del database (separa IT e US)
app.get('/api/stats', (req, res) => {
    if (!fs.existsSync(DB_FILE)) {
        return res.json({ it_count: 0, us_count: 0 });
    }

    try {
        const db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
        let it_count = 0;
        let us_count = 0;

        for (const [ticker, history] of Object.entries(db)) {
            if (ticker.endsWith('.MI') || ticker.endsWith('.AS')) {
                it_count++;
            } else {
                us_count++;
            }
        }

        res.json({ it_count, us_count });
    } catch (e) {
        res.json({ it_count: 0, us_count: 0 });
    }
});

app.listen(PORT, () => {
    console.log(`Server avviato sulla porta ${PORT}`);
});