#!/usr/bin/env python3
"""Draft plan.json from words.json: caption lines by pauses/punctuation, soft punches on the removed pauses,
a reframe every ~20 s, the style defaults. The editor refines it afterwards.
Usage: python3 draft_plan.py <project> --style impact|card|data [--lang pt]"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('--style', default='impact'); ap.add_argument('--lang', default=None)
a = ap.parse_args()
proj = common.project(a.project)
words = common.load(os.path.join(proj, 'words.json'))
cuts = common.load(os.path.join(proj, 'work', 'cuts.json'), {'cuts': []})
brand = common.load(os.path.join(proj, 'brand.json'), None) or common.load(os.path.join(common.TEMPLATE, 'brand.json'))
dur = common.probe(os.path.join(proj, 'assets', 'aroll.mp4'))['duration']

lines, cur = [], []


def flush():
    if cur:
        lines.append(list(cur)); cur.clear()


for i, w in enumerate(words):
    cur.append(w)
    text = ' '.join(x['text'] for x in cur)
    nxt = words[i + 1] if i + 1 < len(words) else None
    gap = (nxt['start'] - w['end']) if nxt else 9
    if w['text'][-1:] in '.?!' or gap > 0.5 or len(cur) >= 6 or len(text) > 26:
        flush()
flush()

beats = []
for k, ws in enumerate(lines):
    t = max(0.0, ws[0]['start'] - 0.05)
    end = ws[-1]['end'] + 0.25
    if k + 1 < len(lines):
        end = min(end, max(lines[k + 1][0]['start'] - 0.05, t + 0.35))
    beats.append({'type': 'line', 't': round(t, 3), 'end': round(min(end, dur), 3), 'text': ' '.join(w['text'] for w in ws),
                  'slot': 'chest'})
for c in cuts.get('cuts', []):
    beats.append({'type': 'punch', 't': round(c['t'], 3)})
# a reframe at the start of the line nearest every ~20 s, alternating 1.0 / 1.18
zoom, last = 1.18, -99
for b in [x for x in beats if x['type'] == 'line']:
    if b['t'] - last >= 20 and b['t'] > 2:
        beats.append({'type': 'cut', 't': b['t'], 'zoom': zoom}); zoom = 1.0 if zoom > 1 else 1.18; last = b['t']
plan = {'version': 1, 'style': a.style, 'language': a.lang or 'pt', 'brand': brand,
        'beats': sorted(beats, key=lambda b: b['t'])}
out = os.path.join(proj, 'plan.json')
if os.path.exists(out):
    print(f'{out} exists: writing plan.draft.json instead (keep your edits)'); out = os.path.join(proj, 'plan.draft.json')
common.save(out, plan)
print(f'{out}: {len(lines)} lines, {len(cuts.get("cuts", []))} punches, {sum(1 for b in beats if b["type"] == "cut")} reframes, {dur:.1f} s')
print('Next: mark punch words (type word, size, slot behind/chest, accent), add card/stat/compare beats, then validate_plan.py')
