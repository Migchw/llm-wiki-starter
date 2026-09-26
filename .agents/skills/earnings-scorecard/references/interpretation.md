# Reading an earnings scorecard

Work through these in order. Each step names what to look at, why it matters, and what to write. Worked example: TD SYNNEX (SNX) fiscal 3Q26, reported 2026-09-24.

## 1. Guidance vs consensus — the forward signal

Compare the midpoint of next-quarter guidance with next-quarter consensus. Prices move on the change in expectations, so this usually matters more than the quarter just reported.

- Guidance above consensus → analysts will likely raise estimates; the beat has momentum.
- Beat on the quarter but guidance at or below consensus → "beat and lower" often sells off.
- SNX: revenue guide mid $22.2B vs consensus $19.44B (+14.2%); EPS mid $5.90 vs $4.87 (+21.2%). A strong raise — yet the stock fell ~11% intraday, so the market was already positioned for more, or reacted to something else (step 6).

## 2. Where did the beat come from?

Split the EPS beat into its sources:
- **Revenue** (demand) — the most durable kind.
- **Margin** (mix, pricing, cost control) — durable only if the cause is structural.
- **Below the line** (lower tax rate, share buybacks, one-off gains) — low quality; say so.

Check operating leverage: if profit grows faster than revenue, margins expanded. SNX: revenue +37.7% YoY, adjusted EPS +58.7% → operating leverage on a thin 3.4% margin.

## 3. Beat vs the company's own guidance

A company that beats its own guide by a wide margin every quarter may be guiding conservatively (sandbagging). Compare the last few quarters' guide-vs-actual gaps before treating a new beat as a surprise. SNX's reported revenue $21.56B vs its prior guide $18.6B is a large beat of its own outlook.

## 4. Segment mix

Which segment drove growth, and is it the higher- or lower-margin one? A faster-growing low-margin segment can lift revenue while diluting margins.

SNX: Hyve Solutions (designs and builds servers for hyperscale data centers) grew faster than Distribution. That points the growth at data-center builds rather than general IT spending. Segment figures come from the press release, not yfinance.

## 5. Earnings quality

- **GAAP vs non-GAAP gap.** Large or growing adjustments (stock comp, restructuring, acquisition amortisation) deserve a line. SNX: GAAP diluted EPS $5.18 vs non-GAAP $5.68.
- **Cash and working capital.** For distributors and manufacturers, revenue growth funded by rising inventory and receivables is weaker than it looks. Check operating cash flow and the cash conversion cycle when the statements land.
- **Gross vs net revenue.** Distributors report gross billings above revenue because some sales are recognised net (agent). Watch both; a shift in mix changes revenue without changing the business.

## 6. How the stock usually reacts

The scorecard's history shows EPS surprise and the report-day move for eight quarters. If the stock regularly falls on beats, the market already prices beats in — the next leg needs a guidance raise or a new narrative. SNX averaged a 13.6% EPS surprise over eight quarters but its report-day move averaged about zero, and it fell after large beats in 2Q26 and 3Q26.

## 7. Industry read-through

Treat one company's report as a reading on its industry, then check other nodes before calling a trend:

- **Same layer (competitors):** did peers report the same thing? For SNX: Arrow, Avnet, Ingram Micro (distribution); Celestica, Super Micro, Wiwynn (server builders). If only one company beats, it's share gain; if all do, it's the industry.
- **Upstream (suppliers):** strong server builds should show up at power, PCB and component makers. In this vault: Delta Electronics (Thailand) reported sales +46.5% on AI data-center demand; KCE noted AI demand tightening glass-fibre supply.
- **Downstream (customers):** hyperscaler capex guidance confirms or contradicts the build-out.

Write each read-through as an interpretation with the entity it affects, and link the entities in the vault (`end_markets`, `upstream`) so `/delta-report` can check the theme across companies next quarter. Agreement across nodes is what turns one good quarter into evidence of a trend — the narrative and fundamental layers of the three-layer momentum check.

## Thailand-specific notes

- Consensus often comes from one or two brokers; yfinance may show `numberOfAnalysts = 1`. Treat surprises as a comparison with that broker's model.
- Many Thai companies don't give numeric guidance. Use management commentary in the MD&A or opportunity-day deck, quoted, instead of a guidance number.
- Broker research PDFs are the practical source of consensus detail — ingest them as Raw with `trust` noted.
