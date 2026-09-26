import type { Metadata } from 'next';
import GraphExplorer from '@/components/graph-explorer';
import { wiki } from '@/lib/wiki-data';

export const metadata: Metadata = {
  title: 'Graph View · Wiki Market Desk',
  description: 'กราฟความเชื่อมโยงของโน้ตทั้งหมดในวอลต์ จาก wikilink',
};

export default function GraphPage() {
  return <GraphExplorer graph={wiki.graph} />;
}
