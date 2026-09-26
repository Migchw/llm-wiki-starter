'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Library, ListChecks, Network, ScrollText, Workflow } from 'lucide-react';
import { CommandPalette } from '@/components/command-palette';
import { Separator } from '@/components/ui/separator';
import { ThemeToggle } from '@/components/theme-toggle';
import { cn } from '@/lib/utils';
import type { NavDoc } from '@/lib/wiki';

const nav = [
  { href: '/', label: 'ภาพรวม', icon: LayoutDashboard },
  { href: '/library', label: 'คลังความรู้', icon: Library },
  { href: '/graph', label: 'Graph View', icon: Network },
  { href: '/read/activity-log', label: 'Activity Log', icon: ScrollText },
  { href: '/read/ingest-queue', label: 'Ingest Queue', icon: ListChecks },
  { href: '/read/schema-workflow', label: 'Workflow', icon: Workflow },
];

function Brand() {
  return (
    <Link href="/" className="flex items-center gap-3 outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-md">
      <span className="num grid size-9 place-items-center rounded-md bg-primary text-lg font-bold text-primary-foreground">W</span>
      <span className="leading-tight">
        <strong className="block whitespace-nowrap font-heading text-base">Wiki Market Desk</strong>
        <span className="meta block">Local research</span>
      </span>
    </Link>
  );
}

export function AppShell({ docs, vaultName, children }: { docs: NavDoc[]; vaultName: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const isActive = (href: string) => (href === '/' ? pathname === '/' : pathname === href || (href === '/library' && pathname.startsWith('/library')));

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar/95 px-4 py-6 backdrop-blur lg:flex">
        <div className="px-2"><Brand /></div>
        <CommandPalette docs={docs} className="mt-7 h-11 justify-start gap-2 px-3" />
        <nav aria-label="เมนูหลัก" className="mt-6 grid gap-1">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              aria-current={isActive(href) ? 'page' : undefined}
              className={cn(
                'flex items-center gap-3 rounded-md border-l-2 border-transparent px-3 py-2.5 text-base text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground',
                isActive(href) && 'border-primary bg-sidebar-accent text-foreground',
              )}
            >
              <Icon className="size-4" aria-hidden />{label}
            </Link>
          ))}
        </nav>
        <div className="mt-auto">
          <Separator className="mb-4" />
          <div className="flex items-center gap-3 px-2">
            <span className="size-2.5 rounded-full bg-positive" aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="meta">เชื่อมต่อ vault</p>
              <p className="num truncate text-sm">{vaultName}</p>
            </div>
            <ThemeToggle className="size-9 shrink-0" />
          </div>
        </div>
      </aside>

      <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur lg:hidden">
        <div className="flex items-center justify-between gap-3 px-4 py-3">
          <Brand />
          <div className="flex items-center gap-2"><ThemeToggle className="size-10" /><CommandPalette docs={docs} iconOnly className="size-10 shrink-0 px-0" /></div>
        </div>
        <nav aria-label="เมนูหลัก" className="thin-scroll flex gap-1 overflow-x-auto px-3 pb-2">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href} aria-current={isActive(href) ? 'page' : undefined} className={cn('flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-base text-muted-foreground', isActive(href) && 'bg-accent text-foreground')}>
              <Icon className="size-4" aria-hidden />{label}
            </Link>
          ))}
        </nav>
      </header>

      <div className="lg:pl-64">{children}</div>
    </div>
  );
}
