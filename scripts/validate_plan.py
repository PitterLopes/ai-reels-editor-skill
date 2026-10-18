#!/usr/bin/env python3
"""Validate plan.json (schema, safe zone, head coverage, overlaps, pacing, transcript coverage) and write plan.resolved.json.
Usage: python3 validate_plan.py <project>   (exit 1 on errors)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import planlib  # noqa: E402

proj = common.project(sys.argv[1])
plan = common.load(os.path.join(proj, 'plan.json'))
head = common.load(os.path.join(proj, 'head.json'), [])
words = common.load(os.path.join(proj, 'words.json'), [])
dur = common.probe(os.path.join(proj, 'assets', 'aroll.mp4'))['duration']
plan, errors, warnings = planlib.resolve(plan, head, dur)
# captions say what was said: each word/line beat near a spoken word
import re
def norm(s): return re.sub(r'[^\w]', '', s.lower())
spoken = [(w['start'], norm(w['text'])) for w in words]
for i, b in enumerate(plan['beats']):
    if b['type'] in ('line', 'word'):
        first = norm(b.get('text', '').split()[0]) if b.get('text') else ''
        if first and not any(abs(s - b['t']) < 0.6 and (first in tx or tx in first) for s, tx in spoken):
            warnings.append(f'beat {i} "{b.get("text")}": first word not spoken within 0.6 s of t={b["t"]:.2f}')
# coverage: spoken seconds without a caption in the previous 3 s (a card with items is the caption while it is up)
line_ts = [(b['t'], b['end']) for b in plan['beats'] if b['type'] in ('line', 'word') or (b['type'] == 'card' and b.get('items'))]
gaps = []
for s, _ in spoken:
    if not any(t - 0.3 <= s <= e + 3 for t, e in line_ts):
        gaps.append(round(s, 1))
if gaps:
    warnings.append(f'{len(gaps)} spoken moments without a caption line nearby (first: {gaps[:5]})')
for w in warnings:
    print('WARNING', w)
for e in errors:
    print('ERROR', e)
resolved = os.path.join(proj, 'plan.resolved.json')
if errors:
    if os.path.exists(resolved):
        os.remove(resolved)
    print(f'{len(errors)} error(s), {len(warnings)} warning(s); fix plan.json (plan.resolved.json NOT written)')
    sys.exit(1)
common.save(resolved, plan)
print(f'0 error(s), {len(warnings)} warning(s); plan.resolved.json written')
