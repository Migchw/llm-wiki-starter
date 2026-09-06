---
name: wiki-health-check
description: Lint is the wiki's health check. Runs a deterministic pass (broken links, orphaned pages, missing frontmatter, empty sections) via scripts/wiki_tool.py --lint, then a semantic pass (contradictions, stale claims, missing pages, unreferenced entities). Writes a detailed report with suggested fixes to lint_pending/ for review and approval — nothing is changed until approved. Use when the user asks to lint, health-check, or audit the wiki, or via /wiki-health-check.
---

# Wiki lint / health check

Two phases: deterministic (script, exact) then semantic (you, reads the actual notes). Do not skip either — the script cannot see meaning, and you should not re-derive by hand what it computes exactly. Nothing gets edited in this skill — it only produces a reviewable report.

## Phase 1: Deterministic

Run:

```
python scripts/wiki_tool.py --lint
```

Catches: broken `[[wikilinks]]`, orphaned pages (0 inbound links), dead-end pages (0 outbound links), missing/invalid frontmatter per `04-Schema/Templates/`, and empty sections (a required header like `## Claim Table` or `## Investor Implication` exists but has no content before the next header). Carry its findings into the report verbatim — do not re-verify by hand.

## Phase 2: Semantic

Read every file under `02-Wiki/Concepts/`, `02-Wiki/Entities/`, `02-Wiki/Sources/`, `02-Wiki/Theses/`, `02-Wiki/Synthesis/` (skip `README.md` and `.gitkeep`). Only report a finding you can point to with a file path and quote/line — no vague impressions.

1. **Contradictions** — two notes making incompatible factual claims about the same entity/metric/date (e.g. different capacity figures for the same fab, conflicting guidance numbers). Cite both files.
2. **Stale claims** — a note whose `verification`/`review_date` predates a newer Source Note on the same topic that would change or update the claim. Compare `created`/`published`/`review_date` frontmatter across related notes, not gut feel.
3. **Missing pages** — a term used repeatedly as prose (not already `[[linked]]`) across 2+ notes that reads like a durable mental model (per `04-Schema/Concept Checklist.md`), but has no note in `02-Wiki/Concepts/`.
4. **Unreferenced entities** — an Entity note with 0 or near-0 inbound links from Source/Concept/Thesis notes despite being discussed in the vault's prose, or an entity mentioned by name in running text that never resolved to a link. Cross-check against Phase 1's orphan list — an unreviewed, freshly-created note is not the same finding as a stale unreferenced one.

## Output: write a report to lint_pending/, do not edit notes

Create `lint_pending/YYYYMMDD-lint-report.md`:

```markdown
---
type: lint-report
status: pending
created: YYYY-MM-DD
---

# Lint Report — YYYY-MM-DD

## Deterministic

### Broken links
- [ ] `path/to/file.md` line N: `` [[target]] `` does not resolve — fix: <rename target / create missing note / remove link>

### Missing frontmatter
- [ ] `path/to/file.md` — missing `field` (type: `note-type`) — fix: <value to add, or "ask user">

### Empty sections
- [ ] `path/to/file.md` — `## Section` header present, no content — fix: <what belongs there, drawn from the note's other content, or "ask user">

### Orphaned / dead-end pages
- [ ] `path/to/file.md` — 0 inbound links — fix: <which note(s) should link to it>

## Semantic

### Contradictions
- [ ] `` [[Note A]] `` vs `` [[Note B]] ``: <the conflicting claim, one line each> — fix: <which figure is likely correct and why, or "needs primary-source check">

### Stale claims
- [ ] `` [[Note]] `` (reviewed YYYY-MM-DD) superseded by `` [[Newer Source]] `` (YYYY-MM-DD) — fix: <what to update>

### Missing pages
- [ ] "<term>" mentioned in `` [[Note A]] ``, `` [[Note B]] `` — fix: create Concept note per `04-Schema/Templates/Concept.md`

### Unreferenced entities
- [ ] `` [[Entity]] `` — fix: <which note(s) should link to it>
```

Every checkbox item needs a concrete suggested fix, not just a description of the problem — that's what makes the report reviewable instead of just another lint dump. If no confident fix exists, say `"ask user"` explicitly rather than guessing.

Do not check any boxes yourself, and do not edit `02-Wiki/`, `01-Raw/`, or frontmatter in this pass — this phase produces the report only.

## Applying approved fixes (separate, explicit request)

Only when the user asks to apply a report's approved fixes:
1. Read the report in `lint_pending/`. Apply only items checked `[x]`. Skip `[ ]` (undecided) and `[-]` (rejected) items entirely.
2. For each applied item, make the exact edit described in its "fix" — nothing broader (no adjacent cleanup, no reformatting).
3. If a fix can't be applied as written (e.g. the file changed since the report was generated), stop on that item and say so instead of improvising.
4. Once every item in the report is `[x]` or `[-]` (none left `[ ]`), append a summary section to `05-Index/Vault Health.md` (newest first) — counts applied/rejected and a one-line log entry — then delete the report from `lint_pending/`.
5. Prepend one line to `03-Logs/Log.md` (newest on top, right after the header) noting the run (e.g. "Wiki lint: N found, M applied, K rejected — see [[05-Index/Vault Health]]").

## Boundaries

- Do not invent contradictions or gaps to fill out the report — an empty section is a valid, good result.
- Do not apply any fix without an explicit `[x]` from the user, even when the fix looks obviously correct.
- If a finding needs a primary-source check to confirm, say so explicitly in the fix rather than asserting it as fact.
