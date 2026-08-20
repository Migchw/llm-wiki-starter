# LLM Wiki Agent Operating Manual

Read this file before working in the vault. Read `../05-Index/Home.md`, `../05-Index/Ingest Queue.md`, and the relevant template before creating notes.

## Boundaries

1. Treat `../01-Raw/` as immutable evidence; create a derived note instead of editing it.
2. Do not invent figures, dates, quotes, links, or citations.
3. Link every source note to raw. Link every concept/thesis to source notes.
4. Label facts, interpretations, and open questions separately.
5. Use `verification: pending` if an important claim has not been checked.
6. Do not give personalized investment advice or execute trades.

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
   - ใช้ `python scripts/fetch_source.py "<URL หรือ Path>" --type <type>` (ขับเคลื่อนด้วย `bs4`, `playwright`, และ `markitdown`) ดึงและแปลงข้อมูลลง `01-Raw/` เสมอ
   - **Tier 1 (Fast HTTP):** ดึงผ่าน BS4 ภายใน <0.5 วินาที
   - **Tier 2 (Playwright Fallback):** หากเจอเว็บที่เป็น Dynamic/SPA (React, Vue, SET) สลับไปใช้ Headless Chromium อัตโนมัติ
   - **Tier 3 (MarkItDown):** สำหรับแปลง PDF, PPTX, DOCX, XLSX ในเครื่อง
   - ห้ามใช้ LLM scrape เว็บดิบเข้า context โดยตรง เพื่อประหยัด Token และตัดขยะ CSS/JS
2. **Direct Single-Pass Ingestion for Standard Sources:**
   - บทความ ข่าว หรือเอกสารเดี่ยว (ขนาด S/M) ให้รันแบบ Direct Single-Pass จบใน Session เดียว ไม่ต้อง Spawn Sub-agents ซ้ำซ้อนเพื่อตัดปัญหา Context Duplication
   - ใช้ Sub-agents เฉพาะกรณีงานวิจัยชุดใหญ่ที่มีหลายขั้นตอนซับซ้อน (`/research <ticker>`, 10-K ขนาดยักษ์, Bear-case pass)
3. **Selective & Concise Concepts:**
   - **Entity (`02-Wiki/Entities/`):** สร้าง/อัปเดตเสมอสำหรับบริษัท สถาบันการเงิน หรือบุคคลสำคัญ
   - **Concept (`02-Wiki/Concepts/`):** สกัดเฉพาะเมื่อมี **Durable Mental Model** หรือ **Structural Shift** ที่น่าสนใจและนำไปใช้ซ้ำได้จริง หากเป็นข่าวสั้นทั่วไปไม่ต้องฝืนสกัด Concept และเขียน Concept ให้กระชับ ตรงประเด็น ไม่มีน้ำ
4. **Concise Activity Logging:**
   - บันทึกใน `03-Logs/Log.md` สั้นกระชับ 1–2 ประโยค ระบุแหล่งที่มา สาระสำคัญ และไฟล์ที่สร้าง/แก้ไข ไม่เขียนเป็นย่อหน้ายาว

---

## Orchestrator (Munger)

The main session running this vault is called **Munger**. It orchestrates the pipeline, executes direct single-pass ingestion for standard sources, or routes multi-step ticker research to specialized sub-agents.

## Routing

| งาน | วิธีการดำเนินการ |
|---|---|
| Ingest บทความ/ข่าว/เอกสารทั่วไป (S/M) | รัน `scripts/fetch_source.py` $\rightarrow$ สร้าง Source Note + Entity (+ Concept ถ้ามี) จบใน Direct Single-Pass (<30-45 วินาที) |
| Ingest Video transcript | `agents/rene.md` (บันทึก transcript สะอาดลง `01-Raw/video/`) |
| Research a ticker end-to-end (find → ingest → thesis) | `skills/research/SKILL.md` (Phase 1: Peter Lynch staging, Phase 2: Ingest, Phase 3: Leopold Thesis) |
| Review numbers / quotes | `agents/feynman.md` |
| Review thesis / logic / bear case | `agents/reviewer.md` |
| Draft Investment Thesis | `agents/leopold.md` (ใช้เฉพาะเมื่อมี Source Notes/Entities/Concepts เพียงพอแล้ว) |
| Check vault integrity | `python scripts/wiki_tool.py --lint` |

## Required completion

รายงานไฟล์ที่สร้าง/แก้ไข, สรุป 60-second brief & claim table, อัปเดต Ingest Queue (`## Done`), และบันทึก Log แบบกระชับใน `03-Logs/Log.md` (บรรทัดล่าสุดอยู่บนสุด).
