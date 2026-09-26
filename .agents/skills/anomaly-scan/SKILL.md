---
name: anomaly-scan
description: Scan the watchlist for things that look abnormal and turn them into research tasks. A script measures price/volume outliers (1-day z-score, volume vs 20-day average, 20-day return vs the watchlist median, 6-month highs/lows) and social-mention jumps; you then diff each company's newest Source Note against its previous one for language changes (first-time mentions, dropped topics, tone shifts, numbers that contradict earlier claims). Findings go to a report in 03-Logs/Anomaly/ and new rows in the Ingest Queue — theses are never edited. Use for /anomaly-scan, "มีอะไรผิดปกติไหม", "หุ้นตัวไหนวิ่งแปลก", unusual volume, a stock moving against its sector, "what's weird in my watchlist", or checking whether management said something new — even if the word "anomaly" isn't used.
---

# /anomaly-scan

An anomaly is only interesting relative to a normal, so the script measures and you explain. Keep that split: numbers come from code (exact, repeatable), meaning comes from reading documents. The output is a list of *questions worth researching*, never a signal to trade — by the time a price move is visible, someone already acted on it; the edge is in finding out why, fast and with evidence.

## Phase 1: Measure

```
py .agents/skills/anomaly-scan/scripts/anomaly_scan.py
```

Useful flags: `--tickers KCE DELTA` to narrow, `--offline` when there's no network (uses the dashboard's cached closes, so volume is unavailable), `--z 2 --vol 2.5 --rel 8` to loosen thresholds for a quiet market. The watchlist lives in `dashboard/config/watchlist.json`; add a ticker there, not in this skill.

The script prints three sections: a price/volume table with flags, the newest-vs-previous Source Note pair per company, and social mention counts (only once `01-Raw/social/` exists). Report the data source line too — a scan run on stale cached closes must say so.

## Phase 2: Explain the numeric flags

For each flagged ticker, look for the cause in this order and stop when you find it:
1. The vault — a recent Source Note, Log entry, or Ingest Queue row that already explains it.
2. The market context — did the whole sector or index move? Use the TradingView MCP (`get_quote`, `compare_symbols`, `get_news`) if it's connected.
3. A quick web search for company news on that date.

Write the cause as a **hypothesis with its source URL or file**, never as fact. If nothing explains it, write "ไม่พบสาเหตุ" — an unexplained move is itself the finding, and it becomes a P1 research task. Never fill the gap with a plausible story.

## Phase 3: Diff the language

For each document pair (newest vs previous Source Note for the same company), read both and look only for:
- **First mentions** — a customer, product, market, capacity plan, or risk that appears for the first time.
- **Dropped topics** — something the company emphasised before that is now absent.
- **Tone shifts** — wording that moves (e.g. "เติบโต" → "ทรงตัว", "ชั่วคราว" → "ต่อเนื่อง") on the same topic.
- **Number reversals** — a figure in the newest claim table that contradicts or sharply revises one in the previous note.

Quote both sides with file names. Skip pairs where the company is only mentioned in passing (a course or podcast that names the ticker once is not a company document) — say you skipped it and why. If a company has only one Source Note, note that a diff needs the next filing.

## Phase 4: Social attention (only if data exists)

A jump in mentions is a reason to look, not a reason to believe. Report the change (this window vs the previous one), never the level alone, and pair it with whatever Phase 2 found. Social data is `trust: low`: it can create a research task but cannot confirm anything.

## Output

1. **Report** — create `03-Logs/Anomaly/YYYYMMDD-anomaly-scan.md` (make the folder if needed), in Thai with English finance terms:

```markdown
---
type: anomaly-scan
status: pending
created: YYYY-MM-DD
data_source: <from script>
---

# Anomaly Scan — YYYY-MM-DD

## สรุป
<!-- flagged tickers and language changes worth attention, most important first; or "ไม่พบความผิดปกติ" -->

## ตัวเลข
| Ticker | สิ่งที่ผิดปกติ | สมมติฐานสาเหตุ | ที่มา | ต้องตรวจอะไรต่อ |
|---|---|---|---|---|

## ภาษาในเอกสาร
| บริษัท | ประเภท | ฉบับก่อน | ฉบับล่าสุด | นัยต่อ thesis |
|---|---|---|---|---|

## ความสนใจบนโซเชียล
<!-- or "ยังไม่มีข้อมูลใน 01-Raw/social/" -->

## งานที่ส่งเข้า Ingest Queue
- P1/P2 — <task>
```

2. **Ingest Queue** — for every finding that needs a document, add a row to the `## Inbox / triage` table in `05-Index/Ingest Queue.md`: Priority `P1` if it touches a thesis kill condition or an unexplained large move, otherwise `P2`; Status `inbox`; Raw source = the specific document to fetch (e.g. "SET news KCE 2026-09-24", "Q3 MD&A"); Type; Why now? = the anomaly in one line; Next action = `/ingest <url>` or `/research <ticker>`. Don't add a row that duplicates an existing open one — update its "Why now?" instead.

3. **Log** — prepend one row to `03-Logs/Log.md` (newest on top): date, "Anomaly scan", report path, one-line headline.

If a finding bears directly on a thesis, mention it in the report and let `/delta-report` or the owner decide — this skill doesn't edit `02-Wiki/`.

## Boundaries

- No trade signals, targets, or "buy the dip" language. Output is research tasks.
- Every cause is a hypothesis with a source; "ไม่พบสาเหตุ" beats a guess.
- Thresholds are defaults, not truths. If the owner changes them, note the values used in the report.
