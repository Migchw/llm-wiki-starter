# README visual assets

| Asset | Purpose | How to update |
|---|---|---|
| [research-desk.png](research-desk.png) | Original editorial illustration of source documents, a research notebook and a magnifying glass. | Generate a replacement illustration using the prompt below. Keep headings and product claims in native Markdown. |
| `flow-*.svg` | Swimlane diagram per command: who does what at each step, what goes in and out. | Edit the specs in [`../diagrams/flows.py`](../diagrams/flows.py), then run `py docs/diagrams/build_flows.py`. Do not edit the SVGs by hand. |

## Swimlane flow diagrams

The layout follows the Data flow type of [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) (MIT): lanes are actors, columns are steps, the chip on the left of a box is its input and the chip on the right its output, and one orange handoff per diagram marks the step that matters most. Text inside the SVGs is ASCII so it renders the same through GitHub's `<img>`; the Thai explanation for each sits next to it in [the workflow guide](../workflows.md#ผัง-swimlane-ของทุกคำสั่ง).

The diagrams describe what the skills and agents instruct. They do not assert that every review step is enforced by code. Check a rendered PNG after editing: labels must not touch a line or a box.

## Illustration

The illustration is conceptual artwork, not a product screenshot or a representation of financial data. It was created with OpenAI Image Generator on 2026-09-18. It contains no project logo or external brand assets.

## Illustration prompt

```text
Use case: stylized-concept. Asset type: standalone, text-free editorial illustration for a public investment-research wiki README. Create one polished, wide landscape image, approximately 2.5:1 aspect ratio. Subject: a carefully arranged physical research workspace, with an open cream-paper research notebook as the focal object, a small stack of source documents, one charcoal archive box, and a clear magnifying glass resting across an unprinted page. Simple abstract gray typographic strokes on paper only, never readable words or numeric data. These are tangible editorial objects, not a website screenshot or diagram. Style: premium restrained 3D paper-and-matte-material editorial illustration, precise crafted edges, soft realistic directional studio shadows, quietly analytical and approachable. Composition: spacious asymmetrical horizontal still life across the middle of the canvas; let each object breathe, with clean margins around the whole scene. Palette: neutral charcoal #121212 and lifted charcoal #232323, off-white paper, small lavender #BB86FC and teal #03DAC6 bookmarks or tabs only. Large surfaces stay neutral. No neon, no glow, no gradients as structure. No humans, robots, brains, logos, company marks, stock symbols, charts, arrows, connecting lines, flow diagrams, tables, labels, headings, words, watermark or UI. The image conveys retaining source material and carefully reviewing research; it must not imply investment performance or automatic truth verification. All exact README text will remain native Markdown outside this illustration.
```
