'use client';

import { AlertTriangle, CalendarClock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { BeatVerdict, EarningsData, EarningsScorecard as Scorecard } from '@/lib/wiki';

const fmtNum = (v: number | null | undefined, digits = 2) =>
  typeof v === 'number' ? v.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—';

/** Revenue in billions/millions so the table reads like an earnings sheet. */
function money(v: number | null | undefined) {
  if (typeof v !== 'number') return '—';
  const a = Math.abs(v);
  if (a >= 1e9) return `${fmtNum(v / 1e9)}B`;
  if (a >= 1e6) return `${fmtNum(v / 1e6, 1)}M`;
  return fmtNum(v);
}

function Pct({ v, className }: { v: number | null | undefined; className?: string }) {
  if (typeof v !== 'number') return <span className={cn('text-muted-foreground', className)}>—</span>;
  return <span className={cn('num', v >= 0 ? 'text-positive' : 'text-negative', className)}>{v >= 0 ? '+' : ''}{v.toFixed(2)}%</span>;
}

/** Verdict always carries a word, never colour alone. */
function Verdict({ v }: { v: BeatVerdict | 'above' | 'below' | undefined }) {
  if (!v) return <span className="text-muted-foreground">—</span>;
  const good = v === 'beat' || v === 'above';
  const bad = v === 'miss' || v === 'below';
  const label = { beat: 'Beat', miss: 'Miss', 'in line': 'In line', above: 'สูงกว่า', below: 'ต่ำกว่า' }[v];
  return <span className={cn('font-medium', good && 'text-positive', bad && 'text-negative', !good && !bad && 'text-muted-foreground')}>{label}</span>;
}

const th = 'px-3 py-2 text-right text-sm font-medium text-muted-foreground first:text-left';
const td = 'num px-3 py-2.5 text-right text-base first:text-left first:font-sans';

export default function EarningsScorecard({ ticker, data }: { ticker: string; data: EarningsData }) {
  const card: Scorecard | undefined = data?.scorecards?.[ticker];

  if (!card || (!card.latest && !card.eps_history?.length)) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-2xl">Earnings scorecard</CardTitle></CardHeader>
        <CardContent>
          <p className="text-base text-muted-foreground">
            {card?.errors?.length ? `ดึงข้อมูลไม่สำเร็จ: ${card.errors.join('; ')}` : 'ยังไม่มีข้อมูลงบของหุ้นนี้ รัน npm run earnings หรือ /earnings-scorecard'}
          </p>
        </CardContent>
      </Card>
    );
  }

  const L = card.latest;
  const fq = card.forward?.next_quarter;
  const guide = card.forward?.guidance;
  const history = card.eps_history || [];
  const maxAbs = Math.max(5, ...history.map((h) => Math.abs(h.surprise_pct ?? 0)));

  return (
    <Card>
      <CardHeader className="border-b border-border">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-2xl">Earnings scorecard · <span className="num">{ticker}</span></CardTitle>
            <CardDescription className="text-base">
              งบล่าสุด <span className="num">{L?.date ?? '—'}</span>
              {card.next_report && <> · งบถัดไป <span className="num">{card.next_report}</span></>}
            </CardDescription>
          </div>
          {L?.reaction && (
            <div className="text-right">
              <p className="text-sm text-muted-foreground">ราคาวันรายงาน{L.reaction.intraday ? ' (ระหว่างวัน)' : ''}</p>
              <Pct v={L.reaction.d0_pct} className="text-2xl" />
              {typeof L.reaction.d5_pct === 'number' && <p className="text-sm text-muted-foreground">+5 วัน <Pct v={L.reaction.d5_pct} /></p>}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-4">
        {L && (
          <div className="overflow-x-auto rounded-md border border-border">
            <table className="w-full min-w-[36rem]">
              <thead className="bg-muted/50">
                <tr>{['', 'Reported', 'Consensus', 'Beat/Miss', 'Surprise', 'YoY'].map((h) => <th key={h} className={th}>{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr>
                  <td className={td}>Revenue</td>
                  <td className={td}>{money(L.revenue.actual)}</td>
                  <td className={td}>{money(L.revenue.consensus)}</td>
                  <td className={td}><Verdict v={L.revenue.beat} /></td>
                  <td className={td}><Pct v={L.revenue.surprise_pct} /></td>
                  <td className={td}><Pct v={L.revenue.yoy_pct} /></td>
                </tr>
                <tr>
                  <td className={td}>EPS</td>
                  <td className={td}>{fmtNum(L.eps.actual)}</td>
                  <td className={td}>{fmtNum(L.eps.consensus)}</td>
                  <td className={td}><Verdict v={L.eps.beat} /></td>
                  <td className={td}><Pct v={L.eps.surprise_pct} /></td>
                  <td className={td}><Pct v={L.eps.yoy_pct} /></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {guide && (guide.revenue || guide.eps) && (
          <div>
            <h3 className="mb-2 text-lg font-medium">Guidance ไตรมาสหน้า เทียบ consensus</h3>
            <div className="overflow-x-auto rounded-md border border-border">
              <table className="w-full min-w-[36rem]">
                <thead className="bg-muted/50">
                  <tr>{['', 'Guidance (ช่วง)', 'จุดกึ่งกลาง', 'Consensus', 'เทียบ consensus'].map((h) => <th key={h} className={th}>{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(['revenue', 'eps'] as const).map((k) => {
                    const g = guide[k];
                    if (!g) return null;
                    const f = k === 'revenue' ? money : (v: number | null) => fmtNum(v);
                    return (
                      <tr key={k}>
                        <td className={td}>{k === 'revenue' ? 'Revenue' : 'EPS'}</td>
                        <td className={td}>{f(g.low)}–{f(g.high)}</td>
                        <td className={td}>{f(g.mid)}</td>
                        <td className={td}>{f(g.consensus)}</td>
                        <td className={td}><Verdict v={g.verdict} /> <Pct v={g.vs_consensus_pct} /></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(16rem,20rem)]">
          <div>
            <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-lg font-medium">EPS surprise ย้อนหลัง</h3>
              {card.beat_stats && (
                <p className="num text-sm text-muted-foreground">
                  beat {card.beat_stats.beats}/{card.beat_stats.quarters} ไตรมาส · surprise เฉลี่ย {fmtNum(card.beat_stats.avg_surprise_pct)}%
                  {typeof card.beat_stats.avg_reaction_pct === 'number' && <> · ราคาเฉลี่ยวันรายงาน {fmtNum(card.beat_stats.avg_reaction_pct)}%</>}
                </p>
              )}
            </div>
            <ol className="grid gap-1.5" aria-label="EPS surprise และการตอบสนองของราคาแต่ละไตรมาส">
              {history.slice().reverse().map((h) => {
                const s = h.surprise_pct ?? 0;
                const width = `${Math.max(2, (Math.abs(s) / maxAbs) * 50)}%`;
                return (
                  <li key={h.date} className="grid grid-cols-[6.5rem_minmax(0,1fr)_4.5rem_4.5rem] items-center gap-2 text-sm">
                    <span className="num text-muted-foreground">{h.date}</span>
                    <span className="relative h-5 rounded-sm bg-muted/40" aria-hidden>
                      <span className="absolute inset-y-0 left-1/2 w-px bg-border" />
                      <span
                        className={cn('absolute inset-y-0.5 rounded-sm', s >= 0 ? 'left-1/2 bg-positive/70' : 'right-1/2 bg-negative/70')}
                        style={{ width }}
                      />
                    </span>
                    <Pct v={h.surprise_pct} className="text-right" />
                    <span className="text-right">{h.reaction ? <Pct v={h.reaction.d0_pct} /> : <span className="text-muted-foreground">—</span>}</span>
                  </li>
                );
              })}
            </ol>
            <p className="mt-2 text-sm text-muted-foreground">แท่ง = EPS surprise · คอลัมน์ขวาสุด = ราคาวันรายงานเทียบวันก่อนหน้า</p>
          </div>

          {fq && (
            <dl className="grid content-start gap-3 rounded-md border border-border p-4">
              <p className="text-lg font-medium">Consensus ไตรมาสถัดไป</p>
              <div>
                <dt className="text-sm text-muted-foreground">EPS</dt>
                <dd className="num text-xl">{fmtNum(fq.eps)} <span className="text-sm text-muted-foreground">({fmtNum(fq.eps_low)}–{fmtNum(fq.eps_high)} · {fq.eps_analysts ?? 0} คน)</span></dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Revenue</dt>
                <dd className="num text-xl">{money(fq.revenue)} <span className="text-sm text-muted-foreground">({fq.revenue_analysts ?? 0} คน)</span></dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">โต YoY ตาม consensus</dt>
                <dd className="text-base">Revenue <Pct v={fq.revenue_growth_pct} /> · EPS <Pct v={fq.eps_growth_pct} /></dd>
              </div>
            </dl>
          )}
        </div>

        {!!card.flags?.length && (
          <ul className="space-y-1.5">
            {card.flags.map((f) => (
              <li key={f} className="flex items-start gap-2 text-base text-pending"><AlertTriangle className="mt-1 size-4 shrink-0" aria-hidden />{f}</li>
            ))}
          </ul>
        )}

        <p className="flex flex-wrap items-center gap-1.5 border-t border-border pt-3 text-sm text-muted-foreground">
          <CalendarClock className="size-4" aria-hidden />
          {data.provider} · ดึงเมื่อ <span className="num">{data.fetchedAt?.slice(0, 16).replace('T', ' ')}Z</span>
          {L?.revenue.consensus_source && <> · revenue consensus: {L.revenue.consensus_source}</>}
          {L?.revenue.actual_source && <> · revenue จริง: {L.revenue.actual_source}</>}
          · consensus จาก Yahoo อาจต่างจาก FactSet/LSEG เล็กน้อย
        </p>
      </CardContent>
    </Card>
  );
}
