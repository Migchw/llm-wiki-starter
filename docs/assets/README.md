# README visual assets

| Asset | Purpose | How to update |
|---|---|---|
| [research-desk.png](research-desk.png) | Original editorial illustration of source documents, a research notebook and a magnifying glass. | Generate a replacement illustration using the prompt below. Keep headings and product claims in native Markdown. |
| [research-workflow.svg](research-workflow.svg) | Readable preview of the research workflow, with native SVG text and an accessible description. | Update the editable scene and refresh this preview, preserving the filename or updating the README links. |
| [research-workflow.excalidraw](research-workflow.excalidraw) | Editable source for the workflow: shapes, text and continuous connectors. | Import into Excalidraw, edit, then save the scene and export an SVG with a background. |

The illustration is conceptual artwork, not a product screenshot or a representation of financial data. It was created with OpenAI Image Generator on 2026-09-18. It contains no project logo or external brand assets.

The workflow was authored separately as an editable Excalidraw scene. Its text, decisions and connectors are deterministic; they were not generated as part of the illustration. The SVG preview uses a Roboto / Helvetica / Arial / sans-serif font stack; the editable scene uses Excalidraw's native sans-serif font for portability. No font files or external scripts are required to display the preview.

[Open the initial scene in Excalidraw](https://excalidraw.com/#json=DnhuJkqM6YF_7cglT4gGo,F_F2qdu4xW-aQudwaognBw). This shared link is a snapshot; use the committed `.excalidraw` file as the source of truth for future edits and refresh the link when publishing a new version.

## Workflow sources

The diagram summarizes the project configuration; it does not assert that every review step is automatically enforced by code.

- [Agent contract](../../.agents/AGENTS.md): Python capture, immutable Raw, linked Source Notes, Entities and selective Concepts.
- [Research skill](../../.claude/skills/research/SKILL.md): evidence required before the thesis phase.
- [Leopold](../../.claude/agents/leopold.md): drafting and handoff for review.
- [Feynman](../../.claude/agents/feynman.md) and [Reviewer](../../.claude/agents/reviewer.md): numerical and reasoning checks.

When editing, keep Source Notes visible as direct inputs to evidence review, show Concept extraction as selective, and keep the final output labeled **Draft Thesis**. If evidence is insufficient, research stays pending. A draft still needs review before it is marked `reviewed`.

## Illustration prompt

```text
Use case: stylized-concept. Asset type: standalone, text-free editorial illustration for a public investment-research wiki README. Create one polished, wide landscape image, approximately 2.5:1 aspect ratio. Subject: a carefully arranged physical research workspace, with an open cream-paper research notebook as the focal object, a small stack of source documents, one charcoal archive box, and a clear magnifying glass resting across an unprinted page. Simple abstract gray typographic strokes on paper only, never readable words or numeric data. These are tangible editorial objects, not a website screenshot or diagram. Style: premium restrained 3D paper-and-matte-material editorial illustration, precise crafted edges, soft realistic directional studio shadows, quietly analytical and approachable. Composition: spacious asymmetrical horizontal still life across the middle of the canvas; let each object breathe, with clean margins around the whole scene. Palette: neutral charcoal #121212 and lifted charcoal #232323, off-white paper, small lavender #BB86FC and teal #03DAC6 bookmarks or tabs only. Large surfaces stay neutral. No neon, no glow, no gradients as structure. No humans, robots, brains, logos, company marks, stock symbols, charts, arrows, connecting lines, flow diagrams, tables, labels, headings, words, watermark or UI. The image conveys retaining source material and carefully reviewing research; it must not imply investment performance or automatic truth verification. All exact README text will remain native Markdown outside this illustration.
```
