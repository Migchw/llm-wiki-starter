'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY, type Simulation, type SimulationLinkDatum, type SimulationNodeDatum } from 'd3-force';
import { Maximize2, Minus, Plus } from 'lucide-react';
import { useReducedMotion } from 'motion/react';
import { cn } from '@/lib/utils';

export type GraphNode = { id: string; label: string; kind: string; pending: boolean };
export type GraphLink = { source: string; target: string };
export type WikiGraph = { nodes: GraphNode[]; links: GraphLink[] };

type SimNode = GraphNode & SimulationNodeDatum & { degree: number };
type SimLink = SimulationLinkDatum<SimNode>;
type View = { x: number; y: number; k: number };

export const graphKinds = [
  { kind: 'entity', label: 'Entity', color: 'var(--primary)' },
  { kind: 'thesis', label: 'Thesis', color: 'var(--thesis)' },
  { kind: 'concept', label: 'Concept', color: 'var(--chart-2)' },
  { kind: 'source', label: 'Source', color: 'var(--muted-foreground)' },
] as const;
const kindColor = Object.fromEntries(graphKinds.map((item) => [item.kind, item.color])) as Record<string, string>;

const nodeRadius = (degree: number) => 3.5 + Math.sqrt(degree) * 2.4;

/** Nodes within `depth` hops of `focus` (Obsidian's local graph). */
export function localSubgraph(graph: WikiGraph, focus: string, depth: number): WikiGraph {
  const keep = new Set([focus]);
  let frontier = [focus];
  for (let step = 0; step < depth; step += 1) {
    const next: string[] = [];
    for (const link of graph.links) {
      for (const [from, to] of [[link.source, link.target], [link.target, link.source]]) {
        if (frontier.includes(from) && !keep.has(to)) { keep.add(to); next.push(to); }
      }
    }
    frontier = next;
  }
  return {
    nodes: graph.nodes.filter((node) => keep.has(node.id)),
    links: graph.links.filter((link) => keep.has(link.source) && keep.has(link.target)),
  };
}

type Props = {
  graph: WikiGraph;
  focus?: string;
  highlight?: string;
  height?: number | string;
  className?: string;
};

/**
 * Obsidian-style graph: small dots sized by link count, thin links, labels that appear on zoom,
 * hover dims everything except the node and its neighbours. Wheel zooms, drag on empty space pans,
 * drag a node to move it, click a node to open the note.
 */
