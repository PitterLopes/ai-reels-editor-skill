#!/usr/bin/env python3
"""Normalize the source (1080x1920, 30 fps CFR), cut dead air, transcribe with word times.

Usage: python3 ingest.py <project> <video> [--lang pt] [--model small] [--keep-pauses] [--pause 0.6] [--air 0.2]
Writes: source.json, assets/aroll.mp4, work/cuts.json, words.json. Never touches the original file."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from common import say  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('video')
ap.add_argument('--lang', default='pt'); ap.add_argument('--model', default=None)
ap.add_argument('--keep-pauses', action='store_true')
ap.add_argument('--pause', type=float, default=0.6, help='pauses longer than this are cut (s)')
ap.add_argument('--air', type=float, default=0.2, help='air kept across a cut pause (s)')
a = ap.parse_args()

proj = common.project(a.project)
src = os.path.abspath(os.path.expanduser(a.video))
if not os.path.isfile(src):
    sys.exit(f'video not found: {src}')
FF = common.tool('ffmpeg')
info = common.probe(src)
if not info.get('duration') or not info.get('audio'):
    sys.exit(f'this file has no readable video+audio stream: {src} ({info})')
common.save(os.path.join(proj, 'source.json'), {'path': src, **info})
say(f"source {info['width']}x{info['height']} {info['fps']:.2f} fps {info['duration']:.1f} s audio={info['audio']}")

# 1. normalize: cover 1080x1920, centre crop, constant 30 fps, AAC 48 kHz, audio aligned from t=0
norm = os.path.join(proj, 'work', 'norm.mp4')
vf = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setpts=PTS-STARTPTS'
cmd = [FF, '-loglevel', 'error', '-y', '-i', src, '-map', '0:v:0', '-vf', vf, '-fps_mode', 'cfr',
       '-c:v', 'libx264', '-crf', '15', '-preset', 'medium', '-pix_fmt', 'yuv420p']
if info['audio']:
    cmd += ['-map', '0:a:0', '-af', 'asetpts=PTS-STARTPTS', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000']
cmd += [norm]
subprocess.run(cmd, check=True)

# 2. dead air: silencedetect on the normalized file, keep `air` across each cut pause
keep = [(0.0, common.probe(norm)['duration'])]
cuts = []
if info['audio'] and not a.keep_pauses:
    out = subprocess.run([FF, '-i', norm, '-af', f'silencedetect=n=-40dB:d={a.pause}', '-vn', '-f', 'null', '-'],
                         **common.TEXT).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    pauses = [(s, e) for s, e in zip(starts, ends) if e - s > a.pause]
    dur = keep[0][1]
    keep, pos = [], 0.0
    for s, e in pauses:
        cut_from, cut_to = s + a.air / 2, e - a.air / 2
        if cut_to - cut_from < 0.1:
            continue
        keep.append((pos, cut_from)); cuts.append({'src_from': cut_from, 'src_to': cut_to})
        pos = cut_to
    keep.append((pos, dur))
    keep = [(s, e) for s, e in keep if e - s > 0.05]

aroll = os.path.join(proj, 'assets', 'aroll.mp4')
if len(keep) == 1 and cuts == []:
    shutil.copyfile(norm, aroll)
else:
    expr = '+'.join(f'between(t,{s:.3f},{e:.3f})' for s, e in keep)
    fc = (f"[0:v]select='{expr}',setpts=N/30/TB[v];[0:a]aselect='{expr}',asetpts=N/SR/TB[a]")
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', norm, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
                    '-r', '30', '-fps_mode', 'cfr', '-c:v', 'libx264', '-crf', '15', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                    '-g', '30', '-keyint_min', '30', '-c:a', 'aac', '-b:a', '192k', aroll], check=True)
# cut positions on the cut timeline (for soft punches that hide the jump)
t_cut, removed = [], 0.0
for c in cuts:
    t_cut.append(round(c['src_from'] - removed, 3)); removed += c['src_to'] - c['src_from']
    c['t'] = t_cut[-1]
common.save(os.path.join(proj, 'work', 'cuts.json'), {'kept': keep, 'cuts': cuts})
d = common.probe(aroll)['duration']
say(f'aroll.mp4 {d:.1f} s ({len(cuts)} pause(s) removed, {removed:.1f} s)')

# 3. transcribe on the cut video (HyperFrames -> whisper), word-level times
model = a.model or ('small.en' if a.lang == 'en' else 'small')
argv, env = common.hf_command(['transcribe', 'assets/aroll.mp4', '-l', a.lang, '-m', model, '--json'])
r = subprocess.run(argv, cwd=proj, env=env, **common.TEXT)
tr = os.path.join(proj, 'transcript.json')
m = re.search(r'"transcriptPath"\s*:\s*"([^"]+)"', r.stdout or '')
if m:
    tr = m.group(1)
if not os.path.exists(tr):
    say(r.stdout[-800:]); say(r.stderr[-800:])
    sys.exit('transcription failed (see above); fix and re-run, or write words.json by hand: [{"text","start","end"}]')
raw = common.load(tr)
items = raw if isinstance(raw, list) else raw.get('words') or raw.get('entries') or []
words = [{'text': w['text'].strip(), 'start': round(float(w['start']), 3), 'end': round(float(w['end']), 3)}
         for w in items if w.get('text', '').strip()]
common.save(os.path.join(proj, 'words.json'), words)
say(f'words.json: {len(words)} words. Preview: ' + ' '.join(w['text'] for w in words[:30]))
say('Fix mishearings (names, numbers) in words.json before planning.')
