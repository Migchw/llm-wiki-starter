#!/usr/bin/env python3
"""Deterministic pass for /delta-report.

Finds Source Notes created or updated inside a date window, maps them to the
theses and entities they touch, and extracts each thesis's kill conditions
(frontmatter `kill_conditions` + bullets under "## What Would Change My Mind").

It does not judge anything. The agent reads its output, then reads the
actual notes and decides strengthen / weaken / kill.

Usage:
  py .agents/skills/delta-report/scripts/delta_scan.py                # last 7 days
  py .agents/skills/delta-report/scripts/delta_scan.py --since 2026-08-01
  py .agents/skills/delta-report/scripts/delta_scan.py --json
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def find_vault(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "02-Wiki").is_dir() and (p / "01-Raw").is_dir():
            return p
    sys.exit("Could not find the vault root (a folder containing 02-Wiki and 01-Raw).")


def read_note(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = {}
    m = FRONTMATTER.match(text)
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            fm = {}
        body = text[m.end():]
    else:
        body = text
    return fm, body


def to_date(value):
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def stem(link: str) -> str:
    return Path(link.strip()).stem if link else ""


def links_in(value) -> set:
    """Collect wikilink stems from a frontmatter value (str or list) or body text."""
    out = set()
    items = value if isinstance(value, list) else [value]
    for item in items:
        if isinstance(item, str):
            for target in WIKILINK.findall(item):
                s = stem(target)
                if s:
                    out.add(s)
    return out


def section(body: str, heading: str) -> str:
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body, re.S | re.M)
    return m.group(1) if m else ""


def bullets(text: str) -> list:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    items = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ")) and len(line) > 2:
            items.append(line[2:].strip())
    return items


def main():
    ap = argparse.ArgumentParser(description="Map new Source Notes to theses/entities for /delta-report")
    ap.add_argument("--vault", type=str, default=None, help="Vault root (auto-detected if omitted)")
    ap.add_argument("--since", type=str, default=None, help="Start date YYYY-MM-DD (default: 7 days ago)")
    ap.add_argument("--until", type=str, default=None, help="End date YYYY-MM-DD (default: today)")
    ap.add_argument("--review-horizon", type=int, default=14, help="Flag theses whose review_date falls within N days")
    ap.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = ap.parse_args()

    vault = Path(args.vault).resolve() if args.vault else find_vault(Path(__file__).resolve())
    until = dt.date.fromisoformat(args.until) if args.until else dt.date.today()
    since = dt.date.fromisoformat(args.since) if args.since else until - dt.timedelta(days=7)

    wiki = vault / "02-Wiki"
    notes = {}
    for path in wiki.rglob("*.md"):
        if path.name == "README.md":
            continue
        fm, body = read_note(path)
        notes[path.stem] = {"path": path.relative_to(vault).as_posix(), "fm": fm, "body": body}

    # Entities: name + aliases (title, ticker, aliases)
    entities = {}
    for name, n in notes.items():
        if n["fm"].get("type") != "entity":
            continue
        aliases = {name}
        for key in ("title", "ticker"):
            v = n["fm"].get(key)
            if isinstance(v, str) and v.strip():
                aliases.add(v.strip())
        extra = n["fm"].get("aliases") or []
        if isinstance(extra, str):
            extra = [extra]
        aliases.update(a for a in extra if isinstance(a, str) and a.strip())
        entities[name] = {
            "path": n["path"],
            "entity_type": str(n["fm"].get("entity_type", "")).strip().lower(),
            "aliases": sorted(aliases),
            "listed_sources": links_in(n["fm"].get("sources")),
        }

    # Theses
    theses = []
    for name, n in notes.items():
        fm = n["fm"]
        if fm.get("type") != "thesis":
            continue
        kills = []
        fm_kills = fm.get("kill_conditions") or []
        if isinstance(fm_kills, str):
            fm_kills = [fm_kills]
        kills += [k for k in fm_kills if isinstance(k, str) and k.strip()]
        kills += bullets(section(n["body"], "What Would Change My Mind"))
        review = to_date(fm.get("review_date"))
        theses.append({
            "name": name,
            "path": n["path"],
            "title": fm.get("title", name),
            "entities": sorted(links_in(fm.get("entity"))),
            "concepts": sorted(links_in(fm.get("concepts"))),
            "cited_sources": sorted(links_in(fm.get("sources")) | links_in(section(n["body"], "Sources"))),
            "kill_conditions": kills,
            "review_date": review.isoformat() if review else None,
            "review_due": bool(review and review <= until + dt.timedelta(days=args.review_horizon)),
            "updated": str(fm.get("updated", "")),
        })

    # New sources in window
    new_sources = []
    for name, n in notes.items():
        fm = n["fm"]
        if fm.get("type") != "source-note":
            continue
        created, updated = to_date(fm.get("created")), to_date(fm.get("updated"))
        dates = [d for d in (created, updated) if d]
        if not any(since <= d <= until for d in dates):
            continue
        body_links = links_in(n["body"]) | links_in(fm.get("sources"))
        touched = set()
        for ename, e in entities.items():
            if ename in body_links or name in e["listed_sources"]:
                touched.add(ename)
                continue
            for alias in e["aliases"]:
                if len(alias) >= 3 and re.search(rf"(?<![\w]){re.escape(alias)}(?![\w])", n["body"]):
                    touched.add(ename)
                    break
        new_sources.append({
            "name": name,
            "path": n["path"],
            "title": fm.get("title", name),
            "created": created.isoformat() if created else None,
            "updated": updated.isoformat() if updated else None,
            "verification": fm.get("verification"),
            "confidence": fm.get("confidence"),
            "entities": sorted(touched),
            "concept_links": sorted(body_links & {k for k, v in notes.items() if v["fm"].get("type") == "concept"}),
        })
    new_sources.sort(key=lambda s: (s["created"] or "", s["name"]))

    # Map sources -> theses
    for t in theses:
        hits = []
        for s in new_sources:
            if set(s["entities"]) & set(t["entities"]) or set(s["concept_links"]) & set(t["concepts"]):
                hits.append({"source": s["name"], "path": s["path"], "already_cited": s["name"] in t["cited_sources"]})
        t["new_evidence"] = hits

    thesis_entities = {e for t in theses for e in t["entities"]}
    # Only companies are candidates for a thesis; people, publishers and
    # institutions are context, so they are counted but not listed.
    entity_only, other_entities = {}, set()
    for s in new_sources:
        for e in s["entities"]:
            if e in thesis_entities:
                continue
            if entities[e]["entity_type"] == "company":
                entity_only.setdefault(e, []).append(s["name"])
            else:
                other_entities.add(e)
    unmapped = [s["name"] for s in new_sources if not s["entities"] and not s["concept_links"]]

    result = {
        "vault": str(vault), "since": since.isoformat(), "until": until.isoformat(),
        "new_sources": new_sources, "theses": theses,
        "entities_without_thesis": [
            {"entity": e, "path": entities[e]["path"], "new_sources": v} for e, v in sorted(entity_only.items())
        ],
        "unmapped_sources": unmapped,
        "non_company_entities_touched": sorted(other_entities),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"# Delta scan {since} → {until}\n")
    print(f"New or updated Source Notes in window: {len(new_sources)}\n")
    for s in new_sources:
        ents = ", ".join(s["entities"]) or "-"
        print(f"- `{s['path']}` created {s['created']} · verification {s['verification']} · entities: {ents}")
    print("\n## Theses\n")
    if not theses:
        print("No thesis notes found in 02-Wiki/Theses/.")
    for t in theses:
        flag = " · REVIEW DUE" if t["review_due"] else ""
        print(f"### {t['title']}\n`{t['path']}` · entities: {', '.join(t['entities']) or '-'} · review_date {t['review_date']}{flag}\n")
        print("Kill conditions:" if t["kill_conditions"] else "Kill conditions: NONE WRITTEN (flag this in the report)")
        for k in t["kill_conditions"]:
            print(f"  - {k}")
        if t["new_evidence"]:
            print("New evidence to judge:")
            for h in t["new_evidence"]:
                note = " (already cited)" if h["already_cited"] else ""
                print(f"  - `{h['path']}`{note}")
        else:
            print("New evidence to judge: none in window")
        print()
    print("## Companies with new sources but no thesis\n")
    for e in result["entities_without_thesis"]:
        print(f"- {e['entity']} (`{e['path']}`): {', '.join(e['new_sources'])}")
    if not result["entities_without_thesis"]:
        print("- none")
    if other_entities:
        print(f"\nNon-company entities also touched (context only): {', '.join(sorted(other_entities))}")
    if unmapped:
        print("\n## Sources not linked to any entity or thesis concept\n")
        for u in unmapped:
            print(f"- {u}")


if __name__ == "__main__":
    main()
