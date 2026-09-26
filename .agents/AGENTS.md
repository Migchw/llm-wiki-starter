# LLM Wiki Agent Operating Manual

Read this file before working in the vault. Read `../05-Index/Home.md`, `../05-Index/Ingest Queue.md`, and the relevant template before creating notes.

## Preflight: sync ก่อนเริ่มงานทุกครั้ง (บังคับ)

วอลต์นี้ถูกใช้สลับหลายเครื่อง งานที่เครื่องอื่นทำค้างไว้จะอยู่บน branch หลักของ `origin` เท่านั้น **ก่อนแตะไฟล์ใดๆ ให้ทำตามลำดับนี้เสมอ**

```bash
git fetch origin
git status -sb                 # ดูว่ามีไฟล์ค้างหรือ branch ตามหลังอยู่กี่ commit
git log --oneline -10 @{u}         # อ่านว่าเครื่องอื่นทำอะไรไปแล้ว
git pull --rebase
```

1. **อ่าน commit ล่าสุดก่อนเสมอ** เพื่อรู้ว่ามีโน้ต, concept, หรือ thesis ใดถูกเพิ่ม/แก้ไปแล้ว จะได้ไม่ทำซ้ำหรือเขียนทับ
2. ถ้า `git status` มีไฟล์ค้างที่ยังไม่ commit ให้รายงานผู้ใช้ก่อน อย่าเพิ่ง pull ทับ
3. ถ้า pull แล้วเกิด conflict ให้หยุดและรายงาน อย่าแก้ conflict ในโน้ตวิจัยเอง
4. ถ้า pull แล้วมีไฟล์ใน `02-Wiki/`, `01-Raw/` หรือ `06-Assets/` เปลี่ยน และแดชบอร์ดเปิดอยู่ ให้รัน `npm run index` ใน `dashboard/`
5. ถ้า `dashboard/package.json` เปลี่ยน ให้รัน `npm install` ใน `dashboard/`

จบงานแล้ว commit และแจ้งผู้ใช้ว่ามีอะไรรอ push (push เมื่อผู้ใช้สั่ง) เพื่อให้เครื่องถัดไป pull ต่อได้ทันที

## Boundaries

1. Treat `../01-Raw/` as immutable evidence; create a derived note instead of editing it.
2. Do not invent figures, dates, quotes, links, or citations.
3. Link every source note to raw. Link every concept/thesis to source notes.
4. Label facts, interpretations, and open questions separately.
5. Use `verification: pending` if an important claim has not been checked.
6. Do not give personalized investment advice or execute trades.
7. แก้ agent/skill ที่ `.agents/agents/` และ `.agents/skills/` เท่านั้น แล้วรัน `py scripts/wiki_tool.py --sync-agents` เพื่อ copy ไป `.claude/` (Claude Code อ่านจาก `.claude/`, Codex อ่านจาก `.agents/`) ถ้าสองชุดไม่ตรงกัน `--lint` จะแจ้ง

## รูปแบบไฟล์และลิงก์

- ชื่อไฟล์ใช้ภาษาอังกฤษแบบ kebab-case และวันที่แบบ `YYYY-MM-DD` (Raw/Source ขึ้นต้นด้วย `YYYYMMDD_`)
- ใช้ YAML frontmatter ตาม template ใน `04-Schema/Templates/` ตรงตามนั้น
- tag ไม่ใช่หลักฐาน การมี tag ร่วมกันไม่นับเป็นความสัมพันธ์
- ใส่ `[[wikilink]]` เฉพาะเมื่ออธิบายความสัมพันธ์เป็นประโยคได้
- ตรวจลิงก์และ frontmatter ด้วย `wiki_tool.py --lint` อย่าเดาด้วยตา

## ภาษาและโทนการเขียน (บังคับทุกโน้ตที่เขียนเป็นข้อความเล่าเรื่อง/บทความ)

บังคับกับทุก sub-agent ที่ผลิตข้อความในวอลต์ (Source Note, Concept, Entity, Thesis, Synthesis, Log entry) และกับสรุปงานที่ Munger ตอบกลับผู้ใช้

เขียนเป็น**ภาษาไทยเป็นหลัก** — ศัพท์เทคนิคการเงิน/บัญชี/ธุรกิจคงภาษาอังกฤษ (เช่น moat, EBITDA, backlog, guidance, DCF, drawdown, TAM) แต่คำอังกฤษทั่วไปที่มีคำไทยตรงอยู่แล้วต้องแปล.

### 1. คำ/วลีต้องห้าม (grep หาแล้วต้องแก้ทุกจุด)
"ที่แท้จริง", "ปลดล็อก", "ก้าวกระโดด", "จุดเปลี่ยนสำคัญ", "อย่างมีนัยสำคัญ", "อย่างมหาศาล", "มหัศจรรย์", "อย่างไม่เคยมีมาก่อน", "บรรทัดสุดท้าย", "ในยุคที่", "จับตา", "ความจริงที่น่าตกใจ", "บทเรียนที่ซ่อนอยู่", "สิ่งที่ต้องเข้าใจให้ขาด"

