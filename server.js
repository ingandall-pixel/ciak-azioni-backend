const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Endpoint per avviare l'aggiornamento del database
app.get('/api/update-db', (req, res) => {
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const pythonProcess = spawn(pythonCmd, ['update_db.py']);
    
    let stderrOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        stderrOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.json({ success: true, message: 'Database aggiornato con successo.' });
        } else {
            res.status(500).json({ success: false, message: 'Errore durante l\'aggiornamento del DB', error: stderrOutput });
        }
    });
});

// Endpoint per avviare l'analisi completa dei dati
app.get('/api/analyze', (req, res) => {
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const pythonProcess = spawn(pythonCmd, ['analyzer.py']);
    
    let output = '';
    let stderrOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        stderrOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code === 0) {
            try {
                const results = JSON.parse(output);
                res.json({ success: true, data: results });
            } catch (e) {
                res.status(500).json({ success: false, message: 'Errore di parsing JSON dall\'analisi', raw: output });
            }
        } else {
            res.status(500).json({ success: false, message: 'Errore durante l\'esecuzione dell\'analisi', error: stderrOutput });
        }
    });
});

// Endpoint per monitorare lo stato di avanzamento in tempo reale
app.get('/api/progress', (req, res) => {
    const progressPath = path.join(__dirname, 'progress.json');
    if (fs.existsSync(progressPath)) {
        try {
            const data = fs.readFileSync(progressPath, 'utf8');
            res.json(JSON.parse(data));
        } catch (e) {
            res.json({ percent: 0, status: 'Lettura progresso in corso...' });
        }
    } else {
        res.json({ percent: 0, status: 'In attesa dell\'avvio' });
    }
});

app.listen(PORT, () => {
    console.log(`Server Node.js avviato sulla porta ${PORT}`);
});
