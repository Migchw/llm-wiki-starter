#!/usr/bin/env python3
"""
LLM Wiki Tool & Linter (Karpathy-style Vault Integrity Engine)

Audits Obsidian Markdown Vault for:
1. Broken [[Wikilinks]] (Missing target files, heading anchors)
2. Orphan Notes (0 inbound links)
3. Dead-end Notes (0 outbound links)
4. Schema & Frontmatter Validation (YAML keys per note type)
5. Investor Quality Gates (Claim table, Investor Archetypes, Verification status)
6. Vault Health & Knowledge Graph Scorecard

Usage:
    python scripts/wiki_tool.py --lint
    python scripts/wiki_tool.py --stats
"""

import os
import sys
import re
import yaml
import json
import argparse
from pathlib import Path
from collections import defaultdict

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Root path of the vault
VAULT_ROOT = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name in ['scripts', '.agents'] else Path(__file__).resolve().parent

# Required Frontmatter Fields by Note Type
SCHEMA_REQUIREMENTS = {
    'raw': ['title', 'type', 'source_type', 'url', 'status'],
    'source-note': ['title', 'type', 'status', 'created', 'sources', 'confidence', 'verification'],
    'concept': ['title', 'type', 'status', 'created', 'sources', 'confidence', 'verification', 'archetype'],
    'entity': ['title', 'type', 'entity_type', 'status', 'created'],
    'thesis': ['title', 'type', 'status', 'created', 'confidence', 'verification'],
    'index': ['type', 'status']
}

VALID_ARCHETYPES = [
    'capital-cycle',
    'moat-unit-economics',
    'structural-shift',
    'valuation-trap'
]

# Patterns that are illustrative/examples in docs and should not be treated as broken links
IGNORED_LINK_PATTERNS = {
    'wikilink', 'wikilinks', 'raw-file-name', 'links', 'ชื่อโน้ต', 'ชื่อโน้ต#หัวข้อ',
    'source-20260813-company-call', 'source-20260813-company-a-earnings-call',
    'Operating leverage', 'Industry price war', 'Company A', 'thesis-company-a',
    'source-x', '02-Wiki/Sources/', '02-Wiki/Concepts/...', '02-Wiki/Entities/...'
}

