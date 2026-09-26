'use client';

import { useReducedMotion } from 'motion/react';
import CountUp from '@/components/CountUp';
import SpotlightCard from '@/components/SpotlightCard';
import { cn } from '@/lib/utils';

export type Stat = { label: string; value: number; hint: string; tone?: 'default' | 'pending' };

/** One instrument panel instead of four identical cards; the spotlight follows the cursor. */
export function StatStrip({ stats }: { stats: Stat[] }) {
  const reduced = useReducedMotion();
  return (
    <SpotlightCard className="grid grid-cols-2 divide-x divide-border xl:grid-cols-4" aria-label="สถิติ Wiki">
      {stats.map((stat) => (
        <div key={stat.label} className="px-6 py-5 first:pl-6">
          <p className="text-base text-muted-foreground">{stat.label}</p>
          <p className={cn('num mt-2 text-5xl font-medium leading-none', stat.tone === 'pending' && 'text-pending')}>
            {reduced ? stat.value : <CountUp to={stat.value} duration={1.4} />}
          </p>
          <p className="mt-2 text-base text-muted-foreground">{stat.hint}</p>
        </div>
      ))}
    </SpotlightCard>
  );
}
