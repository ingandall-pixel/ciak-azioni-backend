const express = require('express');
const cors = require('cors');
const cron = require('node-cron');

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;

// INTEREZZA DEL MERCATO ITALIANO (Tutti i principali titoli di Piazza Affari)
const ITA_TICKERS = [
  { ticker: 'A2A.MI', name: 'A2A S.p.A.', investingUrl: 'https://it.investing.com/equities/a2a' },
  { ticker: 'AMP.MI', name: 'Amplifon S.p.A.', investingUrl: 'https://it.investing.com/equities/amplifon' },
  { ticker: 'ANL.MI', name: 'Alkemy S.p.A.', investingUrl: 'https://it.investing.com/equities/alkemy' },
  { ticker: 'ARIS.MI', name: 'Ariston Holding N.V.', investingUrl: 'https://it.investing.com/equities/ariston-holding-nv' },
  { ticker: 'AZM.MI', name: 'Azimut Holding S.p.A.', investingUrl: 'https://it.investing.com/equities/azimut-holding' },
  { ticker: 'BGN.MI', name: 'Banca Generali S.p.A.', investingUrl: 'https://it.investing.com/equities/banca-generali' },
  { ticker: 'BMED.MI', name: 'Banca Mediolanum S.p.A.', investingUrl: 'https://it.investing.com/equities/banca-mediolanum' },
  { ticker: 'BPE.MI', name: 'BPER Banca S.p.A.', investingUrl: 'https://it.investing.com/equities/banca-popolare-dell-emilia-romagna' },
  { ticker: 'BMPS.MI', name: 'Banca Monte dei Paschi di Siena', investingUrl: 'https://it.investing.com/equities/banca-monte-de-paschi-di-siena' },
  { ticker: 'BAMI.MI', name: 'Banco BPM S.p.A.', investingUrl: 'https://it.investing.com/equities/banco-bpm' },
  { ticker: 'BZU.MI', name: 'Buzzi Unicem S.p.A.', investingUrl: 'https://it.investing.com/equities/buzzi-unicem' },
  { ticker: 'CPR.MI', name: 'Davide Campari-Milano N.V.', investingUrl: 'https://it.investing.com/equities/davide-campari-milano' },
  { ticker: 'DIA.MI', name: 'Diasorin S.p.A.', investingUrl: 'https://it.investing.com/equities/diasorin' },
  { ticker: 'ENEL.MI', name: 'Enel S.p.A.', investingUrl: 'https://it.investing.com/equities/enel' },
  { ticker: 'ENI.MI', name: 'Eni S.p.A.', investingUrl: 'https://it.investing.com/equities/eni' },
  { ticker: 'ERG.MI', name: 'ERG S.p.A.', investingUrl: 'https://it.investing.com/equities/erg' },
  { ticker: 'EXO.MI', name: 'Exor N.V.', investingUrl: 'https://it.investing.com/equities/exor' },
  { ticker: 'RACE.MI', name: 'Ferrari N.V.', investingUrl: 'https://it.investing.com/equities/ferrari-nv' },
  { ticker: 'FNM.MI', name: 'FinecoBank S.p.A.', investingUrl: 'https://it.investing.com/equities/finecobank' },
  { ticker: 'G.MI', name: 'Assicurazioni Generali S.p.A.', investingUrl: 'https://it.investing.com/equities/generali' },
  { ticker: 'HER.MI', name: 'Hera S.p.A.', investingUrl: 'https://it.investing.com/equities/hera' },
  { ticker: 'ISP.MI', name: 'Intesa Sanpaolo S.p.A.', investingUrl: 'https://it.investing.com/equities/intesa-sanpaolo' },
  { ticker: 'IG.MI', name: 'Italgas S.p.A.', investingUrl: 'https://it.investing.com/equities/italgas' },
  { ticker: 'LION.MI', name: 'Leonardo S.p.A.', investingUrl: 'https://it.investing.com/equities/finmeccanica' },
  { ticker: 'MB.MI', name: 'Mediobanca S.p.A.', investingUrl: 'https://it.investing.com/equities/mediobanca' },
  { ticker: 'MIRC.MI', name: 'Maire Tecnimont S.p.A.', investingUrl: 'https://it.investing.com/equities/maire-tecnimont' },
  { ticker: 'MONC.MI', name: 'Moncler S.p.A.', investingUrl: 'https://it.investing.com/equities/moncler' },
  { ticker: 'NEXI.MI', name: 'Nexi S.p.A.', investingUrl: 'https://it.investing.com/equities/nexi-spa' },
  { ticker: 'PRY.MI', name: 'Prysmian S.p.A.', investingUrl: 'https://it.investing.com/equities/prysmian' },
  { ticker: 'REC.MI', name: 'Recordati S.p.A.', investingUrl: 'https://it.investing.com/equities/recordati' },
  { ticker: 'SFER.MI', name: 'Salvatore Ferragamo S.p.A.', investingUrl: 'https://it.investing.com/equities/salvatore-ferragamo' },
  { ticker: 'SPM.MI', name: 'Saipem S.p.A.', investingUrl: 'https://it.investing.com/equities/saipem' },
  { ticker: 'SRG.MI', name: 'Snam S.p.A.', investingUrl: 'https://it.investing.com/equities/snam' },
  { ticker: 'STLAM.MI', name: 'Stellantis N.V.', investingUrl: 'https://it.investing.com/equities/stellantis-nv' },
  { ticker: 'STMMI.MI', name: 'STMicroelectronics N.V.', investingUrl: 'https://it.investing.com/equities/stmicroelectronics' },
  { ticker: 'TIT.MI', name: 'Telecom Italia S.p.A.', investingUrl: 'https://it.investing.com/equities/telecom-italia' },
  { ticker: 'TEN.MI', name: 'Tenaris S.A.', investingUrl: 'https://it.investing.com/equities/tenaris' },
  { ticker: 'TRN.MI', name: 'Terna S.p.A.', investingUrl: 'https://it.investing.com/equities/terna' },
  { ticker: 'UCG.MI', name: 'Unicredit S.p.A.', investingUrl: 'https://it.investing.com/equities/unicredit' },
  { ticker: 'UNI.MI', name: 'Unipol Gruppo S.p.A.', investingUrl: 'https://it.investing.com/equities/unipol' },
  { ticker: 'IP.MI', name: 'Gruppo API IP', investingUrl: 'https://it.investing.com/equities/gruppo-api' },
  { ticker: 'MAR.MI', name: 'Marr S.p.A.', investingUrl: 'https://it.investing.com/equities/marr' },
  { ticker: 'SAMI.MI', name: 'Safilo Group S.p.A.', investingUrl: 'https://it.investing.com/equities/safilo-group' },
  { ticker: 'TOS.MI', name: 'Toscana Aeroporti S.p.A.', investingUrl: 'https://it.investing.com/equities/toscana-aeroporti' },
  { ticker: 'BFF.MI', name: 'BFF Bank S.p.A.', investingUrl: 'https://it.investing.com/equities/bff-bank-spa' }
];