class VaultLinter:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.md_files = {}           # rel_path -> full Path
        self.file_titles = {}        # stem / name / title -> rel_path
        self.frontmatters = {}       # rel_path -> dict
        self.outbound_links = defaultdict(set)  # rel_path -> set of (target, line_no)
        self.inbound_links = defaultdict(set)   # rel_path -> set of source rel_paths
        self.broken_links = defaultdict(list)   # rel_path -> list of (link_text, line_no)
        self.schema_errors = defaultdict(list)  # rel_path -> list of error strings
        self.quality_warnings = defaultdict(list)# rel_path -> list of warning strings
        self.stats = {
            'total_notes': 0,
            'by_type': defaultdict(int),
            'verified_count': 0,
            'pending_count': 0,
            'broken_links_count': 0
        }

    def scan(self):
        """Discovers all markdown files and parses metadata + wikilinks."""
        # 1. Collect all MD files
        for p in self.root_dir.rglob('*.md'):
            parts = p.relative_to(self.root_dir).parts
            if any(part.startswith('.') and part not in ['.agents'] for part in parts):
                continue
            if 'node_modules' in parts or '.venv' in parts or '__pycache__' in parts:
                continue

            rel_str = str(p.relative_to(self.root_dir)).replace('\\', '/')
            self.md_files[rel_str] = p
            
            # Map identifiers to relative path
            self.file_titles[p.stem] = rel_str
            self.file_titles[rel_str] = rel_str
            if rel_str.endswith('.md'):
                self.file_titles[rel_str[:-3]] = rel_str

        self.stats['total_notes'] = len(self.md_files)

        # 2. Parse Frontmatter and Wikilinks in each file
        for rel_path, file_path in self.md_files.items():
            self._parse_file(rel_path, file_path)

        # 3. Resolve Outbound / Inbound Graph & Find Broken Links
        self._resolve_graph()

    def _parse_file(self, rel_path, file_path):
        is_template = '04-Schema/Templates/' in rel_path
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            self.schema_errors[rel_path].append(f"Cannot read file: {e}")
            return

        # Check YAML Frontmatter
        fm = {}
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                except Exception as e:
                    self.schema_errors[rel_path].append(f"Invalid YAML frontmatter: {e}")
                body = parts[2]

        self.frontmatters[rel_path] = fm
        note_type = fm.get('type', 'untyped')
        self.stats['by_type'][note_type] += 1

        if fm.get('verification') == 'verified':
            self.stats['verified_count'] += 1
        elif fm.get('verification') == 'pending':
            self.stats['pending_count'] += 1

        # Skip schema validation for templates
        if not is_template:
            self._validate_schema(rel_path, fm, body, note_type)

        # Extract Wikilinks (ignoring code spans `...`)
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            # Remove inline code blocks `...` to avoid extracting illustrative examples
            clean_line = re.sub(r'`[^`]*`', '', line)
            matches = re.findall(r'\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]', clean_line)
            for m in matches:
                target_raw = m.strip()
                self.outbound_links[rel_path].add((target_raw, idx))

    def _check_section(self, rel_path, body, variants, label):
        """Warns if none of the header variants are present, or the matched one has no content before the next '## ' header."""
        for header in variants:
            idx = body.find(header)
            if idx == -1:
                continue
            rest = body[idx + len(header):]
            next_header = rest.find('\n## ')
            content = rest if next_header == -1 else rest[:next_header]
            if not content.strip():
                self.quality_warnings[rel_path].append(f"Empty '{header}' section (header present, no content)")
            return
        self.quality_warnings[rel_path].append(f"Missing '{label}' section")

    def _validate_schema(self, rel_path, fm, body, note_type):
        if note_type in SCHEMA_REQUIREMENTS:
            required_keys = SCHEMA_REQUIREMENTS[note_type]
            for k in required_keys:
                if k not in fm or fm[k] is None or fm[k] == "":
                    self.schema_errors[rel_path].append(f"Missing required frontmatter key: '{k}' (type: {note_type})")

        # Concept Note Validations
        if note_type == 'concept':
            archetype = fm.get('archetype')
            if archetype and archetype not in VALID_ARCHETYPES:
                self.schema_errors[rel_path].append(f"Invalid archetype '{archetype}'. Must be one of: {VALID_ARCHETYPES}")

            # Check investor-centric sections (presence + non-empty)
            self._check_section(rel_path, body, ['## Investor Implication', '## Investor implication'], '## Investor Implication')
            self._check_section(rel_path, body, ['## Value Chain & Second-Order Effects', '## Value Chain'], '## Value Chain & Second-Order Effects')
            self._check_section(rel_path, body, ['## Boundaries & Falsification Criteria', '## Boundaries', '## When it applies'], '## Boundaries / Falsification Criteria')

        elif note_type == 'source-note':
            self._check_section(rel_path, body, ['## 60-Second Brief', '## 60-second brief'], '## 60-second brief')
            self._check_section(rel_path, body, ['## Claim Table', '## Claim table'], '## Claim table')
            if 'sources' in fm and (not fm['sources'] or len(fm['sources']) == 0):
                self.quality_warnings[rel_path].append("Source note has empty 'sources' list (must link to 01-Raw)")

    def _resolve_graph(self):
        resolved_outbound = defaultdict(set)

        for src, raw_targets in self.outbound_links.items():
            is_template = '04-Schema/Templates/' in src or src.startswith('COURSE-PRESENTATION')
            
            for target_str, line_no in raw_targets:
                # Ignore heading internal links e.g. [[#การเริ่มใช้ทีละระยะ]]
                if target_str.startswith('#'):
                    continue
                
                # Ignore illustrative doc examples
                if target_str in IGNORED_LINK_PATTERNS or is_template:
                    continue

                # Strip subheadings if any e.g. [[Note#Heading]]
                base_target = target_str.split('#')[0].strip()
                if not base_target:
                    continue

                clean_target = base_target.replace('\\', '/').strip()
                resolved_rel = None

                if clean_target in self.file_titles:
                    resolved_rel = self.file_titles[clean_target]
                elif f"{clean_target}.md" in self.file_titles:
                    resolved_rel = self.file_titles[f"{clean_target}.md"]
                elif Path(clean_target).stem in self.file_titles:
                    resolved_rel = self.file_titles[Path(clean_target).stem]

                if resolved_rel:
                    resolved_outbound[src].add(resolved_rel)
                    self.inbound_links[resolved_rel].add(src)
                else:
                    self.broken_links[src].append((target_str, line_no))
                    self.stats['broken_links_count'] += 1

        self.outbound_links = resolved_outbound

    def run_lint(self):
        """Prints detailed lint audit report."""
        self.scan()

        print("=" * 70)
        print("🧠 LLM WIKI LINTER & INTEGRITY AUDITOR (Karpathy Standard)")
        print(f"📁 Vault Root: {self.root_dir}")
        print(f"📊 Total Notes Scanned: {self.stats['total_notes']}")
        print("=" * 70)

        # 1. Broken Links Report
        print("\n🔗 1. WIKILINK INTEGRITY AUDIT")
        if not self.broken_links:
            print("  ✅ All [[Wikilinks]] resolve perfectly! (0 broken links)")
        else:
            print(f"  ❌ Found {self.stats['broken_links_count']} broken wikilink(s):")
            for file, links in self.broken_links.items():
                print(f"     📄 {file}:")
                for link_name, line_no in links:
                    print(f"        Line {line_no}: [[{link_name}]] -> Target does not exist")

        # 2. Schema & Frontmatter Validation Report
        print("\n📐 2. SCHEMA & FRONTMATTER VALIDATION")
        if not self.schema_errors:
            print("  ✅ All YAML frontmatter blocks comply with schema contracts!")
        else:
            print(f"  ❌ Found schema errors in {len(self.schema_errors)} file(s):")
            for file, errs in self.schema_errors.items():
                print(f"     📄 {file}:")
                for err in errs:
                    print(f"        - {err}")

        # 3. Quality Gate & Investor Warnings
        print("\n🚦 3. QUALITY GATE & INVESTOR VALUE CHECK")
        if not self.quality_warnings:
            print("  ✅ All notes satisfy Investor Quality Gates!")
        else:
            print(f"  ⚠️ Found {len(self.quality_warnings)} note(s) with quality warnings:")
            for file, warns in self.quality_warnings.items():
                print(f"     📄 {file}:")
                for w in warns:
                    print(f"        - {w}")

        # 4. Graph Topology: Orphans & Dead-ends
        print("\n🕸️ 4. GRAPH TOPOLOGY (Orphans & Dead-Ends)")
        ignore_orphan_prefixes = ('00-Start-Here', '04-Schema', '05-Index', '03-Logs', 'README', 'ONBOARDING', 'AGENTS', 'COURSE-PRESENTATION', 'PROJECT-BLUEPRINT', '.agents', 'lint_pending')
        
        orphans = [
            f for f in self.md_files.keys() 
            if len(self.inbound_links[f]) == 0 and not any(f.startswith(pfx) for pfx in ignore_orphan_prefixes)
        ]
        dead_ends = [
            f for f in self.md_files.keys() 
            if len(self.outbound_links[f]) == 0 and not f.startswith('01-Raw') and not any(f.startswith(pfx) for pfx in ignore_orphan_prefixes)
        ]

        if not orphans:
            print("  ✅ No orphan notes found (All knowledge notes have inbound connections).")
        else:
            print(f"  ℹ️ Found {len(orphans)} orphan note(s) (0 inbound links):")
            for o in orphans:
                print(f"     - {o}")

        if not dead_ends:
            print("  ✅ No dead-end notes found (All wiki notes link outwards).")
        else:
            print(f"  ℹ️ Found {len(dead_ends)} dead-end note(s) (0 outbound links):")
            for d in dead_ends:
                print(f"     - {d}")

        # 5. Overall Health Scorecard
        total_issues = len(self.broken_links) + len(self.schema_errors)
        print("\n" + "=" * 70)
        print("📈 VAULT SCORECARD & HEALTH SUMMARY")
        print("=" * 70)
        print(f"  • Total Markdown Notes:   {self.stats['total_notes']}")
        print(f"  • Notes by Type:")
        for t, cnt in sorted(self.stats['by_type'].items()):
            print(f"      - {t:15s}: {cnt}")
        print(f"  • Verification Status:")
        print(f"      - Verified Claims : {self.stats['verified_count']}")
        print(f"      - Pending Audits  : {self.stats['pending_count']}")
        
        if total_issues == 0:
            print("\n  🌟 VAULT HEALTH: 100% HEALTHY (Production Ready)")
            return 0
        else:
            print(f"\n  ⚠️ VAULT HEALTH: {total_issues} critical issue(s) require resolution.")
            return 1

    def run_stats(self):
        """Displays network and connection statistics."""
        self.scan()
        print("=" * 70)
        print("📊 KNOWLEDGE GRAPH STATISTICS")
        print("=" * 70)
        print(f"Total Notes: {len(self.md_files)}")
        
        conn_scores = []
        for f in self.md_files:
            in_c = len(self.inbound_links[f])
            out_c = len(self.outbound_links[f])
            conn_scores.append((in_c + out_c, in_c, out_c, f))
            
        conn_scores.sort(reverse=True)
        print("\n🔝 Top 10 Most Connected Knowledge Hubs:")
        for total, in_c, out_c, f in conn_scores[:10]:
            print(f"  [{total:2d} links | {in_c:2d} in, {out_c:2d} out] -> {f}")

def main():
    parser = argparse.ArgumentParser(description="LLM Wiki Integrity Linter & Graph Tool")
    parser.add_argument("--lint", action="store_true", help="Run full vault integrity lint check")
    parser.add_argument("--stats", action="store_true", help="Display knowledge graph statistics")
    parser.add_argument("--path", type=str, default=str(VAULT_ROOT), help="Path to vault root")
    
    args = parser.parse_args()
    linter = VaultLinter(args.path)
    
    if args.stats:
        linter.run_stats()
    else:
        sys.exit(linter.run_lint())

if __name__ == '__main__':
    main()
