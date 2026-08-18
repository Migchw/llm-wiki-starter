---
name: onboarding
description: Interactive first-run walkthrough for someone who just cloned this vault. Asks who they are and what they're researching, then walks them through opening the vault in Obsidian, capturing one real source, and creating their first Source Note and Concept — pointing to README.md/PROJECT-BLUEPRINT.md for the full reference instead of repeating it. Use when the user runs /onboarding, or says this is their first time in the vault.
---

# Onboarding — first 10 minutes in this vault

Read `.agents/AGENTS.md` before this. This skill's job is to get a brand-new user to one real, working example — not to explain the whole system (that's `README.md` and `PROJECT-BLUEPRINT.md`).

## Step 1: Ask who they are — don't assume

Ask, don't skip:
1. "ชื่ออะไรเรียกยังไงดีครับ?" (name — used only for tone, not stored anywhere)
2. "สนใจลงทุนแนวไหน หรือมีหุ้น/หัวข้อที่กำลังดูอยู่ไหม?" (what they invest in / a ticker or topic they're already curious about — this becomes the example used in Step 3)
3. "เคยใช้ Obsidian มาก่อนไหม?" (prior Obsidian experience — decides how much to explain about Properties/Backlinks/Graph vs. skip straight to the workflow)

## Step 2: Confirm the environment, don't guess

1. Ask if they've already run **Open folder as vault** in Obsidian on this folder. If not, tell them to do that first (Obsidian → Open folder as vault → this repo) and wait.
2. Check for the optional Python tools (`python --version`, then `pip show pymupdf pypdf markitdown faster-whisper yt-dlp`) only if their answer in Step 1 suggests they'll ingest a PDF/filing/video soon — plain web articles don't need them. If missing, mention the `pip install` line from `README.md` "Tools ที่ต้องมีในเครื่อง" but don't block on it.

## Step 3: One real source, end to end

Using the topic/ticker from Step 1:
1. Ask for one real link (an article, filing, or video) about it — never invent one on their behalf.
2. Run it through `/ingest <url>` yourself (delegates to `agents/ingest-runner.md` per `AGENTS.md` routing) so they watch a real Raw → Source Note → Concept pass happen, not a toy example.
3. After each stage completes, point at the actual file just created (`01-Raw/...`, `02-Wiki/Sources/...`, `02-Wiki/Concepts/...` if one was warranted) and name what it is in one sentence — don't dump the full pipeline explanation, that's what `PROJECT-WORKFLOW.md` is for if they want the deep dive.

## Step 4: Show them where things live, then stop

Close with a short pointer, not a re-teach:
- `05-Index/Home.md` — where to start every future session
- `05-Index/Ingest Queue.md` — where to triage the next source
- `PROJECT-WORKFLOW.md` — the full command/agent map, if they want it
- `04-Schema/Obsidian Fundamentals.md` — frontmatter/links/Graph reference

Then stop — don't keep walking them through more sources unless they ask. The goal of `/onboarding` is one working example and a map of where to go next, not a full session.