let cachedMarketData = { ITA: [], USA: [], lastUpdate: 'Non ancora eseguito' };

// Funzione per prelevare AUTOMATICAMENTE L'INTEREZZA del mercato USA (migliaia di ticker da NYSE e NASDAQ)
async function getAllUSStocks() {
  try {
    const response = await fetch('https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.json');
    if (response.ok) {
      const symbols = await response.json();
      return symbols.map(s => {
        const ticker = typeof s === 'string' ? s : (s.symbol || s.ticker);
        // Filtra simboli anomali o con caratteri speciali non validi per le API
        if (!ticker || ticker.includes('.')) return null;
        return {
          ticker: ticker.toUpperCase(),
          name: ticker.toUpperCase(),
          investingUrl: `https://it.investing.com/search/?q=${ticker}`
        };
      }).filter(Boolean);
    }
  } catch (e) {
    console.error("Errore recupero listino USA completo:", e);
  }
  return [];
}

// Formule matematiche
const calculateMean = (arr) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
const calculateMedian = (arr) => {
  if (!arr.length) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};
const calculateStdDev = (arr, mean) => {
  if (!arr.length) return 0;
  const variance = arr.reduce((sq, val) => sq + Math.pow(val - mean, 2), 0) / arr.length;
  return Math.sqrt(variance);
};
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runMarketAnalysis(ruleMonths = 6, ruleStdMonths = 6, ruleStdPct = 3.0) {
  const results = { ITA: [], USA: [], lastUpdate: new Date().toLocaleString('it-IT') };
  const daysMedian = ruleMonths * 21;
  const daysStd = ruleStdMonths * 21;

  // 1. Analisi Mercato Italiano
  for (let i = 0; i < ITA_TICKERS.length; i += 5) {
    const batch = ITA_TICKERS.slice(i, i + 5);
    await Promise.all(batch.map(async (item) => {
      try {
        const url = `https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=2y`;
        const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
        if (!response.ok) return;

        const json = await response.json();
        const resultObj = json.chart?.result?.[0];
        if (!resultObj) return;

        const timestamps = resultObj.timestamp;
        const quotes = resultObj.indicators.quote[0];
        if (!timestamps || !quotes || !quotes.close) return;

        const prices = quotes.close.filter(p => p !== null && !isNaN(p));
        if (prices.length < Math.max(daysMedian, daysStd)) return;

        const pricesMedian = prices.slice(-daysMedian);
        const meanMed = calculateMean(pricesMedian);
        const medMed = calculateMedian(pricesMedian);
        if (medMed <= meanMed) return;

        const pricesStd = prices.slice(-daysStd);
        const meanStd = calculateMean(pricesStd);
        const stdDev = calculateStdDev(pricesStd, meanStd);
        if (stdDev < (ruleStdPct / 100) * meanStd) return;

        const currentPrice = prices[prices.length - 1];
        const prevClose = prices.length >= 2 ? prices[prices.length - 2] : currentPrice;
        const dailyChangePct = ((currentPrice - prevClose) / prevClose) * 100;
        const priceAgo = pricesMedian[0] || currentPrice;
        const changePeriodPct = ((currentPrice - priceAgo) / priceAgo) * 100;

        const recentPrices = prices.slice(-10);
        const chartConfig = JSON.stringify({
          type: 'line',
          data: {
            labels: recentPrices.map((_, idx) => idx),
            datasets: [{
              data: recentPrices.map(p => Number(p.toFixed(2))),
              borderColor: dailyChangePct >= 0 ? '#22c55e' : '#ef4444',
              borderWidth: 3, fill: false, pointRadius: 0
            }]
          },
          options: { legend: { display: false }, scales: { x: { display: false }, y: { display: false } } }
        });
        const chartUrl = `https://quickchart.io/chart?c=${encodeURIComponent(chartConfig)}&w=220&h=110&bkg=transparent`;

        results.ITA.push({
          id: item.ticker,
          name: item.name,
          ticker: item.ticker,
          price: `${currentPrice.toFixed(2)} €`,
          dailyChangePct,
          changePeriodPct,
          formattedDateTime: new Date(timestamps[timestamps.length - 1] * 1000).toLocaleDateString('it-IT'),
          chartUrl,
          investingUrl: item.investingUrl
        });
      } catch (e) {}
    }));
    await delay(100);
  }

  // 2. Analisi Interezza Mercato USA (Tutti i ticker scaricati dinamicamente)
  const US_TICKERS = await getAllUSStocks();
  console.log(`📊 Avvio scansione intero mercato USA: ${US_TICKERS.length} azioni trovate.`);

  for (let i = 0; i < US_TICKERS.length; i += 10) {
    const batch = US_TICKERS.slice(i, i + 10);
    await Promise.all(batch.map(async (item) => {
      try {
        const url = `https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=2y`;
        const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
        if (!response.ok) return;

        const json = await response.json();
        const resultObj = json.chart?.result?.[0];
        if (!resultObj) return;

        const timestamps = resultObj.timestamp;
        const quotes = resultObj.indicators.quote[0];
        if (!timestamps || !quotes || !quotes.close) return;

        const prices = quotes.close.filter(p => p !== null && !isNaN(p));
        if (prices.length < Math.max(daysMedian, daysStd)) return;

        const pricesMedian = prices.slice(-daysMedian);
        const meanMed = calculateMean(pricesMedian);
        const medMed = calculateMedian(pricesMedian);
        if (medMed <= meanMed) return;

        const pricesStd = prices.slice(-daysStd);
        const meanStd = calculateMean(pricesStd);
        const stdDev = calculateStdDev(pricesStd, meanStd);
        if (stdDev < (ruleStdPct / 100) * meanStd) return;

        const currentPrice = prices[prices.length - 1];
        const prevClose = prices.length >= 2 ? prices[prices.length - 2] : currentPrice;
        const dailyChangePct = ((currentPrice - prevClose) / prevClose) * 100;
        const priceAgo = pricesMedian[0] || currentPrice;
        const changePeriodPct = ((currentPrice - priceAgo) / priceAgo) * 100;

        const recentPrices = prices.slice(-10);
        const chartConfig = JSON.stringify({
          type: 'line',
          data: {
            labels: recentPrices.map((_, idx) => idx),
            datasets: [{
              data: recentPrices.map(p => Number(p.toFixed(2))),
              borderColor: dailyChangePct >= 0 ? '#22c55e' : '#ef4444',
              borderWidth: 3, fill: false, pointRadius: 0
            }]
          },
          options: { legend: { display: false }, scales: { x: { display: false }, y: { display: false } } }
        });
        const chartUrl = `https://quickchart.io/chart?c=${encodeURIComponent(chartConfig)}&w=220&h=110&bkg=transparent`;

        results.USA.push({
          id: item.ticker,
          name: item.name,
          ticker: item.ticker,
          price: `${currentPrice.toFixed(2)} $`,
          dailyChangePct,
          changePeriodPct,
          formattedDateTime: new Date(timestamps[timestamps.length - 1] * 1000).toLocaleDateString('it-IT'),
          chartUrl,
          investingUrl: item.investingUrl
        });
      } catch (e) {}
    }));
    await delay(150);
  }

  return results;
}

