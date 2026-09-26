#!/usr/bin/env python3
"""
Build the public template from this private vault, for review before pushing.

Starts from the public template's branch (upstream/master), which already holds
the empty 01-Raw/02-Wiki/03-Logs/05-Index scaffolding, then copies the
framework paths from the current branch over it. Research content never leaves.

    py scripts/export_template.py                  # -> branch template-export in ../llm-wiki-template-export
    py scripts/export_template.py --base upstream/master --out ../somewhere

Nothing is pushed. Review the worktree, then push the branch yourself.
Exits 1 if a leak check hits (private repo name or an Entity name from this vault).
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent

# Framework: copied from the private branch.
FRAMEWORK = ['.agents', '.claude', 'scripts', '04-Schema', 'dashboard', 'docs',
             'AGENTS.md', 'README.md', 'PROJECT-BLUEPRINT.md', 'PROJECT-WORKFLOW.md',
             'Concepts.base', '05-Index/Home.md', '.gitignore', 'tests']

# Removed after the copy: personal files, and a skill without a license.
EXCLUDE = ['.agents/skills/scrutinize', '.claude/skills/scrutinize',
           'dashboard/HANDOFF.md']

# Lines dropped from exported files because they point at an EXCLUDE path.
STRIP_LINES = {'.agents/AGENTS.md': 'skills/scrutinize/'}

# Personal data replaced with an empty starting point.
RESET = {'dashboard/config/watchlist.json': '{\n  "stocks": []\n}\n',
         'dashboard/data/consensus-history.json': '{}\n'}


def git(*args, cwd=ROOT):
    return subprocess.run(['git', *args], cwd=cwd, check=True, text=True,
                          capture_output=True, encoding='utf-8').stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', default='upstream/master')
    ap.add_argument('--branch', default='template-export')
    ap.add_argument('--out', default=str(ROOT.parent / 'llm-wiki-template-export'))
    args = ap.parse_args()

    out = Path(args.out).resolve()
    source = git('rev-parse', '--abbrev-ref', 'HEAD').strip()
    if out.exists():
        sys.exit(f'{out} already exists; remove it with `git worktree remove {out}` first')

    git('worktree', 'add', '-B', args.branch, str(out), args.base)
    present = [p for p in FRAMEWORK if git('ls-tree', '--name-only', source, '--', p).strip()]
    # Replace (not overlay) so files deleted on the private side are gone too.
    git('rm', '-r', '-q', '--ignore-unmatch', '--', *present, cwd=out)
    git('checkout', source, '--', *present, cwd=out)

    for p in EXCLUDE:
        if (out / p).exists():
            git('rm', '-r', '-q', '-f', '--', p, cwd=out)
    for p, marker in STRIP_LINES.items():
        f = out / p
        kept = [l for l in f.read_text(encoding='utf-8').splitlines(keepends=True) if marker not in l]
        f.write_text(''.join(kept), encoding='utf-8')
        git('add', '--', p, cwd=out)
    for p, text in RESET.items():
        (out / p).write_text(text, encoding='utf-8')
        git('add', '--', p, cwd=out)

    private_repo = git('remote', 'get-url', 'origin').strip().rstrip('/').removesuffix('.git').rsplit('/', 1)[-1]
    entities = [p.stem for p in (ROOT / '02-Wiki' / 'Entities').glob('*.md') if p.stem != 'README']
    needles = [n.lower() for n in [private_repo, *entities]]
    hits = []
    for rel in git('ls-files', cwd=out).splitlines():
        try:                                            # every tracked text file; skip binaries
            text = (out / rel).read_text(encoding='utf-8')
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for n, line in enumerate(text.lower().splitlines(), 1):
            hits += [f'{rel}:{n}: {needle}' for needle in needles if needle in line]

    print(f'Worktree: {out}  (branch {args.branch} from {args.base}, framework from {source})')
    print(git('status', '--short', cwd=out) or 'no changes vs base')
    if hits:
        print(f'Leak check: {len(hits)} hit(s) — fix in the worktree before pushing:')
        print('\n'.join(f'  {h}' for h in hits))
        return 1
    print('Leak check: clean. Review, commit, then push the branch yourself.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
