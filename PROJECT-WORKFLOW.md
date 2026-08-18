# Project Workflow

How this vault actually runs: who commands whom, what gets delegated, what skill each step uses, and where the output file lands. Source of truth for the rules themselves is `.agents/AGENTS.md` — this file is the map on top of it.

## Actors at a glance

| Actor | Type | Job | Reads / uses | Writes to |
|---|---|---|---|---|
| **Munger** | orchestrating session (not a sub-agent — this is the main Claude Code session itself) | Plans, delegates, checks each sub-agent actually finished, posts the running checklist, decides what happens next | `.agents/AGENTS.md` routing table | `03-Logs/Log.md`, `05-Index/Ingest Queue.md` status |
| `peter-lynch` | sub-agent | Finds & verifies primary sources for a ticker, stages them, triages priority | `skills/research/SKILL.md` | `01-Raw/inbox/`, `05-Index/Ingest Queue.md` |
| `ingest-runner` | sub-agent | Executes the ingest pipeline for exactly one source, sequencing the delegates below | `skills/ingest/SKILL.md` | (sequences others; no file of its own) |
| `rene` | sub-agent | Cleans a YouTube/podcast transcript into a Raw note | — | `01-Raw/video/` |
| `researcher` | sub-agent | Distills a Raw source into a readable Source Note with a claim table | `04-Schema/Templates/Source Note.md` | `02-Wiki/Sources/` |
| `feynman` | sub-agent | Audits figures/dates/quotes against primary sources; re-opens links itself, doesn't trust a staged status blindly | — | returns a verdict table (no file of its own) |
| `reviewer` | sub-agent | Critiques logic, bear case, moat/competitors; flags gaps instead of inventing | — | returns findings (no file of its own) |
| `darwin` | sub-agent | Extracts durable, reusable investment concepts and entities | `04-Schema/Concept Checklist.md` | `02-Wiki/Concepts/`, `02-Wiki/Entities/` |
| `leopold` | sub-agent | Drafts/updates an Investment Thesis, grounded only in already-reviewed evidence | `04-Schema/Templates/Thesis.md` | `02-Wiki/Theses/` |
| `wiki-health-check` | skill (runs as Munger, not delegated) | Lints the vault: deterministic pass + semantic pass | `scripts/wiki_tool.py --lint` | `lint_pending/` (report only, changes need approval) |

---

## 1. The general shape — an agentic loop, not a fixed pipeline

Every command below is a specific instance of the same loop: Munger decides what's next, a sub-agent executes it, Munger checks the result before deciding the next step. Nothing is scripted end-to-end in advance — a broken link, a thin evidence base, or a failed re-check changes what happens next.

```mermaid
flowchart LR
    subgraph Loop["Agentic workflow — this vault"]
        direction LR
        UQ["User command<br/>/ingest, /research,<br/>/wiki-health-check"] --> PD["Plan &amp; decide<br/>(Munger reads AGENTS.md<br/>routing, picks next step)"]
        PD --> EX["Execute<br/>(delegate to one sub-agent<br/>+ its skill)"]
        EX --> RO["Reflect &amp; observe<br/>(Munger checks the artifact<br/>+ checklist got updated)"]
        RO -. "more steps left / a gate failed" .-> PD
        RO --> OC["Outcome<br/>(files in 01-Raw…02-Wiki,<br/>Log.md entry)"]
    end
    style Loop fill:#eafaf1,stroke:#2f9e63
```

*Non-deterministic on purpose*: if Feynman's link re-check fails, or Reviewer flags "moat not covered in sources," Munger routes back — it doesn't push a broken artifact forward just to finish the pipeline.

---

## 2. `/ingest <source>` — one source, full depth

```mermaid
flowchart TD
    IN["Input: URL / PDF / video / pasted text"] --> IR["Munger delegates to<br/>agents/ingest-runner.md"]
    IR --> T{"Media type?"}
    T -->|video, no caption| RENE["agents/rene.md<br/>clean transcript"]
    T -->|article / filing / PDF / dataset| RAW["Save as-is"]
    RENE --> RAWOUT["01-Raw/video/YYYYMMDD_slug.md"]
    RAW --> RAWOUT2["01-Raw/&lt;type&gt;/YYYYMMDD_slug.md<br/>+ original file kept if binary"]
    RAWOUT --> RN["agents/researcher.md<br/>distill + claim table"]
    RAWOUT2 --> RN
    RN --> SN["02-Wiki/Sources/YYYYMMDD_slug.md"]
    SN --> FY["agents/feynman.md<br/>audit numbers + re-open links"]
    FY -->|thesis-relevant| RV["agents/reviewer.md<br/>logic / bear-case gate"]
    FY -->|not thesis-relevant| DW
    RV --> DW["agents/darwin.md<br/>extract durable concepts"]
    DW --> CN["02-Wiki/Concepts/*.md<br/>02-Wiki/Entities/*.md"]
    CN --> LOG["05-Index/Ingest Queue.md → Done<br/>03-Logs/Log.md entry"]
```

