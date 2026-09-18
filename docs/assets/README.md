# README visual assets

| Asset | Purpose | How to update |
|---|---|---|
| [research-desk.png](research-desk.png) | Original editorial illustration of source documents, a research notebook and a magnifying glass. | Generate a replacement illustration using the prompt below. Keep headings and product claims in native Markdown. |
| [research-workflow.svg](research-workflow.svg) | Readable preview of the research workflow, with native SVG text and an accessible description. | Update the editable scene and refresh this preview, preserving the filename or updating the README links. |
| [research-workflow.excalidraw](research-workflow.excalidraw) | Editable source for the workflow: shapes, text and continuous connectors. | Import into Excalidraw, edit, then save the scene and export an SVG with a background. |

## Detailed workflow diagrams

The six diagrams below adapt contributor-supplied reference screenshots into editable scenes. Labels and routes were checked against the current project configuration. All diagram shapes, text, decisions and connectors were authored in Excalidraw; no new image-generation call, screenshot reconstruction or external brand asset was used for this set.

| Diagram | SVG preview | Editable source |
|---|---|---|
| Research ingestion and knowledge linking | [knowledge-pipeline.svg](knowledge-pipeline.svg) | [knowledge-pipeline.excalidraw](knowledge-pipeline.excalidraw) · [Web](https://excalidraw.com/#json=US6OQb8Fe0G_MGmp2onBj,CMaM0MsZq2mEz2WmafoI5A) |
| Five conceptual layers | [knowledge-layers.svg](knowledge-layers.svg) | [knowledge-layers.excalidraw](knowledge-layers.excalidraw) · [Web](https://excalidraw.com/#json=A8mLQwk3lKUJI0uxMD6G7,DMig4MYEdB_vH66A7dAbAQ) |
| Munger and eight specialists | [agent-roster.svg](agent-roster.svg) | [agent-roster.excalidraw](agent-roster.excalidraw) · [Web](https://excalidraw.com/#json=cyL90oMJ9osNjo-AEbyS5,m_GgSSLKsNSl0MlURql6HQ) |
| Direct and delegated ingestion | [ingest-flow.svg](ingest-flow.svg) | [ingest-flow.excalidraw](ingest-flow.excalidraw) · [Web](https://excalidraw.com/#json=O5AON2gNsEI_tjyHfXcGf,WmYuuBqr_Z0Tr_tx0IHJJw) |
| Research discovery, ingestion and thesis review | [research-flow.svg](research-flow.svg) | [research-flow.excalidraw](research-flow.excalidraw) · [Web](https://excalidraw.com/#json=xzRAKUJj2aU9DryeaChcj,T0KB10_xNOEOR2D_haasUQ) |
| Health-check reporting and approved fixes | [health-check-flow.svg](health-check-flow.svg) | [health-check-flow.excalidraw](health-check-flow.excalidraw) · [Web](https://excalidraw.com/#json=WsDv0jTkk6AKPyIdhavqp,-zz-e4g_Pk5IffIHXnIWtw) |

[The workflow guide](../workflows.md) includes a Thai text equivalent and repository source links for every diagram. Use the committed scenes for future edits and export an SVG with its background; verify label fit and arrow direction after exporting. Keep SVG alt text, native explanations and any shared web snapshots in sync with the scene.

The reference wording was corrected where necessary: Munger coordinates eight specialist definitions, standard ingestion can run directly, Concept extraction is selective, and transcript availability is not automatic speech-to-text. The health-check command ends at a report; applying approved changes is a separate request. The three research groups describe functions without introducing a new command or formal phase contract.

## Illustration and typography

The illustration is conceptual artwork, not a product screenshot or a representation of financial data. It was created with OpenAI Image Generator on 2026-09-18. It contains no project logo or external brand assets.

The workflow was authored separately as an editable Excalidraw scene. Its text, decisions and connectors are deterministic; they were not generated as part of the illustration. The SVG preview uses a Roboto / Helvetica / Arial / sans-serif font stack; the editable scene uses Excalidraw's native sans-serif font for portability. No font files or external scripts are required to display the preview.

[Open the initial scene in Excalidraw](https://excalidraw.com/#json=DnhuJkqM6YF_7cglT4gGo,F_F2qdu4xW-aQudwaognBw). This shared link is a snapshot; use the committed `.excalidraw` file as the source of truth for future edits and refresh the link when publishing a new version.

## Workflow sources

The diagram summarizes the project configuration; it does not assert that every review step is automatically enforced by code.

- [Agent contract](../../.agents/AGENTS.md): Python capture, immutable Raw, linked Source Notes, Entities and selective Concepts.
- [Research skill](../../.claude/skills/research/SKILL.md): evidence required before the thesis phase.
- [Ingest skill](../../.claude/skills/ingest/SKILL.md): direct capture, Source Note, linked knowledge, Queue and Log.
- [Wiki health-check skill](../../.claude/skills/wiki-health-check/SKILL.md): report-only checks and separately requested approved fixes.
- [Source lifecycle](../../04-Schema/Source%20Lifecycle.md) and [Ingest Queue](../../05-Index/Ingest%20Queue.md): triage and queue statuses.
- [Leopold](../../.claude/agents/leopold.md): drafting and handoff for review.
- [Feynman](../../.claude/agents/feynman.md) and [Reviewer](../../.claude/agents/reviewer.md): numerical and reasoning checks.

When editing, keep Source Notes visible as direct inputs to evidence review, show Concept extraction as selective, and keep the final output labeled **Draft Thesis**. If evidence is insufficient, research stays pending. A draft still needs review before it is marked `reviewed`.

## Illustration prompt

```text
Use case: stylized-concept. Asset type: standalone, text-free editorial illustration for a public investment-research wiki README. Create one polished, wide landscape image, approximately 2.5:1 aspect ratio. Subject: a carefully arranged physical research workspace, with an open cream-paper research notebook as the focal object, a small stack of source documents, one charcoal archive box, and a clear magnifying glass resting across an unprinted page. Simple abstract gray typographic strokes on paper only, never readable words or numeric data. These are tangible editorial objects, not a website screenshot or diagram. Style: premium restrained 3D paper-and-matte-material editorial illustration, precise crafted edges, soft realistic directional studio shadows, quietly analytical and approachable. Composition: spacious asymmetrical horizontal still life across the middle of the canvas; let each object breathe, with clean margins around the whole scene. Palette: neutral charcoal #121212 and lifted charcoal #232323, off-white paper, small lavender #BB86FC and teal #03DAC6 bookmarks or tabs only. Large surfaces stay neutral. No neon, no glow, no gradients as structure. No humans, robots, brains, logos, company marks, stock symbols, charts, arrows, connecting lines, flow diagrams, tables, labels, headings, words, watermark or UI. The image conveys retaining source material and carefully reviewing research; it must not imply investment performance or automatic truth verification. All exact README text will remain native Markdown outside this illustration.
```
