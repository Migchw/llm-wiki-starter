---
type: index
status: active
updated: 2026-09-07
---

# Ingest Queue

Raw จำนวนมากไม่ใช่ backlog ที่ต้องทำให้หมดทันที. หน้านี้คือ **คิวตัดสินใจ**: เลือกสิ่งที่คุ้มทำต่อก่อน, พัก/ตัดสิ่งที่ไม่คุ้ม, และเห็นว่าค้างอยู่ตรงไหน.

## วิธีใช้

1. เมื่อมีไฟล์เข้า `01-Raw/inbox/` ให้เพิ่มหนึ่งบรรทัดในตาราง Inbox.
2. ทำ triage 30–45 นาที/สัปดาห์; ให้คะแนนและเปลี่ยนสถานะ ไม่ต้อง ingest ทั้งหมด.
3. เลือกทำเฉพาะ `next` 1–3 ชิ้นต่อ session. เมื่อสร้าง source note แล้ว ให้ย้ายบรรทัดไป Done พร้อมลิงก์.
4. `deferred` และ `rejected` เป็นผลลัพธ์ที่ดี: ช่วยไม่ให้ backlog กลายเป็นความรู้สึกผิด.

## สถานะ

| Status | ความหมาย | การกระทำต่อ |
|---|---|---|
| `inbox` | ยังไม่ประเมิน | triage |
| `next` | คุ้มทำใน 1–2 sessions | ingest |
| `in-progress` | กำลังแปลง/สรุป/ตรวจ | ทำขั้นปัจจุบันให้จบ |
| `waiting` | รอ transcript, filing, หรือข้อมูล | ระบุสิ่งที่รอ |
| `done` | มี source note แล้ว | link output |
| `deferred` | อาจมีค่าภายหลัง | ใส่เหตุผล/review date |
| `rejected` | ไม่คุ้ม ingest | ใส่เหตุผลสั้น ๆ |

## Inbox / triage

| Priority | Status | Raw source | Type | Why now? | Effort | Output target | Next action |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

### การให้ Priority

- **P1:** เกี่ยวกับ thesis/decision ที่กำลังทำ, แหล่ง primary, หรือมีวันหมดอายุ
- **P2:** เสริม mental model/industry context ที่ใช้ได้กว้าง
- **P3:** น่าสนใจแต่ยังไม่มีคำถามนำ
- **P0:** ต้องตรวจด่วนเพราะอาจล้ม thesis ปัจจุบัน

ให้ทำ `P0/P1` ก่อนเสมอ และใช้ Effort `S/M/L` กันงานใหญ่กินทั้งวัน.

## In progress

| Source | Current stage | Blocker | Owner / next action |
|---|---|---|---|
|  | raw → readable source note → verify → synthesize |  |  |

## Done

| Date | Raw source | Readable source note | Concepts / thesis updated |
|---|---|---|---|
| 2026-09-07 | (Phase 3 synthesis — no new raw) | — | Thesis draft [[02-Wiki/Theses/BDMS]] (Watch: CoE + dual FCF); Entity [[02-Wiki/Entities/BDMS]] linked |
| 2026-09-07 | [[01-Raw/filing/20260907_20260907-bdms-thailand-focus2026]] (+ inbox PDF/note) | [[02-Wiki/Sources/20260907_BDMS-thailand-focus-2026]] | Entity [[02-Wiki/Entities/BDMS]] updated; Concept [[02-Wiki/Concepts/Hospital-Wellness-Ecosystem-Feed]] created; [[02-Wiki/Concepts/CoE-Concentration-Hospital-Network]] updated |
| 2026-09-07 | [[01-Raw/filing/20260907_bdms-one-report-2025-en]] (+ inbox PDF/note) | [[02-Wiki/Sources/20260907_BDMS-one-report-2025]] | Entity [[02-Wiki/Entities/BDMS]] updated; Concept [[02-Wiki/Concepts/Hospital-Network-FCF-Dual-Allocation]] created; [[02-Wiki/Concepts/CoE-Concentration-Hospital-Network]] linked |
| 2026-09-07 | [[01-Raw/filing/20260907_20260824-bdms-earnings-call-2q2026]] (+ inbox PDF/note) | [[02-Wiki/Sources/20260907_BDMS-oppday-earnings-call-2q2026]] | Entity [[02-Wiki/Entities/BDMS]] updated; Concept [[02-Wiki/Concepts/CoE-Concentration-Hospital-Network]] |
| 2026-09-07 | [[01-Raw/filing/20260907_20260814-bdms-mdna-2q2026-en]] (+ inbox PDF/note) | [[02-Wiki/Sources/20260907_BDMS-mda-2q2026]] | Entity [[02-Wiki/Entities/BDMS]] updated; no new Concepts |
| 2026-09-07 | [[01-Raw/filing/20260907_20260814-bdms-fs-2q2026-en]] (+ inbox PDF/note; binary also at `01-Raw/filing/20260907_20260814-bdms-fs-2q2026-en.pdf`) | [[02-Wiki/Sources/20260907_BDMS-financial-statements-2q2026]] | Entity [[02-Wiki/Entities/BDMS]]; no new Concepts |

## Deferred / rejected

| Source | Status | Reason | Review date |
|---|---|---|---|
| SET Oppday / Company Snapshot *text transcript* (BDMS) — page https://www.set.or.th/en/market/product/stock/quote/BDMS/company-profile/oppday-company-snapshot | deferred | Page verified-open (HTTP 200) but SPA; no downloadable transcript/PDF extracted this session. Staged IR Earnings Call (Opp Day) 2Q2026 PDF instead. User may supply SET video/transcript if needed. | 2026-09-14 |
| BDMS Analyst Presentation 2Q2026 Results — https://bdms.listedcompany.com/misc/PRESN/20260821-bdms-analyst-presentation-2q2026.pdf | deferred | verified-open but not staged; Thailand Focus 2026 chosen as P1 investor presentation; Opp Day deck covers results messaging. Stage if user wants earnings-slide duplicate. | 2026-09-14 |
