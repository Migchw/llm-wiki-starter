# Raw: หลักฐานที่เปลี่ยนไม่ได้

แยกตาม **ชนิดสื่อ** ดี เพราะเป็นตัวกำหนดวิธี ingest, metadata และ tool:

- `article/` — web article/newsletter
- `video/` — YouTube/podcast transcript
- `filing/` — annual report, 56-1, MD&A, earnings transcript
- `book/` — PDF/book chapters
- `dataset/` — CSV/XLSX export พร้อม data dictionary
- `inbox/` — รับเข้าชั่วคราว; triage ภายใน 7 วัน

อย่าแยก Raw ตาม ticker/sector: source เดียวมีหลายหัวข้อ. ใช้ tags และ Wiki links จัดหัวข้อแทน. ชื่อไฟล์แนะนำ `YYYYMMDD_source-slug.md`.
