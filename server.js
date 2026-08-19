const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Endpoint per ottenere i dati elaborati con i filtri e l'arco temporale
app.post('/api/analizza', (req, res) => {
    const { mercato, arcoTemporale, minMediana, minDev } = req.body;
    
    const dbPath = path.join(__dirname, 'market_db.json');
    if (!fs.existsSync(dbPath)) {
        return res.json({ italia: [], usa: [] });
    }

    const db = JSON.parse(fs.readFileSync(dbPath, 'utf8'));
    let risultatiItalia = [];
    let risultatiUsa = [];

    for (const [ticker, info] of Object.entries(db)) {
        // Logica di filtraggio per mercato (italia / usa)
        const tipoMercato = info.mercato ? info.mercato.toLowerCase() : 'italia';
        
        if (mercato !== 'tutti' && tipoMercato !== mercato) {
            continue;
        }

        const storico = info.istorico || [];
        if (storico.length === 0) continue;

        const ultimoPrezzo = storico[storico.length - 1].close || 0;
        const varGiornaliera = storico[storico.length - 1].change || 0;
        const varPeriodo = info.var_periodo || 0; // O calcolata sul periodo

        // Link Investing.com associato direttamente al titolo
        const linkInvesting = info.link_investing || `https://www.investing.com/search/?q=${ticker}`;
        
        // Ultimo grafico giornaliero disponibile (Trend)
        const trendGrafico = info.trend_html || '';

        // Valori simulati o calcolati tramite analyzer (qui rappresentati come metriche di esempio)
        const medianaMedia = info.mediana_media || 0.0;
        const devStdMedia = info.dev_std_media || 0.0;

        // Applicazione dei filtri come limiti inferiori
        if (medianaMedia >= parseFloat(minMediana) && devStdMedia >= parseFloat(minDev)) {
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