Skill used: `skills/ingest/SKILL.md` (the only place these steps are defined — `ingest-runner` executes it, doesn't redefine it).

---

## 3. `/research <ticker>` — find, ingest, then write the call

```mermaid
flowchart TD
    subgraph P1["Phase 1 — agents/peter-lynch.md (find &amp; stage only)"]
        TK["Ticker + venue"] --> FIND["Find candidate sources<br/>(EDGAR/SET/IR per venue)"]
        FIND --> VERIFY["Open &amp; verify every link<br/>this session — no guessed URLs"]
        VERIFY --> STAGE["01-Raw/inbox/*.md<br/>+ 05-Index/Ingest Queue.md rows,<br/>priority P0/P1/P2"]
    end
    subgraph P2["Phase 2 — Munger loops per queued item"]
        STAGE --> Q{"Next item<br/>by priority"}
        Q --> IR2["agents/ingest-runner.md<br/>(same as §2 above)"]
        IR2 --> Q
    end
    subgraph P3["Phase 3 — write the call"]
        Q -->|enough reviewed<br/>Concepts + Entity exist| LEO["agents/leopold.md<br/>drafts thesis, grounded only<br/>in reviewed evidence"]
        LEO --> TH["02-Wiki/Theses/&lt;slug&gt;.md"]
        TH --> FY2["agents/feynman.md"]
        FY2 --> RV2["agents/reviewer.md<br/>bear case + moat/competitors"]
        RV2 --> DONE["Thesis marked reviewed<br/>(or Leopold/Munger stop and say<br/>why evidence isn't enough yet)"]
    end
```

Skill used: `skills/research/SKILL.md` orchestrates both phases; Phase 2 reuses `skills/ingest/SKILL.md` via `ingest-runner`, so there is exactly one ingest code path whether you type `/ingest` or `/research`.

Calling `agents/peter-lynch.md` directly (not via `/research`) stops after Phase 1 — staging + recommended order only, nothing written past `01-Raw/inbox/`.

---

## 4. `/wiki-health-check` — vault integrity, human-approved fixes

```mermaid
flowchart LR
    CMD["/wiki-health-check"] --> DET["Deterministic pass<br/>scripts/wiki_tool.py --lint<br/>(broken links, orphans,<br/>missing frontmatter)"]
    DET --> SEM["Semantic pass (Munger)<br/>contradictions, stale claims,<br/>missing pages, unreferenced entities"]
    SEM --> REPORT["lint_pending/&lt;date&gt;.md<br/>suggested fixes, nothing changed yet"]
    REPORT --> HUMAN{"User reviews<br/>and approves?"}
    HUMAN -->|yes| APPLY["Apply approved fixes"]
    HUMAN -->|no / partial| SKIP["Leave unapproved items<br/>in lint_pending/"]
```

This one is deliberately **not fully agentic** — it always stops at a human checkpoint before touching any file, unlike ingest/research which write directly (evidence capture is reversible; silently "fixing" existing wiki content is not).

---

## Where output lands — folder map

| Folder | What goes there | Written by |
|---|---|---|
| `01-Raw/` | Immutable captured evidence (never edited after creation) | `ingest-runner` → `rene` / raw save step |
| `02-Wiki/Sources/` | Readable Source Notes + claim tables | `researcher` |
| `02-Wiki/Concepts/` | Durable, reusable mental models | `darwin` |
| `02-Wiki/Entities/` | Company/institution reference notes | `darwin` |
| `02-Wiki/Theses/` | Investment theses | `leopold` |
| `03-Logs/Log.md` | Newest-on-top activity log, one entry per ingest/knowledge change | Munger |
| `04-Schema/` | Templates and schema definitions — read, not written by the pipeline | — |
| `05-Index/Ingest Queue.md` | Triage state: staged → in-progress → done/waiting/deferred/rejected | `peter-lynch` (adds rows), Munger (updates status) |
| `06-Assets/<slug>/` | Extracted images/slides tied to a Raw source | `ingest-runner` (Step 2b/2d of the ingest skill) |
| `lint_pending/` | Health-check reports awaiting human approval | `wiki-health-check` skill |

## Skills vs. sub-agents — the distinction this vault relies on

- A **skill** (`.claude/skills/*/SKILL.md`) is a *procedure* — the steps, in order, with the rules for each. It has no identity of its own and isn't "invoked" as an actor.
- An **agent** (`.claude/agents/*.md`) is an *actor* — something Munger delegates a scoped job to, that reads a skill (or acts on its own narrow persona) and reports back.
- `ingest-runner` and `research`/`ingest` skills are split this way on purpose: the skill defines *what* the pipeline is, the agent is *who* runs it — so both `/ingest` and `/research` Phase 2 share one definition instead of drifting apart.
