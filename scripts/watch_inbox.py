#!/usr/bin/env python3
"""
Ingest whatever lands in 01-Raw/inbox/, unattended, and stop before commit.

Meant for Windows Task Scheduler (or cron). Each run costs nothing unless
there is work: it exits early when the inbox is empty or when the last run's
output is still uncommitted (you have not reviewed it yet).

    py scripts/watch_inbox.py            # run once
    py scripts/watch_inbox.py --dry-run  # show what it would do

Register hourly on Windows (runs only while you are logged in):
    schtasks /Create /SC HOURLY /TN "LLM Wiki inbox" /TR "py \"<vault>\\scripts\\watch_inbox.py\""
Remove:
    schtasks /Delete /TN "LLM Wiki inbox" /F

Output of every run goes to 03-Logs/Watch/. Files it could not ingest are moved
to 01-Raw/inbox/hold/ with a row in the Ingest Queue, so they are not retried.
"""

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / '01-Raw' / 'inbox'
LOGS = ROOT / '03-Logs' / 'Watch'
IGNORE = {'.gitkeep', 'README.md'}

PROMPT = """Unattended run started by scripts/watch_inbox.py. Nobody is watching, so never ask a question.

Run /ingest for every file listed below, one at a time, oldest first:
{files}

Rules for this run:
- Follow .agents/AGENTS.md, but skip `git pull`: the script already checked the tree is clean.
- After a file's Source Note, Entity and Queue/Log rows are written, `git mv` the file from 01-Raw/inbox/ to its 01-Raw/<media-type>/ folder, keeping its name.
- If a file cannot be ingested (unreadable, empty, needs a login, unclear what it is), move it to 01-Raw/inbox/hold/, add an Ingest Queue row with status `waiting` and the reason, and continue with the next file.
- Do not commit, push, edit theses, or touch .agents/, scripts/ or dashboard/.
- Finish with: files ingested, files held and why, notes created, and any claim left `pending` that looks decision-relevant."""


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True,
                          encoding='utf-8').stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    files = sorted((p for p in INBOX.iterdir() if p.is_file() and p.name not in IGNORE and not p.name.startswith('.')),
                   key=lambda p: p.stat().st_mtime) if INBOX.is_dir() else []
    if not files:
        print('inbox empty; nothing to do')
        return 0
    # New inbox files are untracked by definition; any other change is an unreviewed run.
    if git('status', '--porcelain', '--', '.', ':!01-Raw/inbox').strip():
        print(f'{len(files)} file(s) waiting, but the working tree has uncommitted changes; '
              'review and commit the last run first')
        return 0

    claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude.exe')
    prompt = PROMPT.format(files='\n'.join(f'- 01-Raw/inbox/{p.name}' for p in files))
    cmd = [claude, '-p', prompt, '--permission-mode', 'acceptEdits', '--allowedTools',
           'Bash(py:*)', 'Bash(python:*)', 'Bash(git status:*)', 'Bash(git log:*)', 'Bash(git mv:*)',
           'WebFetch', 'WebSearch']
    if args.dry_run:
        print('would run:', ' '.join(cmd[:2]), '<prompt>', ' '.join(cmd[3:]))
        print(prompt)
        return 0

    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f'{dt.datetime.now():%Y%m%d-%H%M%S}.md'
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, encoding='utf-8')
    log.write_text(f'# Inbox run {log.stem}\n\nFiles: {", ".join(p.name for p in files)}\n\n'
                   f'Exit code: {result.returncode}\n\n{result.stdout}\n{result.stderr}', encoding='utf-8')
    print(f'ran claude on {len(files)} file(s); log: {log.relative_to(ROOT).as_posix()}')
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
