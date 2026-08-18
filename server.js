const express = require('express');
const path = require('path');
const { exec } = require('child_process');
const app = express();

const PORT = process.env.PORT || 3000;

// Rotta per forzare l'aggiornamento dei dati tramite update_db.py
app.get('/api/update', (req, res) => {
    exec('python3 update_db.py', (error, stdout, stderr) => {
        if (error) {
            console.error(`Errore esecuzione script: ${error}`);
            return res.status(500).json({ status: "Errore nell'aggiornamento" });
        }
        res.json({ status: "Database aggiornato con successo", output: stdout });
    });
});

// Serve il file market_db.json
app.get('/market_db.json', (req, res) => {
    res.sendFile(path.join(__dirname, 'market_db.json'));
});

// Serve i file statici dalla cartella public
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server avviato sulla porta ${PORT}`);
});
