// Server-only: imports the full generated index (includes every note's Markdown).
import wikiIndex from '@/data/wiki-index.json';
import marketData from '@/data/market-data.json';
import earningsData from '@/data/earnings-data.json';
import type { DocSummary, EarningsData, MarketData, NavDoc, WikiIndex } from '@/lib/wiki';

export const wiki = wikiIndex as unknown as WikiIndex;
export const market = marketData as unknown as MarketData;
export const earnings = earningsData as unknown as EarningsData;

export function navDocs(): NavDoc[] {
  return wiki.documents.map(({ slug, title, kind }) => ({ slug, title, kind }));
}

export function docSummaries(): DocSummary[] {
  return wiki.documents.map(({ markdown, ...summary }) => { void markdown; return summary; });
}
