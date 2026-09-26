'use client';

import { useRouter } from 'next/navigation';
import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import { Command } from 'lucide-react';
import { Command as CommandRoot, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Button } from '@/components/ui/button';
import { loadSearchIndex, type SearchHit, type SearchIndex } from '@/lib/search';
import { kindLabel, type NavDoc } from '@/lib/wiki';

export function CommandPalette({ docs, className, iconOnly = false }: { docs: NavDoc[]; className?: string; iconOnly?: boolean }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [index, setIndex] = useState<SearchIndex | null>(null);
  const deferred = useDeferredValue(query);
  const router = useRouter();

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    if (open && !index) loadSearchIndex().then(setIndex);
  }, [open, index]);

  const needle = deferred.trim().toLowerCase();
  const titleHits = useMemo(() => {
    const matching = needle ? docs.filter((doc) => doc.title.toLowerCase().includes(needle)) : docs.filter((doc) => doc.kind !== 'source' && doc.kind !== 'schema');
    return matching.slice(0, needle ? 6 : 12);
  }, [docs, needle]);
  const contentHits: SearchHit[] = useMemo(() => (index && needle ? index.search(needle, 12) : []), [index, needle]);

  const go = (href: string) => { setOpen(false); setQuery(''); router.push(href); };

  return (
    <>
      <Button variant="outline" onClick={() => setOpen(true)} className={className} aria-label="ค้นหาทั้ง Wiki (Ctrl+K)">
        <Command className="size-4" aria-hidden />
        {!iconOnly && <span className="flex-1 text-left text-base text-muted-foreground">ค้นหาใน Wiki</span>}
        {!iconOnly && <kbd className="num rounded border border-border px-1.5 text-sm text-muted-foreground">Ctrl K</kbd>}
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen} title="ค้นหาใน Wiki" description="ค้นทั้งชื่อโน้ตและเนื้อหา" className="sm:max-w-3xl">
        <CommandRoot shouldFilter={false}>
          <CommandInput value={query} onValueChange={setQuery} placeholder="ค้นชื่อโน้ตหรือเนื้อหา เช่น กระแสเงินสด, backlog" className="text-base" />
          <CommandList className="max-h-[65vh]">
            <CommandEmpty className="py-8 text-base">ไม่พบคำนี้ในชื่อหรือเนื้อหาโน้ต ลองคำที่สั้นลงหรือสะกดแบบอื่น</CommandEmpty>
            {titleHits.length > 0 && (
              <CommandGroup heading={needle ? 'ชื่อโน้ต' : 'Entity, Concept, Thesis'}>
                {titleHits.map((doc) => (
                  <CommandItem key={doc.slug} value={`title:${doc.slug}`} onSelect={() => go(`/read/${doc.slug}`)} className="gap-3 py-2 text-base">
                    <span className="num w-20 shrink-0 text-sm text-muted-foreground">{kindLabel[doc.kind]}</span>
                    <span className="truncate">{doc.title}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
            {contentHits.length > 0 && (
              <CommandGroup heading="ในเนื้อหา">
                {contentHits.map((hit) => (
                  <CommandItem key={`${hit.slug}#${hit.anchor}`} value={`body:${hit.slug}#${hit.anchor}`} onSelect={() => go(`/read/${hit.slug}${hit.anchor ? `#${hit.anchor}` : ''}`)} className="flex-col items-start gap-1 py-2.5">
                    <span className="flex w-full items-center gap-3 text-base">
                      <span className="num w-20 shrink-0 text-sm text-muted-foreground">{kindLabel[hit.kind]}</span>
                      <span className="truncate font-medium">{hit.title}</span>
                      {hit.heading && hit.heading !== hit.title && <span className="shrink-0 truncate text-sm text-muted-foreground">/ {hit.heading}</span>}
                    </span>
                    <span className="line-clamp-2 pl-23 text-base leading-relaxed text-muted-foreground">
                      {hit.snippet.before}<mark className="rounded-sm bg-primary/25 px-0.5 text-foreground">{hit.snippet.match}</mark>{hit.snippet.after}
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
            {needle && !index && <p className="px-4 py-3 text-base text-muted-foreground">กำลังโหลดดัชนีเนื้อหา…</p>}
          </CommandList>
        </CommandRoot>
      </CommandDialog>
    </>
  );
}
