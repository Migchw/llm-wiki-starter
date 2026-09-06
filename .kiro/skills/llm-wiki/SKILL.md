---
name: llm-wiki
description: Ingest, organize, verify, and synthesize investing research in this Obsidian LLM Wiki. Use when handling articles, videos, PDFs, filings, transcripts, source notes, concepts, entities, investment theses, wiki links, vault metadata, or knowledge-base retrieval for this project.
---

# LLM Wiki workflow

Read `.kiro/steering/00-operating-manual.md`, `05-Index/Ingest Queue.md`, `04-Schema/Workflow.md`, `04-Schema/Source Lifecycle.md`, and the relevant template in `04-Schema/Templates/` before writing.

## Route work

1. Triage the source in Ingest Queue. Do not process all Raw; choose only `P0/P1` or explicit `next` items.
2. Put source snapshots in `01-Raw/<media-type>/`; preserve them unchanged.
3. Create a one-to-one readable source note in `02-Wiki/Sources/` from the template.
4. Separate fact, interpretation, and open question in its claim table.
5. For a material investment claim, invoke the fact-review workflow (`.kiro/personas/feynman.md`) before creating a thesis.
6. Create concepts only when they have an investor implication, a boundary, and source links.
7. Add meaningful wikilinks, append the activity log, and update the Queue status.

## Writing rules

- Use kebab-case English filenames and `YYYY-MM-DD` dates.
- Use YAML frontmatter exactly as provided by templates.
- Do not turn tags into evidence or treat shared tags as a relationship.
- Use `[[wikilinks]]` only when the relationship can be stated in prose.

## Tool selection

- Use `scripts/fetch_source.py` (Python-first: bs4 / playwright / markitdown) for raw capture and document conversion, then verify tables/numbers against the original.
- Use a transcript acquisition method (`.kiro/personas/rene.md`) for video/audio; preserve source URL and quality status.
- Use deterministic scripts (`python scripts/wiki_tool.py --lint`) for link/frontmatter checks; do not visually guess broken links.
