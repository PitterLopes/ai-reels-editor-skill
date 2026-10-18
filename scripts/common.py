"""Shared helpers for the reels-editor skill scripts (standard library only)."""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL_DIR, 'template')
HYPERFRAMES = 'hyperframes@0.8.172'
TEXT = dict(capture_output=True, encoding='utf-8', errors='replace')


def say(*a):
    print(*a, flush=True)


def tool(name):
    p = shutil.which(name)
    if not p:
        sys.exit(f'{name} not found. Run: python3 scripts/setup.py')
    return p


def project(arg):
    p = os.path.abspath(os.path.expanduser(arg))
    for d in ('assets', 'work', 'renders'):
        os.makedirs(os.path.join(p, d), exist_ok=True)
    return p


_REQUIRED = object()


def load(path, default=_REQUIRED):
    """JSON file; `default` (even None) is returned when the file is absent; without a default the run stops."""
    if not os.path.exists(path):
        if default is not _REQUIRED:
            return default
        sys.exit(f'missing {path}')
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def save(path, data):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)


def probe(path):
    out = subprocess.run([tool('ffprobe'), '-v', 'error', '-show_entries',
                          'stream=codec_type,width,height,r_frame_rate,duration:format=duration',
                          '-of', 'json', path], **TEXT).stdout
    j = json.loads(out or '{}')
    info = {'width': 0, 'height': 0, 'fps': 30.0, 'duration': 0.0, 'audio': False}
    for s in j.get('streams', []):
        if s.get('codec_type') == 'video' and not info['width']:
            info['width'], info['height'] = int(s.get('width', 0)), int(s.get('height', 0))
            n, d = (s.get('r_frame_rate') or '30/1').split('/')
            info['fps'] = float(n) / float(d or 1)
            if s.get('duration'):
                info['duration'] = float(s['duration'])
        if s.get('codec_type') == 'audio':
            info['audio'] = True
    if j.get('format', {}).get('duration'):
        info['duration'] = float(j['format']['duration'])
    return info


def frames(path):
    out = subprocess.run([tool('ffprobe'), '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                          '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', path], **TEXT).stdout
    return int((out.strip().split(',') or ['0'])[0] or 0)


def _node_version(path):
    try:
        v = subprocess.run([path, '--version'], **TEXT).stdout.strip().lstrip('v')
        return int(v.split('.')[0])
    except Exception:
        return 0


def node22():
    """A Node 22+ binary, wherever it lives (PATH, nvm, Homebrew); None if there is none."""
    candidates = []
    if shutil.which('node'):
        candidates.append(shutil.which('node'))
    candidates += sorted(glob.glob(os.path.expanduser('~/.nvm/versions/node/*/bin/node')), reverse=True)
    candidates += ['/opt/homebrew/bin/node', '/usr/local/bin/node']
    for c in candidates:
        if os.path.exists(c) and _node_version(c) >= 22:
            return c
    return None


def hf_command(args):
    """argv and env to run the pinned HyperFrames with a Node 22+ on this machine."""
    node = node22()
    if not node:
        sys.exit('HyperFrames needs Node.js 22+. Install it (https://nodejs.org or `brew install node`) and re-run.')
    bindir = os.path.dirname(node)
    npx = os.path.join(bindir, 'npx')
    if not os.path.exists(npx):
        npx = shutil.which('npx') or 'npx'
    env = dict(os.environ)
    env['PATH'] = bindir + os.pathsep + env.get('PATH', '')
    return [npx, '--yes', HYPERFRAMES] + list(args), env


def slug(text):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s[:40] or 'reel'
