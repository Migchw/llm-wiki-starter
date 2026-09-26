'use client';

import Link from 'next/link';
import { isValidElement, useEffect, useId, useState, type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSlug from 'rehype-slug';
import { FileText, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { KindBadge, VerificationBadge } from '@/components/status-badge';
import { NotesExplorer } from '@/components/notes-explorer';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useTheme } from '@/components/use-theme';
import { cn } from '@/lib/utils';
import { kindLabel, type DocSummary, type WikiDoc } from '@/lib/wiki';

const darkVars = {
  fontFamily: 'Anuphan, sans-serif', fontSize: '18px', background: '#1a1917',
  primaryColor: '#2b2822', primaryTextColor: '#f1ece2', primaryBorderColor: '#8a7440',
  secondaryColor: '#24221d', tertiaryColor: '#1f1d19', lineColor: '#d9a441', textColor: '#e8e2d4',
  edgeLabelBackground: '#1a1917', clusterBkg: '#211f1b', clusterBorder: '#514a3a',
};
const lightVars = {
  fontFamily: 'Anuphan, sans-serif', fontSize: '18px', background: '#f6f2e9',
  primaryColor: '#fffaf0', primaryTextColor: '#2a2418', primaryBorderColor: '#b98a2e',
  secondaryColor: '#f3ecdc', tertiaryColor: '#fbf6ea', lineColor: '#9a6a0c', textColor: '#2a2418',
  edgeLabelBackground: '#f6f2e9', clusterBkg: '#f3ecdc', clusterBorder: '#d6c79f',
};

function MermaidDiagram({ chart }: { chart: string }) {
  const theme = useTheme();
  const reactId = useId();
  const id = `mermaid-${reactId.replace(/:/g, '')}`;
  const [svg, setSvg] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    import('mermaid').then(async ({ default: mermaid }) => {
      try {
        await document.fonts.ready;
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'strict',
          theme: 'base',
          fontFamily: 'Anuphan, sans-serif',
          themeVariables: theme === 'dark' ? darkVars : lightVars,
          flowchart: { htmlLabels: false, useMaxWidth: false, wrappingWidth: 340, nodeSpacing: 56, rankSpacing: 72, padding: 22 },
        });
        const result = await mermaid.render(id, chart);
        if (active) setSvg(result.svg);
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : 'Mermaid render error');
      }
    });
    return () => { active = false; };
  }, [chart, id, theme]);

  if (error) return <pre className="mermaid-error"><code>{chart}</code><span>{error}</span></pre>;
  if (!svg) return <div className="mermaid-loading">กำลังวาดแผนภาพ…</div>;
  return <div className="mermaid-diagram" dangerouslySetInnerHTML={{ __html: svg }} />;
}

type Related = { slug: string; title: string; kind: string };

export default function MarkdownReader({ document, related, docs }: { document: WikiDoc; related: Related[]; docs: DocSummary[] }) {
  const [showList, setShowList] = useState(true);

  return (
    <main className="mx-auto w-full max-w-[1800px] px-6 py-6">
      <div className={cn('grid gap-6', showList && 'xl:grid-cols-[21rem_minmax(0,1fr)]')}>
        {showList && (
          <aside className="hidden xl:sticky xl:top-6 xl:block xl:h-[calc(100vh-3rem)]">
            <NotesExplorer docs={docs} currentSlug={document.slug} />
          </aside>
        )}

        <div className="min-w-0">
          <div className="mb-5 flex items-center justify-between gap-3 border-b border-border pb-4">
            <nav aria-label="ตำแหน่งโน้ต" className="flex items-center gap-2 text-base text-muted-foreground">
              <Link href="/library" className="hover:text-foreground">คลังความรู้</Link>
              <span aria-hidden>/</span>
              <span className="text-foreground">{kindLabel[document.kind] || document.kind}</span>
            </nav>
            <Button variant="outline" size="sm" className="hidden h-9 gap-2 px-3 text-base xl:inline-flex" onClick={() => setShowList((value) => !value)} aria-pressed={showList}>
              {showList ? <PanelLeftClose className="size-4" aria-hidden /> : <PanelLeftOpen className="size-4" aria-hidden />}
              {showList ? 'ซ่อนรายการโน้ต' : 'แสดงรายการโน้ต'}
            </Button>
          </div>

          <div className="grid items-start gap-8 2xl:grid-cols-[minmax(0,54rem)_16rem]">
            <div className="min-w-0">
              <header className="mb-6">
                <div className="flex flex-wrap items-center gap-2">
                  <KindBadge label={kindLabel[document.kind] || document.kind} kind={document.kind} />
                  <VerificationBadge value={document.verification} />
                  {document.confidence && <span className="num rounded-md border border-border px-2 py-0.5 text-sm text-muted-foreground">confidence {document.confidence}</span>}
                  {document.date && <span className="num text-sm text-muted-foreground">updated {document.date}</span>}
                </div>
                <h1 className="mt-4 text-3xl leading-tight sm:text-4xl">{document.title}</h1>
                <p className="num mt-3 flex items-center gap-2 text-sm text-muted-foreground"><FileText className="size-4 shrink-0" aria-hidden />{document.path}</p>
              </header>

              <article className="markdown-body rounded-lg border border-border bg-card px-12 py-12">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeSlug]}
                  components={{
                    pre({ children }: { children?: ReactNode }) {
                      const child = Array.isArray(children) ? children[0] : children;
                      if (isValidElement<{ className?: string; children?: ReactNode }>(child) && child.props.className === 'language-mermaid') {
                        return <MermaidDiagram chart={String(child.props.children).replace(/\n$/, '')} />;
                      }
                      return <pre>{children}</pre>;
                    },
                    a({ href, children }) {
                      const external = href?.startsWith('http');
                      if (href?.startsWith('/')) return <Link href={href}>{children}</Link>;
                      return <a href={href} target={external ? '_blank' : undefined} rel={external ? 'noreferrer' : undefined}>{children}</a>;
                    },
                  }}
                >{document.markdown}</ReactMarkdown>
              </article>
            </div>

            <aside className="2xl:sticky 2xl:top-6" aria-label="โน้ตที่เชื่อมโยง">
              <h2 className="mb-3 text-lg">โน้ตที่เชื่อมกัน</h2>
              <div className="grid gap-2 md:grid-cols-2 2xl:grid-cols-1">
                {related.length ? related.map((item) => (
                  <Link key={item.slug} href={`/read/${item.slug}`} className="block outline-none">
                    <Card className="gap-1 py-3 transition-colors hover:border-primary/60 focus-visible:border-primary">
                      <CardContent className="px-4">
                        <KindBadge label={kindLabel[item.kind] || item.kind} kind={item.kind} className="h-5 text-sm" />
                        <span className="mt-2 block text-base leading-snug">{item.title}</span>
                      </CardContent>
                    </Card>
                  </Link>
                )) : <p className="text-base text-muted-foreground">โน้ตนี้ไม่มีลิงก์ไปโน้ตอื่นที่เปิดอ่านได้</p>}
              </div>
            </aside>
          </div>
        </div>
      </div>
    </main>
  );
}
