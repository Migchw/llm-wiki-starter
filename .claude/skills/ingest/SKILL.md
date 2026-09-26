---
name: ingest
description: Fast, token-efficient, and lean end-to-end ingestion pipeline for research (articles, PDFs, YouTube videos, filings, books, datasets) into this Obsidian LLM Wiki. Uses Python-first tooling (bs4, playwright, markitdown) to capture raw evidence cleanly, distills source notes with claim tables, creates/updates entities, selectively extracts durable concepts, and maintains concise logs.
---

# Ingest Skill (Fast & Lean Ingestion Pipeline)

Use this skill to execute a fast, token-efficient ingestion workflow for any research source (URL, PDF, video, filing, or document).

---

## The 4-Step Lean Pipeline

```mermaid
flowchart TD
    A["Input: URL / PDF / Video / Text"] --> B["Step 1: Python-First Raw Capture<br/>(scripts/fetch_source.py -> 01-Raw/)"]
    B --> C["Step 2: Distill Source Note<br/>(02-Wiki/Sources/ with Claim Table)"]
    C --> D["Step 3: Update Entities & Selective Concepts<br/>(02-Wiki/Entities/ & concise Concepts)"]
    D --> E["Step 4: Update Queue & Concise Log<br/>(05-Index/Ingest Queue.md & 03-Logs/Log.md)"]
```

---

### Step 0: Triage vs. Direct Run

- **Single URL / File provided (`/ingest <source>`):** Run immediately in Direct Single-Pass mode (<30–45 seconds).
- **No source given (`/ingest`):** Open `05-Index/Ingest Queue.md`, pick the top `P0`/`P1` item marked `next`.
- **Multiple sources given at once:** Stage into `01-Raw/inbox/` via Python, list in Ingest Queue Inbox, and ask user for prioritization.

---

### Step 1: Python-First Raw Evidence Capture (`01-Raw/`)

**Rule:** Do NOT scrape web pages via LLM tools or dump raw HTML/CSS into LLM context.

1. **For URLs & Web Articles (Tier 1 & 2):**
   Run:
   ```bash
   py scripts/fetch_source.py "<URL>" --type article
   ```
   - **Tier 1:** Fast HTTP + BeautifulSoup (<0.5s)
   - **Tier 2 (Playwright Fallback):** หากเจอเว็บที่เป็น Dynamic/SPA หรือ JS-rendered จะสลับไปใช้ Playwright Headless Chromium อัตโนมัติ (หรือใช้ `--playwright` เพื่อบังคับใช้)

2. **For Local Documents (PDF, DOCX, PPTX, XLSX) (Tier 3):**
   Run:
   ```bash
   py scripts/fetch_source.py "<path/to/file>" --type <filing|book|dataset>
   ```
   แปลงเนื้อหาอย่างรวดเร็วและสะอาดผ่าน `markitdown`.

3. **For YouTube / Videos:**
   - ใช้ `scripts/fetch_source.py "<URL>" --type video` ดึง timestamped transcript ลง `01-Raw/video/` (ใช้ `--timestamps` ระบุวินาทีที่จะแคปภาพ)
   - รักษาถ้อยคำเดิมใน Raw ห้ามสรุปหรือใส่ข้อสรุปการลงทุนในไฟล์ Raw
   - frontmatter ต้องมี URL, channel, วันเผยแพร่/วันเก็บ, วิธีแปลง และ `transcript_quality`
   - คง timestamp ไว้สำหรับ claim ที่เป็นตัวเลขหรือข้อเท็จจริงสำคัญ
   - ชื่อบริษัทหรือตัวเลขที่ถอดเสียงไม่ชัด ห้ามเดาแก้ ให้ระบุช่วงที่มีปัญหาไว้ในรายงานและใส่ `verification: pending`
   - หากวิดีโอมีแผนภูมิ กราฟ สไลด์ หรือวัตถุจัดแสดงที่สำคัญต่อการตัดสินใจลงทุน ให้ใช้ `yt-dlp` + `FFmpeg` แคปเจอร์ภาพลงใน `06-Assets/<slug>/img_XX_<name>.png` และบันทึก `images: N` พร้อม `img_dir`

---

### Step 2: Distill Readable Source Note (`02-Wiki/Sources/`)

