---
name: template-export
description: Prepare the public template repo from this private vault — copy only the framework (agents, skills, scripts, schema, dashboard, docs) onto the public template's branch, reset personal data, and run a leak check, without pushing. Use for /template-export, "อัปเดต template", "เอาไปแจกคนอื่น", "push ขึ้น public", or after changing a skill/agent/script/dashboard that other people who cloned the template should get.
---

# Template export

วอลต์นี้เป็น repo private ที่มีงานวิจัยจริง ส่วน template ที่คนอื่น clone อยู่ที่ remote `upstream` (public) งานนี้ย้ายเฉพาะตัวระบบไปฝั่ง public โดยงานวิจัยไม่หลุดออกไป

## ขั้นตอน

1. ต้อง commit งานบน branch ปัจจุบันให้หมดก่อน เพราะสคริปต์ copy จาก commit ไม่ใช่จากไฟล์ที่ยังไม่ commit
2. `git fetch upstream` แล้วรัน `py scripts/export_template.py`
   - สร้าง worktree `../llm-wiki-template-export` บน branch `template-export` จาก `upstream/master`
   - แทนที่ path ของตัวระบบ (`FRAMEWORK` ในสคริปต์) ด้วยเวอร์ชันจาก branch ปัจจุบัน
   - ลบไฟล์ส่วนตัวและ skill ที่ไม่มี license (`EXCLUDE`) และรีเซ็ต watchlist กับ consensus history ให้ว่าง (`RESET`)
   - ตัดบรรทัดที่อ้างถึง path ที่ถูกลบ (`STRIP_LINES`) เช่น routing ของ scrutinize ใน AGENTS
   - หาชื่อ repo private และชื่อ Entity ทุกตัวในวอลต์นี้ (ไม่สนตัวพิมพ์ใหญ่เล็ก) ในทุกไฟล์ข้อความ ถ้าเจอจะ exit 1 พร้อมบอก `file:line`
3. ถ้า leak check เจอ ให้แก้ต้นทางในวอลต์ private (ให้ข้อความเป็นกลาง) แล้ว commit และรันใหม่ ห้ามแก้เฉพาะใน worktree เพราะรอบหน้าจะหลุดอีก
4. ตรวจว่า dashboard ยังรันได้บน vault เปล่า: ใน `../llm-wiki-template-export/dashboard` รัน `npm ci` แล้ว `npm run build`
5. รายงานผู้ใช้: ไฟล์ที่เปลี่ยนเทียบกับ `upstream/master` (`git -C ../llm-wiki-template-export status --short`), ผล leak check และผล build
6. **ห้าม push เอง** รอผู้ใช้อนุมัติ แล้วค่อย commit ใน worktree และส่งขึ้น repo public ด้วย URL ตรง เพราะ push URL ของ remote `upstream` ถูกปิดไว้กันพลาด:
   ```bash
   git -C ../llm-wiki-template-export push https://github.com/Migchw/llm-wiki-starter.git template-export
   gh pr create --repo Migchw/llm-wiki-starter --base master --head template-export
   ```
7. เสร็จแล้วลบ worktree: `git worktree remove ../llm-wiki-template-export`

## เมื่อไรต้องแก้สคริปต์

- เพิ่มโฟลเดอร์ตัวระบบใหม่ที่ root → เพิ่มใน `FRAMEWORK`
- เพิ่มไฟล์ที่มีข้อมูลส่วนตัวในโฟลเดอร์ตัวระบบ → เพิ่มใน `EXCLUDE` หรือ `RESET`
- vendor skill จากคนอื่นที่ไม่มี license → เพิ่มใน `EXCLUDE`