export default function KnowledgeGraph({ graph, focus, highlight = '', height = 560, className }: Props) {
  const router = useRouter();
  const reduced = useReducedMotion();
  const wrapRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const simRef = useRef<Simulation<SimNode, SimLink> | null>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const gesture = useRef<{ type: 'pan' | 'node'; startX: number; startY: number; view: View; node?: SimNode; moved: boolean } | null>(null);
  const [size, setSize] = useState({ w: 900, h: 560 });
  const sizeRef = useRef(size);
  const [view, setView] = useState<View>({ x: 0, y: 0, k: 1 });
  const [nodes, setNodes] = useState<SimNode[]>([]);
  const [hovered, setHovered] = useState<string | null>(null);

  const neighbours = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const node of graph.nodes) map.set(node.id, new Set());
    for (const link of graph.links) {
      map.get(link.source)?.add(link.target);
      map.get(link.target)?.add(link.source);
    }
    return map;
  }, [graph]);

  useEffect(() => {
    const element = wrapRef.current;
    if (!element) return;
    const measure = (w: number, h: number) => { sizeRef.current = { w: Math.max(320, w), h: Math.max(320, h) }; setSize(sizeRef.current); };
    const rect = element.getBoundingClientRect();
    measure(rect.width, rect.height);
    const observer = new ResizeObserver(([entry]) => measure(entry.contentRect.width, entry.contentRect.height));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const fit = useCallback((nodes = nodesRef.current) => {
    if (!nodes.length) return;
    const { w, h } = sizeRef.current;
    const xs = nodes.map((node) => node.x ?? 0);
    const ys = nodes.map((node) => node.y ?? 0);
    const [minX, maxX, minY, maxY] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const pad = 80;
    const k = Math.min(2, Math.max(0.3, Math.min((w - pad * 2) / (maxX - minX || 1), (h - pad * 2) / (maxY - minY || 1))));
    setView({ k, x: w / 2 - ((minX + maxX) / 2) * k, y: h / 2 - ((minY + maxY) / 2) * k });
  }, []);

  useEffect(() => {
    const previous = new Map(nodesRef.current.map((node) => [node.id, node]));
    const nodes: SimNode[] = graph.nodes.map((node, index) => {
      const old = previous.get(node.id);
      const angle = index * 2.399;
      return { ...node, degree: neighbours.get(node.id)?.size ?? 0, x: old?.x ?? Math.cos(angle) * 12 * Math.sqrt(index + 1), y: old?.y ?? Math.sin(angle) * 12 * Math.sqrt(index + 1) };
    });
    const links: SimLink[] = graph.links.map((link) => ({ ...link }));
    nodesRef.current = nodes;
    const simulation = forceSimulation<SimNode>(nodes)
      .force('link', forceLink<SimNode, SimLink>(links).id((node) => node.id).distance((link) => 55 + 6 * Math.sqrt(Math.max((link.source as SimNode).degree, (link.target as SimNode).degree))).strength(0.5))
      .force('charge', forceManyBody<SimNode>().strength((node) => -160 - node.degree * 28).distanceMax(500))
      .force('x', forceX<SimNode>(0).strength(0.09))
      .force('y', forceY<SimNode>(0).strength(0.09))
      .force('center', forceCenter(0, 0))
      .force('collide', forceCollide<SimNode>().radius((node) => nodeRadius(node.degree) + 14))
      .alphaDecay(0.035);
    simRef.current = simulation;
    // Lay out most of the way synchronously so the first paint is already readable and framed;
    // with motion allowed, the last stretch animates so the graph visibly settles.
    simulation.stop();
    simulation.tick(reduced ? 300 : 160);
    fit(nodes);
    setNodes([...nodes]);
    if (!reduced) {
      simulation.on('tick', () => setNodes([...nodes])).alpha(0.12).restart();
    }
    return () => { simulation.stop(); };
  }, [graph, neighbours, reduced, fit]);

  const toGraph = (clientX: number, clientY: number, current = view) => {
    const rect = svgRef.current!.getBoundingClientRect();
    return { x: (clientX - rect.left - current.x) / current.k, y: (clientY - rect.top - current.y) / current.k };
  };

  // Native, non-passive wheel listener so zooming the graph does not also scroll the page.
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const rect = svg.getBoundingClientRect();
      const px = event.clientX - rect.left;
      const py = event.clientY - rect.top;
      setView((current) => {
        const k = Math.min(4, Math.max(0.25, current.k * Math.exp(-event.deltaY * 0.0015)));
        return { k, x: px - ((px - current.x) / current.k) * k, y: py - ((py - current.y) / current.k) * k };
      });
    };
    svg.addEventListener('wheel', onWheel, { passive: false });
    return () => svg.removeEventListener('wheel', onWheel);
  }, []);

  function zoomBy(factor: number) {
    setView((current) => {
      const k = Math.min(4, Math.max(0.25, current.k * factor));
      const cx = size.w / 2;
      const cy = size.h / 2;
      return { k, x: cx - ((cx - current.x) / current.k) * k, y: cy - ((cy - current.y) / current.k) * k };
    });
  }

  function onPointerDown(event: React.PointerEvent<SVGSVGElement>) {
    const target = (event.target as Element).closest<SVGGElement>('[data-node]');
    const node = target ? nodesRef.current.find((item) => item.id === target.dataset.node) : undefined;
    svgRef.current!.setPointerCapture(event.pointerId);
    gesture.current = { type: node ? 'node' : 'pan', startX: event.clientX, startY: event.clientY, view, node, moved: false };
    if (node) { node.fx = node.x; node.fy = node.y; simRef.current?.alphaTarget(0.25).restart(); }
  }

  function onPointerMove(event: React.PointerEvent<SVGSVGElement>) {
    const active = gesture.current;
    if (!active) return;
    const dx = event.clientX - active.startX;
    const dy = event.clientY - active.startY;
    if (Math.abs(dx) + Math.abs(dy) > 3) active.moved = true;
    if (active.type === 'pan') {
      setView({ ...active.view, x: active.view.x + dx, y: active.view.y + dy });
    } else if (active.node) {
      const point = toGraph(event.clientX, event.clientY);
      active.node.fx = point.x;
      active.node.fy = point.y;
      if (reduced) { active.node.x = point.x; active.node.y = point.y; setNodes([...nodesRef.current]); }
    }
  }

  function onPointerUp() {
    const active = gesture.current;
    gesture.current = null;
    if (!active) return;
    if (active.node) {
      active.node.fx = null;
      active.node.fy = null;
      simRef.current?.alphaTarget(0);
      if (!active.moved) router.push(`/read/${active.node.id}`);
    }
  }

  const needle = highlight.trim().toLowerCase();
  const matches = (node: SimNode) => needle && node.label.toLowerCase().includes(needle);
  const activeSet = hovered ? new Set([hovered, ...(neighbours.get(hovered) ?? [])]) : null;
  const byId = new Map(nodes.map((node) => [node.id, node]));
  // Only the few biggest hubs are labelled at rest; zooming in reveals the rest, as in Obsidian.
  const hubThreshold = Math.max(4, [...nodes].sort((a, b) => b.degree - a.degree)[Math.min(2, nodes.length - 1)]?.degree ?? 4);

  // Label placement in screen space: priority labels first (hover, focus, search match), then by
  // link count; a label is skipped if its box would overlap one already placed.
  const labelled = new Set<string>();
  const placed: { x1: number; x2: number; y1: number; y2: number }[] = [];
  const shortLabel = (label: string) => (label.length > 42 ? `${label.slice(0, 40)}…` : label);
  const candidates = [...nodes]
    .filter((node) => view.k > 1.6 || node.degree >= hubThreshold || node.id === focus || activeSet?.has(node.id) || matches(node))
    .sort((a, b) => {
      const rank = (node: SimNode) => (node.id === hovered ? 3 : node.id === focus ? 2 : matches(node) ? 1 : 0);
      return rank(b) - rank(a) || b.degree - a.degree;
    });
  for (const node of candidates) {
    const width = shortLabel(node.label).length * 7.4 + 8;
    const cx = (node.x ?? 0) * view.k + view.x;
    const top = (node.y ?? 0) * view.k + view.y + nodeRadius(node.degree) * view.k + 2;
    const box = { x1: cx - width / 2, x2: cx + width / 2, y1: top, y2: top + 18 };
    const force = node.id === hovered || node.id === focus;
    if (!force && placed.some((other) => box.x1 < other.x2 && box.x2 > other.x1 && box.y1 < other.y2 && box.y2 > other.y1)) continue;
    placed.push(box);
    labelled.add(node.id);
  }

  return (
    <div ref={wrapRef} className={cn('relative overflow-hidden rounded-lg border border-border bg-sunken', className)} style={{ height }}>
      <svg
        ref={svgRef}
        width={size.w}
        height={size.h}
        role="img"
        aria-label={`กราฟความเชื่อมโยงของโน้ต ${nodes.length} โน้ต ${graph.links.length} ลิงก์`}
        className="block cursor-grab touch-none select-none active:cursor-grabbing"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
          <g>
            {graph.links.map((link) => {
              const source = byId.get(link.source);
              const target = byId.get(link.target);
              if (!source || !target) return null;
              const lit = hovered && (link.source === hovered || link.target === hovered);
              return (
                <line
                  key={`${link.source}|${link.target}`}
                  x1={source.x} y1={source.y} x2={target.x} y2={target.y}
                  stroke={lit ? 'var(--primary)' : 'var(--link-stroke)'}
                  strokeWidth={(lit ? 1.6 : 1) / view.k}
                  strokeOpacity={activeSet && !lit ? 0.12 : lit ? 0.9 : 0.55}
                  style={{ transition: 'stroke-opacity 150ms' }}
                />
              );
            })}
          </g>
          <g>
            {nodes.map((node) => {
              const r = nodeRadius(node.degree);
              const dimmed = (activeSet && !activeSet.has(node.id)) || (needle && !matches(node));
              const isFocus = node.id === focus;
              const showLabel = labelled.has(node.id);
              return (
                <g
                  key={node.id}
                  data-node={node.id}
                  transform={`translate(${node.x ?? 0} ${node.y ?? 0})`}
                  opacity={dimmed ? 0.18 : 1}
                  style={{ transition: 'opacity 150ms', cursor: 'pointer' }}
                  onPointerEnter={() => setHovered(node.id)}
                  onPointerLeave={() => setHovered(null)}
                  tabIndex={0}
                  role="link"
                  aria-label={`${node.kind} ${node.label}`}
                  onKeyDown={(event) => { if (event.key === 'Enter') router.push(`/read/${node.id}`); }}
                  onFocus={() => setHovered(node.id)}
                  onBlur={() => setHovered(null)}
                  className="outline-none"
                >
                  {(isFocus || hovered === node.id) && <circle r={r + 5} fill="none" stroke="var(--primary)" strokeWidth={1.5 / view.k} />}
                  <circle r={r} fill={kindColor[node.kind] ?? 'var(--muted-foreground)'} stroke={node.pending ? 'var(--pending)' : 'var(--background)'} strokeWidth={(node.pending ? 1.8 : 1.2) / view.k} />
                  {showLabel && (
                    <text
                      y={r + 14 / view.k}
                      textAnchor="middle"
                      fontSize={14 / view.k}
                      fill="var(--foreground)"
                      fillOpacity={hovered === node.id || isFocus ? 1 : 0.78}
                      fontWeight={hovered === node.id || isFocus ? 600 : 400}
                      paintOrder="stroke"
                      stroke="var(--surface-sunken)"
                      strokeWidth={3 / view.k}
                      style={{ pointerEvents: 'none' }}
                    >
                      {shortLabel(node.label)}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </g>
      </svg>

      <div className="absolute right-3 top-3 flex flex-col overflow-hidden rounded-md border border-border bg-card/90 backdrop-blur">
        <button onClick={() => zoomBy(1.25)} className="grid size-9 place-items-center hover:bg-accent" aria-label="ซูมเข้า"><Plus className="size-4" /></button>
        <button onClick={() => zoomBy(0.8)} className="grid size-9 place-items-center border-y border-border hover:bg-accent" aria-label="ซูมออก"><Minus className="size-4" /></button>
        <button onClick={() => fit()} className="grid size-9 place-items-center hover:bg-accent" aria-label="พอดีกรอบ"><Maximize2 className="size-4" /></button>
      </div>

      <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-md bg-card/85 px-3 py-1.5 text-sm text-muted-foreground backdrop-blur">
        {graphKinds.map((item) => (
          <span key={item.kind} className="flex items-center gap-1.5"><span className="size-2.5 rounded-full" style={{ background: item.color }} />{item.label}</span>
        ))}
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full border-2 border-pending" />pending</span>
      </div>
    </div>
  );
}
