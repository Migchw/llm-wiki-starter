import type { Metadata } from 'next';
import '@fontsource/anuphan/400.css';
import '@fontsource/anuphan/500.css';
import '@fontsource/anuphan/600.css';
import '@fontsource/anuphan/700.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/500.css';
import '@fontsource/jetbrains-mono/700.css';
import './globals.css';
import { AppShell } from '@/components/app-shell';
import { TooltipProvider } from '@/components/ui/tooltip';
import { navDocs, wiki } from '@/lib/wiki-data';

export const metadata: Metadata = {
  title: 'Wiki Market Desk',
  description: 'Local research dashboard generated from an LLM Wiki vault.',
};

const themeScript = "(function(){try{var t=localStorage.getItem('theme');var d=t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.classList.toggle('dark',d)}catch(e){}})()";

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="th" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
      <body>
        <TooltipProvider>
          <AppShell docs={navDocs()} vaultName={wiki.vaultName}>{children}</AppShell>
        </TooltipProvider>
      </body>
    </html>
  );
}
