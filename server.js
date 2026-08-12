const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;

// Memoria temporanea (RAM) del server
let marketCache = {
  ITA: [],
  USA: [],
  lastUpdate: null
};

// LISTINO AZIONARIO
const TICKERS = {
  ITA: [
    { ticker: 'ENI.MI', name: 'Eni S.p.A.', investingUrl: 'https://it.investing.com/equities/eni' },
    { ticker: 'ENEL.MI', name: 'Enel S.p.A.', investingUrl: 'https://it.investing.com/equities/enel' },
    { ticker: 'TIT.MI', name: 'Telecom Italia', investingUrl: 'https://it.investing.com/equities/telecom-italia' },
    { ticker: 'ISP.MI', name: 'Intesa Sanpaolo', investingUrl: 'https://it.investing.com/equities/intesa-sanpaolo' },
    { ticker: 'RACE.MI', name: 'Ferrari N.V.', investingUrl: 'https://it.investing.com/equities/ferrari-nv' },
    { ticker: 'UCG.MI', name: 'Unicredit S.p.A.', investingUrl: 'https://it.investing.com/equities/unicredit' },
    { ticker: 'BPE.MI', name: 'BPER Banca', investingUrl: 'https://it.investing.com/equities/banca-popolare-dell-emilia-romagna' },
    { ticker: 'BMPS.MI', name: 'Banca Monte dei Paschi', investingUrl: 'https://it.investing.com/equities/banca-monte-dei-paschi-di-siena' },
    { ticker: 'STMMI.MI', name: 'STMicroelectronics', investingUrl: 'https://it.investing.com/equities/stmicroelectronics' },
    { ticker: 'TRN.MI', name: 'Terna S.p.A.', investingUrl: 'https://it.investing.com/equities/terna' },
    { ticker: 'PRY.MI', name: 'Prysmian S.p.A.', investingUrl: 'https://it.investing.com/equities/prysmian' },
    { ticker: 'MONC.MI', name: 'Moncler S.p.A.', investingUrl: 'https://it.investing.com/equities/moncler' },
    { ticker: 'G.MI', name: 'Assicurazioni Generali', investingUrl: 'https://it.investing.com/equities/generali' },
    { ticker: 'TEN.MI', name: 'Tenaris S.A.', investingUrl: 'https://it.investing.com/equities/tenaris' },
    { ticker: 'SRG.MI', name: 'Snam S.p.A.', investingUrl: 'https://it.investing.com/equities/snam' }
  ],
  USA: [
    { ticker: 'AAPL', name: 'Apple Inc.', investingUrl: 'https://it.investing.com/equities/apple-computer-inc' },
    { ticker: 'TSLA', name: 'Tesla Inc.', investingUrl: 'https://it.investing.com/equities/tesla-motors' },
    { ticker: 'NVDA', name: 'NVIDIA Corp.', investingUrl: 'https://it.investing.com/equities/nvidia-corp' },
    { ticker: 'MSFT', name: 'Microsoft Corp.', investingUrl: 'https://it.investing.com/equities/microsoft-corp' },
    { ticker: 'AMZN', name: 'Amazon.com Inc.', investingUrl: 'https://it.investing.com/equities/amazon-com-inc' },
    { ticker: 'GOOGL', name: 'Alphabet Inc.', investingUrl: 'https://it.investing.com/equities/google-inc' },
    { ticker: 'META', name: 'Meta Platforms', investingUrl: 'https://it.investing.com/equities/facebook-inc' },
    { ticker: 'AVGO', name: 'Broadcom Inc.', investingUrl: 'https://it.investing.com/equities/avago-technologies' },
    { ticker: 'JPM', name: 'JPMorgan Chase', investingUrl: 'https://it.investing.com/equities/jp-morgan-chase' },
    { ticker: 'AMD', name: 'Advanced Micro Devices', investingUrl: 'https://it.investing.com/equities/adv-micro-device' }
  ]
};

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

let isAnalyzing = false;

// Funzione di scansione
async function executeMassiveAnalysis() {
  if (isAnalyzing) return;
  isAnalyzing = true;
  console.log(`[${new Date().toISOString()}] Avvio scansione mercati...`);

  const results = { ITA: [], USA: [], lastUpdate: new Date().toLocaleString('it-IT') };
  const daysMedian = 6 * 21;
  const daysStd = 6 * 21;
  const minStdDevPct = 3.0;

  for (const mkt of ['ITA', 'USA']) {
    const list = TICKERS[mkt];
    
    for (let i = 0; i < list.length; i += 5) {
      const batch = list.slice(i, i + 5);

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

          // REGOLA 1: Mediana > Media
          const pricesMedian = prices.slice(-daysMedian);
          const meanMed = calculateMean(pricesMedian);
          const medMed = calculateMedian(pricesMedian);
          if (medMed <= meanMed) return;

          // REGOLA 2: Deviazione Standard > 3%
          const pricesStd = prices.slice(-daysStd);
          const meanStd = calculateMean(pricesStd);
          const stdDev = calculateStdDev(pricesStd, meanStd);
          if (stdDev < (minStdDevPct / 100) * meanStd) return;

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

          results[mkt].push({
            id: item.ticker,
            name: item.name,
            ticker: item.ticker,
            price: `${currentPrice.toFixed(2)} ${mkt === 'ITA' ? '€' : '$'}`,
            dailyChangePct,
            changePeriodPct,
            formattedDateTime: new Date(timestamps[timestamps.length - 1] * 1000).toLocaleDateString('it-IT'),
            chartUrl,
            investingUrl: item.investingUrl
          });
        } catch (e) {}
      }));

      await delay(400);
    }
  }

  marketCache = results;
  isAnalyzing = false;
  console.log(`[${new Date().toISOString()}] Scansione completata con successo!`);
}

// ROUTE BASE DI BENVENUTO
app.get('/', (req, res) => {
  res.send('Server CIAK Azioni è attivo e funzionante!');
});

// ROUTE 1: L'App chiama questa porta per scaricare i dati pronti
app.get('/api/market-data', (req, res) => {
  if (!marketCache.lastUpdate && !isAnalyzing) {
    executeMassiveAnalysis();
    return res.status(202).json({ message: 'Analisi in corso... Riprova tra pochi secondi.' });
  }
  return res.json(marketCache);
});

// ROUTE 2: Il timer delle 05:00 AM chiama questa porta per far partire la scansione
app.get('/api/trigger-analysis', async (req, res) => {
  res.json({ message: 'Scansione avviata in background!' });
  executeMassiveAnalysis();
});

app.listen(PORT, () => {
  console.log(`Server avviato sulla porta ${PORT}`);
  executeMassiveAnalysis();
});
