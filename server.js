const express = require('express');
const cors = require('cors');
const cron = require('node-cron');

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;

// API Key opzionale per Twelve Data (prezzo realtime sulle finaliste)
const TWELVE_DATA_API_KEY = process.env.TWELVE_DATA_API_KEY || '';

// 🇮🇹 LISTINO MERCATO ITALIANO (Esteso + Slug specifici per Investing.com)
const ITA_TICKERS = [
  { ticker: 'A2A.MI', name: 'A2A S.p.A.', slug: 'a2a' },
  { ticker: 'AMP.MI', name: 'Amplifon S.p.A.', slug: 'amplifon' },
  { ticker: 'ANL.MI', name: 'Alkemy S.p.A.', slug: 'alkemy-spa' },
  { ticker: 'ARIS.MI', name: 'Ariston Holding N.V.', slug: 'ariston-holding' },
  { ticker: 'AZM.MI', name: 'Azimut Holding S.p.A.', slug: 'azimut' },
  { ticker: 'BGN.MI', name: 'Banca Generali S.p.A.', slug: 'bca-generali' },
  { ticker: 'BMED.MI', name: 'Banca Mediolanum S.p.A.', slug: 'bca-mediolanum' },
  { ticker: 'BPE.MI', name: 'BPER Banca S.p.A.', slug: 'bper-banca' },
  { ticker: 'BMPS.MI', name: 'Banca Monte dei Paschi di Siena', slug: 'bca-paschi-siena' },
  { ticker: 'BAMI.MI', name: 'Banco BPM S.p.A.', slug: 'banco-bpm-spa' },
  { ticker: 'BZU.MI', name: 'Buzzi Unicem S.p.A.', slug: 'buzzi-unicem' },
  { ticker: 'CPR.MI', name: 'Davide Campari-Milano N.V.', slug: 'campari' },
  { ticker: 'DIA.MI', name: 'Diasorin S.p.A.', slug: 'diasorin' },
  { ticker: 'ENEL.MI', name: 'Enel S.p.A.', slug: 'enel' },
  { ticker: 'ENI.MI', name: 'Eni S.p.A.', slug: 'eni' },
  { ticker: 'ERG.MI', name: 'ERG S.p.A.', slug: 'erg' },
  { ticker: 'EXO.MI', name: 'Exor N.V.', slug: 'exor-holding' },
  { ticker: 'RACE.MI', name: 'Ferrari N.V.', slug: 'ferrari-nv' },
  { ticker: 'FNM.MI', name: 'FinecoBank S.p.A.', slug: 'finecobank' },
  { ticker: 'G.MI', name: 'Assicurazioni Generali S.p.A.', slug: 'generali' },
  { ticker: 'HER.MI', name: 'Hera S.p.A.', slug: 'hera' },
  { ticker: 'ISP.MI', name: 'Intesa Sanpaolo S.p.A.', slug: 'intesa-sanpaolo' },
  { ticker: 'IG.MI', name: 'Italgas S.p.A.', slug: 'italgas-spa' },
  { ticker: 'LION.MI', name: 'Leonardo S.p.A.', slug: 'finmeccanica' },
  { ticker: 'MB.MI', name: 'Mediobanca S.p.A.', slug: 'mediobanca' },
  { ticker: 'MIRC.MI', name: 'Maire Tecnimont S.p.A.', slug: 'maire-tecnimont' },
  { ticker: 'MONC.MI', name: 'Moncler S.p.A.', slug: 'moncler' },
  { ticker: 'NEXI.MI', name: 'Nexi S.p.A.', slug: 'nexi-spa' },
  { ticker: 'PRY.MI', name: 'Prysmian S.p.A.', slug: 'prysmian' },
  { ticker: 'REC.MI', name: 'Recordati S.p.A.', slug: 'recordati' },
  { ticker: 'SFER.MI', name: 'Salvatore Ferragamo S.p.A.', slug: 'salvatore-ferragamo' },
  { ticker: 'SPM.MI', name: 'Saipem S.p.A.', slug: 'saipem' },
  { ticker: 'SRG.MI', name: 'Snam S.p.A.', slug: 'snam' },
  { ticker: 'STLAM.MI', name: 'Stellantis N.V.', slug: 'stellantis-nv' },
  { ticker: 'STMMI.MI', name: 'STMicroelectronics N.V.', slug: 'stmicroelectronics' },
  { ticker: 'TIT.MI', name: 'Telecom Italia S.p.A.', slug: 'telecom-italia' },
  { ticker: 'TEN.MI', name: 'Tenaris S.A.', slug: 'tenaris' },
  { ticker: 'TRN.MI', name: 'Terna S.p.A.', slug: 'terna' },
  { ticker: 'UCG.MI', name: 'Unicredit S.p.A.', slug: 'unicredit' },
  { ticker: 'UNI.MI', name: 'Unipol Gruppo S.p.A.', slug: 'unipol' },
  { ticker: 'IP.MI', name: 'Gruppo API IP', slug: 'interpump-group' },
  { ticker: 'MAR.MI', name: 'Marr S.p.A.', slug: 'marr' },
  { ticker: 'SAMI.MI', name: 'Safilo Group S.p.A.', slug: 'safilo-group' },
  { ticker: 'TOS.MI', name: 'Toscana Aeroporti S.p.A.', slug: 'toscana-aeroporti' },
  { ticker: 'BFF.MI', name: 'BFF Bank S.p.A.', slug: 'bff-bank-spa' },
  { ticker: 'ACE.MI', name: 'Acea S.p.A.', slug: 'acea' },
  { ticker: 'ANIM.MI', name: 'Anima Holding', slug: 'anima-holding' },
  { ticker: 'BRC.MI', name: 'Brembo S.p.A.', slug: 'brembo' },
  { ticker: 'FCT.MI', name: 'Fincantieri S.p.A.', slug: 'fincantieri' },
  { ticker: 'IPG.MI', name: 'Interpump Group S.p.A.', slug: 'interpump-group' },
  { ticker: 'LUVE.MI', name: 'Lu-Ve S.p.A.', slug: 'lu-ve-spa' },
  { ticker: 'PIRC.MI', name: 'Pirelli & C. S.p.A.', slug: 'pirelli-and-c' },
  { ticker: 'IGD.MI', name: 'IGD SIIQ S.p.A.', slug: 'immobiliare-grande-distribuzione' },
  { ticker: 'DADA.MI', name: 'Digital Bros S.p.A.', slug: 'digital-bros' },
  { ticker: 'OVS.MI', name: 'OVS S.p.A.', slug: 'ovs-spa' },
  { ticker: 'TIN.MI', name: 'Tiscali S.p.A.', slug: 'tiscali' },
  { ticker: 'SOL.MI', name: 'SOL S.p.A.', slug: 'sol' },
  { ticker: 'AVIO.MI', name: 'Avio S.p.A.', slug: 'avio-spa' },
  { ticker: 'SECM.MI', name: 'Seco S.p.A.', slug: 'seco-spa' },
  { ticker: 'TYN.MI', name: 'Tamburi Investment Partners', slug: 'tamburi-invest' },
  { ticker: 'REVO.MI', name: 'Revo Insurance S.p.A.', slug: 'revo-insurance-spa' },
  { ticker: 'SIT.MI', name: 'SIT S.p.A.', slug: 'sit-spa' },
  { ticker: 'JUVE.MI', name: 'Juventus Football Club', slug: 'juventus-fc' },
  { ticker: 'LKT.MI', name: 'Lottomatica Group', slug: 'lottomatica-group-spa' },
  { ticker: 'WEBL.MI', name: 'Webuild S.p.A.', slug: 'salini-impregilo' }
];

