const express = require('express');
const path = path = require('path');
const app = express();
const PORT = process.env.PORT || 10000;

// Serve i file statici (come index.html) dalla cartella 'public'
app.use(express.static(path.join(__dirname, 'public')));

// Endpoint esplicito per servire il file di database JSON dalla root
app.get('/market_db.json', (req, res) => {
    res.sendFile(path.join(__dirname, 'market_db.json'));
});

app.listen(PORT, () => {
    console.log(`Server Node.js in ascolto sulla porta ${PORT}`);
});
