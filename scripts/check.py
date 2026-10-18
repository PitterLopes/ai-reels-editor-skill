#!/usr/bin/env python3
"""Frame-exact QA from the final render: a frame after every reframe/punch and inside every big beat, in one sheet
(work/check.jpg), audio peaks, and an optional 720p phone copy.
Usage: python3 check.py <project> <render.mp4> [--phone]"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

proj = common.project(sys.argv[1]); render = os.path.abspath(sys.argv[2])
plan = common.load(os.path.join(proj, 'plan.resolved.json'), None) or common.load(os.path.join(proj, 'plan.json'))
FF = common.tool('ffmpeg')
times = []
for b in plan['beats']:
    if b['type'] in ('cut', 'punch'):
        times.append(b['t'] + 0.05)
    elif b['type'] in ('card', 'stat', 'compare'):
        times.append(b['t'] + 0.9)
    elif b['type'] == 'word' and b.get('size') in ('xl', 'huge', 'big'):
        times.append(b['t'] + 0.3)
times = sorted(set(round(t, 2) for t in times))[:48]
cf = os.path.join(proj, 'work', 'cf'); os.makedirs(cf, exist_ok=True)
for k, t in enumerate(times):
    subprocess.run([FF, '-loglevel', 'error', '-y', '-ss', f'{t:.3f}', '-i', render, '-frames:v', '1', '-vf', 'scale=180:-2',
                    os.path.join(cf, f'f{k:03d}.png')], check=True)
cols = min(8, max(1, len(times)))
rows = -(-len(times) // cols)
sheet = os.path.join(proj, 'work', 'check.jpg')
subprocess.run([FF, '-loglevel', 'error', '-y', '-i', os.path.join(cf, 'f%03d.png'), '-vf', f'tile={cols}x{rows}', '-frames:v', '1',
                '-update', '1', sheet], check=True)
print(f'{len(times)} frames at {times} -> {sheet}')
out = subprocess.run([FF, '-i', render, '-af', 'volumedetect', '-vn', '-f', 'null', '-'], **common.TEXT).stderr
m = re.search(r'max_volume: ([-\d.]+) dB', out)
print('audio max', m.group(1) + ' dB' if m else '?', '(aim for -2 to -5 dB; the voice must stay above the SFX)')
if '--phone' in sys.argv:
    phone = os.path.splitext(render)[0] + '-phone.mp4'
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'slow',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', phone], check=True)
    print('phone copy', phone, f'{os.path.getsize(phone) / 1e6:.1f} MB')
