'use client';

import { useEffect, useId, useRef, useState } from 'react';
import type { Quote } from '@/lib/wiki';

const HEIGHT = 300;
const PAD = { top: 16, right: 64, bottom: 28, left: 8 };

function formatPrice(value: number) {
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function formatDate(time: string) {
  return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(time));
}
function monthLabel(time: string) {
  return new Intl.DateTimeFormat('en-GB', { month: 'short' }).format(new Date(time));
}

export default function MarketChart({ quote, ticker }: { quote: Quote; ticker: string }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const gradientId = useId().replace(/:/g, '');
  const [width, setWidth] = useState(720);
  const [hover, setHover] = useState<number | null>(null);
  const points = quote.points;

  useEffect(() => {
    const element = wrapRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(320, Math.floor(entry.contentRect.width))));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const values = points.map((point) => point.close);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const innerW = width - PAD.left - PAD.right;
  const innerH = HEIGHT - PAD.top - PAD.bottom;
  const x = (index: number) => PAD.left + (index / (points.length - 1)) * innerW;
  const y = (value: number) => PAD.top + (1 - (value - min) / span) * innerH;
  const line = points.map((point, index) => `${index ? 'L' : 'M'}${x(index).toFixed(1)},${y(point.close).toFixed(1)}`).join(' ');
  const area = `${line} L${x(points.length - 1).toFixed(1)},${HEIGHT - PAD.bottom} L${x(0).toFixed(1)},${HEIGHT - PAD.bottom} Z`;
  const ticks = [max, min + span / 2, min];
  const monthTicks = points
    .map((point, index) => ({ index, label: monthLabel(point.time), month: new Date(point.time).getMonth() }))
    .filter((tick, position, all) => position === 0 || tick.month !== all[position - 1].month)
    .filter((tick) => tick.index > 3);

  function onMove(event: React.PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - rect.left - PAD.left) / innerW;
    setHover(Math.max(0, Math.min(points.length - 1, Math.round(ratio * (points.length - 1)))));
  }

  const active = hover === null ? null : points[hover];
  const latest = points.at(-1)!;
  const first = points[0];
  const summary = `กราฟราคาปิด ${ticker} ย้อนหลัง ${points.length} วันทำการ เริ่ม ${formatPrice(first.close)} จบ ${formatPrice(latest.close)} ต่ำสุด ${formatPrice(min)} สูงสุด ${formatPrice(max)}`;

  return (
    <div ref={wrapRef} className="relative">
      <svg width={width} height={HEIGHT} role="img" aria-label={summary} onPointerMove={onMove} onPointerLeave={() => setHover(null)} className="block touch-pan-y">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.28" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={PAD.left} x2={width - PAD.right} y1={y(tick)} y2={y(tick)} stroke="var(--border)" strokeDasharray="2 5" />
            <text x={width - PAD.right + 8} y={y(tick) + 4} className="num" fontSize="13" fill="var(--muted-foreground)">{formatPrice(tick)}</text>
          </g>
        ))}
        {monthTicks.map((tick) => (
          <text key={tick.index} x={x(tick.index)} y={HEIGHT - 8} textAnchor="middle" className="num" fontSize="13" fill="var(--muted-foreground)">{tick.label}</text>
        ))}
        <path d={area} fill={`url(#${gradientId})`} />
        <path d={line} fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={x(points.length - 1)} cy={y(latest.close)} r="4" fill="var(--primary)" stroke="var(--background)" strokeWidth="2" />
        {hover !== null && active && (
          <g pointerEvents="none">
            <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={HEIGHT - PAD.bottom} stroke="var(--muted-foreground)" strokeDasharray="3 4" />
            <circle cx={x(hover)} cy={y(active.close)} r="5" fill="var(--primary)" stroke="var(--background)" strokeWidth="2" />
          </g>
        )}
      </svg>
      {hover !== null && active && (
        <div
          className="pointer-events-none absolute top-2 z-10 rounded-md border border-border bg-popover px-3 py-2 shadow-lg"
          style={{ left: Math.min(Math.max(x(hover) + 12, 8), width - 190) }}
          role="status"
        >
          <p className="num text-sm text-muted-foreground">{formatDate(active.time)}</p>
          <p className="num text-lg font-medium">{formatPrice(active.close)} <span className="text-sm text-muted-foreground">{quote.currency}</span></p>
        </div>
      )}
    </div>
  );
}
