# Project Workflow

How this vault actually runs: who commands whom, what gets delegated, what skill each step uses, and where the output file lands. Source of truth for the rules themselves is `.agents/AGENTS.md` — this file is the map on top of it.

## Actors at a glance

| Actor | Type | Job | Reads / uses | Writes to |
|---|---|---|---|---|
| **Munger** | Orchestrating session (the main session chatting with the user) | Direct Single-Pass Ingest for standard sources, plans, delegates complex research, posts running checklist | `.agents/AGENTS.md` routing table | `03-Logs/Log.md`, `05-Index/Ingest Queue.md` status |
| `peter-lynch` | sub-agent | Finds & verifies primary sources for a ticker, stages them, triages priority | `skills/research/SKILL.md` | `01-Raw/inbox/`, `05-Index/Ingest Queue.md` |
| `ingest-runner` | sub-agent | Executes the fast and lean ingest pipeline for exactly one source | `skills/ingest/SKILL.md` | `01-Raw/`, `02-Wiki/` |
| `rene` | sub-agent | Cleans a YouTube/podcast transcript into a Raw note | — | `01-Raw/video/` |
| `researcher` | sub-agent | Distills a Raw source into a readable Source Note with a claim table | `04-Schema/Templates/Source Note.md` | `02-Wiki/Sources/` |
| `feynman` | sub-agent | Audits figures/dates/quotes against primary sources | — | returns a verdict table |
| `reviewer` | sub-agent | Critiques logic, bear case, moat/competitors; flags gaps instead of inventing | — | returns findings |
| `darwin` | sub-agent | Extracts durable, reusable investment concepts and entities | `04-Schema/Concept Checklist.md` | `02-Wiki/Concepts/`, `02-Wiki/Entities/` |
| `leopold` | sub-agent | Drafts/updates an Investment Thesis, grounded only in already-reviewed evidence | `04-Schema/Templates/Thesis.md` | `02-Wiki/Theses/` |
| `wiki-health-check` | skill (runs as Munger, not delegated) | Lints the vault: deterministic pass + semantic pass | `scripts/wiki_tool.py --lint` | `lint_pending/` (report only, changes need approval) |

---

## 1. The Core Ingestion Architecture: Python-First & Tiered Extraction

To ensure blazing-fast execution (<30–45s) and prevent LLM token waste on raw HTML/CSS/JS, raw evidence acquisition is offloaded to a dedicated Python CLI tool (`scripts/fetch_source.py`):

```mermaid
flowchart TD
    A["Input: URL / Local Document"] --> B{"Input Type?"}
    B -->|Local File: PDF/DOCX/PPTX/XLSX| C["Tier 3: MarkItDown<br/>Direct local conversion into Markdown"]
    B -->|Web URL| D["Tier 1: Fast HTTP + BeautifulSoup<br/>Ultra-fast clean body extraction (<0.5s)"]
    D --> E{"Content Extracted & Valid?"}
    E -->|Yes| F["Save to 01-Raw/<media_type>/"]
    E -->|No / React / SPA / Heavy JS| G["Tier 2: Playwright Headless Chromium<br/>Full DOM & Dynamic JavaScript Rendering"]
    G --> F
    C --> F
```

---

## 2. `/ingest <source>` — Fast Lean Ingestion (Single-Pass by Default)

For standard articles, news, and single filings (S/M size), the orchestrator executes a **Direct Single-Pass Ingestion** directly:

```mermaid
flowchart TD
    IN["Input: URL / File"] --> FETCH["scripts/fetch_source.py<br/>(Tiered: BS4 / Playwright / MarkItDown)"]
    FETCH --> RAW["01-Raw/<media_type>/YYYYMMDD_slug.md"]
    RAW --> SN["Create Source Note (02-Wiki/Sources/)<br/>- 60s brief<br/>- Thesis of source<br/>- Claim table (Fact vs Interpretation)"]
    SN --> ENT["Create / Update Entities (02-Wiki/Entities/)<br/>Company, Institution, Publisher"]
    ENT --> CON{"Durable Concept Present?<br/>(Darwin 3-Question Gate)"}
    CON -->|Yes: Novel Mental Model| CN["Create Concept (02-Wiki/Concepts/)<br/>Concise & Punchy (4 Archetypes)"]
    CON -->|No: Routine News| QUEUE
    CN --> QUEUE["Update 05-Index/Ingest Queue.md -> Done"]
    QUEUE --> LOG["03-Logs/Log.md<br/>Concise 1-2 sentence activity log"]
```

> **Efficiency Benchmark:**
> - **Legacy Multi-Agent Overhead:** ~4–5 minutes, ~30,000 tokens (due to context duplication and sub-agent handoffs).
> - **Lean Single-Pass + Python Extraction:** **~30–45 seconds**, **~5,000 tokens** (80%+ token reduction).

---

## 3. `/research <ticker>` — Deep Multi-Source Ticker Research

For full end-to-end equity research, the orchestrator coordinates specialized sub-agents in 3 distinct phases:

```mermaid
flowchart TD
    subgraph P1["Phase 1 — agents/peter-lynch.md (Find & Stage Only)"]
        TK["Ticker + Venue (US/SET)"] --> FIND["Find primary sources<br/>(10-K, MD&A, 56-1 One Report, Oppday)"]
        FIND --> VERIFY["Verify every link & document"]
        VERIFY --> STAGE["01-Raw/inbox/*.md<br/>+ 05-Index/Ingest Queue.md rows (P0/P1/P2)"]
    end
    subgraph P2["Phase 2 — Ingest Loop"]
        STAGE --> Q{"Next item by priority"}
        Q --> IR2["Lean Ingestion Pass<br/>(Raw -> Source Note -> Entity -> Concept)"]
        IR2 --> Q
    end
    subgraph P3["Phase 3 — Investment Thesis Synthesis"]
        Q -->|Sufficient reviewed evidence| LEO["agents/leopold.md<br/>Drafts Thesis grounded only in reviewed notes"]
        LEO --> TH["02-Wiki/Theses/<slug>.md"]
        TH --> FY2["agents/feynman.md (Fact & Numbers Audit)"]
        FY2 --> RV2["agents/reviewer.md (Bear Case & Moat Review)"]
        RV2 --> DONE["Thesis Marked Reviewed"]
    end
```

---

## 4. Where output lands — folder map

| Folder | What goes there | Written by |
|---|---|---|
| `01-Raw/` | Immutable captured evidence (never edited after creation) | `scripts/fetch_source.py`, `rene` |
| `02-Wiki/Sources/` | Readable Source Notes + claim tables | Ingest Pass / `researcher` |
| `02-Wiki/Concepts/` | Durable, reusable mental models (Selective) | Ingest Pass / `darwin` |
| `02-Wiki/Entities/` | Company/institution reference notes (Always) | Ingest Pass / `darwin` |
| `02-Wiki/Theses/` | Actionable Investment theses | `leopold` |
| `03-Logs/Log.md` | Concise 1–2 sentence activity log (Newest on top) | Munger |
| `04-Schema/` | Templates and schema definitions — read-only contracts | — |
| `05-Index/Ingest Queue.md` | Triage state: staged → in-progress → done/waiting/deferred/rejected | `peter-lynch`, Munger |
| `06-Assets/<slug>/` | Extracted images/slides tied to a Raw source | `fetch_source.py` / PyMuPDF |
| `lint_pending/` | Health-check reports awaiting human approval | `wiki-health-check` skill |