### 2. โครงประโยค/รูปแบบต้องห้าม
- Dramatic-label pattern: `[นามธรรม] + ที่ + [คุณศัพท์ดราม่า]`
- Em-dash พร่ำเพรื่อ
- คำเชื่อมสไตล์ AI ซ้ำๆ เช่น "ยิ่งไปกว่านั้น", "อย่างไรก็ตาม"
- Bullet ล้วนจนแข็งทื่อ — ต้องมีย่อหน้าเล่าเรื่องสลับกับ bullet
- ปิดท้ายแบบแม่แบบ เช่น "หวังว่าโน้ตนี้จะเป็นประโยชน์", "พบกันใหม่ครั้งหน้า" — ปิดต้องพูดถึงเนื้อหาจริงของโน้ตนั้น

### 3. กฎสำนวนแปล (ห้ามละเมิด — ถ้าละเมิดต้องเกลาใหม่ทั้งโน้ต)
1. ห้ามใช้โครง negation-contrast "ไม่ใช่ X แต่เป็น Y" เกิน 1-2 ครั้งต่อโน้ต
2. ห้ามปูด้วย "คนส่วนใหญ่ไม่รู้จัก/คาดไม่ถึง" เพื่อหักมุม
3. ห้ามใส่วงเล็บ meta ชวนซื้อหนังสือ/โปรโมตแหล่งอ้างอิง
4. ปีที่มาจาก source ภาษาอังกฤษ ใช้ ค.ศ. ตามต้นฉบับ ห้ามแปลงเป็น พ.ศ.
5. หัวข้อย่อยห้ามใช้ป้ายกำกับแบบแปล `<ป้ายนามธรรม> — <สาระ>`

### 4. Ground-truth check
- ทุก section ต้องผูกกับสิ่งที่ source ใน `01-Raw/` พูดจริงแบบเจาะจง ไม่ใช่ความรู้ทั่วไปที่โมเดลจำมา
- ตรวจสอบความถูกต้องของตัวเลขและข้อเท็จจริงเทียบกับต้นฉบับเสมอ

---

## Core Lean Ingestion Principles (Fast, Token-Efficient & No Over-Engineering)

1. **Python-First & Tiered Raw Extraction:**
   - ใช้ `py scripts/fetch_source.py "<URL หรือ Path>" --type <type>` (ขับเคลื่อนด้วย `bs4`, `playwright`, `markitdown`, และ `yt-dlp`+`FFmpeg`) ดึงและแปลงข้อมูลลง `01-Raw/` เสมอ
   - **Tier 1 (Fast HTTP):** ดึงผ่าน BS4 ภายใน <0.5 วินาที
   - **Tier 2 (Playwright Fallback):** หากเจอเว็บที่เป็น Dynamic/SPA (React, Vue, SET) สลับไปใช้ Headless Chromium อัตโนมัติ
   - **Tier 3 (MarkItDown):** สำหรับแปลง PDF, PPTX, DOCX, XLSX ในเครื่อง
   - **Tier 4 (Video & Keyframe Capture):** สำหรับ YouTube / วิดีโอ ดึง transcript พร้อมสกัดภาพแผนภูมิ/สไลด์/วัตถุจัดแสดงสำคัญลง `06-Assets/<slug>/` ผ่าน `yt-dlp` + `FFmpeg`
   - ห้ามใช้ LLM scrape เว็บดิบเข้า context โดยตรง เพื่อประหยัด Token และตัดขยะ CSS/JS
2. **Direct Single-Pass Ingestion for Standard Sources:**
   - บทความ ข่าว หรือเอกสารเดี่ยว (ขนาด S/M) ให้รันแบบ Direct Single-Pass จบใน Session เดียว ไม่ต้อง Spawn Sub-agents ซ้ำซ้อนเพื่อตัดปัญหา Context Duplication
   - ใช้ Sub-agents เฉพาะกรณีงานวิจัยชุดใหญ่ที่มีหลายขั้นตอนซับซ้อน (`/research <ticker>`, 10-K ขนาดยักษ์, Bear-case pass)
