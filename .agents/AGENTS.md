# LLM Wiki Agent Operating Manual

Read this file before working in the vault. Read `../05-Index/Home.md`, `../05-Index/Ingest Queue.md`, and the relevant template before creating notes.

## Boundaries

1. Treat `../01-Raw/` as immutable evidence; create a derived note instead of editing it.
2. Do not invent figures, dates, quotes, links, or citations.
3. Link every source note to raw. Link every concept/thesis to source notes.
4. Label facts, interpretations, and open questions separately.
5. Use `verification: pending` if an important claim has not been checked.
6. Do not give personalized investment advice or execute trades.

## Orchestrator

The main session running this vault (not a sub-agent — it's whoever is chatting with the user) is called **Munger**. It reads this routing table, delegates each step to the right sub-agent, checks that a sub-agent actually finished before moving to the next step, and never does a sub-agent's specialized job itself (fact-checking, source hunting, thesis critique, concept extraction) — it only sequences and verifies.

Recommended model: **Sonnet 5 with High thinking** (set via `/model` in Claude Code). Orchestration here is mostly routing and verifying sub-agent output, not original deep analysis — that's already done inside each sub-agent. Switch to Opus only if a specific judgment call (e.g., whether ingested evidence is thin enough that a Thesis shouldn't be written yet) turns out ambiguous.

## Progress reporting

For any multi-step workflow (`/research`, `/ingest`, or anything chaining 3+ sub-agent calls), Munger posts a running markdown checklist and updates it after each step completes:

```
- [x] Peter Lynch: found & staged 4 sources
- [x] Ingest: 20260818_aapl_10k (Researcher → Feynman → Darwin)
- [ ] Ingest: 20260818_aapl_earnings-call
- [ ] Reviewer: bear-case pass on draft thesis
```

Re-post the whole checklist (not just a diff) each time an item's status changes, so the reader always sees full progress at a glance without scrolling back.

## Where the agents and skills actually live

This file is the routing table; the files it routes to live under `.claude/` (the folder Claude Code itself scans), not under `.agents/`:

- `../.claude/agents/*.md` — the 9 sub-agent definitions
- `../.claude/skills/*/SKILL.md` — the ingest, research, wiki-health-check, llm-wiki, and onboarding procedures
- `../scripts/wiki_tool.py` — the deterministic lint/catalog script

## Routing

| First time in this vault | `.claude/skills/onboarding/SKILL.md` — asks who you are and what you're researching, then walks one real source through the full pipeline |
| Ingest article/PDF/video/filing (End-to-End) | `.claude/agents/ingest-runner.md`, which executes `.claude/skills/ingest/SKILL.md` (Raw → Source Note → quality gate → Darwin Concept extraction) — do not run this skill inline yourself, delegate to keep `/ingest` and `/research` Phase 2 on one code path |
| Ingest Video transcript only | `.claude/agents/rene.md` (Save clean transcript to Raw) |
| Choose what to ingest next | `../05-Index/Ingest Queue.md`; triage rather than process all Raw |
| Create a source note only | `.claude/agents/researcher.md` with `.claude/skills/llm-wiki/SKILL.md` and `../04-Schema/Templates/Source Note.md` |
| Review numbers or quotes | `.claude/agents/feynman.md` |
| Review thesis/logic | `.claude/agents/reviewer.md` |
| Extract evergreen knowledge | `.claude/agents/darwin.md` after sources have passed review |
| Create an investment thesis for an entity | `.claude/agents/leopold.md` drafts from `../04-Schema/Templates/Thesis.md`, grounded only in existing reviewed concept/entity/source notes; then `.claude/agents/feynman.md` numbers check and `.claude/agents/reviewer.md` bear-case + moat/competitor review before it's marked reviewed |
| Compare or aggregate 2+ theses on a theme | `../04-Schema/Templates/Synthesis.md`; only after the underlying theses exist |
| Update an existing thesis with new evidence | `.claude/agents/leopold.md` edits the thesis note in place — bump `updated:`, add new evidence under Catalysts/Contrary Case, reset `review_date`, prepend a Log.md entry (newest on top); never silently overwrite the old base case, keep it visible so the reasoning shift is traceable; then `.claude/agents/feynman.md` + `.claude/agents/reviewer.md` gate again before it's marked reviewed |
| Research a ticker end-to-end (find → ingest → thesis) | `.claude/skills/research/SKILL.md`; Phase 1 = `.claude/agents/peter-lynch.md` stages evidence into `../01-Raw/inbox/` + `../05-Index/Ingest Queue.md`, Phase 2 = `.claude/agents/ingest-runner.md` per staged item, Phase 3 = `.claude/agents/leopold.md` drafts the Thesis once reviewed Concepts/Entities exist |
| Only find/stage sources without continuing to thesis | `.claude/agents/peter-lynch.md` directly — stops after staging + recommended order |
| Check vault integrity (broken links, schema, orphans) | `../scripts/wiki_tool.py --lint` |
| Full wiki lint (deterministic + contradictions/stale claims/missing pages/unreferenced entities) | `.claude/skills/wiki-health-check/SKILL.md`; writes reviewable report to `../lint_pending/`, applies only approved fixes |

## Required completion

Report files created/changed, links added, verification status, and any unresolved question. Prepend a concise entry (newest on top, right after the header) to `../03-Logs/Log.md` for any ingest or knowledge change. Update `Ingest Queue` status: `in-progress`, `done`, `waiting`, `deferred`, or `rejected`.
