/**
 * In-browser full-text search over heading-sized chunks of every note.
 *
 * Ranking is BM25 (the lexical half of qmd's hybrid search). Thai has no spaces between
 * words, so tokens come from Intl.Segmenter('th'), which splits Thai and English alike.
 * A match in the note title or section heading is boosted, like a field weight.
 */

export type SearchChunk = { slug: string; kind: string; title: string; heading: string; anchor: string; text: string };
export type SearchHit = SearchChunk & { score: number; snippet: { before: string; match: string; after: string } };

const K1 = 1.2;
const B = 0.75;
const segmenter = typeof Intl !== 'undefined' && 'Segmenter' in Intl ? new Intl.Segmenter('th', { granularity: 'word' }) : null;

export function tokenize(value: string): string[] {
  const text = value.toLowerCase();
  if (!segmenter) return text.split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  const tokens: string[] = [];
  for (const part of segmenter.segment(text)) {
    if (part.isWordLike) tokens.push(part.segment);
  }
  return tokens;
}

type Doc = { chunk: SearchChunk; tf: Map<string, number>; length: number; fieldTokens: Set<string> };

export class SearchIndex {
  private docs: Doc[];
  private df = new Map<string, number>();
  private avgLength: number;

  constructor(chunks: SearchChunk[]) {
    this.docs = chunks.map((chunk) => {
      const tokens = tokenize(chunk.text);
      const tf = new Map<string, number>();
      for (const token of tokens) tf.set(token, (tf.get(token) ?? 0) + 1);
      return { chunk, tf, length: tokens.length, fieldTokens: new Set(tokenize(`${chunk.title} ${chunk.heading}`)) };
    });
    for (const doc of this.docs) {
      for (const token of new Set([...doc.tf.keys(), ...doc.fieldTokens])) this.df.set(token, (this.df.get(token) ?? 0) + 1);
    }
    this.avgLength = this.docs.reduce((sum, doc) => sum + doc.length, 0) / Math.max(1, this.docs.length);
  }

  search(query: string, limit = 12): SearchHit[] {
    const terms = [...new Set(tokenize(query))];
    if (!terms.length) return [];
    const total = this.docs.length;
    const hits: SearchHit[] = [];
    for (const doc of this.docs) {
      let score = 0;
      let matched = 0;
      for (const term of terms) {
        const df = this.df.get(term) ?? 0;
        if (!df) continue;
        const idf = Math.log(1 + (total - df + 0.5) / (df + 0.5));
        const tf = doc.tf.get(term) ?? 0;
        const inField = doc.fieldTokens.has(term);
        if (!tf && !inField) continue;
        matched += 1;
        score += idf * ((tf * (K1 + 1)) / (tf + K1 * (1 - B + (B * doc.length) / this.avgLength)));
        if (inField) score += idf * 1.5;
      }
      if (!matched) continue;
      // Prefer chunks that contain every query term.
      score *= matched / terms.length;
      hits.push({ ...doc.chunk, score, snippet: snippet(doc.chunk.text, [query.trim().toLowerCase(), ...terms]) });
    }
    hits.sort((a, b) => b.score - a.score);
    // One result per section, at most three sections per note.
    const perNote = new Map<string, number>();
    return hits.filter((hit) => {
      const count = perNote.get(hit.slug) ?? 0;
      perNote.set(hit.slug, count + 1);
      return count < 3;
    }).slice(0, limit);
  }
}

function snippet(text: string, terms: string[]) {
  const lower = text.toLowerCase();
  let at = -1;
  let term = '';
  // The whole query first (so a Thai phrase is highlighted as one), then single terms, longest first.
  const [phrase, ...rest] = terms;
  for (const candidate of [phrase, ...rest.sort((a, b) => b.length - a.length)]) {
    at = lower.indexOf(candidate);
    if (at >= 0) { term = candidate; break; }
  }
  if (at < 0) return { before: text.slice(0, 160), match: '', after: text.length > 160 ? '…' : '' };
  const start = Math.max(0, at - 70);
  const end = Math.min(text.length, at + term.length + 110);
  return {
    before: `${start > 0 ? '…' : ''}${text.slice(start, at)}`,
    match: text.slice(at, at + term.length),
    after: `${text.slice(at + term.length, end)}${end < text.length ? '…' : ''}`,
  };
}

let loading: Promise<SearchIndex> | null = null;

/** Loads the generated chunk file on first use (it is split out of the main bundle). */
export function loadSearchIndex() {
  loading ??= import('@/data/search-index.json').then((module) => new SearchIndex((module.default as { chunks: SearchChunk[] }).chunks));
  return loading;
}
