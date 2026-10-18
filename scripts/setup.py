#!/usr/bin/env python3
"""Check the machine, fetch the open-licensed fonts, synthesize the sound effects, pin HyperFrames.
Prints STATUS lines and READY. Safe to re-run. Usage: python3 scripts/setup.py"""
import os
import re
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from common import say  # noqa: E402

FONTS_CSS = ('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@800;900&family=Inter:wght@500;600'
             '&family=DM+Serif+Display:ital@0;1&family=Instrument+Serif:ital@1&family=Montserrat:wght@500&display=block')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
GSAP = 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js'
FONT_DIR = os.path.join(common.TEMPLATE, 'assets', 'fonts')
SFX_DIR = os.path.join(common.TEMPLATE, 'assets', 'sfx')


def fetch(url, path=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if path:
        with open(path, 'wb') as fh:
            fh.write(data)
    return data


def check_tools():
    ok = True
    for t in ('ffmpeg', 'ffprobe'):
        if shutil.which(t):
            say(f'STATUS {t}: ok ({shutil.which(t)})')
        else:
            ok = False
            say(f'STATUS {t}: MISSING -> macOS: brew install ffmpeg | Debian/Ubuntu: sudo apt install ffmpeg')
    node = common.node22()
    if node:
        say(f'STATUS node: ok ({node})')
    else:
        ok = False
        say('STATUS node: MISSING or older than 22 -> https://nodejs.org (LTS) or `brew install node`')
    if sys.version_info < (3, 9):
        ok = False
        say(f'STATUS python: {sys.version.split()[0]} is too old -> install Python 3.9+')
    else:
        say(f'STATUS python: ok ({sys.version.split()[0]})')
    return ok


def fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    css_path = os.path.join(FONT_DIR, 'fonts.css')
    if os.path.exists(css_path) and len([f for f in os.listdir(FONT_DIR) if f.endswith('.woff2')]) >= 8:
        say('STATUS fonts: ok (already fetched)')
        return True
    try:
        css = fetch(FONTS_CSS).decode('utf-8')
    except Exception as e:  # offline
        say(f'STATUS fonts: MISSING (could not reach Google Fonts: {e}); the build falls back to system fonts')
        return False
    out = []
    for block in re.findall(r'@font-face\s*\{(.*?)\}', css, re.S):
        if 'U+0000-00FF' not in block:
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        style = re.search(r'font-style:\s*(\w+)', block).group(1)
        weight = re.search(r'font-weight:\s*(\d+)', block).group(1)
        url = re.search(r'url\((https://[^)]+\.woff2)\)', block).group(1)
        name = f"{fam.replace(' ', '')}-{weight}-{style}.woff2"
        fetch(url, os.path.join(FONT_DIR, name))
        out.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};font-display:block;"
                   f"src:url('{name}') format('woff2')}}")
    with open(css_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out) + '\n')
    say(f'STATUS fonts: ok ({len(out)} faces, SIL Open Font License)')
    return True


def sfx():
    os.makedirs(SFX_DIR, exist_ok=True)
    if all(os.path.exists(os.path.join(SFX_DIR, n + '.wav')) for n in ('whoosh', 'pop', 'click', 'thump', 'sparkle')):
        say('STATUS sfx: ok (synthesized)')
        return True
    subprocess.run([sys.executable, os.path.join(common.SKILL_DIR, 'scripts', 'sfx.py'), SFX_DIR], check=True,
                   stdout=subprocess.DEVNULL)
    say('STATUS sfx: ok (synthesized, no third-party audio)')
    return True


def gsap():
    path = os.path.join(common.TEMPLATE, 'assets', 'gsap.min.js')
    if os.path.exists(path):
        say('STATUS gsap: ok')
        return True
    try:
        fetch(GSAP, path)
        say('STATUS gsap: ok (fetched 3.14.2)')
        return True
    except Exception as e:
        say(f'STATUS gsap: MISSING ({e}); the build will use the CDN copy, which needs internet at render time')
        return False


def hyperframes():
    argv, env = common.hf_command(['--version'])
    try:
        v = subprocess.run(argv, env=env, timeout=600, **common.TEXT).stdout.strip().splitlines()[-1]
        say(f'STATUS hyperframes: ok ({v})')
        return True
    except Exception as e:
        say(f'STATUS hyperframes: could not run npx ({e}); check Node and the network')
        return False


if __name__ == '__main__':
    ok = check_tools()
    fonts(); sfx(); gsap()
    ok = hyperframes() and ok
    say('READY' if ok else 'NOT READY: fix the MISSING lines above and re-run')
