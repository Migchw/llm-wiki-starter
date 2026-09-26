import type { Metadata } from 'next';
import Link from 'next/link';
import { docSummaries, wiki } from '@/lib/wiki-data';
import MarkdownReader from './reader';

type PageProps = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return wiki.documents.map((document) => ({ slug: document.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const document = wiki.documents.find((item) => item.slug === slug);
  return document
    ? { title: `${document.title} · Wiki Market Desk`, description: document.brief || `อ่าน ${document.title} จาก local LLM Wiki` }
    : { title: 'ไม่พบโน้ต · Wiki Market Desk', description: 'ไม่พบ Markdown note ที่ต้องการ' };
}

export default async function ReaderPage({ params }: PageProps) {
  const { slug } = await params;
  const document = wiki.documents.find((item) => item.slug === slug);

  if (!document) {
    return (
      <main className="grid min-h-[70vh] place-content-center gap-3 text-center">
        <p className="text-xl">ไม่พบ Markdown note นี้</p>
        <Link href="/library" className="text-primary hover:underline">← กลับไปคลังความรู้</Link>
      </main>
    );
  }

  const related = wiki.documents
    .filter((item) => item.slug !== document.slug && document.markdown.includes(`/read/${item.slug}`))
    .slice(0, 8)
    .map(({ slug: relatedSlug, title, kind }) => ({ slug: relatedSlug, title, kind }));

  return <MarkdownReader document={document} related={related} docs={docSummaries()} />;
}
