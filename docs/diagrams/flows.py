"""
Workflow specs for build_flows.py. One entry per diagram in docs/assets/flow-<name>.svg.

Draw what runs today. A node with cut=True still runs, but duplicates another step and is proposed
for removal or a move; it renders dashed.

Layout limits (diagram-design): <= 4 lanes, <= 6 steps, <= 9 nodes, one focal
step/node/arrow. A cross-lane arrow runs right along the source lane, then
turns once, so the cells it crosses must be empty.
"""

# code: (legend label, colour)
CHIPS = {
    'WB': ('web / file', '#7c8f6f'),
    'RW': ('raw capture', '#5e7a9b'),
    'SN': ('source note', '#b8915a'),
    'KN': ('entity / concept', '#7a8c47'),
    'TH': ('thesis', '#9c6b50'),
    'JS': ('json data', '#5a7d9a'),
    'RP': ('report', '#6b6f80'),
    'FW': ('framework files', '#8a7a9b'),
}

FLOWS = {
    'overview': dict(
        title='LLM Wiki: evidence to thesis to dashboard',
        desc='Python captures raw evidence, Munger writes the Source Note, specialist agents check facts and '
             'draft the thesis, skill scripts watch for changes, and the reader uses Obsidian and the dashboard.',
        lanes=[('Python\nscripts', 'PY'), ('Munger\nmain session', 'MGR'), ('Specialist\nagents', 'SUB'),
               ('You\nreading', 'YOU')],
        steps=['capture', 'distill', 'verify', 'synthesize', 'monitor', 'read'],
        focal_step=1,
        nodes={
            'cap': dict(lane='Python\nscripts', step=0, title='Raw Capture', sub='URL · PDF · video',
                        tool='fetch_source.py', chips=('WB', 'RW')),
            'sn': dict(lane='Munger\nmain session', step=1, title='Source Note', sub='claims · entity · concept',
                       tool='/ingest', chips=('RW', 'SN'), focal=True),
            'gate': dict(lane='Specialist\nagents', step=2, title='Fact & Logic Gate', sub='numbers · bear case',
                         tool='feynman · reviewer', chips=('SN', 'SN')),
            'th': dict(lane='Specialist\nagents', step=3, title='Draft Thesis', sub='base · bear · kill',
                       tool='leopold', chips=('KN', 'TH')),
            'watch': dict(lane='Python\nscripts', step=4, title='Watch Signals', sub='delta · anomaly · EPS',
                          tool='skill scripts', chips=('TH', 'RP')),
            'read': dict(lane='You\nreading', step=5, title='Read & Explore', sub='graph · search · chart',
                         tool='Obsidian · dashboard', chips=('SN', 'JS')),
        },
        arrows=[
            dict(**{'from': 'cap', 'to': 'sn'}, style='accent', label='raw evidence'),
            dict(**{'from': 'sn', 'to': 'gate'}),
            dict(**{'from': 'gate', 'to': 'th'}),
            dict(**{'from': 'th', 'to': 'watch'}),
            dict(**{'from': 'watch', 'to': 'read'}, style='link', dx=-14),
            dict(**{'from': 'sn', 'to': 'read'}, style='link', dx=14, dy=14),
        ],
    ),

    'ingest': dict(
        title='/ingest: one source, one pass',
        desc='The user picks a source, fetch_source.py writes Raw, Munger writes the Source Note, links entities '
             'and selective concepts, then updates the queue and log and runs lint.',
        lanes=[('You', 'YOU'), ('Python\nscripts', 'PY'), ('Munger\nmain session', 'MGR')],
        steps=['triage', 'capture', 'distill', 'link', 'record'],
        focal_step=2,
        nodes={
            'src': dict(lane='You', step=0, title='Pick Source', sub='URL · path · queue', tool='/ingest',
                        chips=(None, 'WB')),
            'fetch': dict(lane='Python\nscripts', step=1, title='Fetch Raw', sub='HTTP > Playwright > MD',
                          tool='fetch_source.py', chips=('WB', 'RW')),
            'sn': dict(lane='Munger\nmain session', step=2, title='Source Note', sub='brief · claims · exhibits',
                       tool='Source Note template', chips=('RW', 'SN'), focal=True),
            'link': dict(lane='Munger\nmain session', step=3, title='Entity / Concept', sub='concept if durable',
                         tool='Concept Checklist', chips=('SN', 'KN')),
            'rec': dict(lane='Munger\nmain session', step=4, title='Queue & Log', sub='Done row · 1-line log',
                        tool='Ingest Queue · Log', chips=('KN', None)),
            'lint': dict(lane='Python\nscripts', step=4, title='Lint', sub='links · schema · mirror',
                         tool='wiki_tool.py --lint', chips=(None, 'RP')),
        },
        arrows=[
            dict(**{'from': 'src', 'to': 'fetch'}),
            dict(**{'from': 'fetch', 'to': 'sn'}, style='accent', label='raw file'),
            dict(**{'from': 'sn', 'to': 'link'}),
            dict(**{'from': 'link', 'to': 'rec'}),
            dict(**{'from': 'rec', 'to': 'lint'}),
        ],
    ),

    'research': dict(
        title='/research TICKER: find, ingest, check what the thesis uses, draft',
        desc='Munger asks for user sources, Peter Lynch finds and stages filings, Munger ingests each one and '
             'Darwin extracts concepts, Feynman checks only the claims the thesis will use, Leopold drafts the '
             'thesis and Feynman plus Reviewer check the draft.',
        lanes=[('Scout', 'PL'), ('Munger\nmain session', 'MGR'), ('Gates', 'GT'), ('Writers', 'WR')],
        steps=['find', 'stage', 'ingest', 'evidence', 'draft', 'review'],
        focal_step=4,
        nodes={
            'ask': dict(lane='Munger\nmain session', step=0, title='Ask for Sources', sub='user files first',
                        tool='/research TICKER', chips=(None, 'WB')),
            'find': dict(lane='Scout', step=0, title='Find & Verify', sub='EDGAR · SET · IR', tool='peter-lynch',
                         chips=('WB', 'WB')),
            'stage': dict(lane='Scout', step=1, title='Stage Inbox', sub='P0 · P1 · P2 rows',
                          tool='01-Raw/inbox', chips=('WB', 'RW')),
            'ing': dict(lane='Munger\nmain session', step=2, title='Ingest Each', sub='claims stay pending',
                        tool='ingest-runner', chips=('RW', 'SN')),
            'dar': dict(lane='Writers', step=2, title='Concepts', sub='durable lens only', tool='darwin',
                        chips=('SN', 'KN')),
            'eg': dict(lane='Gates', step=3, title='Evidence Gate', sub='only claims thesis uses',
                       tool='feynman (read-only)', chips=('SN', 'SN')),
            'th': dict(lane='Writers', step=4, title='Draft Thesis', sub='base · bear · kill', tool='leopold',
                       chips=('KN', 'TH'), focal=True),
            'tg': dict(lane='Gates', step=5, title='Thesis Gate', sub='numbers · bear · moat',
                       tool='feynman · reviewer', chips=('TH', 'TH')),
        },
        arrows=[
            dict(**{'from': 'ask', 'to': 'find'}),
            dict(**{'from': 'find', 'to': 'stage'}),
            dict(**{'from': 'stage', 'to': 'ing'}),
            dict(**{'from': 'ing', 'to': 'dar'}),
            dict(**{'from': 'dar', 'to': 'eg'}),
            dict(**{'from': 'eg', 'to': 'th'}, style='accent', label='checked'),
            dict(**{'from': 'th', 'to': 'tg'}),
        ],
    ),

    'health-check': dict(
        title='/wiki-health-check: report first, fix on approval',
        desc='wiki_tool.py lints structure and the agent mirror, Munger adds a semantic pass and writes a '
             'report to lint_pending, the user ticks items, and only ticked items are applied in a separate request.',
        lanes=[('Python\nscripts', 'PY'), ('Munger\nmain session', 'MGR'), ('You', 'YOU')],
        steps=['lint', 'semantic', 'report', 'approve', 'apply'],
        focal_step=1,
        nodes={
            'lint': dict(lane='Python\nscripts', step=0, title='Lint', sub='links · schema · mirror',
                         tool='wiki_tool.py --lint', chips=('SN', 'RP')),
            'sem': dict(lane='Munger\nmain session', step=1, title='Semantic Pass', sub='contradiction · stale',
                        tool='reads the notes', chips=('RP', 'RP'), focal=True),
            'rep': dict(lane='Munger\nmain session', step=2, title='Write Report', sub='one fix per item',
                        tool='lint_pending/', chips=('RP', 'RP')),
            'ok': dict(lane='You', step=3, title='Tick [x] or [-]', sub='per item', tool='report file',
                       chips=('RP', 'RP')),
            'fix': dict(lane='Munger\nmain session', step=4, title='Apply [x] Only', sub='then Vault Health',
                        tool='separate request', chips=('RP', 'SN')),
        },
        arrows=[
            dict(**{'from': 'lint', 'to': 'sem'}, style='accent', label='lint output'),
            dict(**{'from': 'sem', 'to': 'rep'}),
            dict(**{'from': 'rep', 'to': 'ok'}),
            dict(**{'from': 'ok', 'to': 'fix'}),
        ],
    ),

    'delta': dict(
        title='/delta-report: does new evidence move a thesis?',
        desc='delta_scan.py lists new Source Notes in a window and maps them to theses and kill conditions, '
             'Munger judges each piece of evidence and writes a report, and the user approves thesis edits.',
        lanes=[('Python\nscripts', 'PY'), ('Munger\nmain session', 'MGR'), ('You', 'YOU')],
        steps=['window', 'map', 'judge', 'report', 'approve'],
        focal_step=2,
        nodes={
            'scan': dict(lane='Python\nscripts', step=0, title='New Notes', sub='created in window',
                         tool='delta_scan.py', chips=('SN', 'JS')),
            'map': dict(lane='Python\nscripts', step=1, title='Map to Theses', sub='kill conditions · cites',
                        tool='delta_scan.py', chips=('JS', 'JS')),
            'judge': dict(lane='Munger\nmain session', step=2, title='Judge Evidence', sub='stronger · weaker · kill',
                          tool='reads each note', chips=('JS', 'RP'), focal=True),
            'rep': dict(lane='Munger\nmain session', step=3, title='Delta Report', sub='30-sec summary · cites',
                        tool='03-Logs/Delta/', chips=('RP', 'RP')),
            'ok': dict(lane='You', step=4, title='Approve Edits', sub='checkbox per change',
                       tool='thesis untouched', chips=('RP', 'TH')),
        },
        arrows=[
            dict(**{'from': 'scan', 'to': 'map'}),
            dict(**{'from': 'map', 'to': 'judge'}, style='accent', label='candidates'),
            dict(**{'from': 'judge', 'to': 'rep'}),
            dict(**{'from': 'rep', 'to': 'ok'}, style='link'),
        ],
    ),

    'anomaly': dict(
        title='/anomaly-scan: odd moves become research tasks',
        desc='anomaly_scan.py flags price and volume outliers, Munger explains them from the vault, sector and '
             'news, diffs the language of the two newest Source Notes, writes a report and queues follow-ups.',
        lanes=[('Python\nscripts', 'PY'), ('Munger\nmain session', 'MGR'), ('You', 'YOU')],
        steps=['measure', 'explain', 'diff', 'report', 'queue', 'act'],
        focal_step=1,
        nodes={
            'meas': dict(lane='Python\nscripts', step=0, title='Measure Moves', sub='z-score · volume · 6M',
                         tool='anomaly_scan.py', chips=('JS', 'JS')),
            'exp': dict(lane='Munger\nmain session', step=1, title='Explain Flags', sub='vault · sector · news',
                        tool='TradingView · web', chips=('JS', 'RP'), focal=True),
            'diff': dict(lane='Munger\nmain session', step=2, title='Diff Language', sub='newest vs prior note',
                         tool='Source Notes', chips=('SN', 'RP')),
            'rep': dict(lane='Munger\nmain session', step=3, title='Anomaly Report', sub='numbers · language',
                        tool='03-Logs/Anomaly/', chips=('RP', 'RP')),
            'q': dict(lane='Munger\nmain session', step=4, title='Queue Tasks', sub='P1 / P2 rows',
                      tool='Ingest Queue', chips=('RP', 'WB')),
            'act': dict(lane='You', step=5, title='Pick & Ingest', sub='theses not edited', tool='/ingest',
                        chips=('WB', None)),
        },
        arrows=[
            dict(**{'from': 'meas', 'to': 'exp'}, style='accent', label='flags'),
            dict(**{'from': 'exp', 'to': 'diff'}),
            dict(**{'from': 'diff', 'to': 'rep'}),
            dict(**{'from': 'rep', 'to': 'q'}),
            dict(**{'from': 'q', 'to': 'act'}, style='link'),
        ],
    ),

    'earnings': dict(
        title='/earnings-scorecard: beat or miss, and what it means',
        desc='earnings_scorecard.py pulls consensus and prices, Munger ingests the press release, checks inputs, '
             'interprets beat or miss and guidance, writes the Source Note and entity, and the dashboard card updates.',
        lanes=[('Python\nscripts', 'PY'), ('Munger\nmain session', 'MGR'), ('Dashboard', 'UI')],
        steps=['gather', 'check', 'interpret', 'write', 'show'],
        focal_step=2,
        nodes={
            'yf': dict(lane='Python\nscripts', step=0, title='Pull Consensus', sub='EPS · revenue · price',
                       tool='earnings_scorecard.py', chips=('WB', 'JS')),
            'pr': dict(lane='Munger\nmain session', step=0, title='Press Release', sub='8-K 99.1 · SET MD&A',
                       tool='/ingest', chips=('WB', 'SN')),
            'chk': dict(lane='Munger\nmain session', step=1, title='Check Inputs', sub='period · units · GAAP',
                        tool='fill gaps · re-run', chips=('JS', 'JS')),
            'int': dict(lane='Munger\nmain session', step=2, title='Interpret', sub='beat/miss · guidance',
                        tool='interpretation.md', chips=('JS', 'RP'), focal=True),
            'wr': dict(lane='Munger\nmain session', step=3, title='Write Scorecard', sub='note · entity · log',
                       tool='no thesis edits', chips=('RP', 'SN')),
            'ui': dict(lane='Dashboard', step=4, title='Earnings Card', sub='earnings-data.json',
                       tool='npm run index', chips=('JS', None)),
        },
        arrows=[
            dict(**{'from': 'yf', 'to': 'chk'}, dx=-14),
            dict(**{'from': 'pr', 'to': 'chk'}),
            dict(**{'from': 'chk', 'to': 'int'}, style='accent'),
            dict(**{'from': 'int', 'to': 'wr'}),
            dict(**{'from': 'yf', 'to': 'ui'}, style='link', dy=10),
        ],
    ),

    'template-export': dict(
        title='/template-export: private vault to public template',
        desc='The owner commits framework changes, export_template.py copies them onto upstream/master in a '
             'worktree, resets personal data and runs a leak check, the build and tests run, and the owner '
             'approves before a pull request to the public template.',
        lanes=[('Owner', 'YOU'), ('Python\nscripts', 'PY'), ('Public\ntemplate', 'PUB')],
        steps=['commit', 'copy', 'scrub', 'verify', 'publish'],
        focal_step=2,
        nodes={
            'c': dict(lane='Owner', step=0, title='Commit Changes', sub='skills · scripts · UI',
                      tool='private main', chips=(None, 'FW')),
            'cp': dict(lane='Python\nscripts', step=1, title='Copy Framework', sub='onto upstream/master',
                       tool='export_template.py', chips=('FW', 'FW')),
            'sc': dict(lane='Python\nscripts', step=2, title='Reset & Leak Check', sub='watchlist · names',
                       tool='EXCLUDE · RESET', chips=('FW', 'FW'), focal=True),
            'v': dict(lane='Python\nscripts', step=3, title='Build & Test', sub='npm build · unittest',
                      tool='worktree', chips=('FW', 'RP')),
            'ok': dict(lane='Owner', step=4, title='Approve', sub='review the diff', tool='no auto push',
                       chips=('RP', 'FW')),
            'pub': dict(lane='Public\ntemplate', step=4, title='PR to master', sub='Use this template',
                        tool='GitHub', chips=('FW', None)),
        },
        arrows=[
            dict(**{'from': 'c', 'to': 'cp'}),
            dict(**{'from': 'cp', 'to': 'sc'}, style='accent'),
            dict(**{'from': 'sc', 'to': 'v'}),
            dict(**{'from': 'v', 'to': 'ok'}),
            dict(**{'from': 'ok', 'to': 'pub'}, style='link'),
        ],
    ),
}
