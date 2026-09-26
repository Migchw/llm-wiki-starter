---
name: earnings-scorecard
description: Build an earnings beat/miss scorecard for a watchlist company and interpret it — reported vs consensus vs company guidance vs last year, EPS surprise history, price reaction on report days, next-quarter consensus — then write it into the vault and refresh the dashboard's Earnings scorecard card. Data comes from yfinance (consensus, statements, prices) plus the company press release for revenue, segments, non-GAAP items and next-quarter guidance. Use for /earnings-scorecard, "งบออกแล้ว beat ไหม", "ผลประกอบการเทียบ consensus", earnings season, a company just reported, guidance vs consensus, a screenshot of someone's earnings table the user wants verified, or adding a new ticker's earnings to the dashboard — even when the user doesn't say "scorecard".
---

# /earnings-scorecard

Answers two questions after a company reports: **did the numbers beat what the market expected, and does the outlook move expectations for next quarter?** The second matters more — prices react to the change in expectations, which is why a big beat can still fall (SNX 3Q26: EPS +20.8% vs consensus, stock −11% on the day).

Split of work, same as the vault's other skills: the script measures (exact, repeatable), you verify the inputs and interpret.

## Phase 1: Gather

1. **Run the script** (all watchlist tickers, or `--tickers SNX`):
   ```
   py .agents/skills/earnings-scorecard/scripts/earnings_scorecard.py --tickers SNX
   ```
   It writes `dashboard/data/earnings-data.json` (what the dashboard card shows) and appends a consensus snapshot to `dashboard/data/consensus-history.json`. Snapshots are how revenue surprise gets computed later — yfinance keeps EPS-surprise history but not revenue-consensus history — so keeping that file committed builds a record nobody else has.

2. **Get the press release** — the primary source. US: the 8-K Exhibit 99.1 on EDGAR or the IR site; Thailand: the SET filing/MD&A. Use `/ingest` so it lands in `01-Raw/` with a Source Note. From it take: total revenue, segment revenue, non-GAAP items (gross billings, adjusted EPS, EBITDA), and the next-quarter outlook ranges.

3. **Record what yfinance lacks**, then re-run:
   ```
   py .agents/skills/earnings-scorecard/scripts/earnings_scorecard.py --tickers SNX \
     --actual "SNX:2026-09-24:revenue=21.558e9" \
     --guidance "SNX:2026-09-24:revenue=21.8e9-22.6e9,eps=5.65-6.15"
   ```
   `--actual` fills revenue when yfinance statements lag the report (usually a few days to weeks). `--guidance` stores the outlook range and compares its midpoint to next-quarter consensus. Both persist in the history file, so you only enter them once.

4. **Refresh the dashboard:** `cd dashboard && npm run index` (the dev server picks the new JSON up on reload; `npm run earnings` re-runs step 1 from inside the dashboard).

If the user gave a screenshot or someone else's table, rebuild it from sources rather than copying it, and point out every cell that doesn't reconcile — copied consensus columns and mislabelled units are common.

## Phase 2: Check the inputs before interpreting

- **Consensus source and date.** yfinance consensus is Yahoo's aggregate; FactSet/LSEG/Bloomberg can differ by a percent or two. Say which one you used.
- **Same basis on both sides.** Adjusted (non-GAAP) EPS vs adjusted consensus; GAAP vs GAAP. The script marks `yoy_basis` when YoY came from GAAP statements.
- **Coverage.** Under 3 analysts (the script flags "thin coverage", common for Thai small/mid caps) makes "beat/miss" mostly noise — one broker's model, not a market expectation.
- **Units.** Margin surprise is in percentage points, not percent.
- **Intraday reaction.** If `intraday` is true, the day's move isn't final.

## Phase 3: Interpret

Read `references/interpretation.md` and work through it in order. The short version: guidance vs consensus first; then where the beat came from (revenue, margin, or below the line); beat vs the company's own guidance; segment mix; earnings quality (cash, working capital, GAAP vs non-GAAP gap); how the stock usually reacts; and what the quarter says about the industry (read-through to other vault entities).

## Output

1. **Source Note** for the report (via `/ingest`), with a `## Earnings Scorecard` section: the scorecard table (Reported / Consensus / Beat-Miss / Surprise / Guidance / YoY), the guidance-vs-consensus table, and claim-table rows that label consensus figures as `fact` with source = "yfinance consensus as of YYYY-MM-DD" and your reading as `interpretation`.
2. **Entity update** — add the quarter's headline and link the Source Note; if the read-through touches other entities (supplier, customer, competitor), add the wikilink in both directions.
3. **Industry read-through** as bullets in the Source Note, each tagged with the entity it affects and marked `interpretation`.
4. **Log** — prepend one row to `03-Logs/Log.md`.
5. If a thesis exists for the company, say which kill conditions the quarter touches and suggest running `/delta-report`; don't edit the thesis here.

## Boundaries

- No buy/sell/hold calls or price targets. The scorecard says what happened versus expectations; the owner decides.
- Never invent a consensus or segment figure you couldn't source — leave it `—` and say where it would come from (Visible Alpha, FactSet, broker reports).
- A beat that the stock sells off on is data, not an error. Explain it with evidence (guidance, quality, positioning) or say the cause is unknown.
