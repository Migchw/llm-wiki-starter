import { cp, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import GithubSlugger from 'github-slugger';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const vaultRoot = path.resolve(process.env.WIKI_VAULT_PATH || path.join(projectRoot, '..'));
const watchlist = JSON.parse(await readFile(path.join(projectRoot, 'config', 'watchlist.json'), 'utf8'));

function frontmatter(markdown) {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const result = {};
  for (const line of match[1].split(/\r?\n/)) {
    const item = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (!item) continue;
    result[item[1]] = item[2].replace(/^['"]|['"]$/g, '').trim();
  }
  return result;
}

function tagList(value = '') {
  return value.replace(/^\[|\]$/g, '').split(',').map((tag) => tag.replace(/^['"]|['"]$/g, '').trim()).filter(Boolean);
}

function withoutFrontmatter(markdown) {
  return markdown.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '').trim();
}

function cleanText(value) {
  return value
    .replace(/!\[.*?\]\(.*?\)/g, '')
    .replace(/\[\[(?:[^|\]]+\|)?([^\]]+)\]\]/g, '$1')
    .replace(/[*_`>#-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function section(markdown, heading) {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = markdown.match(new RegExp(`^#{1,3} ${escaped}\\s*\\r?\\n([\\s\\S]*?)(?=^#{1,3} |(?![\\s\\S]))`, 'mi'));
  return match ? cleanText(match[1].split(/\r?\n\r?\n/)[0]) : '';
}

// Fallback summary: the first plain paragraph after the frontmatter (skips headings, tables, lists).
function firstParagraph(markdown) {
  const body = withoutFrontmatter(markdown).split(/\r?\n\r?\n/);
  const paragraph = body.find((block) => block.trim() && !/^(#|\||>|[-*] |\d+\. |---)/.test(block.trim()));
  return paragraph ? cleanText(paragraph) : '';
}

function slugify(value) {
  return value.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 100) || 'note';
}

async function markdownFiles(relativeDir, kind) {
  const absoluteDir = path.join(vaultRoot, relativeDir);
  const names = (await readdir(absoluteDir)).filter((name) => name.endsWith('.md') && name !== 'README.md');
  return Promise.all(names.map(async (name) => {
    const markdown = await readFile(path.join(absoluteDir, name), 'utf8');
    const meta = frontmatter(markdown);
    const fileName = path.basename(name, '.md');
    return {
      kind,
      name: fileName,
      slug: `${kind}-${slugify(fileName)}`,
      title: meta.title || fileName,
      date: meta.updated || meta.created || '',
      status: meta.status || '',
      verification: meta.verification || '',
      confidence: meta.confidence || '',
      tags: tagList(meta.tags),
      group: meta.entity_type || meta.archetype || '',
      brief: section(markdown, '60-second brief') || section(markdown, 'What it is') || section(markdown, 'Definition') || firstParagraph(markdown),
      markdown,
      path: `${relativeDir}/${name}`.replaceAll('\\', '/'),
    };
  }));
}

async function singleDocument(relativePath, slug, title) {
  const markdown = await readFile(path.join(vaultRoot, relativePath), 'utf8');
  const meta = frontmatter(markdown);
  return { kind: 'schema', name: path.basename(relativePath, '.md'), slug, title, date: meta.updated || '', status: meta.status || 'active', verification: '', confidence: '', tags: [], group: '', brief: '', markdown, path: relativePath };
}

const [entities, sources, concepts, theses, workflow, lifecycle, fundamentals, projectWorkflow, projectBlueprint, activityLog, ingestQueue] = await Promise.all([
  markdownFiles('02-Wiki/Entities', 'entity'),
  markdownFiles('02-Wiki/Sources', 'source'),
  markdownFiles('02-Wiki/Concepts', 'concept'),
  markdownFiles('02-Wiki/Theses', 'thesis'),
  singleDocument('04-Schema/Workflow.md', 'schema-workflow', 'Research Workflow'),
  singleDocument('04-Schema/Source Lifecycle.md', 'schema-source-lifecycle', 'Source Lifecycle'),
  singleDocument('04-Schema/Obsidian Fundamentals.md', 'schema-obsidian-fundamentals', 'Obsidian Fundamentals'),
  singleDocument('PROJECT-WORKFLOW.md', 'project-workflow', 'Project Workflow'),
  singleDocument('PROJECT-BLUEPRINT.md', 'project-blueprint', 'Project Blueprint'),
  singleDocument('03-Logs/Log.md', 'activity-log', 'Activity Log'),
  singleDocument('05-Index/Ingest Queue.md', 'ingest-queue', 'Ingest Queue'),
]);

const allDocuments = [...sources, ...concepts, ...entities, ...theses, workflow, lifecycle, fundamentals, projectWorkflow, projectBlueprint, activityLog, ingestQueue];
const documentLookup = new Map();
for (const document of allDocuments) {
  documentLookup.set(document.name.toLowerCase(), document);
  documentLookup.set(document.path.replace(/\.md$/i, '').toLowerCase(), document);
}

function readerMarkdown(markdown) {
  return withoutFrontmatter(markdown)
    .replace(/!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g, (_, target) => {
      const normalized = target.replaceAll('\\', '/').replace(/^06-Assets\//, '');
      return `![${path.basename(normalized)}](/vault-assets/${normalized.split('/').map(encodeURIComponent).join('/')})`;
    })
    .replace(/\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]/g, (_, target, label) => {
      const normalized = target.replace(/\.md$/i, '').replaceAll('\\', '/').trim();
      const document = documentLookup.get(normalized.toLowerCase()) || documentLookup.get(path.basename(normalized).toLowerCase());
      const text = (label || path.basename(normalized)).trim();
      return document ? `[${text}](/read/${document.slug})` : `\`${text}\``;
    });
}

// Entities a note links to through a real wikilink (never a bare-name text match).
function linkedEntities(document) {
  if (document.kind === 'entity' || document.kind === 'schema') return [];
  return entities
    .filter((entity) => document.markdown.includes(`Entities/${entity.name}`) || document.markdown.includes(`[[${entity.name}]]`) || document.markdown.includes(`[[${entity.name}|`))
    .map((entity) => entity.title);
}

const documents = allDocuments.map((document) => ({
  slug: document.slug,
  kind: document.kind,
  title: document.title,
  date: document.date,
  status: document.status,
  verification: document.verification,
  confidence: document.confidence,
  tags: document.tags,
  group: document.group,
  related: linkedEntities(document),
  brief: (document.brief || '').slice(0, 520),
  path: document.path,
  markdown: readerMarkdown(document.markdown),
}));

const stocks = watchlist.stocks.map((stock) => {
  const entity = entities.find((item) => item.name === stock.entity);
  const linkedSources = sources
    .filter((source) => source.markdown.includes(`Entities/${stock.entity}`) || source.markdown.includes(`[[${stock.entity}]]`))
    .sort((a, b) => b.date.localeCompare(a.date));
  const linkedConcepts = concepts.filter((concept) => concept.markdown.includes(stock.entity));
  const linkedTheses = theses.filter((thesis) => thesis.markdown.includes(stock.entity) || thesis.name.toLowerCase().includes(stock.ticker.toLowerCase()));
  return {
    ...stock,
    entityPath: entity?.path || '',
    entitySlug: entity?.slug || '',
    sourceCount: linkedSources.length,
    pendingCount: linkedSources.filter((source) => source.verification === 'pending').length,
    conceptCount: linkedConcepts.length,
    thesisCount: linkedTheses.length,
    latestSourceDate: linkedSources[0]?.date || '',
    latestSourceTitle: linkedSources[0]?.title || 'ยังไม่มี source note ที่เชื่อมตรง',
  };
});

const recentSources = sources
  .sort((a, b) => b.date.localeCompare(a.date))
  .slice(0, 12)
  .map(({ markdown, ...source }) => ({
    ...source,
    brief: (source.brief || 'เปิด source note เพื่ออ่านรายละเอียดและ claim table').slice(0, 520),
    entities: stocks.filter((stock) => markdown.includes(`Entities/${stock.entity}`)).map((stock) => stock.ticker),
  }));

// Vault-wide link graph, built only from real [[wikilinks]] (frontmatter included), like Obsidian's graph view.
const graphDocuments = allDocuments.filter((document) => document.kind !== 'schema');
const edgeKeys = new Set();
const graphLinks = [];
for (const document of graphDocuments) {
  for (const match of document.markdown.matchAll(/(?<!!)\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g)) {
    const normalized = match[1].replace(/\.md$/i, '').replaceAll('\\', '/').trim().toLowerCase();
    const target = documentLookup.get(normalized) || documentLookup.get(path.basename(normalized));
    if (!target || target === document || target.kind === 'schema') continue;
    const key = [document.slug, target.slug].sort().join('|');
    if (edgeKeys.has(key)) continue;
    edgeKeys.add(key);
    graphLinks.push({ source: document.slug, target: target.slug });
  }
}
const graph = {
  nodes: graphDocuments.map((document) => ({ id: document.slug, label: document.title, kind: document.kind, pending: document.verification === 'pending' })),
  links: graphLinks,
};

// Full-text search chunks: one chunk per heading section, anchored to the heading id rehype-slug generates.
function headingText(value) {
  return value
    .replace(/\[\[(?:[^|\]]+\|)?([^\]]+)\]\]/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[*_`]/g, '')
    .trim();
}
const searchChunks = [];
for (const document of allDocuments) {
  const slugger = new GithubSlugger();
  let heading = '';
  let anchor = '';
  let buffer = [];
  const flush = () => {
    const text = cleanText(buffer.join('\n').replace(/\|/g, ' ')).slice(0, 1500);
    if (text) searchChunks.push({ slug: document.slug, kind: document.kind, title: document.title, heading, anchor, text });
    buffer = [];
  };
  for (const line of withoutFrontmatter(document.markdown).split(/\r?\n/)) {
    const match = line.match(/^(#{1,4})\s+(.*)$/);
    if (match) {
      flush();
      heading = headingText(match[2]);
      anchor = slugger.slug(heading);
    } else {
      buffer.push(line);
    }
  }
  flush();
}

// Activity feed: rows of the vault log table (newest first, as written in Log.md).
const PIPE = '\u0001';
const activity = activityLog.markdown.split(/\r?\n/)
  .filter((line) => /^\|\s*\d{4}-\d{2}-\d{2}\s*\|/.test(line))
  .map((line) => {
    const cells = line.replace(/\[\[([^\]]*)\]\]/g, (match) => match.replaceAll('|', PIPE)).split('|').slice(1, -1).map((cell) => cleanText(cell.replaceAll(PIPE, '|')));
    return { date: line.match(/\d{4}-\d{2}-\d{2}/)[0], action: cells[1] || '', files: cells[2] || '', decision: cells[3] || '' };
  })
  .slice(0, 12);

const index = {
  generatedAt: new Date().toISOString(),
  vaultName: path.basename(vaultRoot),
  stats: {
    entities: entities.length,
    sources: sources.length,
    concepts: concepts.length,
    theses: theses.length,
    pending: sources.filter((source) => source.verification === 'pending').length,
    pendingConcepts: concepts.filter((concept) => concept.verification === 'pending').length,
  },
  stocks,
  activity,
  recentSources,
  documents,
  graph,
};

await mkdir(path.join(projectRoot, 'data'), { recursive: true });
await mkdir(path.join(projectRoot, 'public', 'vault-assets'), { recursive: true });
await cp(path.join(vaultRoot, '06-Assets'), path.join(projectRoot, 'public', 'vault-assets'), { recursive: true, force: true });
await writeFile(path.join(projectRoot, 'data', 'wiki-index.json'), `${JSON.stringify(index, null, 2)}\n`, 'utf8');
await writeFile(path.join(projectRoot, 'data', 'search-index.json'), `${JSON.stringify({ chunks: searchChunks })}\n`, 'utf8');
console.log(`Indexed ${sources.length} source notes, ${entities.length} entities, and ${documents.length} readable documents from ${vaultRoot}`);
