export type DocKind = 'source' | 'concept' | 'entity' | 'thesis' | 'schema';

export type WikiDoc = {
  slug: string; kind: DocKind; title: string; date: string; status: string;
  verification: string; confidence: string; tags: string[]; group: string; related: string[]; brief: string; path: string; markdown: string;
};
export type DocSummary = Omit<WikiDoc, 'markdown'>;
export type SourceItem = Pick<WikiDoc, 'slug' | 'title' | 'date' | 'verification' | 'brief' | 'path'> & { entities: string[] };
export type NavDoc = Pick<WikiDoc, 'slug' | 'title' | 'kind'>;

export type Stock = {
  entity: string; ticker: string; exchange: string; marketSymbol: string; currency: string;
  entitySlug: string; sourceCount: number; pendingCount: number; conceptCount: number; thesisCount: number;
  latestSourceDate: string; latestSourceTitle: string;
};
export type ActivityItem = { date: string; action: string; files: string; decision: string };
export type Quote = {
  status: string; symbol?: string; currency?: string; latest?: number; previous?: number;
  change?: number; changePercent?: number; points: { time: string; close: number }[];
};
export type MarketData = { provider: string; fetchedAt: string; quotes: Record<string, Quote> };

export type BeatVerdict = 'beat' | 'miss' | 'in line' | null;
export type Reaction = { intraday?: boolean; reaction_day: string; d0_pct: number; d5_pct: number | null };
export type EpsReport = {
  date: string; eps_estimate: number | null; eps_actual: number | null; surprise_pct: number | null;
  beat?: BeatVerdict; reaction?: Reaction | null;
};
export type GuidanceLine = { low: number; high: number; mid: number; consensus: number | null; vs_consensus_pct: number | null; verdict: 'above' | 'below' | null };
export type ForwardConsensus = {
  eps: number | null; eps_low: number | null; eps_high: number | null; eps_analysts: number | null; eps_growth_pct: number | null;
  revenue: number | null; revenue_low: number | null; revenue_high: number | null; revenue_analysts: number | null; revenue_growth_pct: number | null;
};
export type EarningsScorecard = {
  ticker: string; symbol: string; currency?: string; entity?: string; next_report?: string | null;
  latest?: {
    date: string;
    eps: { actual: number | null; consensus: number | null; surprise_pct: number | null; beat: BeatVerdict; year_ago?: number | null; yoy_pct?: number | null };
    revenue: { actual: number | null; actual_source: string | null; consensus: number | null; consensus_source: string | null; surprise_pct: number | null; beat: BeatVerdict; year_ago: number | null; yoy_pct: number | null };
    reaction?: Reaction | null;
  } | null;
  beat_stats?: { quarters: number; beats: number; beat_rate_pct: number | null; avg_surprise_pct: number | null; avg_reaction_pct?: number | null };
  eps_history?: EpsReport[];
  forward?: { next_quarter: ForwardConsensus; next_quarter_key: string; guidance?: { source: string; revenue?: GuidanceLine; eps?: GuidanceLine } };
  flags?: string[]; errors?: string[];
};
export type EarningsData = { provider: string; fetchedAt: string; scorecards: Record<string, EarningsScorecard> };

export type WikiIndex = {
  generatedAt: string; vaultName: string;
  stats: { entities: number; sources: number; concepts: number; theses: number; pending: number; pendingConcepts: number };
  stocks: Stock[]; activity: ActivityItem[]; documents: WikiDoc[]; recentSources: SourceItem[];
  graph: import('@/components/knowledge-graph').WikiGraph;
};

export const kindLabel: Record<string, string> = {
  source: 'SOURCE', concept: 'CONCEPT', entity: 'ENTITY', thesis: 'THESIS', schema: 'SYSTEM',
};

export function dateLabel(date: string) {
  if (!date) return 'ไม่ระบุวันที่';
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return date;
  return new Intl.DateTimeFormat('th-TH-u-ca-gregory', { day: 'numeric', month: 'short', year: 'numeric' }).format(parsed);
}
