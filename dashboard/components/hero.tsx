'use client';

import { useReducedMotion } from 'motion/react';
import DecryptedText from '@/components/DecryptedText';
import LetterGlitch from '@/components/LetterGlitch';
import { useTheme } from '@/components/use-theme';

export function Hero({ vaultName, indexedAt }: { vaultName: string; indexedAt: string }) {
  const reduced = useReducedMotion();
  const light = useTheme() === 'light';
  const stamp = indexedAt ? new Date(indexedAt).toISOString().slice(0, 16).replace('T', ' ') + 'Z' : 'NOT BUILT';

  return (
    <section className="relative overflow-hidden rounded-lg border border-border bg-card">
      {!reduced && (
        <div className="absolute inset-0 opacity-40 [mask-image:linear-gradient(90deg,transparent_10%,#000_100%)]" aria-hidden>
          <LetterGlitch key={light ? 'light' : 'dark'} lightMode={light} backgroundColor={light ? '#fbf8f1' : '#171614'} glitchColors={light ? ['#e6d9bd', '#c98a1c', '#d8cbb0'] : ['#3a2d12', '#f5a623', '#5a4a26']} glitchSpeed={60} outerVignette centerVignette={false} smooth />
        </div>
      )}
      <div className="relative px-6 py-10 sm:px-10 sm:py-14">
        <h1 className="num text-4xl font-bold tracking-tight sm:text-6xl">
          {reduced ? 'WIKI MARKET DESK' : <DecryptedText text="WIKI MARKET DESK" animateOn="view" sequential speed={45} maxIterations={14} characters="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&" className="text-foreground" encryptedClassName="text-primary" />}
        </h1>
        <p className="mt-4 max-w-xl text-lg leading-relaxed text-muted-foreground">
          อ่านและตรวจงานวิจัยจาก Wiki ในวอลต์ได้จากที่เดียว ทุกตัวเลขและสถานะ verification มาจากโน้ตต้นทาง
        </p>
        <p className="meta mt-5">index {stamp} · vault {vaultName}</p>
      </div>
    </section>
  );
}
