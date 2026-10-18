#!/usr/bin/env python3
"""Head top / head x-span / body box every 0.5 s, read from the cutout alpha -> head.json (frame 1080x1920).
Usage: python3 headpos.py <project>"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

proj = common.project(sys.argv[1])
subject = os.path.join(proj, 'assets', 'subject.webm')
if not os.path.exists(subject):
    sys.exit('run cutout.py first')
W, H, STEP = 270, 480, 0.5
p = subprocess.Popen([common.tool('ffmpeg'), '-loglevel', 'error', '-c:v', 'libvpx-vp9', '-i', subject,
                      '-vf', f'alphaextract,fps=1/{STEP},scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1'],
                     stdout=subprocess.PIPE)
samples, k = [], 0
while True:
    buf = p.stdout.read(W * H)
    if len(buf) < W * H:
        break
    rows = [y for y in range(H) if any(buf[y * W + x] > 128 for x in range(0, W, 2))]
    t = round(k * STEP, 2); k += 1
    if not rows:
        samples.append({'t': t, 'head_top': None}); continue
    top = rows[0]
    y = min(H - 1, top + 25)
    xs = [x for x in range(W) if buf[y * W + x] > 128]
    cols = [x for x in range(W) if any(buf[yy * W + x] > 128 for yy in range(0, H, 4))]
    samples.append({'t': t, 'head_top': top * 4, 'head_x': [xs[0] * 4, xs[-1] * 4] if xs else None,
                    'body': [cols[0] * 4, top * 4, cols[-1] * 4, rows[-1] * 4]})
p.wait()
common.save(os.path.join(proj, 'head.json'), samples)
tops = [s['head_top'] for s in samples if s['head_top'] is not None]
print(f'head.json: {len(samples)} samples; head top min {min(tops)} max {max(tops)}' if tops else 'no subject found')