let cachedMarketData = { ITA: [], USA: [], lastUpdate: 'Non ancora eseguito' };

// Generatore di URL diretto per Investing.com
function getInvestingUrl(item, isUSA = false) {
  if (isUSA) {
    return `https://it.investing.com/search/?q=${encodeURIComponent(item.ticker)}`;
  }
  if (item.slug) {
    return `https://it.investing.com/equities/${item.slug}`;
  }
  const cleanTicker = item.ticker.replace('.MI', '').toLowerCase();
  return `https://it.investing.com/equities/${cleanTicker}`;
}

// Recupero dinamico dei 300 titoli USA
async function getTop300USStocks() {
  try {
    const response = await fetch('https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.json');
    if (response.ok) {
      const symbols = await response.json();
      return symbols.map(s => {
        const ticker = typeof s === 'string' ? s : (s.symbol || s.ticker);
        if (!ticker || ticker.includes('.') || ticker.length > 5) return null;
        return { ticker: ticker.toUpperCase(), name: ticker.toUpperCase() };
      }).filter(Boolean).slice(0, 300);
    }
  } catch (e) {
    console.error("Errore recupero listino USA:", e);
  }
  const fallbackTopUS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'INTC', 'NFLX', 'JPM', 'V', 'JNJ', 'WMT', 'DIS'];
  return fallbackTopUS.map(t => ({ ticker: t, name: t }));
}

// Chiamata HTTP protetta con User-Agent e Retry Anti-Blocco
async function fetchYahooData(ticker, retries = 2) {
  const url = `https://query2.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=5y`;
  const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
  };

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, { headers });
      if (response.status === 429) {
        // Se riceviamo troppe richieste, attendiamo un momento prima di riprovare
        await new Promise(r => setTimeout(r, 1500 * (attempt + 1)));
        continue;
      }
      if (!response.ok) return null;
      return await response.json();
    } catch (e) {
      if (attempt === retries) return null;
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  return null;
}

