'use client';

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';
import { CheckCircle2, CircleDashed, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import type { DocSummary } from '@/lib/wiki';

const groups = [
  { kind: 'all', label: 'ทั้งหมด' },
  { kind: 'source', label: 'Source' },
  { kind: 'concept', label: 'Concept' },
  { kind: 'entity', label: 'Entity' },
  { kind: 'thesis', label: 'Thesis' },
] as const;

const dot: Record<string, string> = {
  entity: 'bg-primary',
  concept: 'bg-chart-2',
  thesis: 'bg-thesis',
  source: 'bg-muted-foreground/60',
  schema: 'bg-muted-foreground/60',
};

/** Left pane of the reader: browse every note by type without going back to the library. */
export function NotesExplorer({ docs, currentSlug }: { docs: DocSummary[]; currentSlug: string }) {
  const current = docs.find((doc) => doc.slug === currentSlug);
  const [kind, setKind] = useState<string>(current && current.kind !== 'schema' ? current.kind : 'all');
  const [query, setQuery] = useState('');
  const listRef = useRef<HTMLUListElement>(null);

  const counts = useMemo(() => Object.fromEntries(groups.map((group) => [group.kind, group.kind === 'all' ? docs.filter((d) => d.kind !== 'schema').length : docs.filter((d) => d.kind === group.kind).length])), [docs]);

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return docs
      .filter((doc) => doc.kind !== 'schema')
      .filter((doc) => kind === 'all' || doc.kind === kind)
      .filter((doc) => !needle || `${doc.title} ${doc.tags.join(' ')}`.toLowerCase().includes(needle))
      .sort((a, b) => (kind === 'all' ? a.kind.localeCompare(b.kind) : 0) || b.date.localeCompare(a.date) || a.title.localeCompare(b.title));
  }, [docs, kind, query]);

  useEffect(() => {
    listRef.current?.querySelector('[aria-current="page"]')?.scrollIntoView({ block: 'center' });
  }, [currentSlug]);

  return (
    <nav aria-label="รายการโน้ต" className="flex h-full min-h-0 flex-col rounded-lg border border-border bg-card">
      <div className="space-y-3 border-b border-border p-3">
        <div className="flex flex-wrap gap-1" role="group" aria-label="กรองประเภท">
          {groups.map((group) => (
            <button
              key={group.kind}
              onClick={() => setKind(group.kind)}
              aria-pressed={kind === group.kind}
              className={cn('rounded-md px-2.5 py-1 text-base text-muted-foreground transition-colors hover:text-foreground', kind === group.kind && 'bg-accent text-foreground')}
            >
              {group.label} <span className="num text-sm">{counts[group.kind]}</span>
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ค้นชื่อหรือ tag" aria-label="ค้นหาโน้ต" className="h-9 pl-9 text-base md:text-base" />
        </div>
      </div>
      <ul ref={listRef} className="thin-scroll min-h-0 flex-1 overflow-y-auto py-1">
        {rows.map((doc) => {
          const active = doc.slug === currentSlug;
          return (
            <li key={doc.slug}>
              <Link
                href={`/read/${doc.slug}`}
                aria-current={active ? 'page' : undefined}
                className={cn('flex gap-3 border-l-2 border-transparent px-3 py-2.5 outline-none transition-colors hover:bg-accent/60 focus-visible:bg-accent/60', active && 'border-primary bg-accent')}
              >
                <span className={cn('mt-2.5 size-2 shrink-0 rounded-full', dot[doc.kind])} aria-hidden />
                <span className="min-w-0 flex-1">
                  <span className={cn('line-clamp-2 text-base leading-snug', active && 'font-medium')}>{doc.title}</span>
                  <span className="num mt-0.5 flex items-center gap-2 text-sm text-muted-foreground">
                    {doc.date}
                    {doc.verification === 'pending' && <span className="inline-flex items-center gap-1 text-pending"><CircleDashed className="size-3.5" aria-hidden />pending</span>}
                    {doc.verification === 'verified' && <CheckCircle2 className="size-3.5 text-positive" aria-label="verified" />}
                  </span>
                </span>
              </Link>
            </li>
          );
        })}
        {!rows.length && <li className="px-4 py-10 text-center text-base text-muted-foreground">ไม่พบโน้ตที่ตรงกับคำค้น</li>}
      </ul>
    </nav>
  );
}
