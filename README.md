# LLM Wiki for Investors — Course Vault

Obsidian vault สำหรับสอนผู้เริ่มต้นสร้างความจำระยะยาวร่วมกับ LLM.

## เริ่มใน 10 นาที

1. เปิด Obsidian → **Open folder as vault** → เลือกโฟลเดอร์นี้
2. อ่าน [[ONBOARDING]] (คู่มือระบบฉบับสมบูรณ์สำหรับ AI & นักลงทุน) หรือ [[00-Start-Here]]
3. นำ source เข้า `01-Raw/` ตามชนิดสื่อ หรือใช้คำสั่ง `/ingest <URL>`
4. สร้าง source note ใน `02-Wiki/Sources/` แล้วใช้ `[[wikilink]]` เชื่อมกลับ raw
5. สร้าง concept เฉพาะความรู้ที่ใช้ซ้ำได้ตามเกณฑ์ 4 Archetypes ของ Darwin ใน [[04-Schema/Concept Checklist]]

## หลักการ

- **Raw** = หลักฐานดิบ, ไม่แก้เนื้อหาเดิม
- **Wiki** = ความเข้าใจที่แก้ไขได้ และต้องอ้างกลับหา raw
- **Schema** = กติกา, templates และ workflow
- **Logs** = ร่องรอยงาน
- **Index** = จุดเริ่มค้นของคนและ AI

อ่าน [[05-Index/Home]] เป็นจุดเริ่มต้นเสมอ.

## Tools ที่ต้องมีในเครื่อง (สำหรับ ingest/research ที่มี PDF, filing, รูปสไลด์)

การอ่าน/ค้นเว็บทั่วไป (WebSearch/WebFetch ของ agent) พอสำหรับข่าว/บทความทั่วไป แต่ **ใช้ไม่ได้กับหลาย
เว็บ IR/SET ที่กันบอท (403) หรือ PDF ที่ WebFetch แกะข้อความไม่ออก** — งานที่มี PDF filing/oppday deck/
investor day ต้องมี Python และไลบรารีต่อไปนี้ติดตั้งในเครื่อง เพื่อดาวน์โหลด+แกะเนื้อหาแบบเดียวกับที่
`.claude/skills/ingest/SKILL.md` Step 2b ใช้จริง (วิธีเดียวกับที่เคยพิสูจน์แล้วในโปรเจกต์
`infinity_trade_cloud`):

- **Python 3.10+** — เช็กด้วย `python --version`
- **`pymupdf`** (`import fitz`) — แกะรูป/render สไลด์จาก PDF
- **`pypdf`** — เช็ก text layer ก่อนเสมอ (กัน PDF สแกนที่ทำให้ agent เขียนจากความจำ) + แกะข้อความ
- **`markitdown`** — แปลง PDF/HTML → Markdown สำหรับกรณีเนื้อหายาว
- **PowerShell** (`Invoke-WebRequest -UserAgent '...'`) — ดาวน์โหลดไฟล์จากเว็บที่บล็อก WebFetch tool
  (เว็บ IR หลายเจ้า เช่น `top.listedcompany.com` บล็อกการเข้าถึงแบบ agent fetch แต่ยอมรับ request
  ที่มี User-Agent ของเบราว์เซอร์จริง)
- **`ffmpeg`** — แกะเสียงออกจากไฟล์วิดีโอ/บันทึกเสียงที่ผู้ใช้ส่งมาเอง (ไม่ใช่ลิงก์ YouTube หรือคลิปที่ไม่มี
  caption) ก่อนส่งเข้า transcribe
- **`faster-whisper`** — transcribe ไฟล์เสียง/วิดีโอที่ไม่มี caption สำเร็จรูปให้อยู่ในรูปข้อความ (เลือกโมเดล
  `small`/`medium` ตามสมดุลความเร็ว-ความแม่นยำที่ต้องการ)
- **`yt-dlp`** — ดาวน์โหลดวิดีโอ YouTube ชั่วคราวเพื่อจับภาพสไลด์ (`.claude/skills/ingest/SKILL.md` Step 2d)

ติดตั้งไลบรารีที่ขาด: `pip install pymupdf pypdf markitdown faster-whisper yt-dlp` (และติดตั้ง `ffmpeg` แยกที่ระดับ OS — ไม่ใช่ pip package)

ไม่มีเครื่องมือพวกนี้ = ingest ได้แค่บทความเว็บทั่วไปกับข้อความสั้นๆ — PDF/filing/สไลด์จะติดปัญหา
เหมือนที่เจอตอนทดสอบ `/research TOP` (ดู `03-Logs/Log.md` วันที่ 2026-08-17)