// Prezzo realtime facoltativo da Twelve Data
async function fetchRealtimePrice(symbol) {
  if (!TWELVE_DATA_API_KEY) return null;
  try {
    const res = await fetch(`https://api.twelvedata.com/price?symbol=${symbol}&apikey=${TWELVE_DATA_API_KEY}`);
    const data = await res.json();
    if (data && data.price) return parseFloat(data.price);
  } catch (e) {}
  return null;
}

// Funzioni matematiche
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

// Funzione di scansione principale
async function runMarketAnalysis(ruleMonths = 6, ruleStdMonths = 6, ruleStdPct = 3.0) {
  const results = { ITA: [], USA: [], lastUpdate: new Date().toLocaleString('it-IT') };
  const daysMedian = ruleMonths * 21;
  const daysStd = ruleStdMonths * 21;

  // --- 1. MERCATO ITALIANO ---
  console.log(`🇮🇹 Avvio scansione ITA (${ITA_TICKERS.length} azioni) con protezione anti-blocco...`);
  const BATCH_SIZE = 4; // Processiamo 4 azioni per volta per evitare rate-limiting

  for (let i = 0; i < ITA_TICKERS.length; i += BATCH_SIZE) {
    const batch = ITA_TICKERS.slice(i, i + BATCH_SIZE);
    await Promise.all(batch.map(async (item) => {
      try {
        const json = await fetchYahooData(item.ticker);
        const resultObj = json?.chart?.result?.[0];
        if (!resultObj) return;

        const timestamps = resultObj.timestamp;
        const quotes = resultObj.indicators?.quote?.[0];
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

        let currentPrice = await fetchRealtimePrice(item.ticker);
        if (!currentPrice) currentPrice = prices[prices.length - 1];

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
          investingUrl: getInvestingUrl(item, false)
        });
      } catch (e) {}
    }));
    // Pausa dinamica casuale (jittering) tra un batch e l'altro
    await delay(350 + Math.random() * 300);
  }

  // --- 2. MERCATO USA ---
  const US_TICKERS = await getTop300USStocks();
  console.log(`🇺🇸 Avvio scansione USA (${US_TICKERS.length} azioni) con protezione anti-blocco...`);

  for (let i = 0; i < US_TICKERS.length; i += BATCH_SIZE) {
    const batch = US_TICKERS.slice(i, i + BATCH_SIZE);
    await Promise.all(batch.map(async (item) => {
      try {
        const json = await fetchYahooData(item.ticker);
        const resultObj = json?.chart?.result?.[0];
        if (!resultObj) return;

        const timestamps = resultObj.timestamp;
        const quotes = resultObj.indicators?.quote?.[0];
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

        let currentPrice = await fetchRealtimePrice(item.ticker);
        if (!currentPrice) currentPrice = prices[prices.length - 1];

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
          investingUrl: getInvestingUrl(item, true)
        });
      } catch (e) {}
    }));
    await delay(350 + Math.random() * 300);
  }

  return results;
}

// Cronjob: Esecuzione automatica alle 05:00 del mattino
cron.schedule('0 5 * * *', async () => {
  console.log('⏰ [CRON] Avvio analisi automatica globale dei mercati...');
  try {
    cachedMarketData = await runMarketAnalysis();
    console.log('✅ [CRON] Analisi completata!');
  } catch (err) {
    console.error('❌ [CRON] Errore:', err);
  }
}, { scheduled: true, timezone: "Europe/Rome" });

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
            .card:hover { border-color: #38bdf8; transform: translateY(-2px); }
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

            <div id="content" class="loading">Clicca su "Avvia Analisi" per scansionare i mercati.</div>
        </div>

        <script>
            let globalData = { ITA: [], USA: [] };
            let currentMarket = 'ITA';

            async function loadData() {
                const months = document.getElementById('ruleMonths').value;
                const stdMonths = document.getElementById('ruleStdMonths').value;
                const stdPct = document.getElementById('ruleStdPct').value;

                document.getElementById('content').innerHTML = '<div class="loading">Scansione protetta in corso su ~360+ titoli... Elaborazione sicura in background ⏳</div>';

                try {
                    const res = await fetch(\`/api/market-analysis?ruleMonths=\${months}&ruleStdMonths=\${stdMonths}&ruleStdPct=\${stdPct}\`);
                    globalData = await res.json();
                    render();
                } catch(e) {
                    document.getElementById('content').innerHTML = '<div class="loading" style="color:red;">Errore di comunicazione con il server.</div>';
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
                    container.innerHTML = '<div class="loading">Nessuna azione soddisfa i criteri selezionati.</div>';
                    return;
                }

                container.innerHTML = list.map(item => \`
                    <a href="\${item.investingUrl}" target="_blank" rel="noopener noreferrer" class="card">
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
