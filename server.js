const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const app = express();

// --- CONFIGURAZIONI BASE ---
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// --- ROTTA PRINCIPALE ---
// Carica l'interfaccia grafica (la tua Home con il titolo "CIAK! - AZIONI 🖕")
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// --- ROTTA PROGRESSO ---
// Il frontend chiama questa rotta ogni secondo per far muovere la barra di caricamento
app.get('/api/progress', (req, res) => {
    try {
        // Legge lo stato dal file aggiornato dallo script Python
        const progressData = fs.readFileSync('progress.json', 'utf8');
        res.json(JSON.parse(progressData));
    } catch (err) {
        // Se il file non esiste ancora, restituisce 0%
        res.json({ percent: 0, status: "Avvio in corso..." });
    }
});

// --- ROTTA AVVIO ANALISI ---
// Si attiva quando clicchi "Avvia analisi" o quando parte l'automazione notturna
app.post('/api/run-analysis', (req, res) => {
    console.log("Ricevuto comando: Inizio costruzione/aggiornamento Database...");
    
    // 1. Inizializza/Resetta il file di progresso a 0
    fs.writeFileSync('progress.json', JSON.stringify({ percent: 0, status: "Inizializzazione script Python..." }));
    
    // 2. Lancia lo script di aggiornamento Intelligente (update_db.py)
    const pythonProcess = spawn('python3', ['update_db.py']);
    
    // 3. Risponde SUBITO al frontend. 
    // In questo modo il browser non rimane in caricamento per minuti, ma fa partire la barra.
    res.json({ success: true, message: "Processo avviato in background." });

    // 4. Gestione della chiusura del processo Python (Vero completamento o Crash)
    pythonProcess.on('close', (code) => {
        console.log(`Script Python terminato con codice ${code}`);
        if (code === 0) {
            // Se finisce con codice 0, significa che è andato tutto perfettamente
            fs.writeFileSync('progress.json', JSON.stringify({ percent: 100, status: "Completato!" }));
        } else {
            // Se finisce con qualsiasi altro codice, è crashato!
            fs.writeFileSync('progress.json', JSON.stringify({ percent: 100, status: "Errore! Guarda i log di Render" }));
        }
    });

    // Registra gli errori di Python direttamente nei log di Render per facilitare il debug
    pythonProcess.stderr.on('data', (data) => {
        console.error(`ERRORE PYTHON: ${data.toString()}`);
    });
});

// --- AVVIO DEL SERVER ---
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server attivo e in ascolto sulla porta ${PORT}`);
    console.log(`Pronto per gestire l'analisi del mercato Italiano e Americano.`);
});
