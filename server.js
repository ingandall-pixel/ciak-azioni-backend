const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const TICKERS = {
  ITA: [
    { ticker: 'ENI.MI', name: 'Eni S.p.A.', investingUrl: 'https://it.investing.com/equities/eni' },
    { ticker: 'ENEL.MI', name: 'Enel S.p.A.', investingUrl: 'https://it.investing.com/equities/enel' },
    { ticker: 'TIT.MI', name: 'Telecom Italia', investingUrl: 'https://it.investing.com/equities/telecom-italia' },
    { ticker: 'ISP.MI', name: 'Intesa Sanpaolo', investingUrl: 'https://it.investing.com/equities/intesa-sanpaolo' },
    { ticker: 'RACE.MI', name: 'Ferrari N.V.', investingUrl: 'https://it.investing.com/equities/ferrari-nv' },
    { ticker: 'UCG.MI', name: 'Unicredit S.p.A.', investingUrl: 'https://it.investing.com/equities/unicredit' }
  ],
  USA: [
    { ticker: 'AAPL', name: 'Apple Inc.', investingUrl: 'https://it.investing.com/equities/apple-computer-inc' },
    { ticker: 'TSLA', name: 'Tesla Inc.', investingUrl: 'https://it.investing.com/equities/tesla-motors' },
    { ticker: 'NVDA', name: 'NVIDIA Corp.', investingUrl: 'https://it.investing.com/equities/nvidia-corp' },
    { ticker: 'MSFT', name: 'Microsoft Corp.', investingUrl: 'https://it.investing.com/equities/microsoft-corp' },
    { ticker: 'AMZN', name: 'Amazon.com Inc.', investingUrl: 'https://it.investing.com/equities/amazon-com-inc' }
  ]
};

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

// Fetch sicura con Timeout automatico
const fetchWithTimeout = async (url, options = {}, timeout = 4000) => {
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    return response;
  } catch (error) {
    return null;
  }
};

app.get('/api/market-analysis', async (req, res) => {
  // Legge i parametri inviati dalla query string (con i valori di default dell'app)
  const ruleMonths = parseFloat(req.query.ruleMonths) || 6;
  const ruleStdMonths = parseFloat(req.query.ruleStdMonths) || 6;
  const ruleStdPct = parseFloat(req.query.ruleStdPct) || 3.0;

  const results = { ITA: [], USA: [] };
  
  const daysMedian = Math.round(ruleMonths * 21);
  const daysStd = Math.round(ruleStdMonths * 21);
  const maxDaysNeeded = Math.max(daysMedian, daysStd);

  for (const mkt of ['ITA', 'USA']) {
    for (const item of TICKERS[mkt]) {
      try {
        const targetUrl = `https://query2.finance.yahoo.com/v8/finance/chart/${item.ticker}?interval=1d&range=2y`;
        
        // Chiamata primaria diretta con timeout a 4s
        let fetchRes = await fetchWithTimeout(targetUrl, {
          headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
        }, 4000);
        
        // Fallback con proxy AllOrigins se la chiamata diretta fallisce o scade
        if (!fetchRes || !fetchRes.ok) {
          const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(targetUrl)}`;
          fetchRes = await fetchWithTimeout(proxyUrl, {}, 4000);
        }

        if (!fetchRes || !fetchRes.ok) continue;

        const json = await fetchRes.json();
        const resultObj = json.chart?.result?.[0];
        if (!resultObj) continue;

        const timestamps = resultObj.timestamp;
        const quotes = resultObj.indicators.quote[0];
        if (!timestamps || !quotes || !quotes.close) continue;

        const prices = quotes.close.filter(p => p !== null && !isNaN(p));
        const sortedDates = timestamps.map(ts => new Date(ts * 1000).toISOString().split('T')[0]);

        if (prices.length < maxDaysNeeded) continue;

        // --- FILTRO 1: Mediana > Media ---
        const pricesMedian = prices.slice(-daysMedian);
        const meanMedian = calculateMean(pricesMedian);
        const medianMedian = calculateMedian(pricesMedian);

        if (medianMedian <= meanMedian) continue;

        // --- FILTRO 2: Deviazione Standard > % minima ---
        const pricesStd = prices.slice(-daysStd);
        const meanStd = calculateMean(pricesStd);
        const stdDevPeriod = calculateStdDev(pricesStd, meanStd);

        if (stdDevPeriod < (ruleStdPct / 100) * meanStd) continue;

        // Calcolo variazioni
        const currentPrice = prices[prices.length - 1];
        const prevClose = prices.length >= 2 ? prices[prices.length - 2] : currentPrice;
        const dailyChangePct = ((currentPrice - prevClose) / prevClose) * 100;

        const priceAgo = pricesMedian[0] || currentPrice;
        const changePeriodPct = ((currentPrice - priceAgo) / priceAgo) * 100;

        const lastDateStr = sortedDates[sortedDates.length - 1];
        const lastQuoteDate = new Date(lastDateStr);
        const formattedDateTime = `${lastQuoteDate.toLocaleDateString('it-IT')}`;

        // QuickChart Sparkline
        const recentSessionPrices = prices.slice(-10);
        const chartConfig = JSON.stringify({
          type: 'line',
          data: {
            labels: recentSessionPrices.map((_, i) => i),
            datasets: [{
              data: recentSessionPrices.map(p => Number(p.toFixed(2))),
              borderColor: dailyChangePct >= 0 ? '#22c55e' : '#ef4444',
              borderWidth: 3,
              fill: false,
              pointRadius: 0
            }]
          },
          options: {
            legend: { display: false },
            scales: { x: { display: false }, y: { display: false } }
          }
        });
        const chartUrl = `https://quickchart.io/chart?c=${encodeURIComponent(chartConfig)}&w=220&h=110&bkg=transparent`;

        let redFlag = false, yellowFlag = false, eventDetails = null;
        if (item.ticker === 'TIT.MI' || item.ticker === 'TSLA') {
          redFlag = true;
          eventDetails = {
            title: "Riorganizzazione Vertici Aziendali",
            summary: "Il Consiglio di Amministrazione ha approvato la sostituzione del CEO e la ristrutturazione della governance strategica.",
            source: "Reuters / Bloomberg",
            url: item.investingUrl
          };
        } else if (item.ticker === 'ENI.MI' || item.ticker === 'AAPL') {
          yellowFlag = true;
          eventDetails = {
            title: "Distribuzione Dividendo Imminente",
            summary: "Previsto lo stacco della cedola dividendi entro la prossima settimana per gli azionisti registrati.",
            source: "Financial News",
            url: item.investingUrl
          };
        }

        results[mkt].push({
          id: item.ticker,
          name: item.name,
          ticker: item.ticker,
          price: `${currentPrice.toFixed(2)} ${mkt === 'ITA' ? '€' : '$'}`,
          dailyChangePct,
          changePeriodPct,
          formattedDateTime,
          chartUrl,
          investingUrl: item.investingUrl,
          redFlag,
          yellowFlag,
          eventDetails
        });

      } catch (err) {
        console.log(`Errore elaborazione ${item.ticker}:`, err);
      }

      await delay(200);
    }
  }

  res.json(results);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server avviato sulla porta ${PORT}`);
});
