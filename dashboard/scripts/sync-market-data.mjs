import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const watchlist = JSON.parse(await readFile(path.join(projectRoot, 'config', 'watchlist.json'), 'utf8'));
const quotes = {};

for (const stock of watchlist.stocks) {
  if (!stock.marketSymbol) continue;
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(stock.marketSymbol)}?range=6mo&interval=1d`;
    const response = await fetch(url, { headers: { 'User-Agent': 'llm-wiki-dashboard/0.1 (personal research)' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const result = payload.chart?.result?.[0];
    if (!result) throw new Error(payload.chart?.error?.description || 'No chart result');
    const closes = result.indicators?.quote?.[0]?.close || [];
    const points = (result.timestamp || []).map((timestamp, index) => ({
      time: new Date(timestamp * 1000).toISOString(),
      close: closes[index],
    })).filter((point) => Number.isFinite(point.close));
    const latest = points.at(-1)?.close ?? result.meta.regularMarketPrice ?? null;
    const previous = points.at(-2)?.close ?? result.meta.chartPreviousClose ?? null;
    quotes[stock.ticker] = {
      status: 'ok', symbol: result.meta.symbol, currency: result.meta.currency,
      exchange: result.meta.exchangeName, timezone: result.meta.exchangeTimezoneName,
      latest, previous, change: latest !== null && previous !== null ? latest - previous : null,
      changePercent: latest !== null && previous ? ((latest - previous) / previous) * 100 : null,
      points,
    };
  } catch (error) {
    quotes[stock.ticker] = { status: 'error', message: error instanceof Error ? error.message : String(error), points: [] };
  }
}

const market = { provider: 'Yahoo Finance public chart endpoint', fetchedAt: new Date().toISOString(), quotes };
await writeFile(path.join(projectRoot, 'data', 'market-data.json'), `${JSON.stringify(market, null, 2)}\n`, 'utf8');
console.log(`Synced market data for ${Object.values(quotes).filter((quote) => quote.status === 'ok').length} symbols`);
