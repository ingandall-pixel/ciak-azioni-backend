const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

const PROGRESS_FILE = path.join(__dirname, 'progress.json');

app.post('/api/run-download', (req, res) => {
    const pythonProcess = spawn('python', ['analyzer.py', 'download']);
    pythonProcess.unref();
    res.json({ status: "started" });
});

app.get('/api/progress', (req, res) => {
    if (fs.existsSync(PROGRESS_FILE)) {
        try {
            const data = fs.readFileSync(PROGRESS_FILE, 'utf-8');
            return res.json(JSON.parse(data));
        } catch (e) {
            return res.json({ percent: 0, status: "Errore di lettura" });
        }
    }
    res.json({ percent: 0, status: "In attesa..." });
});

app.get('/api/analyze', (req, res) => {
    const { market, tf, median_markup, std_ratio } = req.query;
    
    const py = spawn('python', ['analyzer.py', market || 'IT', tf || '1m', median_markup || '1', std_ratio || '1']);
    let output = '';

    py.stdout.on('data', (data) => {
        output += data.toString();
    });

    py.on('close', () => {
        try {
            const parsed = JSON.parse(output);
            res.json(parsed);
        } catch (e) {
            res.json([]);
        }
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server attivo sulla porta ${PORT}`);
});