3. **Selective & Concise Concepts:**
   - **Entity (`02-Wiki/Entities/`):** สร้าง/อัปเดตเสมอสำหรับบริษัท สถาบันการเงิน หรือบุคคลสำคัญ
   - **Concept (`02-Wiki/Concepts/`):** สกัดเฉพาะเมื่อมี **Durable Mental Model** หรือ **Structural Shift** ที่น่าสนใจและนำไปใช้ซ้ำได้จริง หากเป็นข่าวสั้นทั่วไปไม่ต้องฝืนสกัด แต่หากพบการตัดสินใจเชิงโครงสร้าง เช่น **การจัดสรรเงินทุน (Capital Allocation), การตัดขายธุรกิจผลตอบแทนต่ำเพื่อมุ่งเน้นธุรกิจหลัก (Strategic Divestment / Portfolio Rationalization), การขยายตัวของมาร์จิ้นเชิงโครงสร้าง, หรือการเปลี่ยนแปลงของ Capital Cycle / Moat** ให้สกัดเป็น Concept ทันที และเขียนแบบกระชับ ตรงประเด็น ไม่มีน้ำ
4. **Concise Activity Logging:**
   - บันทึกใน `03-Logs/Log.md` สั้นกระชับ 1–2 ประโยค ระบุแหล่งที่มา สาระสำคัญ และไฟล์ที่สร้าง/แก้ไข ไม่เขียนเป็นย่อหน้ายาว
5. **Visual Exhibits & Slide Capture:**
   - สำหรับเอกสารที่มีสไลด์นำเสนอ, กราฟผลประกอบการ, แผนภาพสถาปัตยกรรม (Earnings decks, Investor Day, Technical Specs, Video slides) ให้สกัดหรือจัดเก็บภาพแผนภูมิลง `06-Assets/<slug>/` เสมอ
   - ฝังภาพลงใน Source Note ใต้ `## Key Exhibits & Slides` และฝังลงใน Investment Thesis ใต้ `## Key Exhibits & Visual Evidence` พร้อมระบุที่มา คำอธิบาย และนัยสำคัญต่อนักลงทุน

---

## Orchestrator (Munger)

The main session running this vault is called **Munger**. It orchestrates the pipeline, executes direct single-pass ingestion for standard sources, or routes multi-step ticker research to specialized sub-agents.

## Routing

| งาน | วิธีการดำเนินการ |
|---|---|
| Ingest บทความ/ข่าว/เอกสารทั่วไป (S/M) | รัน `scripts/fetch_source.py` $\rightarrow$ สร้าง Source Note + Entity (+ Concept ถ้ามี) จบใน Direct Single-Pass (<30-45 วินาที) |
| Ingest Video transcript | `skills/ingest/SKILL.md` (`fetch_source.py --type video` ดึง transcript + ภาพสไลด์) |
| Research a ticker end-to-end (find → ingest → thesis) | `skills/research/SKILL.md` (Phase 1: Peter Lynch staging, Phase 2: Ingest, Phase 3: Leopold Thesis) |
| Review numbers / quotes | `agents/feynman.md` (อ่านอย่างเดียว คืนตาราง Verification แล้ว Munger เป็นคนแก้ในโน้ต) |
| Review thesis / logic / bear case | `agents/reviewer.md` (อ่านอย่างเดียว คืนข้อเสนอ ผู้เขียนเป็นคนแก้) |
| Draft Investment Thesis | `agents/leopold.md` (ใช้เฉพาะเมื่อมี Source Notes/Entities/Concepts เพียงพอแล้ว) |
| Check vault integrity | `py scripts/wiki_tool.py --lint` |
| Weekly thesis review: หลักฐานใหม่ทำให้ thesis แข็งขึ้น/อ่อนลง/ชน kill condition | `skills/delta-report/SKILL.md` (รายงานลง `03-Logs/Delta/` เสนอแก้ thesis เป็น checkbox ไม่แก้เอง) |
| หาความผิดปกติของราคา/volume/ภาษาในเอกสาร/ความสนใจโซเชียล | `skills/anomaly-scan/SKILL.md` (รายงานลง `03-Logs/Anomaly/` + เพิ่มงานใน Ingest Queue) |
| งบออกแล้ว: beat/miss เทียบ consensus, guidance เทียบ consensus, อ่าน read-through อุตสาหกรรม | `skills/earnings-scorecard/SKILL.md` (yfinance + press release → `dashboard/data/earnings-data.json` และ Source Note) |
| เขียน/แก้โค้ดใน `scripts/`, `.agents/skills/*/scripts/`, `dashboard/` | `skills/karpathy-guidelines/SKILL.md` (แก้เท่าที่จำเป็น ไม่เพิ่มฟีเจอร์เผื่อ ตั้งเกณฑ์ตรวจผลก่อนลงมือ) |
| เตรียม template public จากวอลต์นี้ | `skills/template-export/SKILL.md` |

## Required completion

รายงานไฟล์ที่สร้าง/แก้ไข, สรุป 60-second brief & claim table, อัปเดต Ingest Queue (`## Done`), และบันทึก Log แบบกระชับใน `03-Logs/Log.md` (บรรทัดล่าสุดอยู่บนสุด). จากนั้น commit งานทั้งหมดและบอกผู้ใช้ว่ามีอะไรรอ push ไป `origin` ก่อนย้ายไปทำงานเครื่องอื่น.
