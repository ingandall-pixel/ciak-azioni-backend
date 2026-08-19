const express = require('express');
const fs = require('fs');
const path = require('path');
const { calcola_statistiche_periodo } = require('./analyzer'); // se analyzer fosse in python, qui gestiamo la chiamata o simuliamo in JS. 
// Attenzione: analyzer.py è in Python. Nel server Node.js dobbiamo calcolare i valori o passarli.
// Per semplicità e coerenza con la tua struttura, vediamo come leggerli dal DB o calcolarli.
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

app.post('/api/analizza', (req, res) => {
    const { mercato, arcoTemporale, minMediana, minDev } = req.body;
    
    const dbPath = path.join(__dirname, 'market_db.json');
    if (!fs.existsSync(dbPath)) {
        return res.json({ italia: [], usa: [] });
    }

    const db = JSON.parse(fs.readFileSync(dbPath, 'utf8'));
    let risultatiItalia = [];
    let risultatiUsa = [];

    const minMedNum = parseFloat(minMediana) || 0;
    const minDevNum = parseFloat(minDev) || 0;

    for (const [ticker, info] of Object.entries(db)) {
        const tipoMercato = info.mercato ? info.mercato.toLowerCase() : 'italia';
        
        if (mercato !== 'tutti' && tipoMercato !== mercato) {
            continue;
        }

        const storico = info.istorico || [];
        if (storico.length === 0) continue;

        const ultimoElemento = storico[storico.length - 1];
        const ultimoPrezzo = ultimoElemento.close || 0;
        const varGiornaliera = ultimoElemento.change || 0;
        
        // Variazione di periodo (puoi regolarla in base a come salvi i dati nel db)
        const varPeriodo = info.var_periodo || 0; 

        const linkInvesting = info.link_investing || `https://www.investing.com/search/?q=${ticker}`;
        const trendGrafico = info.trend_html || '';

        // Recuperiamo o simuliamo i valori calcolati in base all'arco temporale
        // (Se vengono salvati nel DB o calcolati al volo)
        const medianaMedia = info.mediana_media || 0.0;
        const devStdMedia = info.dev_std_media || 0.0;

        // Applicazione rigorosa dei filtri come limiti inferiori
        if (medianaMedia >= minMedNum && devStdMedia >= minDevNum) {
            const elemento = {
                titolo: ticker,
                link: linkInvesting,
                prezzo: ultimoPrezzo.toFixed(2),
                trend: trendGrafico,
                varPeriodo: varPeriodo.toFixed(2),
                varGiornaliera: varGiornaliera.toFixed(2),
                medianaMedia: medianaMedia.toFixed(2),
                devStdMedia: devStdMedia.toFixed(2)
            };

            if (tipoMercato === 'usa') {
                risultatiUsa.push(elemento);
            } else {
                risultatiItalia.push(elemento);
            }
        }
    }

    res.json({ italia: risultatiItalia, usa: risultatiUsa });
});

app.listen(PORT, () => {
    console.log(`Server avviato sulla porta ${PORT}`);
});
