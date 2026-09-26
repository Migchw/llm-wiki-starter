'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { ArrowDownRight, ArrowUpRight, CircleDashed, Lock, Search } from 'lucide-react';
import { LocalGraphCard } from '@/components/graph-explorer';
import type { WikiGraph } from '@/components/knowledge-graph';
import { Hero } from '@/components/hero';
import { StatStrip } from '@/components/stat-strip';
import MarketChart from '@/components/market-chart';
import EarningsScorecard from '@/components/earnings-scorecard';
import { VerificationBadge } from '@/components/status-badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { dateLabel, type ActivityItem, type EarningsData, type MarketData, type SourceItem, type Stock } from '@/lib/wiki';

type Props = {
  vaultName: string; generatedAt: string;
  stats: { entities: number; sources: number; concepts: number; theses: number; pending: number; pendingConcepts: number };
  stocks: Stock[]; recentSources: SourceItem[]; pendingSources: SourceItem[]; activity: ActivityItem[];
  graph: WikiGraph; market: MarketData; earnings: EarningsData;
};

function Delta({ change, percent, className }: { change?: number; percent?: number; className?: string }) {
  if (typeof percent !== 'number') return null;
  const up = percent >= 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span className={cn('num inline-flex items-center gap-1', up ? 'text-positive' : 'text-negative', className)}>
      <Icon className="size-4" aria-hidden />
      {typeof change === 'number' && <span>{up ? '+' : ''}{change.toFixed(2)}</span>}
      <span>({up ? '+' : ''}{percent.toFixed(2)}%)</span>
    </span>
  );
}

const stamp = (iso: string) => (iso ? `${new Date(iso).toISOString().slice(0, 16).replace('T', ' ')}Z` : '—');