สร้าง `02-Wiki/Sources/YYYYMMDD_<slug>.md` ตาม `04-Schema/Templates/Source Note.md`:
1. **`60-second brief`**: 2–4 ประโยคสรุปสาระสำคัญและความเกี่ยวข้องต่อนักลงทุน
2. **`Thesis of the source`**: ใจความหลักและข้อโต้แย้งเชิงโครงสร้าง
3. **`Key numbers to remember`**: 3–6 ตัวเลขหลักจาก source
4. **`Claim table`**: แยกหมวดหมู่ชัดเจน:
   - `Fact`: ข้อมูลเชิงประจักษ์/ประวัติศาสตร์
   - `Interpretation`: มุมมอง/การคาดการณ์ของผู้เขียน
   - `Question`: ความเสี่ยงหรือประเด็นที่ยังต้องรอคำตอบ
   - Columns: `Claim | Category | Evidence location | Verification`
5. **`Key Exhibits & Slides`**: หากมีภาพที่แคปเจอร์ไว้ใน `06-Assets/<slug>/` ให้ฝังภาพแผนภูมิ/สไลด์ พร้อมระบุคำบรรยายและ timestamp
6. **`What changes my mind?`**: ปัจจัยหรือหลักฐานที่จะล้มล้างข้อสรุปนี้
7. **`Important excerpts`**: โควทสำคัญพร้อมระบุผู้พูด/แหล่งที่มา
8. **`Links`**: ลิงก์ `[[02-Wiki/Entities/...]]` และ `[[02-Wiki/Concepts/...]]`

กฎของ Source Note:
- อ่านไฟล์ Raw จนจบก่อนเขียน ทุกตัวเลข วันที่ และ quote ต้องชี้กลับไปที่ตำแหน่งใน Raw (หน้า/timestamp) ได้
- `Key numbers to remember` ทุกตัวต้องมีแถวอยู่ใน claim table
- fact, interpretation และ question แยกคนละแถว ห้ามรวมในบรรทัดเดียว
- ช่อง `Verification` เริ่มที่ `pending` เสมอ คนเขียนห้าม mark `verified` เอง (Feynman ส่งผลตรวจกลับมา แล้ว Munger เป็นคนแก้ในโน้ต)
- ลิงก์ได้เฉพาะ Entity/Concept ที่มีไฟล์อยู่แล้ว ถ้ายังไม่มีให้สร้างใน Step 3 หรือจดไว้ อย่าสร้างลิงก์ลอย
- ถ้า source บางหรือกำกวม ให้บอกตรงๆ ใน brief อย่าเติมให้ดูมั่นใจ

---

### Step 3: Update Entities & Selective Concepts

1. **Entities (`02-Wiki/Entities/`):**
   - **สร้าง/อัปเดตเสมอ** สำหรับบริษัท, สถาบันการเงิน (เช่น Federal Reserve), หรือสำนักข่าวที่เกี่ยวข้อง
   - คงโครงสร้าง: Definition, Relevance to Macro/Investment Themes, Sources & Related Notes

2. **Concepts (`02-Wiki/Concepts/` — Selective & Concise):**
   - **ไม่ฝืนสกัด Concept พร่ำเพรื่อ** หากเป็นข่าวสั้นหรือตัวเลขประจำไตรมาสทั่วไป
   - **สกัดทันทีเมื่อพบ Durable Mental Model หรือการตัดสินใจเชิงโครงสร้าง:** เช่น
     - **การจัดสรรเงินทุน (Capital Allocation / Capital Cycle):** การตัดขายธุรกิจผลตอบแทนต่ำเพื่อนำทุนไปเร่งธุรกิจหลัก (Strategic Divestment / Portfolio Rationalization)
     - **ความได้เปรียบเชิงการแข่งขัน (Moat / Unit Economics):** Pricing Power, Cost Leadership, Network Effects, Switching Costs
     - **การเปลี่ยนผ่านเชิงโครงสร้าง (Structural Shifts):** S-Curves, Paradigm Shifts, Regulatory Shifts
   - เขียนแบบ **กระชับ ตรงประเด็น ไม่มีน้ำ** ตามเทมเพลต `04-Schema/Templates/Concept.md`

---

### Step 4: Finalize Queue, Log, and Integrity

1. **Update Ingest Queue (`05-Index/Ingest Queue.md`):** ย้ายรายการไปยัง `## Done` พร้อมลิงก์ Raw และ Source note
2. **Concise Activity Log (`03-Logs/Log.md`):** บันทึก **1–2 ประโยคสั้นๆ** ที่ด้านบนสุดของตาราง (Newest on top)
3. **Audit:** รัน `py scripts/wiki_tool.py --lint` ต้องไม่มี broken link และโน้ตที่เพิ่งเขียนต้องไม่อยู่ในรายการ banned phrase (lint แสดงเป็น warning พร้อม `file:line` รายการคำอยู่ใน `.agents/AGENTS.md` หัวข้อ 1)
