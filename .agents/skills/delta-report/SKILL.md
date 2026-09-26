---
name: delta-report
description: Weekly "what changed" review for the investment vault. Finds Source Notes added in a date window, maps them to each Investment Thesis and company Entity, and judges whether the new evidence strengthens, weakens, or triggers a thesis kill condition (the "What Would Change My Mind" section), with file-and-claim citations. Writes a report to 03-Logs/Delta/ and proposes thesis edits as checkboxes without applying them. Use for /delta-report, weekly or Friday reviews, "what changed this week", "อะไรเปลี่ยนไปบ้าง", "thesis ยังใช้ได้ไหม", checking holdings or the watchlist against new filings, earnings, or news, or before a thesis review_date — even when the user doesn't say "delta".
---

# /delta-report

The question this skill answers: **since the last review, did the evidence move — and which way?** A thesis is only useful if it gets re-tested against new facts on a schedule. People skip this because it is tedious; that is exactly why the vault should do it. The report is read by the owner in about five minutes, so lead with what changed and cite everything.

Two phases: a script finds *what is new and where it belongs* (exact), then you read the notes and judge *what it means* (semantic). Don't hand-derive what the script computes, and don't let the script's mapping stand in for actually reading the source.

## Phase 1: Deterministic scan

```
py .agents/skills/delta-report/scripts/delta_scan.py            # default: last 7 days
py .agents/skills/delta-report/scripts/delta_scan.py --since YYYY-MM-DD
```

Use `--since` when the user names a period ("since earnings", "this month") or when the last report in `03-Logs/Delta/` is older than 7 days — start from that report's date so nothing falls through the gap. On the very first run (no reports in `03-Logs/Delta/` yet), start from the earliest thesis `created` date so the baseline covers all existing evidence.

The output lists new/updated Source Notes, each thesis with its kill conditions and the new evidence mapped to it (flagging sources already cited), and companies that got new sources but have no thesis yet. If the window has zero new sources, say so plainly and still check `REVIEW DUE` flags — a quiet week is a valid result.

## Phase 2: Judge each piece of evidence

For every thesis with new evidence, read the thesis (Thesis Statement, Base Case, Contrary Case, What Would Change My Mind) and then each new Source Note — start with its 60-second brief and claim table, and open the Raw file only when a claim is ambiguous.

Classify each relevant claim into exactly one bucket:

| Verdict | Meaning |
|---|---|
| **Strengthens** | supports a specific Base Case point — name the point |
| **Weakens** | supports the Contrary Case or erodes a Base Case assumption |
| **Kill: triggered** | meets a kill condition as written |
| **Kill: approaching** | moves toward a kill condition's threshold without crossing it — state the distance |
| **Neutral / already priced in** | new document, no new information versus what the thesis already cites |

Rules that keep the report trustworthy:
- Every verdict cites the source file and the claim-table row (or a short quote with page/timestamp). A verdict you can't cite doesn't go in the report.
- Weigh by verification: a claim from a `verification: pending` note or a `fact`-vs-`interpretation` row labelled interpretation is reported, but marked `(pending)` and never alone triggers a kill.
- Anything from `01-Raw/social/` or marked `trust: low` is attention, not evidence. It can raise a question; it cannot strengthen, weaken, or kill.
- A kill condition written vaguely ("demand weakens") can't be tested. Flag it and propose a measurable rewrite instead of guessing whether it fired.
- If a thesis has no kill conditions at all, that is the top finding for that thesis — propose 2–3 measurable ones drawn from its own Risks and Contrary Case.
- Judge the evidence, not the position. Don't ask about or factor in whether the owner holds the stock; this keeps the review from bending toward what we already own.

For companies with new sources but no thesis: one line each on whether the evidence now looks sufficient to draft one (per `agents/leopold.md`), or what is still missing. Don't draft the thesis here.

## Output: write the report, don't edit theses

Create `03-Logs/Delta/YYYYMMDD-delta-report.md` (make the folder if needed). Write in Thai with finance terms kept in English, per the vault's language rules. Replace every `<wikilink ...>` placeholder with a real `[[...]]` link to the note.

```markdown
---
type: delta-report
status: pending
created: YYYY-MM-DD
window: YYYY-MM-DD → YYYY-MM-DD
---

# Delta Report — YYYY-MM-DD

## สรุป 30 วินาที
<!-- 2–4 bullets: the biggest moves in evidence this window, kill-condition hits first -->

## <wikilink ไปที่ thesis>
**ทิศทางรวม:** แข็งขึ้น / อ่อนลง / ทรงตัว / มี kill condition ทำงาน

| Evidence | Verdict | Thesis point / kill condition | Note |
|---|---|---|---|
| <wikilink Source Note> — claim row "..." | Strengthens | Base Case: ... | |

**Kill conditions**
- ✅ ยังไม่ถึง: <condition> — ล่าสุด <value, source>
- ⚠️ ใกล้ถึง: <condition> — ห่างอีก <distance>
- ❌ ทำงานแล้ว: <condition> — <evidence>

**ข้อเสนอแก้ thesis (รออนุมัติ)**
- [ ] <exact edit: section + new text> — เหตุผล: <source>

## บริษัทที่มีหลักฐานใหม่แต่ยังไม่มี thesis
- <wikilink Entity> — <พอร่าง thesis ได้หรือยัง / ยังขาดอะไร>

## Review date ที่ใกล้ถึง
- <wikilink Thesis> — review_date YYYY-MM-DD

## คำถามที่ยังเปิดอยู่
<!-- what evidence would settle the pending/approaching items; these become /research or /ingest targets -->
```

Then prepend one row to the table in `03-Logs/Log.md` (right after the header row, newest on top): date, "Delta report", the report path, and the one-line headline.

Apply proposed thesis edits only when the owner later marks them `[x]` and asks — then make exactly those edits, update the thesis `updated` date, and add the new source to its `sources`.

## Boundaries

- No buy/sell/hold recommendations and no price targets. The report says what the evidence did to the thesis; the owner decides what to do.
- Don't invent movement to make the report look busy. "ไม่มีหลักฐานใหม่" is a complete, correct answer for a thesis.
- Don't edit `01-Raw/`, `02-Wiki/`, or thesis frontmatter in this pass.