export default function Overview({ vaultName, generatedAt, stats, stocks, recentSources, pendingSources, activity, graph, market, earnings }: Props) {
  const [activeTicker, setActiveTicker] = useState(stocks[0]?.ticker || '');
  const [query, setQuery] = useState('');
  const activeStock = stocks.find((stock) => stock.ticker === activeTicker) || stocks[0];
  const quote = activeStock ? market.quotes[activeStock.ticker] : undefined;
  const hasQuote = quote?.status === 'ok' && typeof quote.latest === 'number' && quote.points.length > 1;

  const visibleSources = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return recentSources.filter((source) => {
      const forStock = !activeStock || source.entities.includes(activeStock.ticker);
      return forStock && (!needle || `${source.title} ${source.brief}`.toLowerCase().includes(needle));
    });
  }, [activeStock, recentSources, query]);

  return (
    <main className="mx-auto w-full max-w-[1500px] space-y-8 px-4 py-6 sm:px-8 sm:py-8">
      <Hero vaultName={vaultName} indexedAt={generatedAt} />

      <StatStrip
        stats={[
          { label: 'Source notes', value: stats.sources, hint: 'บทความที่ ingest แล้ว' },
          { label: 'Entities', value: stats.entities, hint: 'บริษัทและบุคคลในวอลต์' },
          { label: 'Concepts', value: stats.concepts, hint: 'กรอบคิดที่ใช้ซ้ำได้' },
          { label: 'รอตรวจ', value: stats.pending, hint: `source ที่ยังไม่ verified (concept ${stats.pendingConcepts})`, tone: 'pending' },
        ]}
      />

      <section aria-labelledby="watchlist-title">
        <div className="mb-3 flex items-end justify-between gap-4">
          <h2 id="watchlist-title" className="text-2xl">หุ้นที่กำลังติดตาม</h2>
          <p className="hidden text-base text-muted-foreground sm:block">เลือกหุ้นเพื่อกรองงานวิจัยและกราฟ</p>
        </div>
        <div className="thin-scroll grid auto-cols-[minmax(13rem,1fr)] grid-flow-col gap-3 overflow-x-auto pb-2 lg:grid-flow-row lg:grid-cols-5">
          {stocks.map((stock) => {
            const q = market.quotes[stock.ticker];
            const selected = stock.ticker === activeTicker;
            return (
              <button
                key={stock.ticker}
                onClick={() => setActiveTicker(stock.ticker)}
                aria-pressed={selected}
                className={cn('rounded-lg border bg-card p-4 text-left outline-none transition-colors hover:border-primary/60 focus-visible:ring-2 focus-visible:ring-ring', selected ? 'border-primary bg-accent/60 shadow-[0_0_0_1px_var(--primary)]' : 'border-border')}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="num text-xl font-bold">{stock.ticker}</span>
                  <span className="num text-sm text-muted-foreground">{stock.exchange}</span>
                </div>
                <p className="mt-1 truncate text-base text-muted-foreground">{stock.entity}</p>
                <div className="mt-3 flex items-baseline justify-between gap-2">
                  {q?.status === 'ok' && typeof q.latest === 'number'
                    ? <><span className="num text-lg">{q.latest.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span><Delta percent={q.changePercent} className="text-sm" /></>
                    : <span className="flex items-center gap-1.5 text-base text-muted-foreground"><Lock className="size-3.5" aria-hidden />ไม่มีราคาตลาด</span>}
                </div>
                <p className="num mt-2 text-sm text-muted-foreground">{stock.sourceCount} sources{stock.pendingCount > 0 && <span className="text-pending"> · {stock.pendingCount} pending</span>}</p>
              </button>
            );
          })}
        </div>
      </section>

      {activeStock && (
        <section className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(22rem,1fr)]">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="meta">{activeStock.exchange} / {activeStock.currency}</p>
                  <CardTitle className="mt-1 text-3xl"><span className="num">{activeStock.ticker}</span></CardTitle>
                  <CardDescription className="text-base">{activeStock.entity}</CardDescription>
                </div>
                {hasQuote && (
                  <div className="text-right">
                    <p className="num text-4xl font-medium leading-none">{quote.latest!.toLocaleString('en-US', { maximumFractionDigits: 2 })} <span className="text-base text-muted-foreground">{quote.currency}</span></p>
                    <Delta change={quote.change} percent={quote.changePercent} className="mt-2 justify-end text-base" />
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {hasQuote ? (
                <>
                  <MarketChart quote={quote} ticker={activeStock.ticker} />
                  <p className="num mt-2 text-sm text-muted-foreground">ราคาปิดรายวัน 6 เดือน · {market.provider} · cache {stamp(market.fetchedAt).slice(0, 10)}</p>
                </>
              ) : (
                <div className="grid h-72 place-content-center gap-2 rounded-md border border-dashed border-border text-center">
                  <Lock className="mx-auto size-6 text-muted-foreground" aria-hidden />
                  <p className="text-lg">{activeStock.marketSymbol ? 'ยังดึงข้อมูลราคาไม่ได้' : 'บริษัทเอกชน ไม่มีราคาตลาดรายวัน'}</p>
                  <p className="num text-sm text-muted-foreground">{activeStock.marketSymbol ? `market symbol: ${activeStock.marketSymbol}` : 'อ่านหลักฐานจาก source notes ด้านขวา'}</p>
                </div>
              )}
              <Separator className="my-5" />
              <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {([['Sources', activeStock.sourceCount], ['Concepts', activeStock.conceptCount], ['Theses', activeStock.thesisCount]] as const).map(([label, value]) => (
                  <div key={label}><dt className="num text-sm text-muted-foreground">{label}</dt><dd className="num mt-1 text-2xl">{value}</dd></div>
                ))}
                <div><dt className="num text-sm text-muted-foreground">Last note</dt><dd className="mt-1 text-lg">{dateLabel(activeStock.latestSourceDate)}</dd></div>
              </dl>
            </CardContent>
          </Card>

          <Card className="min-h-0">
            <CardHeader className="border-b border-border">
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="text-2xl">เรื่องที่ควรตามอ่าน</CardTitle>
                <span className="num rounded-md bg-primary px-2.5 py-1 text-base font-bold text-primary-foreground">{visibleSources.length}</span>
              </div>
              <div className="relative mt-3">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="กรองบทความ…" aria-label="กรองบทความ" className="h-10 pl-9 text-base md:text-base" />
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[34rem]">
                {visibleSources.length ? visibleSources.map((source) => (
                  <Link key={source.path} href={`/read/${source.slug}`} className="group block border-b border-border px-5 py-4 outline-none transition-colors last:border-0 hover:bg-accent/50 focus-visible:bg-accent/50">
                    <div className="flex items-center justify-between gap-2">
                      <span className="num text-sm text-muted-foreground">{source.date}</span>
                      <VerificationBadge value={source.verification} />
                    </div>
                    <h3 className="mt-2 text-lg font-medium leading-snug group-hover:text-primary">{source.title}</h3>
                    <p className="mt-1 line-clamp-2 text-base leading-relaxed text-muted-foreground">{source.brief}</p>
                  </Link>
                )) : (
                  <div className="px-6 py-14 text-center"><p className="text-lg">ยังไม่พบ source note</p><p className="mt-1 text-base text-muted-foreground">หุ้นนี้อาจยังไม่มี wikilink จาก Source ไปยัง Entity หรือคำค้นไม่ตรง</p></div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </section>
      )}

      {activeStock?.marketSymbol && <EarningsScorecard ticker={activeStock.ticker} data={earnings} />}

      {activeStock?.entitySlug && <LocalGraphCard graph={graph} focus={activeStock.entitySlug} title={activeStock.entity} />}

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="border-b border-border">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-2xl">ต้องตรวจก่อนเชื่อ</CardTitle>
              <span className="num text-3xl text-pending">{stats.pending}</span>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {pendingSources.map((source) => (
              <Link key={source.slug} href={`/read/${source.slug}`} className="flex items-start gap-3 border-b border-border px-5 py-3 transition-colors last:border-0 hover:bg-accent/50">
                <CircleDashed className="mt-1 size-4 shrink-0 text-pending" aria-hidden />
                <span className="min-w-0 flex-1"><span className="block text-base leading-snug">{source.title}</span><span className="num text-sm text-muted-foreground">{source.date}</span></span>
              </Link>
            ))}
            {!pendingSources.length && <p className="px-5 py-8 text-base text-muted-foreground">ไม่มี source note ที่ค้าง pending</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-border">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-2xl">ความเคลื่อนไหวล่าสุดของวอลต์</CardTitle>
              <Link href="/read/activity-log" className="text-base text-primary hover:underline">ดูทั้งหมด</Link>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ol>
              {activity.slice(0, 6).map((item, index) => (
                <li key={`${item.date}-${index}`} className="grid grid-cols-[6.5rem_minmax(0,1fr)] gap-3 border-b border-border px-5 py-3 last:border-0">
                  <span className="num pt-0.5 text-sm text-muted-foreground">{item.date}</span>
                  <span className="line-clamp-2 text-base leading-snug">{item.action}</span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </section>

      <footer className="flex flex-wrap justify-between gap-2 border-t border-border pt-4 text-sm text-muted-foreground">
        <span className="num">wiki-index {stamp(generatedAt)}</span>
        <span className="num">market {stamp(market.fetchedAt)} · {market.provider}</span>
      </footer>
    </main>
  );
}
