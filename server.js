// In server.js (all'inizio del file)
let isAnalyzing = false;

app.post('/api/run-analysis', (req, res) => {
    if (isAnalyzing) {
        return res.status(400).json({ success: false, message: "Aggiornamento già in corso." });
    }

    isAnalyzing = true;
    console.log("Ricevuto comando: Inizio aggiornamento database completo...");
    
    fs.writeFileSync('progress.json', JSON.stringify({ percent: 0, status: "Inizializzazione script..." }));
    
    if (fs.existsSync('error_log.txt')) {
        fs.unlinkSync('error_log.txt');
    }

    const pythonProcess = spawn('python3', ['update_db.py']);
    res.json({ success: true, message: "Processo avviato." });

    pythonProcess.on('close', (code) => {
        isAnalyzing = false; // <-- SBLOCCO A FINE PROCESSO
        console.log(`Script Python terminato con codice ${code}`);
        if (code === 0) {
            fs.writeFileSync('progress.json', JSON.stringify({ percent: 100, status: "Completato!" }));
        } else {
            fs.writeFileSync('progress.json', JSON.stringify({ percent: 100, status: "Errore durante il processo!" }));
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        const errMessage = data.toString();
        console.error(`ERRORE PYTHON: ${errMessage}`);
        fs.appendFileSync('error_log.txt', `${new Date().toISOString()} - ${errMessage}\n`);
    });
});
