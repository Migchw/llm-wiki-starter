# LLM Wiki for Investment Research

เปลี่ยนบทความ งบการเงิน และ transcript ให้เป็นคลังความรู้การลงทุนที่ย้อนกลับไปดูหลักฐานได้

ใช้ **Obsidian** อ่านและเชื่อมโยงโน้ต ใช้ **Claude Code** ช่วยเก็บแหล่งข้อมูล เขียน Source Note และร่าง Investment Thesis ส่วนโน้ตเก็บเป็นไฟล์ Markdown ในเครื่อง คุณจึงเปิดอ่าน แก้ไข และย้ายไปใช้กับเครื่องมืออื่นได้

[เริ่มใช้งาน](#เริ่มใช้งาน) · [คำสั่งที่ใช้บ่อย](#คำสั่งที่ใช้บ่อย) · [โครงสร้างไฟล์](#โครงสร้างไฟล์) · [คู่มือเพิ่มเติม](#คู่มือเพิ่มเติม)

## ปัญหาที่โปรเจกต์นี้ช่วยแก้

เมื่ออ่านหลายบริษัทพร้อมกัน ข้อมูลมักกระจายอยู่ใน PDF แท็บเบราว์เซอร์ และบทสนทนากับ AI พอกลับมาทบทวน เราอาจจำข้อสรุปได้ แต่หาตัวเลขหรือคำพูดต้นทางไม่เจอ

Wiki นี้แยก **หลักฐานที่เก็บมา** ออกจาก **ความเข้าใจที่เขียนขึ้น** แล้วเชื่อมสองส่วนเข้าด้วยกัน ข้อมูลใหม่จึงเพิ่มลงในงานวิจัยเดิมได้ โดยยังย้อนดูที่มาของข้อสรุปแต่ละเรื่องได้

## สิ่งที่คุณจะได้

- **Raw capture** — เนื้อหาที่ดึงหรือแปลงมา พร้อม URL และ metadata ของแหล่งข้อมูล
- **Source Note** — สรุปที่อ่านต่อได้ พร้อมตารางแยก fact, interpretation และคำถามที่ยังไม่มีคำตอบ
- **Entity และ Concept** — โน้ตบริษัทหรือบุคคลที่เกี่ยวข้อง และแนวคิดที่ใช้ซ้ำได้ เช่น capital cycle หรือ pricing power เมื่อแหล่งข้อมูลมีเนื้อหารองรับ

เมื่อมีหลักฐานจากหลายแหล่งที่ผ่านการทบทวนเพียงพอ ใช้ `/research <ticker>` ช่วยร่าง **Investment Thesis** พร้อม base case, bear case และเงื่อนไขที่จะทำให้เปลี่ยนใจ ดูรูปแบบผลลัพธ์ได้ที่ [Source Note template](04-Schema/Templates/Source%20Note.md) และ [Thesis template](04-Schema/Templates/Thesis.md)

## เริ่มใช้งาน

Quickstart นี้ใช้ [Obsidian](https://obsidian.md/download), [Claude Code](https://code.claude.com/docs/en/quickstart), **Python 3.10+** และ Git ติดตั้งและลงชื่อเข้าใช้ Claude Code ตามคู่มือของผู้ให้บริการก่อนเริ่ม

### 1. ดาวน์โหลด repo

```bash
git clone https://github.com/Migchw/llm-wiki-starter.git
cd llm-wiki-starter
```

หรือเลือก **Code → Download ZIP** บน GitHub แล้วแตกไฟล์ เปิด terminal ในโฟลเดอร์ที่แตกออกมา

### 2. เตรียม Python สำหรับบทความเว็บและตัวตรวจ Wiki

ตัวอย่างนี้เก็บ virtual environment ไว้นอกโฟลเดอร์ vault และใช้ environment เดียวกันตลอด session

**macOS / Linux**

```bash
python3 --version
python3 -m venv ../.venv-llm-wiki
source ../.venv-llm-wiki/bin/activate
python -m pip install beautifulsoup4 PyYAML
```

<details>
<summary>Windows — Command Prompt</summary>

```bat
py -3 --version
py -3 -m venv ..\.venv-llm-wiki
..\.venv-llm-wiki\Scripts\activate.bat
python -m pip install beautifulsoup4 PyYAML
```

</details>

หากเลขเวอร์ชันที่แสดงต่ำกว่า 3.10 ให้ติดตั้ง Python รุ่นใหม่ก่อนสร้าง environment ส่วน PDF, Office, เว็บที่ใช้ JavaScript และ YouTube มีเครื่องมือเสริมอยู่ด้านล่าง

### 3. เปิดโฟลเดอร์เดียวกันใน Obsidian และ Claude Code

ใน **Obsidian** เลือก **Open folder as vault** แล้วเลือก `llm-wiki-starter` จากนั้นเปิด [Home](05-Index/Home.md) เป็นหน้าหลัก

ใน **terminal ที่เปิด environment แล้ว** และยังอยู่ในโฟลเดอร์ repo ให้รัน:

```bash
claude
```

คำสั่งที่ขึ้นต้นด้วย `/` ใน README นี้ใช้ใน Claude Code โปรเจกต์มี skills อยู่ใน [`.claude/skills/`](.claude/skills/) ให้โหลดจากโฟลเดอร์นี้

### 4. ลองกับแหล่งข้อมูลของคุณหนึ่งชิ้น

ส่งลิงก์บทความที่อ่านได้สาธารณะ โดยแทน `<URL>` ด้วยลิงก์จริง:

```text
/ingest <URL>
```

ถ้าต้องการให้ agent พาทำทีละขั้น ใช้ `/onboarding` แทน ขั้นตอนนั้นจะถามหาแหล่งข้อมูลและนำเข้าให้ด้วย

เมื่อจบงาน เปิด Raw ใน `01-Raw/` เทียบกับต้นฉบับ แล้วอ่าน Source Note ใน `02-Wiki/Sources/` ตรวจว่าตาราง claim ชี้กลับไปยังหลักฐานได้ รายการงานอยู่ใน [Ingest Queue](05-Index/Ingest%20Queue.md) และประวัติการทำงานอยู่ใน [Log](03-Logs/Log.md)

<details>
<summary>เครื่องมือเสริมสำหรับ JavaScript, PDF / Office และ YouTube</summary>

รันเฉพาะชุดที่ต้องใช้ใน terminal ที่เปิด Python environment แล้ว

**เว็บที่ต้องรอ JavaScript แสดงเนื้อหา**

```bash
python -m pip install playwright
python -m playwright install chromium
```

Fetcher จะลอง HTTP ก่อน และใช้ Playwright เป็น fallback เมื่อมีการติดตั้งไว้ การ render หน้าเว็บไม่ได้รับประกันว่าจะผ่านเว็บที่ต้อง login หรือบล็อก bot

**PDF ที่มีข้อความ และไฟล์ DOCX / PPTX / XLSX**

```bash
python -m pip install "markitdown[pdf,docx,pptx,xlsx]" pypdf
```

**YouTube ที่มี transcript ให้เข้าถึงได้**

```bash
python -m pip install youtube-transcript-api
```

ตัว fetcher ปัจจุบันยังไม่ได้ทำ OCR ให้ PDF สแกน หรือถอดเสียงวิดีโอที่ไม่มี transcript โดยอัตโนมัติ หากเนื้อหาที่ได้ว่างหรือขาดช่วง ให้หาแหล่งข้อมูลที่อ่านได้ก่อนนำไปสรุป

</details>

## คำสั่งที่ใช้บ่อย

พิมพ์ในบทสนทนา Claude Code ที่เปิด repo นี้อยู่:

| คำสั่ง | ใช้เมื่อ | ผลลัพธ์ที่คาดหวัง |
|---|---|---|
| `/onboarding` | เพิ่งเริ่มใช้ vault | พาทำความรู้จักโครงสร้างและลองแหล่งข้อมูลแรก |
| `/ingest <URL หรือ path>` | มีบทความหรือเอกสารแล้ว | Raw → Source Note → Entity และ Concept เมื่อมีเนื้อหารองรับ |
| `/research <ticker>` | ต้องการรวบรวมงานวิจัยของบริษัท | หาและจัดลำดับแหล่งข้อมูล นำเข้า แล้วร่าง Thesis เมื่อหลักฐานเพียงพอ |
| `/wiki-health-check` | ต้องการทบทวนคุณภาพ Wiki | รายงานปัญหาโครงสร้างและเนื้อหาใน `lint_pending/` เพื่อพิจารณาแก้ไข |

ตัวอย่าง `/research AAPL` ใช้เริ่มค้นคว้าบริษัท ควรระบุตลาดด้วยเมื่อ ticker อาจซ้ำกัน

<details>
<summary>ใช้ Python CLI เพื่อเก็บ Raw โดยตรง</summary>

รันจากโฟลเดอร์ repo ใน terminal โดยแทนค่าระหว่าง `<...>` ด้วย URL หรือ path จริง:

```bash
python scripts/fetch_source.py "<ARTICLE_URL>" --type article
python scripts/fetch_source.py "<DOCUMENT_URL>" --type filing
python scripts/fetch_source.py "<LOCAL_PDF_PATH>" --type filing
python scripts/fetch_source.py "<YOUTUBE_URL>" --type video
```

ใช้ URL ที่ลงท้ายด้วย `.pdf`, `.docx`, `.pptx` หรือ `.xlsx` สำหรับเอกสารโดยตรง เพิ่ม `--playwright` เมื่อต้องการบังคับ render เว็บด้วย Chromium

CLI แสดง `SAVED_RAW: <path>` หลังบันทึกไฟล์ ทำเฉพาะขั้น Raw capture ส่วน Source Note และ Thesis เป็นงานของ agent ตรวจเนื้อหาในไฟล์ทุกครั้ง เพราะการบันทึกสำเร็จไม่ได้แปลว่าดึงเนื้อหาได้ครบ

สำหรับไฟล์ที่อยู่ในเครื่อง `raw_file` ยังชี้ไปยังตำแหน่งต้นฉบับ จึงต้องเก็บไฟล์นั้นไว้ และปรับ path หากย้ายไฟล์หรือย้าย vault ไปเครื่องอื่น

</details>

## โครงสร้างไฟล์

| โฟลเดอร์ | เก็บอะไร |
|---|---|
| [`01-Raw/`](01-Raw/) | หลักฐานที่ capture มา แยกตาม article, filing, book, video และ dataset |
| [`02-Wiki/`](02-Wiki/) | Source Notes, Entities, Concepts, Theses และ Synthesis ที่เชื่อมหลายเรื่องเข้าด้วยกัน |
| [`03-Logs/`](03-Logs/) | ประวัติการนำเข้าและแก้ไข Wiki |
| [`04-Schema/`](04-Schema/) | Templates, workflow และเกณฑ์คุณภาพของโน้ต |
| [`05-Index/`](05-Index/) | Home, คิวงาน และบันทึกสุขภาพ vault |
| [`06-Assets/`](06-Assets/) | รูปและไฟล์แนบที่ใช้ประกอบโน้ต |
| [`scripts/`](scripts/) | ตัวดึงข้อมูล ตัวบันทึก raw และ linter |
| [`lint_pending/`](lint_pending/) | รายงานตรวจ Wiki ที่รอพิจารณา |

กติกาของโปรเจกต์อยู่ใน [`.agents/AGENTS.md`](.agents/AGENTS.md) ส่วนคำสั่งและ subagents สำหรับ Claude Code อยู่ใน [`.claude/`](.claude/) โน้ตเขียนเป็นภาษาไทยเป็นหลัก และคงศัพท์การเงิน เช่น moat, EBITDA และ DCF ตามบริบท

<details>
<summary>หน้าที่ของแต่ละ agent</summary>

**Munger** คือ session หลักที่คุยกับผู้ใช้ ทำงานนำเข้าทั่วไปโดยตรงและประสานงานวิจัยที่ซับซ้อน ส่วน subagents มีหน้าที่ตามไฟล์กำหนดดังนี้:

| Agent | หน้าที่ |
|---|---|
| [Peter Lynch](.claude/agents/peter-lynch.md) | หา ตรวจลิงก์ และจัดลำดับแหล่งข้อมูล |
| [Ingest Runner](.claude/agents/ingest-runner.md) | ดูแลการนำเข้าหนึ่งแหล่งข้อมูล |
| [René](.claude/agents/rene.md) | จัดเตรียม transcript และ metadata |
| [Researcher](.claude/agents/researcher.md) | เขียน Source Note จาก Raw |
| [Feynman](.claude/agents/feynman.md) | ตรวจตัวเลข วันที่ และคำพูดอ้างอิง |
| [Reviewer](.claude/agents/reviewer.md) | ทบทวนเหตุผล bear case และช่องว่างของหลักฐาน |
| [Darwin](.claude/agents/darwin.md) | สกัดแนวคิดที่ใช้ซ้ำได้และเชื่อม Entity |
| [Leopold](.claude/agents/leopold.md) | ร่าง Thesis จากหลักฐานที่ผ่านการทบทวน |

ดูขั้นตอนและจุดส่งต่องานใน [Project Workflow](PROJECT-WORKFLOW.md)

</details>

## หลักฐานและการตรวจคุณภาพ

**เก็บ Raw เดิมไว้** — เมื่อนำเข้าแหล่งเดิมอีกครั้ง fetcher จะคงหลักฐานเดิมไว้ และสร้าง capture ใหม่เมื่อเนื้อหาหรือ metadata เปลี่ยน เช่น วันที่ capture ไฟล์ชื่อซ้ำไม่เขียนทับกัน ส่วนเอกสารที่ดาวน์โหลดมี `raw_file` ชี้กลับไปยังต้นฉบับของ capture นั้น

**แยกสิ่งที่รู้กับสิ่งที่ตีความ** — Source Note ต้องเชื่อมกลับไปหา Raw และแยก fact, interpretation และ open question ข้อที่ยังตรวจไม่ได้ให้คง `verification: pending` การมี agent สำหรับตรวจสอบไม่ได้ยืนยันว่าทุก claim ผ่านการตรวจแล้ว

**เปิดดูหลักฐานก่อนใช้ข้อสรุป** — ตัวดึงเว็บอาจตกหล่นตารางหรือข้อความบางส่วน และ metadata อาจคลาดเคลื่อน โดยเฉพาะวันที่กับงวดรายงาน ให้เทียบตัวเลขสำคัญกับเอกสารต้นทาง

รันตัวตรวจโครงสร้างและดูสถิติได้จาก terminal:

```bash
python scripts/wiki_tool.py --lint
python scripts/wiki_tool.py --stats
```

Linter ปัจจุบันอาจนับลิงก์ตัวอย่างในคู่มือเป็นลิงก์เสีย และยังตรวจความเชื่อมโยงของหลักฐานได้ไม่ครบ ผล `100% HEALTHY` จึงไม่ได้รับรองความถูกต้องของข้อสรุปการลงทุน

ไฟล์ vault เก็บในเครื่อง แต่เมื่อใช้งานผ่าน AI เนื้อหาที่ agent อ่านอาจถูกส่งไปยังผู้ให้บริการโมเดลตามการตั้งค่าที่ใช้ เลือกแหล่งข้อมูลที่คุณมีสิทธิ์นำมาใช้งานในบริบทนั้น

## ร่วมพัฒนา

แจ้งปัญหาผ่าน [Issues](https://github.com/Migchw/llm-wiki-starter/issues) พร้อมคำสั่งที่ใช้ ผลที่คาดหวัง และตัวอย่างที่ทำซ้ำได้ หรือส่ง PR ที่แก้ปัญหาหนึ่งเรื่องต่อครั้ง สำหรับบั๊กการดึงข้อมูล ควรใช้ fixture ที่แบ่งปันได้แทนเอกสารส่วนตัว

ชุดทดสอบการเก็บ raw ใช้ Python standard library และรันแบบ offline:

```bash
python -m unittest discover -s tests -v
```

## คู่มือเพิ่มเติม

- [Project Blueprint](PROJECT-BLUEPRINT.md) — แนวคิดและภาพรวมของระบบ
- [Project Workflow](PROJECT-WORKFLOW.md) — บทบาท agent และเส้นทางการทำงาน
- [Concept Checklist](04-Schema/Concept%20Checklist.md) — เมื่อใดควรสร้าง Concept ใหม่
- [Obsidian Fundamentals](04-Schema/Obsidian%20Fundamentals.md) — frontmatter, links และการอ่าน vault
- [DeepWiki](https://deepwiki.com/Migchw/llm-wiki-starter/1-overview:-llm-wiki-for-investment-research) — คำอธิบายระบบพร้อมลิงก์กลับไปยังโค้ด อาจอ้างอิง commit เก่ากว่า repo ปัจจุบัน
