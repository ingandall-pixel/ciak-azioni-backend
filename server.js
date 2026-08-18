const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const app = express();

app.use(express.static(path.join(__dirname, 'public')));

// Rotta per avviare l'aggiornamento/analisi tramite Python
app.post('/run-update', (req, res) => {
    // Avvia update_db.py come processo separato
    const pythonProcess = spawn('python', [path.join(__dirname, 'update_db.py')]);

    pythonProcess.on('error', (err) => {
        console.error("Errore nell'avvio dello script Python:", err);
    });

    res.json({ status: "Avviato" });
});

app.listen(3000, () => {
    console.log("Server attivo sulla porta 3000");
});
