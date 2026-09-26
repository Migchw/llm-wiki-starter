import Overview from '@/components/overview';
import type { SourceItem } from '@/lib/wiki';
import { earnings, market, wiki } from '@/lib/wiki-data';

export default function Home() {
  const pendingSources: SourceItem[] = wiki.documents
    .filter((doc) => doc.kind === 'source' && doc.verification === 'pending')
    .sort((a, b) => b.date.localeCompare(a.date))
    .map(({ slug, title, date, verification, brief, path }) => ({ slug, title, date, verification, brief, path, entities: [] }));

  return (
    <Overview
      vaultName={wiki.vaultName}
      generatedAt={wiki.generatedAt}
      stats={wiki.stats}
      stocks={wiki.stocks}
      recentSources={wiki.recentSources}
      pendingSources={pendingSources}
      activity={wiki.activity}
      graph={wiki.graph}
      market={market}
      earnings={earnings}
    />
  );
}
