'use client';

import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import KnowledgeGraph, { graphKinds, localSubgraph, type WikiGraph } from '@/components/knowledge-graph';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

/** Full-vault graph with Obsidian-style filters: note types, pending-only, and a highlight search. */
export default function GraphExplorer({ graph }: { graph: WikiGraph }) {
  const [kinds, setKinds] = useState<Set<string>>(() => new Set(graphKinds.map((item) => item.kind)));
  const [pendingOnly, setPendingOnly] = useState(false);
  const [query, setQuery] = useState('');

  const visible = useMemo(() => {
    const nodes = graph.nodes.filter((node) => kinds.has(node.kind) && (!pendingOnly || node.pending));
    const ids = new Set(nodes.map((node) => node.id));
    return { nodes, links: graph.links.filter((link) => ids.has(link.source) && ids.has(link.target)) };
  }, [graph, kinds, pendingOnly]);

  const toggle = (kind: string) => setKinds((current) => {
    const next = new Set(current);
    if (next.has(kind)) next.delete(kind); else next.add(kind);
    return next;
  });

  return (
    <main className="flex h-screen flex-col gap-4 px-8 py-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl">Graph View</h1>
          <p className="mt-1 text-base text-muted-foreground">ทุกเส้นมาจาก wikilink จริงในโน้ต จุดใหญ่คือโน้ตที่ถูกลิงก์ถึงมาก ชี้เพื่อดูว่าเชื่อมกับอะไร คลิกเพื่อเปิดอ่าน</p>
        </div>
        <p className="num text-base text-muted-foreground">{visible.nodes.length} notes · {visible.links.length} links</p>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ไฮไลต์โน้ตตามชื่อ" aria-label="ไฮไลต์โน้ตตามชื่อ" className="h-10 w-72 pl-9 text-base md:text-base" />
        </div>
        <div role="group" aria-label="ประเภทโน้ตที่แสดง" className="flex gap-1 rounded-lg border border-border p-1">
          {graphKinds.map((item) => (
            <button
              key={item.kind}
              onClick={() => toggle(item.kind)}
              aria-pressed={kinds.has(item.kind)}
              className={cn('flex items-center gap-2 rounded-md px-3 py-1 text-base transition-colors', kinds.has(item.kind) ? 'bg-accent text-foreground' : 'text-muted-foreground line-through')}
            >
              <span className="size-2.5 rounded-full" style={{ background: item.color, opacity: kinds.has(item.kind) ? 1 : 0.35 }} />{item.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => setPendingOnly((value) => !value)}
          aria-pressed={pendingOnly}
          className={cn('rounded-lg border border-border px-3 py-1.5 text-base transition-colors', pendingOnly ? 'border-pending/60 bg-pending/10 text-pending' : 'text-muted-foreground hover:text-foreground')}
        >
          เฉพาะที่ยัง pending
        </button>
      </div>

      <KnowledgeGraph graph={visible} highlight={query} height="100%" className="min-h-0 flex-1" />
    </main>
  );
}

/** Local graph for one entity, with an Obsidian-style depth control. */
export function LocalGraphCard({ graph, focus, title }: { graph: WikiGraph; focus: string; title: string }) {
  const [depth, setDepth] = useState(2);
  const local = useMemo(() => localSubgraph(graph, focus, depth), [graph, focus, depth]);
  return (
    <section className="rounded-lg border border-border bg-card p-5" aria-labelledby="local-graph-title">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="local-graph-title" className="text-2xl">โน้ตที่เชื่อมกับ {title}</h2>
          <p className="mt-1 text-base text-muted-foreground">{local.nodes.length} โน้ต · {local.links.length} ลิงก์ ห่างจาก entity ไม่เกิน {depth} ขั้น</p>
        </div>
        <div role="group" aria-label="ความลึกของกราฟ" className="flex items-center gap-1 rounded-lg border border-border p-1">
          <span className="px-2 text-base text-muted-foreground">ความลึก</span>
          {[1, 2, 3].map((value) => (
            <button key={value} onClick={() => setDepth(value)} aria-pressed={depth === value} className={cn('num min-w-9 rounded-md px-2 py-1 text-base text-muted-foreground', depth === value && 'bg-accent text-foreground')}>{value}</button>
          ))}
        </div>
      </div>
      <KnowledgeGraph key={focus} graph={local} focus={focus} height={560} />
    </section>
  );
}
