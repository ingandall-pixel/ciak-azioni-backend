const express = require('express');
const path = require('path');
const app = express();

const PORT = process.env.PORT || 3000;

// Serve il file market_db.json presente nella radice del progetto
app.get('/market_db.json', (req, res) => {
    res.sendFile(path.join(__dirname, 'market_db.json'));
});

// Serve i file statici dalla cartella 'public' (compreso index.html)
app.use(express.static(path.join(__dirname, 'public')));

// Pagina principale
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server avviato ed in ascolto sulla porta ${PORT}`);
});
