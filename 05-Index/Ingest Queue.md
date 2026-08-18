---
type: index
status: active
updated: 2026-08-18
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
|  |  |  |  |

## Deferred / rejected

| Source | Status | Reason | Review date |
|---|---|---|---|
|  |  |  |  |
