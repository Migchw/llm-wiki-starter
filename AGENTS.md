# Agent Contract

> Canonical project-agent configuration lives in [`.agents/AGENTS.md`](.agents/AGENTS.md).

1. ห้ามแก้เนื้อหาใน `01-Raw/`; หากแปลงใหม่ให้สร้างไฟล์ derived ใหม่.
2. ห้ามสร้างตัวเลข, quote, วันที่ หรือ fact ลงทุนโดยไม่มี source ตรวจย้อนกลับได้.
3. ทุก source note link ไป raw อย่างน้อยหนึ่งไฟล์; ทุก concept/thesis link ไป source notes.
4. แยก **fact**, **interpretation**, และ **open question**.
5. อย่าให้คำแนะนำลงทุนเฉพาะบุคคล; ระบุความไม่แน่นอนเสมอ.

## Core Lean Ingestion Principles (Fast, Token-Efficient & No Over-Engineering)

1. **Python-First & Tiered Raw Extraction:**
   - ใช้ `python scripts/fetch_source.py "<URL หรือ Path>" --type <type>` (ขับเคลื่อนด้วย `bs4`, `playwright`, และ `markitdown`) ดึงและแปลงข้อมูลลง `01-Raw/` เสมอ
2. **Direct Single-Pass Ingestion for Standard Sources:**
   - บทความ ข่าว หรือเอกสารเดี่ยว (ขนาด S/M) ให้รันแบบ Direct Single-Pass จบใน Session เดียว (<30-45 วินาที) ไม่ต้อง Spawn Sub-agents ซ้ำซ้อน
3. **Selective & Concise Concepts:**
   - **Entity (`02-Wiki/Entities/`):** สร้าง/อัปเดตเสมอสำหรับบริษัท สถาบันการเงิน หรือบุคคลสำคัญ
   - **Concept (`02-Wiki/Concepts/`):** สกัดเฉพาะเมื่อมี **Durable Mental Model** หรือ **Structural Shift** ที่น่าสนใจและนำไปใช้ซ้ำได้จริง โดยเฉพาะการตัดสินใจเชิงโครงสร้าง เช่น **การจัดสรรเงินทุน (Capital Allocation), การตัดขายธุรกิจผลตอบแทนต่ำเพื่อมุ่งเน้นธุรกิจหลัก (Strategic Divestment / Portfolio Rationalization), การขยายตัวของมาร์จิ้นเชิงโครงสร้าง, หรือการเปลี่ยนแปลงของ Capital Cycle / Moat** และเขียน Concept ให้กระชับ ตรงประเด็น ไม่มีน้ำ
4. **Concise Activity Logging:**
   - บันทึกใน `03-Logs/Log.md` สั้นกระชับ 1–2 ประโยค ระบุแหล่งที่มา สาระสำคัญ และไฟล์ที่สร้าง/แก้ไข