// Schedulazione automatica alle 05:00 del mattino
cron.schedule('0 5 * * *', async () => {
  console.log('⏰ [CRON] Avvio analisi automatica globale dei mercati...');
  try {
    cachedMarketData = await runMarketAnalysis();
    console.log('✅ [CRON] Analisi globale completata con successo!');
  } catch (err) {
    console.error('❌ [CRON] Errore:', err);
  }
}, {
  scheduled: true,
  timezone: "Europe/Rome"
});

app.get('/api/market-analysis', async (req, res) => {
  const ruleMonths = parseInt(req.query.ruleMonths) || 6;
  const ruleStdMonths = parseInt(req.query.ruleStdMonths) || 6;
  const ruleStdPct = parseFloat(req.query.ruleStdPct) || 3.0;

  if (ruleMonths === 6 && ruleStdMonths === 6 && ruleStdPct === 3.0 && cachedMarketData.ITA.length > 0) {
    return res.json(cachedMarketData);
  }

  const results = await runMarketAnalysis(ruleMonths, ruleStdMonths, ruleStdPct);
  res.json(results);
});

app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CIAK! AZIONI 🖕</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
            .container { max-width: 850px; margin: 0 auto; }
            h1 { text-align: center; font-style: italic; color: #f8fafc; letter-spacing: 1px; }
            .controls { background: #1e293b; padding: 15px; border-radius: 12px; margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px; align-items: center; justify-content: space-between; border: 1px solid #334155; }
            .control-group { display: flex; flex-direction: column; font-size: 13px; color: #94a3b8; }
            .control-group input, .control-group select { background: #0f172a; color: #fff; border: 1px solid #475569; padding: 6px 10px; border-radius: 6px; margin-top: 4px; }
            button.btn-run { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; height: 38px; align-self: flex-end; }
            button.btn-run:hover { background: #1d4ed8; }
            .tabs { display: flex; gap: 10px; margin-bottom: 15px; justify-content: center; }
            .tab { padding: 10px 20px; background: #1e293b; color: #94a3b8; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; }
            .tab.active { background: #2563eb; color: #ffffff; }
            .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 15px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: inherit; transition: 0.2s; }
            .card:hover { border-color: #38bdf8; }
            .ticker { font-size: 18px; font-weight: bold; color: #fff; }
            .name { font-size: 12px; color: #94a3b8; }
            .price { font-size: 16px; font-weight: bold; text-align: right; }
            .green { color: #22c55e; }
            .red { color: #ef4444; }
            .metric { font-size: 12px; color: #94a3b8; text-align: right; }
            .loading { text-align: center; color: #38bdf8; font-size: 18px; margin-top: 40px; }
            img { width: 110px; height: 50px; background: transparent; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CIAK! AZIONI 🖕</h1>
            
            <div class="controls">
                <div class="control-group">
                    <label>Mesi Mediana:</label>
                    <input type="number" id="ruleMonths" value="6" style="width: 60px;">
                </div>
                <div class="control-group">
                    <label>Mesi Std Dev:</label>
                    <input type="number" id="ruleStdMonths" value="6" style="width: 60px;">
                </div>
                <div class="control-group">
                    <label>Min Std Dev %:</label>
                    <input type="number" step="0.5" id="ruleStdPct" value="3.0" style="width: 60px;">
                </div>
                <div class="control-group">
                    <label>Ordina per:</label>
                    <select id="sortBy" onchange="render()">
                        <option value="period">Performance Periodo</option>
                        <option value="daily">Variazione Giornaliera</option>
                        <option value="name">Nome Azione</option>
                    </select>
                </div>
                <button class="btn-run" onclick="loadData()">Avvia Analisi</button>
            </div>

            <div class="tabs">
                <button class="tab active" id="btn-ITA" onclick="switchMarket('ITA')">🇮🇹 ITA</button>
                <button class="tab" id="btn-USA" onclick="switchMarket('USA')">🇺🇸 USA</button>
            </div>

            <div id="content" class="loading">Clicca su "Avvia Analisi" per scansionare l'interezza dei mercati.</div>
        </div>

        <script>
            let globalData = { ITA: [], USA: [] };
            let currentMarket = 'ITA';

            async function loadData() {
                const months = document.getElementById('ruleMonths').value;
                const stdMonths = document.getElementById('ruleStdMonths').value;
                const stdPct = document.getElementById('ruleStdPct').value;

                document.getElementById('content').innerHTML = '<div class="loading">Analisi globale in corso (migliaia di azioni USA e ITA)... Potrebbe richiedere qualche minuto ⏳</div>';

                try {
                    const res = await fetch(\`/api/market-analysis?ruleMonths=\${months}&ruleStdMonths=\${stdMonths}&ruleStdPct=\${stdPct}\`);
                    globalData = await res.json();
                    render();
                } catch(e) {
                    document.getElementById('content').innerHTML = '<div class="loading" style="color:red;">Errore durante la comunicazione con il server.</div>';
                }
            }

            function switchMarket(mkt) {
                currentMarket = mkt;
                document.getElementById('btn-ITA').classList.toggle('active', mkt === 'ITA');
                document.getElementById('btn-USA').classList.toggle('active', mkt === 'USA');
                render();
            }

            function render() {
                let list = [...(globalData[currentMarket] || [])];
                const sortBy = document.getElementById('sortBy').value;

                list.sort((a, b) => {
                    if (sortBy === 'period') return b.changePeriodPct - a.changePeriodPct;
                    if (sortBy === 'daily') return b.dailyChangePct - a.dailyChangePct;
                    if (sortBy === 'name') return a.name.localeCompare(b.name);
                });

                const container = document.getElementById('content');
                
                if(list.length === 0) {
                    container.innerHTML = '<div class="loading">Nessuna azione soddisfa i criteri attuali.</div>';
                    return;
                }

                container.innerHTML = list.map(item => \`
                    <a href="\${item.investingUrl}" target="_blank" class="card">
                        <div>
                            <div class="ticker">\${item.ticker}</div>
                            <div class="name">\${item.name}</div>
                        </div>
                        <div>
                            <img src="\${item.chartUrl}" alt="Grafico">
                        </div>
                        <div>
                            <div class="price">\${item.price}</div>
                            <div class="metric">Periodo: <span class="\${item.changePeriodPct >= 0 ? 'green' : 'red'}">\${item.changePeriodPct >= 0 ? '+' : ''}\${item.changePeriodPct.toFixed(2)}%</span></div>
                            <div class="metric">Giornaliero: <span class="\${item.dailyChangePct >= 0 ? 'green' : 'red'}">\${item.dailyChangePct >= 0 ? '+' : ''}\${item.dailyChangePct.toFixed(2)}%</span></div>
                        </div>
                    </a>
                \`).join('');
            }

            loadData();
        </script>
    </body>
    </html>
  `);
});

app.listen(PORT, () => {
  console.log(`Server avviato sulla porta ${PORT}`);
});
