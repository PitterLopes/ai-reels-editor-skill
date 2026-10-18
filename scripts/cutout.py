#!/usr/bin/env python3
"""Cut the speaker out of assets/aroll.mp4 -> assets/subject.webm (VP9 + alpha) and assert equal frame counts.
Usage: python3 cutout.py <project> [--device cpu|coreml|cuda]   (slow: run in the background)"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

proj = common.project(sys.argv[1])
extra = sys.argv[2:]
aroll = os.path.join(proj, 'assets', 'aroll.mp4')
if not os.path.exists(aroll):
    sys.exit('run ingest.py first')
argv, env = common.hf_command(['remove-background', 'assets/aroll.mp4', '-o', 'assets/subject.webm', '--quality', 'best'] + extra)
code = subprocess.run(argv, cwd=proj, env=env).returncode
if code:
    sys.exit(f'remove-background failed ({code})')
a, s = common.frames(aroll), common.frames(os.path.join(proj, 'assets', 'subject.webm'))
print(f'aroll frames {a} / cutout frames {s}')
if a != s:
    sys.exit('FRAME MISMATCH: the cutout would drift. Re-run ingest.py (constant 30 fps) and this script.')
