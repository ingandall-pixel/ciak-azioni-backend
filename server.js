const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Rotta per leggere lo stato della barra di avanzamento
app.get('/api/progress', (req, res) => {
    try {
        const progressData = fs.readFileSync('progress.json', 'utf8');
        res.json(JSON.parse(progressData));
    } catch (err) {
        res.json({ percent: 0, status: "Pronto per l'avvio..." });
    }
});

// Rotta per scaricare il file di log in caso di errore
app.get('/api/download-log', (req, res) => {
    const logPath = path.join(__dirname, 'error_log.txt');
    if (fs.existsSync(logPath)) {
        res.download(logPath);
    } else {
        res.status(404).send("Nessun file di log trovato. Nessun errore registrato.");
    }
});

// Avvia l'analisi / aggiornamento database
app.post('/api/run-analysis', (req, res) => {
    console.log("Ricevuto comando: Inizio elaborazione database...");
    
    fs.writeFileSync('progress.json', JSON.stringify({ percent: 0, status: "Inizializzazione script..." }));
    
    // Pulisci il vecchio log errori se esiste
    if (fs.existsSync('error_log.txt')) {
        fs.unlinkSync('error_log.txt');
    }

    const pythonProcess = spawn('python3', ['update_db.py']);
    
    res.json({ success: true, message: "Processo avviato." });

    pythonProcess.on('close', (code) => {
        console.log(`Script Python terminato con codice ${code}`);
        if (code === 0) {
            fs.writeFileSync('progress.json', JSON.stringify({ percent: 100, status: "Completato!" }));
        } else {
            fs.writeFileSync('progress.json', JSON.stringify({ percent: 100, status: "Errore durante il processo! Scarica il log." }));
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        const errMessage = data.toString();
        console.error(`ERRORE PYTHON: ${errMessage}`);
        fs.appendFileSync('error_log.txt', `${new Date().toISOString()} - ${errMessage}\n`);
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server attivo sulla porta ${PORT}`);
});
