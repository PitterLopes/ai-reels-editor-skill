#!/usr/bin/env python3
"""plan(.resolved).json + style -> index.html (a HyperFrames composition). Never edit index.html by hand.
Usage: python3 build.py <project> [--safe]     (--safe draws the Reels safe zone in red: snapshots only)"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import planlib  # noqa: E402

SAFE = '--safe' in sys.argv
proj = common.project([a for a in sys.argv[1:] if not a.startswith('--')][0])
os.chdir(proj)
head = common.load('head.json', [])
dur = common.probe('assets/aroll.mp4')['duration']
if os.path.exists('plan.resolved.json') and os.path.getmtime('plan.resolved.json') >= os.path.getmtime('plan.json'):
    plan = common.load('plan.resolved.json')
else:
    sys.exit('plan.resolved.json is missing or older than plan.json: run validate_plan.py first (and fix its errors)')
brand = {**common.load(os.path.join(common.TEMPLATE, 'brand.json')), **plan.get('brand', {})}
style = plan.get('style', 'impact')
HAS_CUT = os.path.exists('assets/subject.webm')
NUDGE = 0.002
SFX_GAIN = 0.7

# project assets from the template (fonts, sfx, gsap), copied once
for name in ('fonts', 'sfx'):
    src, dst = os.path.join(common.TEMPLATE, 'assets', name), os.path.join('assets', name)
    if os.path.isdir(src) and not os.path.isdir(dst):
        shutil.copytree(src, dst)
gs = os.path.join(common.TEMPLATE, 'assets', 'gsap.min.js')
if os.path.exists(gs) and not os.path.exists('assets/gsap.min.js'):
    shutil.copyfile(gs, 'assets/gsap.min.js')
GSAP_SRC = 'assets/gsap.min.js' if os.path.exists('assets/gsap.min.js') else 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js'

STYLES = {
    'impact': dict(grade='contrast(1.06) saturate(.92) brightness(.98)', subject=None,
                   tone='linear-gradient(180deg,rgba(20,55,75,.14),rgba(60,40,20,.08))', vignette=.40, bottom=.30,
                   word_font=brand['display'], word_weight=900, word_case='none', punch=True),
    'card': dict(grade='contrast(1.04) saturate(.95) brightness(1.0)', subject=None,
                 tone='linear-gradient(180deg,rgba(25,30,60,.12),rgba(20,20,30,.10))', vignette=.30, bottom=.22,
                 word_font=brand['display'], word_weight=800, word_case='none', punch=True),
    'data': dict(grade='contrast(1.05) saturate(.9) brightness(.97)', subject=None,
                 tone='linear-gradient(180deg,rgba(10,25,45,.18),rgba(10,10,20,.12))', vignette=.35, bottom=.26,
                 word_font=brand['display'], word_weight=800, word_case='none', punch=True),
}
if style not in STYLES:
    sys.exit(f'style {style} is not implemented in build.py (implemented: {", ".join(STYLES)}); see references/styles.md')
ST = STYLES[style]
ACC, INK, CREAM = brand['accent'], brand['ink'], brand.get('cream', '#F7F4EE')
PT = plan.get('language', 'pt') != 'en'

html, tw, sfx = [], [], []


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def add_sfx(name, t, vol=1.0):
    if t < 0 or t > dur - .05:
        return
    sfx.append((name, round(t, 3), vol))


# ---------------------------------------------------------------- reframes (hard cuts, held) and soft punches
cuts = sorted([b for b in plan['beats'] if b['type'] == 'cut'], key=lambda b: b['t'])


def zoom_at(t):
    z, cx, cy = 1.0, 0.5, 0.38
    for c in cuts:
        if c['t'] <= t:
            z, cx, cy = c['zoom'], c.get('cx', .5), c.get('cy', .38)
    return z, cx, cy


tw.append("gsap.set('.g',{scale:1,transformOrigin:'50% 38%'});")
for c in cuts:
    tw.append(f"tl.set('.g',{{scale:{c['zoom']},transformOrigin:'{c.get('cx', .5) * 100:.1f}% {c.get('cy', .38) * 100:.1f}%'}},{c['t'] - NUDGE:.3f});")
    add_sfx('thump', c['t'], .45)
if ST['punch']:
    for b in plan['beats']:
        if b['type'] == 'punch':
            z, _, _ = zoom_at(b['t'])
            tw.append(f"tl.fromTo('.g',{{scale:{z * 1.05:.3f}}},{{scale:{z:.3f},duration:.32,ease:'power2.out',immediateRender:false}},{b['t'] - NUDGE:.3f});")


def head_top_on_screen(t, head_top):
    """where the head top lands after the active reframe (the cutout scales with the video)."""
    z, cx, cy = zoom_at(t)
    oy = cy * 1920
    return oy + (head_top - oy) * z


# ---------------------------------------------------------------- words and lines
cards = [b for b in plan['beats'] if b['type'] == 'card']


def under_card(b):
    return any(c['t'] - .5 <= b['t'] <= c['end'] for c in cards)


k = 0
for b in plan['beats']:
    if b['type'] not in ('line', 'word'):
        continue
    if b['type'] == 'line' and under_card(b):
        continue   # the card is the caption there
    k += 1
    wid = f'w{k}'
    size = planlib.SIZES[b.get('size', 'sm' if b['type'] == 'line' else 'md')]
    top = b['top']
    if b['type'] == 'word' and b.get('slot') == 'behind':
        rng = planlib.head_range(head, b['t'], b['end'])
        if rng:
            top = max(180, planlib.behind_top(head_top_on_screen(b['t'], rng[0]), size))
    cls = 'dw' + (' back' if b.get('slot') == 'behind' and HAS_CUT else '') + (' y' if b.get('accent') else '')
    html.append(f'<div id="{wid}" class="{cls}" style="top:{top}px;font-size:{size}px">{esc(b["text"])}</div>')
    t, e = b['t'], b['end']
    tw.append(f"gsap.set('#{wid}',{{autoAlpha:0}});")
    if b['type'] == 'word':
        tw.append(f"tl.fromTo('#{wid}',{{autoAlpha:0,scale:1.18,filter:'blur(18px)'}},{{autoAlpha:1,scale:1,filter:'blur(0px)',"
                  f"duration:.22,ease:'expo.out',immediateRender:false}},{t:.3f});")
        if b.get('size') in ('xl', 'huge', 'big'):
            add_sfx('pop', t, .8)
    else:
        tw.append(f"tl.fromTo('#{wid}',{{autoAlpha:0,y:16}},{{autoAlpha:1,y:0,duration:.2,ease:'power3.out',immediateRender:false}},{t:.3f});")
    if e < dur - .05:
        tw.append(f"tl.to('#{wid}',{{autoAlpha:0,scale:.97,filter:'blur(12px)',duration:.14,ease:'power2.in'}},{max(t + .1, e - .14):.3f});")
        tw.append(f"tl.set('#{wid}',{{autoAlpha:0}},{e:.3f});")

# ---------------------------------------------------------------- presentation cards (the speaker becomes a framed card)
CARD_SCALE = 0.56   # stage top lands at ~805 px; a card with 4 items ends at ~790
tw.append("gsap.set('#stage',{scale:1,y:0,borderRadius:0,transformOrigin:'50% 100%'});gsap.set('#corners',{autoAlpha:0});")
for i, c in enumerate(cards):
    cid = f'card{i}'
    t0, t1 = c['t'] - .45, c['end']
    items = ''.join(
        f'<div class="item" id="{cid}i{j}"><span class="mark {it.get("mark", "")}"></span><span>{esc(it["text"])}</span></div>'
        for j, it in enumerate(c.get('items', [])))
    kicker = f'<div class="kicker">{esc(c["kicker"])}</div>' if c.get('kicker') else ''
    html.append(f'<div id="{cid}" class="pcard">{kicker}<div class="title">{esc(c["title"])}</div>{items}</div>')
    tw += [f"tl.to('#stage',{{scale:{CARD_SCALE},y:-40,borderRadius:44,duration:.45,ease:'power3.inOut'}},{t0:.3f});",
           f"tl.set('#corners',{{autoAlpha:1}},{t0 + .3:.3f});",
           f"gsap.set('#{cid}',{{autoAlpha:0,y:30}});",
           f"tl.to('#{cid}',{{autoAlpha:1,y:0,duration:.4,ease:'power3.out'}},{t0 + .2:.3f});"]
    add_sfx('whoosh', t0, .7)
    for j, it in enumerate(c.get('items', [])):
        tw += [f"gsap.set('#{cid}i{j}',{{autoAlpha:0,x:-24}});",
               f"tl.to('#{cid}i{j}',{{autoAlpha:1,x:0,duration:.32,ease:'power3.out'}},{max(t0 + .3, it['t']):.3f});"]
        add_sfx('click', max(t0 + .3, it['t']), .6)
    tw += [f"tl.to('#{cid}',{{autoAlpha:0,y:-24,duration:.3,ease:'power2.in'}},{t1 - .3:.3f});",
           f"tl.set('#corners',{{autoAlpha:0}},{t1 - .3:.3f});",
           f"tl.to('#stage',{{scale:1,y:0,borderRadius:0,duration:.45,ease:'power3.inOut'}},{t1 - .45:.3f});"]
    add_sfx('whoosh', t1 - .45, .5)

# ---------------------------------------------------------------- data cards (stat / compare) in the top band
js_fmt = ("function fmt(v,d,p,s){var n=v.toFixed(d);" + ("n=n.replace('.',',');" if PT else "") +
          "return (p||'')+n+(s||'');}")
for i, b in enumerate([x for x in plan['beats'] if x['type'] in ('stat', 'compare')]):
    did = f'data{i}'
    t0, t1 = b['t'], b['end']
    if b['type'] == 'stat':
        d = int(b.get('decimals', 0))
        html.append(f'<div id="{did}" class="dcard"><div class="label">{esc(b.get("label", ""))}</div>'
                    f'<div class="value" id="{did}v">{esc(b.get("prefix", ""))}{("0," if PT else "0.") + "0" * d if d else "0"}{esc(b.get("suffix", ""))}</div>'
                    f'<div class="track"><div class="fill" id="{did}f"></div></div></div>')
        tw += [f"gsap.set('#{did}',{{autoAlpha:0,y:40,filter:'blur(10px)'}});gsap.set('#{did}f',{{scaleX:0,transformOrigin:'0 50%'}});",
               f"tl.to('#{did}',{{autoAlpha:1,y:0,filter:'blur(0px)',duration:.4,ease:'power3.out'}},{t0:.3f});",
               f"var o{i}={{v:{float(b.get('from', 0))}}};tl.to(o{i},{{v:{float(b['to'])},duration:1.1,ease:'power3.out',"
               f"onUpdate:function(){{document.getElementById('{did}v').textContent=fmt(o{i}.v,{d},{json.dumps(b.get('prefix', ''))},{json.dumps(b.get('suffix', ''))});}}}},{t0 + .25:.3f});",
               f"tl.to('#{did}f',{{scaleX:{float(b.get('bar', 1.0)):.3f},duration:.9,ease:'power3.out'}},{t0 + .25:.3f});"]
        add_sfx('whoosh', t0, .6); add_sfx('click', t0 + .25, .6)
    else:
        a_, b_ = b['a'], b['b']
        mx = max(float(a_.get('num', 1)), float(b_.get('num', 1)), 1e-9)
        rows = ''
        for side, s in (('a', a_), ('b', b_)):
            col = ' bad' if s.get('bad') else (' good' if s.get('good') else '')
            rows += (f'<div class="row{col}"><div class="rl"><span>{esc(s["label"])}</span><b>{esc(s["value"])}</b></div>'
                     f'<div class="track"><div class="fill" id="{did}{side}"></div></div></div>')
        ratio = f'<div class="ratio">{esc(b["ratio"])}</div>' if b.get('ratio') else ''
        html.append(f'<div id="{did}" class="dcard"><div class="label">{esc(b.get("title", ""))}</div>{rows}{ratio}</div>')
        tw += [f"gsap.set('#{did}',{{autoAlpha:0,y:40,filter:'blur(10px)'}});gsap.set(['#{did}a','#{did}b'],{{scaleX:0,transformOrigin:'0 50%'}});",
               f"tl.to('#{did}',{{autoAlpha:1,y:0,filter:'blur(0px)',duration:.4,ease:'power3.out'}},{t0:.3f});",
               f"tl.to('#{did}a',{{scaleX:{float(a_.get('num', 1)) / mx:.3f},duration:.9,ease:'power3.out'}},{t0 + .3:.3f});",
               f"tl.to('#{did}b',{{scaleX:{float(b_.get('num', 1)) / mx:.3f},duration:.9,ease:'power3.out'}},{t0 + .6:.3f});"]
        if b.get('ratio'):
            tw += [f"gsap.set('#{did} .ratio',{{autoAlpha:0,scale:1.6}});",
                   f"tl.to('#{did} .ratio',{{autoAlpha:1,scale:1,duration:.3,ease:'back.out(2)'}},{t0 + 1.3:.3f});"]
            add_sfx('pop', t0 + 1.3, .7)
        add_sfx('whoosh', t0, .6); add_sfx('click', t0 + .3, .5); add_sfx('click', t0 + .6, .5)
    tw += [f"tl.to('#{did}',{{autoAlpha:0,y:-30,filter:'blur(8px)',duration:.3,ease:'power2.in'}},{t1 - .3:.3f});"]

# ---------------------------------------------------------------- sound effects on their own lanes
SFX_LEN = {'whoosh': .55, 'pop': .3, 'click': .09, 'thump': .6, 'sparkle': .9}
audio, lanes = [], []
for n, (name, t, vol) in enumerate(sorted(sfx, key=lambda x: x[1])):
    d = min(SFX_LEN[name], dur - t)
    lane = next((i for i, end in enumerate(lanes) if end <= t), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = t + d
    audio.append(f'<audio id="sfx{n}" src="assets/sfx/{name}.wav" data-start="{t:.3f}" data-duration="{d:.3f}" '
                 f'data-track-index="{10 + lane}" data-volume="{vol * SFX_GAIN:.3f}"></audio>')

CSS = f'''
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:{INK}}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{INK}}}
#stage{{position:absolute;inset:0;overflow:hidden;transform-origin:50% 100%}}
.full{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
#bgv{{z-index:0}}
.dw.back{{z-index:3}}
#cutwrap{{position:absolute;inset:0;z-index:4}}
#corners{{position:absolute;inset:18px;z-index:6;pointer-events:none}}
#corners i{{position:absolute;width:70px;height:70px;border:7px solid #fff;opacity:.9}}
#corners .tl{{left:0;top:0;border-right:0;border-bottom:0}}#corners .tr{{right:0;top:0;border-left:0;border-bottom:0}}
#corners .bl{{left:0;bottom:0;border-right:0;border-top:0}}#corners .br{{right:0;bottom:0;border-left:0;border-top:0}}
.fx{{position:absolute;inset:0;pointer-events:none;z-index:7}}
#tone{{background:{ST['tone']};mix-blend-mode:soft-light}}
#vig{{background:radial-gradient(95% 62% at 50% 46%,rgba(0,0,0,0) 55%,rgba(0,0,0,{ST['vignette']}) 100%)}}
#grad{{background:linear-gradient(180deg,rgba(0,0,0,.30) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 60%,rgba(0,0,0,{ST['bottom']}) 100%)}}
.dw{{position:absolute;left:0;right:0;text-align:center;z-index:8;color:#fff;font-family:'{ST['word_font']}','Inter Tight',sans-serif;
  font-weight:{ST['word_weight']};letter-spacing:-.045em;line-height:.9;text-transform:{ST['word_case']};
  text-shadow:0 10px 40px rgba(0,0,0,.55),0 2px 8px rgba(0,0,0,.35);transform-origin:50% 60%;white-space:nowrap}}
.dw.y{{color:{ACC}}}
.pcard{{position:absolute;left:60px;top:120px;width:960px;z-index:9;padding:44px 48px;border-radius:32px;
  background:rgba(12,12,20,.88);border:2px solid rgba(255,255,255,.16);box-shadow:0 30px 80px rgba(0,0,0,.45);color:{CREAM}}}
.pcard .kicker{{font:600 32px/1 '{brand['text']}',Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:{ACC};margin-bottom:18px}}
.pcard .title{{font:400 92px/1.05 '{brand['serif']}','DM Serif Display',serif;margin-bottom:28px}}
.pcard .item{{display:flex;align-items:center;gap:22px;font:500 46px/1.25 '{brand['text']}',Inter,sans-serif;padding:14px 0;border-top:1px solid rgba(255,255,255,.1)}}
.pcard .mark{{width:34px;height:34px;border-radius:50%;border:3px solid rgba(255,255,255,.35);flex:none;position:relative}}
.pcard .mark.check{{background:#2FC55A;border-color:#2FC55A}}.pcard .mark.cross{{background:#E5322D;border-color:#E5322D}}
.pcard .mark.check::after{{content:'';position:absolute;left:11px;top:5px;width:9px;height:17px;border:solid #fff;border-width:0 4px 4px 0;transform:rotate(45deg)}}
.pcard .mark.cross::after{{content:'×';position:absolute;left:0;right:0;top:-6px;text-align:center;color:#fff;font:700 34px/1.2 sans-serif}}
.dcard{{position:absolute;left:60px;top:110px;width:960px;z-index:9;padding:40px 48px;border-radius:32px;
  background:rgba(12,12,20,.88);border:2px solid rgba(255,255,255,.16);box-shadow:0 30px 80px rgba(0,0,0,.45);color:{CREAM}}}
.dcard .label{{font:500 36px/1.2 '{brand['text']}',Inter,sans-serif;color:rgba(255,255,255,.72);margin-bottom:10px}}
.dcard .value{{font:400 120px/1.05 '{brand['serif']}','DM Serif Display',serif;color:{ACC};margin:6px 0 18px;font-variant-numeric:tabular-nums}}
.dcard .track{{height:18px;border-radius:9px;background:rgba(255,255,255,.12);overflow:hidden}}
.dcard .fill{{height:100%;width:100%;border-radius:9px;background:{ACC}}}
.dcard .row{{margin-top:22px}}.dcard .row.bad .fill{{background:#FF5A5F}}.dcard .row.good .fill{{background:#2FC55A}}
.dcard .rl{{display:flex;justify-content:space-between;align-items:baseline;font:500 40px/1.2 '{brand['text']}',Inter,sans-serif;margin-bottom:10px}}
.dcard .rl b{{font:400 64px/1 '{brand['serif']}','DM Serif Display',serif;font-variant-numeric:tabular-nums}}
.dcard .row.bad .rl b{{color:#FF5A5F}}.dcard .row.good .rl b{{color:#2FC55A}}
.dcard .ratio{{position:absolute;right:40px;top:-28px;padding:12px 26px;border-radius:40px;background:{ACC};color:{INK};font:700 44px/1 '{brand['text']}',Inter,sans-serif;transform:rotate(-6deg)}}
'''
SAFE_GUIDE = ('<div style="position:absolute;inset:0;z-index:99;pointer-events:none">'
              '<div style="position:absolute;left:0;right:0;top:0;height:220px;background:rgba(255,0,0,.28)"></div>'
              '<div style="position:absolute;left:0;right:0;top:1470px;bottom:0;background:rgba(255,0,0,.28)"></div>'
              '<div style="position:absolute;left:0;width:35px;top:220px;height:1250px;background:rgba(255,0,0,.28)"></div>'
              '<div style="position:absolute;right:0;width:35px;top:220px;height:935px;background:rgba(255,0,0,.28)"></div>'
              '<div style="position:absolute;right:0;width:100px;top:1155px;height:315px;background:rgba(255,0,0,.28)"></div></div>')
back = [h for h in html if 'class="dw back' in h]
front = [h for h in html if h not in back]
cut_layer = (f'<div id="cutwrap"><video id="cut" class="full g" src="assets/subject.webm" muted playsinline data-start="0" '
             f'data-media-start="0" data-duration="{dur:.3f}" data-track-index="1"></video></div>') if HAS_CUT else ''
nl = '\n'
page = f'''<!doctype html>
<html lang="{plan.get('language', 'pt')}" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<link rel="stylesheet" href="assets/fonts/fonts.css" />
<script src="{GSAP_SRC}"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="1080" data-height="1920">
  <audio id="bga" src="assets/aroll.mp4" data-start="0" data-media-start="0" data-duration="{dur:.3f}" data-track-index="2" data-volume="1"></audio>
{nl.join(audio)}
  <div id="stage">
    <video id="bgv" class="full g" src="assets/aroll.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{dur:.3f}" data-track-index="0"></video>
{nl.join(back)}
    {cut_layer}
    <div id="corners"><i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i></div>
  </div>
  <div id="tone" class="fx"></div><div id="vig" class="fx"></div><div id="grad" class="fx"></div>
{nl.join(front)}
{SAFE_GUIDE if SAFE else ''}
</div>
<script>
gsap.set('.g',{{filter:'{ST['grade']}'}});
{js_fmt}
const tl = gsap.timeline({{ paused: true }});
{nl.join(tw)}
tl.set({{}}, {{}}, {dur:.3f});
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
with open('index.html', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(page)
print(f'index.html: style {style}, {dur:.2f} s, {k} words/lines, {len(cards)} cards, {len(sfx)} sfx, cutout={HAS_CUT}' + (' [SAFE GUIDE ON: do not render]' if SAFE else ''))
