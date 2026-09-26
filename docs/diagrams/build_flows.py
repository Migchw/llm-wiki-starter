#!/usr/bin/env python3
"""
Render the workflow diagrams in docs/assets/flow-*.svg from the specs in flows.py.

Layout follows the "Data flow" type of cathrynlavery/diagram-design (MIT):
lanes = who does the work, steps = pipeline stage, chips = what goes in/out.
Edit flows.py, then run:  py docs/diagrams/build_flows.py

Text inside the SVG stays ASCII: GitHub shows SVGs through <img> with no web
fonts, so Thai would fall back to whatever the viewer has. Thai explanations
live in docs/workflows.md next to each image.
"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).parent))
from flows import CHIPS, FLOWS  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / 'assets'

PAPER, INK, MUTED, SOFT = '#f5f5f5', '#2d3142', '#4f5d75', '#7a8399'
ACCENT, LINK, CUT = '#eb6c36', '#2e5aa8', '#b85450'
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
SANS = "'Geist', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

LABEL_W, SLOT_W, RIGHT_PAD, HEADER_H, LANE_H, LEGEND_H = 140, 112, 28, 36, 80, 80
NODE_W, NODE_H = 100, 64


def cx(step):
    return LABEL_W + step * SLOT_W + SLOT_W / 2


def lane_top(k):
    return HEADER_H + k * LANE_H


def node_y(k):
    return lane_top(k) + 8


def t(x, y, s, cls, **attrs):
    # CSS sets text-anchor on every <text>, so an override has to be inline style.
    if 'text_anchor' in attrs:
        attrs['style'] = f"text-anchor:{attrs.pop('text_anchor')}"
    extra = ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<text x="{x:g}" y="{y:g}" class="{cls}"{extra}>{escape(s)}</text>'


def chip(x, y, code):
    return (f'<rect x="{x:g}" y="{y:g}" width="16" height="8" rx="3" fill="{CHIPS[code][1]}"/>'
            + t(x + 8, y + 6, code, 'chip'))


def arrow(a, lanes, nodes):
    src, dst = nodes[a['from']], nodes[a['to']]
    ks, kd = lanes.index(src['lane']), lanes.index(dst['lane'])
    js, jd = src['step'], dst['step']
    style = a.get('style', 'muted')
    if src.get('cut') or dst.get('cut'):
        style = 'dashed'
    color = {'muted': MUTED, 'dashed': MUTED, 'accent': ACCENT, 'link': LINK}[style]
    marker = {'muted': 'm', 'dashed': 'm', 'accent': 'a', 'link': 'l'}[style]
    width = 1.2 if style == 'accent' else 1
    dash = ' stroke-dasharray="4,3"' if style == 'dashed' else ''
    dx = a.get('dx', 0)
    y0 = lane_top(ks) + LANE_H / 2 + a.get('dy', 0)
    if ks == kd:                                        # same lane, left to right
        d = f'M{cx(js) + NODE_W / 2:g} {y0:g} H{cx(jd) - NODE_W / 2:g}'
        lx = (cx(js) + cx(jd)) / 2
    elif js == jd:                                      # same step, straight down/up
        x = cx(js) + dx
        if kd > ks:
            d = f'M{x:g} {node_y(ks) + NODE_H:g} V{node_y(kd):g}'
        else:
            d = f'M{x:g} {node_y(ks):g} V{node_y(kd) + NODE_H:g}'
        lx = None
    else:                                               # right, then one elbow down/up
        x = cx(jd) + dx
        sgn = 1 if kd > ks else -1
        y1 = node_y(kd) if kd > ks else node_y(kd) + NODE_H
        d = (f'M{cx(js) + NODE_W / 2:g} {y0:g} H{x - 8:g} '
             f'Q{x:g} {y0:g} {x:g} {y0 + 8 * sgn:g} V{y1:g}')
        lx = None
    out = [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#arr-{marker})"/>']
    if a.get('label'):
        w = len(a['label']) * 4.9 + 8
        if lx is not None:                              # above the horizontal run
            out.append(f'<rect x="{lx - w / 2:g}" y="{y0 - 17:g}" width="{w:g}" height="12" rx="2" fill="{PAPER}"/>')
            out.append(t(lx, y0 - 8, a['label'].upper(), 'alabel', fill=color))
        else:                                           # beside the vertical run, in open canvas
            ym = (y0 + 8 * sgn + y1) / 2
            out.append(f'<rect x="{x + 4:g}" y="{ym - 6:g}" width="{w:g}" height="12" rx="2" fill="{PAPER}"/>')
            out.append(t(x + 8, ym + 3, a['label'].upper(), 'alabel', fill=color, text_anchor='start'))
    return out


def node(n, lanes, keys):
    k = lanes.index(n['lane'])
    x, y, c = cx(n['step']) - NODE_W / 2, node_y(k), cx(n['step'])
    focal, cut = n.get('focal'), n.get('cut')
    if focal:
        box = f'fill="rgba(235,108,54,0.07)" stroke="{ACCENT}" stroke-width="1.2"'
        role_fill, role_cls = 'rgba(235,108,54,0.20)', 'role focal'
    elif cut:
        box = f'fill="{PAPER}" stroke="{CUT}" stroke-opacity="0.6" stroke-dasharray="3,2"'
        role_fill, role_cls = 'rgba(184,84,80,0.15)', 'role cut'
    else:
        box = f'fill="{PAPER}" stroke="rgba(45,49,66,0.25)"'
        role_fill, role_cls = 'rgba(45,49,66,0.12)', 'role'
    role = 'CUT?' if cut else keys[n['lane']]
    rw = 22 if cut else 18
    out = [f'<rect x="{x:g}" y="{y:g}" width="{NODE_W}" height="{NODE_H}" rx="6" {box}/>',
           f'<rect x="{x + 4:g}" y="{y + 4:g}" width="{rw}" height="10" rx="3" fill="{role_fill}"/>',
           t(x + 4 + rw / 2, y + 11.2, role, role_cls),
           t(c, y + 25, n['title'], 'title', **({'fill': SOFT} if cut else {})),
           t(c, y + 37, n.get('sub', ''), 'sub'),
           t(c, y + 49, n.get('tool', ''), 'tool')]
    chips = n.get('chips', (None, None))
    if chips[0]:
        out.append(chip(x + 4, y + 54, chips[0]))
    if chips[1]:
        out.append(chip(x + 80, y + 54, chips[1]))
    return out


def render(spec):
    lanes = [l[0] for l in spec['lanes']]
    keys = {l[0]: l[1] for l in spec['lanes']}
    steps = spec['steps']
    nodes = spec['nodes']
    W = LABEL_W + len(steps) * SLOT_W + RIGHT_PAD
    body_h = HEADER_H + len(lanes) * LANE_H
    H = body_h + LEGEND_H
    focal_step = spec.get('focal_step')

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 1.5:g}" height="{H * 1.5:g}" role="img" aria-labelledby="t d">',
         f'<title id="t">{escape(spec["title"])}</title><desc id="d">{escape(spec["desc"])}</desc>',
         f'''<style>
  text {{ font-family: {MONO}; text-anchor: middle; }}
  .num {{ fill: {INK}; font-size: 7px; font-weight: 600; }}
  .step {{ fill: {MUTED}; font-size: 7px; font-weight: 500; letter-spacing: 0.12em; }}
  .lane {{ fill: {MUTED}; font-size: 8px; font-weight: 500; letter-spacing: 0.14em; }}
  .role {{ fill: {INK}; font-size: 6px; font-weight: 600; }}
  .title {{ fill: {INK}; font: 600 9px {SANS}; }}
  .sub {{ fill: {MUTED}; font-size: 6.5px; }}
  .tool {{ fill: {SOFT}; font-size: 6.5px; }}
  .chip {{ fill: #fff; font-size: 5px; font-weight: 700; }}
  .alabel {{ font-size: 7.5px; letter-spacing: 0.06em; }}
  .focal {{ fill: {ACCENT}; }}
  .cut {{ fill: {CUT}; }}
  .lg {{ fill: {MUTED}; font-size: 7px; font-weight: 500; letter-spacing: 0.12em; text-anchor: end; }}
  .lt {{ fill: {MUTED}; font: 400 7px {SANS}; text-anchor: start; }}
</style>''',
         f'''<defs>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="11" cy="11" r="0.8" fill="rgba(45,49,66,0.10)"/></pattern>
  <marker id="arr-m" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="{MUTED}"/></marker>
  <marker id="arr-a" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="{ACCENT}"/></marker>
  <marker id="arr-l" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="{LINK}"/></marker>
</defs>''',
         f'<rect width="{W}" height="{H}" fill="{PAPER}"/><rect width="{W}" height="{H}" fill="url(#dots)"/>']

    for k in range(len(lanes)):
        if k % 2 == 0:
            s.append(f'<rect x="0" y="{lane_top(k)}" width="{W}" height="{LANE_H}" fill="rgba(45,49,66,0.018)"/>')
    for k in range(len(lanes) + 1):
        s.append(f'<line x1="0" y1="{lane_top(k)}" x2="{W}" y2="{lane_top(k)}" stroke="rgba(45,49,66,0.12)" stroke-width="0.8"/>')
    s.append(f'<line x1="{LABEL_W}" y1="{HEADER_H}" x2="{LABEL_W}" y2="{body_h}" stroke="rgba(45,49,66,0.12)" stroke-width="0.8"/>')

    for j, label in enumerate(steps):
        f = j == focal_step
        s.append(f'<rect x="{cx(j) - 16:g}" y="6" width="32" height="16" rx="8" fill="{"rgba(235,108,54,0.20)" if f else "rgba(45,49,66,0.12)"}"/>')
        s.append(t(cx(j), 16.5, f'{j + 1:02d}', 'num focal' if f else 'num'))
        s.append(t(cx(j), 31, label.upper(), 'step focal' if f else 'step'))

    for k, (name, _key) in enumerate(spec['lanes']):
        lines = name.upper().split('\n')
        mid = lane_top(k) + LANE_H / 2
        for i, line in enumerate(lines):
            s.append(t(LABEL_W / 2, mid - 4 + 12 * i - 6 * (len(lines) - 2), line, 'lane'))

    for a in spec['arrows']:
        s += arrow(a, lanes, nodes)
    for n in nodes.values():
        s += node(n, lanes, keys)

    # Legend: data types used, then flow styles.
    y = body_h + 20
    used = []
    for n in nodes.values():
        for c in n.get('chips', ()):
            if c and c not in used:
                used.append(c)
    s.append(t(LABEL_W + 24, y + 3, 'DATA', 'lg'))
    x = LABEL_W + 40
    for c in used:
        s.append(chip(x, y - 4, c))
        s.append(t(x + 22, y + 3, CHIPS[c][0], 'lt'))
        x += 30 + len(CHIPS[c][0]) * 4.1
    y += 22
    s.append(t(LABEL_W + 24, y + 3, 'FLOW', 'lg'))
    x = LABEL_W + 40
    has_cut = any(n.get('cut') for n in nodes.values())
    styles = [('muted', 'handoff'), ('accent', 'focal handoff'), ('link', 'to reader')]
    for style, label in styles + ([('dashed', 'proposed')] if has_cut else []):
        color = {'muted': MUTED, 'dashed': MUTED, 'accent': ACCENT, 'link': LINK}[style]
        m = {'muted': 'm', 'dashed': 'm', 'accent': 'a', 'link': 'l'}[style]
        dash = ' stroke-dasharray="4,3"' if style == 'dashed' else ''
        s.append(f'<line x1="{x}" y1="{y}" x2="{x + 22}" y2="{y}" stroke="{color}"{dash} marker-end="url(#arr-{m})"/>')
        s.append(t(x + 30, y + 3, label, 'lt'))
        x += 50 + len(label) * 4.1
    note = 'chip on the left of a box = what goes in, chip on the right = what comes out.'
    if has_cut:
        s.append(f'<rect x="{x}" y="{y - 5}" width="22" height="10" rx="3" fill="{PAPER}" stroke="{CUT}" stroke-opacity="0.6" stroke-dasharray="3,2"/>')
        s.append(t(x + 30, y + 3, 'proposed cut', 'lt'))
        note += ' A dashed box still runs today but duplicates another step and is proposed for removal.'
    s.append(t(LABEL_W + 40, y + 25, note, 'lt'))
    s.append('</svg>')
    return '\n'.join(s) + '\n'


def main():
    for name, spec in FLOWS.items():
        path = OUT / f'flow-{name}.svg'
        path.write_text(render(spec), encoding='utf-8')
        print(f'wrote {path.relative_to(OUT.parent.parent).as_posix()}')


if __name__ == '__main__':
    main()
