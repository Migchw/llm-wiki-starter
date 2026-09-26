'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { BookOpen, Search } from 'lucide-react';
import { KindBadge, VerificationBadge } from '@/components/status-badge';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { kindLabel, type DocSummary } from '@/lib/wiki';

const tabs = [
  { value: 'all', label: 'ทั้งหมด' },
  { value: 'source', label: 'Sources' },
  { value: 'concept', label: 'Concepts' },
  { value: 'entity', label: 'Entities' },
  { value: 'thesis', label: 'Theses' },
] as const;

const filters = [
  { value: 'all', label: 'ทุกสถานะ' },
  { value: 'pending', label: 'pending' },
  { value: 'verified', label: 'verified' },
] as const;

const kindOrder: Record<string, number> = { thesis: 0, source: 1, concept: 2, entity: 3 };

export default function Library({ docs }: { docs: DocSummary[] }) {
  const notes = useMemo(() => docs.filter((doc) => doc.kind !== 'schema'), [docs]);
  const [kind, setKind] = useState<string>('all');
  const [filter, setFilter] = useState<string>('all');
  const [query, setQuery] = useState('');

  const counts = useMemo(() => Object.fromEntries(tabs.map((tab) => [tab.value, tab.value === 'all' ? notes.length : notes.filter((doc) => doc.kind === tab.value).length])), [notes]);

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return notes
      .filter((doc) => kind === 'all' || doc.kind === kind)
      .filter((doc) => filter === 'all' || doc.verification === filter)
      .filter((doc) => !needle || `${doc.title} ${doc.brief} ${doc.tags.join(' ')} ${doc.related.join(' ')}`.toLowerCase().includes(needle))
      .sort((a, b) => (kind === 'all' ? (kindOrder[a.kind] ?? 9) - (kindOrder[b.kind] ?? 9) : 0) || b.date.localeCompare(a.date) || a.title.localeCompare(b.title));
  }, [notes, kind, filter, query]);

  return (
    <main className="mx-auto w-full max-w-[1700px] space-y-6 px-8 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl">คลังความรู้</h1>
          <p className="mt-2 max-w-2xl text-lg text-muted-foreground">อ่านโน้ตทั้งหมดในวอลต์โดยไม่ต้องเปิด Obsidian เลือกดูตามประเภท กรองตามสถานะ verification แล้วกดชื่อเพื่ออ่านฉบับเต็ม</p>
        </div>
        <p className="num text-base text-muted-foreground">{rows.length} / {counts[kind]} notes</p>
      </header>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs value={kind} onValueChange={setKind}>
          <TabsList className="h-auto p-1">
            {tabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value} className="gap-2 px-4 py-2 text-base">
                {tab.label}<span className="num text-sm text-muted-foreground">{counts[tab.value]}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="flex items-center gap-3">
          <div role="group" aria-label="กรองสถานะ" className="flex rounded-lg border border-border p-1">
            {filters.map((item) => (
              <button
                key={item.value}
                onClick={() => setFilter(item.value)}
                aria-pressed={filter === item.value}
                className={cn('rounded-md px-3 py-1 text-base text-muted-foreground transition-colors hover:text-foreground', filter === item.value && 'bg-accent text-foreground')}
              >{item.label}</button>
            ))}
          </div>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ค้นชื่อ สรุป tag หรือบริษัท" aria-label="ค้นหาในคลัง" className="h-10 w-72 pl-9 text-base md:text-base" />
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-card">
        <Table>
          <TableHeader className="bg-secondary">
            <TableRow className="hover:bg-transparent">
              <TableHead className="h-12 w-14 pl-5 text-base">#</TableHead>
              <TableHead className="h-12 w-28 text-base">ประเภท</TableHead>
              <TableHead className="h-12 w-56 text-base">บริษัท / กลุ่ม</TableHead>
              <TableHead className="h-12 w-[26rem] text-base">ชื่อโน้ต</TableHead>
              <TableHead className="h-12 text-base">สรุป</TableHead>
              <TableHead className="h-12 w-32 text-base">อัปเดต</TableHead>
              <TableHead className="h-12 w-36 text-base">สถานะ</TableHead>
              <TableHead className="h-12 w-14"><span className="sr-only">เปิดอ่าน</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((doc, index) => (
              <TableRow key={doc.slug} className="group">
                <TableCell className="num pl-5 align-top text-sm text-muted-foreground">{index + 1}</TableCell>
                <TableCell className="align-top"><KindBadge label={kindLabel[doc.kind] || doc.kind} kind={doc.kind} /></TableCell>
                <TableCell className="whitespace-normal align-top">
                  {doc.related.length ? (
                    <div className="flex flex-wrap gap-1.5">{doc.related.slice(0, 3).map((name) => <span key={name} className="rounded-md border border-border px-2 py-0.5 text-base leading-snug">{name}</span>)}</div>
                  ) : <span className="text-base text-muted-foreground">{doc.group || '—'}</span>}
                </TableCell>
                <TableCell className="whitespace-normal align-top">
                  <Link href={`/read/${doc.slug}`} className="text-lg font-semibold leading-snug outline-none hover:text-primary focus-visible:text-primary">{doc.title}</Link>
                  {doc.tags.length > 0 && <p className="num mt-1.5 text-sm text-muted-foreground">{doc.tags.slice(0, 4).join('  ')}</p>}
                </TableCell>
                <TableCell className="whitespace-normal align-top"><p className="line-clamp-3 max-w-2xl text-base leading-relaxed text-muted-foreground">{doc.brief || '—'}</p></TableCell>
                <TableCell className="num align-top text-sm">{doc.date || '—'}</TableCell>
                <TableCell className="align-top"><VerificationBadge value={doc.verification} /></TableCell>
                <TableCell className="align-top">
                  <Link href={`/read/${doc.slug}`} aria-label={`เปิดอ่าน ${doc.title}`} className="grid size-9 place-items-center rounded-md text-muted-foreground outline-none transition-colors hover:bg-accent hover:text-primary focus-visible:ring-2 focus-visible:ring-ring">
                    <BookOpen className="size-4" aria-hidden />
                  </Link>
                </TableCell>
              </TableRow>
            ))}
            {!rows.length && (
              <TableRow className="hover:bg-transparent"><TableCell colSpan={8} className="py-20 text-center text-lg text-muted-foreground">ไม่พบโน้ตที่ตรงกับตัวกรอง ลองเลือก “ทุกสถานะ” หรือล้างคำค้น</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </main>
  );
}
