import type { Metadata } from 'next';
import Library from '@/components/library';
import { docSummaries } from '@/lib/wiki-data';

export const metadata: Metadata = {
  title: 'คลังความรู้ · Wiki Market Desk',
  description: 'รายการ Source, Concept, Entity และ Thesis ทั้งหมดในวอลต์',
};

export default function LibraryPage() {
  return <Library docs={docSummaries()} />;
}
