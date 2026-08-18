# lint_pending/

Output queue for `wiki-health-check` runs. Each run writes one dated report here, e.g. `20260818-lint-report.md`. A report holds every finding from both lint phases with a suggested fix — nothing in it is applied automatically.

Review a report and mark each item:
- `[x]` — approved, apply this fix
- leave `[ ]` — not approved yet
- `[-]` — rejected, will not be applied (say why in a one-line note under it)

Then ask the agent to apply the approved items. Once a report has no `[ ]` items left, its summary moves to `../05-Index/Vault Health.md` and the report file is deleted from this folder.
