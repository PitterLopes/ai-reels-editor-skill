---
name: reels-editor
description: "Turns one talking-head video (phone clip, 15 s to 3 min, 9:16) into an edited Reel/TikTok/Short with a chosen editing style from a catalog of 20: dead air cut, word-timed captions, kinetic words behind the head, presentation cards, animated data, sound design, Reels safe zone, frame-exact QA. The AI never writes rendering code: it writes a short plan (which words pop, where cards go) and fixed, measured styles render it with HyperFrames. Trigger with /reels-editor or phrases like 'edit this video into a reel', 'edita esse vídeo', 'faz um reel desse take', 'apply the impact style', 'legenda e motion nesse vídeo'."
---

# /reels-editor

One talking-head video in, one edited Reel out. The user picks a **style** from `references/styles.md`
(20 in the catalog; `impact`, `card` and `data` are implemented in `scripts/build.py`, the others are
specified and waiting for their build code). You never hand-write HTML or GSAP for a video: you write
`plan.json` (what pops, when, where) and the style renders it. That is what keeps every video consistent,
cheap and fast.

Read before the first edit: `references/pipeline.md` (the steps and the files they produce),
`references/plan.md` (the plan format and the validation rules), `references/layout.md` (safe zone and
the behind-the-head formula), `references/gotchas.md` (every trap already hit).

Works on macOS and Linux (Windows untested). Needs ffmpeg, Node 22+, Python 3.9+. `scripts/setup.py`
checks all three, downloads the open-licensed fonts and synthesizes the sound effects (no third-party
audio files are bundled or downloaded).

`SK` below is this skill's folder (the one holding this SKILL.md). `PY` is `python3`.

## Hard rules
1. **No free-form rendering code per video.** Everything on screen comes from `plan.json` through a
   style in `build.py`. If a style cannot express what the video needs, say so and propose a change to
   the style, never a one-off hack in the HTML.
2. **Reels safe zone**, always: nothing in the top 220 px, nothing below y 1470, 35 px off each side,
   and the right 100 px column is clear from y 1155 down. `build.py --safe` draws it; check snapshots
   with it on, render with it off.
3. **Never cover the face** (eyes to chin). Behind-the-head words keep at least ~70% of each letter
   visible; `validate_plan.py` demotes a word to the chest band when the head would hide it.
4. **Captions say what was said.** Fix the transcriber's mishearings of names, products and numbers
   from the user's script or from listening. Numbers on screen only if the speaker said them.
5. **Sound effects under the voice**, never above it (`SFX_GAIN` 0.7 of the base levels).
6. **Prove cuts and beats from the final render** (`check.py`), not from snapshots.
7. **Never delete or modify the user's original files.** Everything is written inside the project folder.

## Workflow

### 0. Setup (first run, then only after updates)
```
PY SK/scripts/setup.py
```
Follow the STATUS lines until it prints READY (it tells the exact install command for what is missing).

### 1. Intake
Ask, in one message, for what is missing: the video file, the **style** (offer the three implemented ones
with one line each; `impact` if unsure), the **brand** (accent color, optional logo; defaults in
`template/brand.json`), the language, and the names/keywords the transcriber will mishear.
Create `<projects>/<slug>/` (default `~/reel-edits/<slug>/`).

### 2. Ingest, cut dead air, transcribe
```
PY SK/scripts/ingest.py <project> <video> [--lang pt] [--keep-pauses]
```
Normalizes to 1080x1920 at 30 fps constant (mandatory before any cutout), removes pauses longer than
0.6 s (keeps 0.2 s of air), writes `assets/aroll.mp4`, `work/cuts.json` and `words.json` (word-level
times on the cut video). Read `words.json` and fix the mishearings in it before planning.

### 3. Cutout and head position (only for styles marked *needs cutout* in styles.md)
```
PY SK/scripts/cutout.py <project>       # background: ~5-8 s per second of video on Apple Silicon
PY SK/scripts/headpos.py <project>      # -> head.json: head top/x-span sampled every 0.5 s
```
Keep working on the plan while the cutout runs.

### 4. Plan
```
PY SK/scripts/draft_plan.py <project> --style impact
```
Drafts `plan.json`: caption lines grouped by pauses and punctuation, cut points as hard reframes, the
style defaults. **Then you edit it as the editor** (this is the creative work): mark the punch words
(`accent`, `size`, `slot: behind`), add `card`/`stat`/`compare` beats where the speech names a list, a
number or a comparison, and remove lines that would read as clutter. Rules in `references/plan.md`.
Pacing for long videos: one big beat every 6-10 s, never two overlapping, a reframe every 15-30 s.
```
PY SK/scripts/validate_plan.py <project>
```
Fix every ERROR; read every WARNING (safe zone, head coverage, overlaps, words not in the transcript).

### 5. Build, snapshot, render, check
```
PY SK/scripts/build.py <project> --safe     # index.html with the red safe-zone guide
PY SK/scripts/hf.py <project> lint
PY SK/scripts/hf.py <project> snapshot --at <8-12 moments> --no-end --describe false
```
Look at the snapshots: readability, safe zone, nothing on the face. Fix the plan, not the HTML. Then:
```
PY SK/scripts/build.py <project>
PY SK/scripts/hf.py <project> render -o renders/<slug>-v1.mp4 --quality high
PY SK/scripts/check.py <project> renders/<slug>-v1.mp4 --phone
```
Look at `work/check.jpg` (a frame after every cut and every beat) and the audio peaks it prints.

### 6. Deliver and iterate
Point to the phone copy (720p) and the full render. Report in plain words what the edit does and what
needs the user's call. Notes from the user ("bigger captions", "no card at 0:42", "other style for the
ending") change `plan.json` or `brand.json`, never the HTML; keep every version in `renders/`.

## Defaults that came from real feedback (do not re-litigate)
- A style is a fixed recipe; the video changes, the recipe does not. Variation comes from the content,
  the brand and the plan, not from improvised code.
- No in-and-out zoom. Reframes are hard cuts held until the next reframe, or slow push-ins.
- Dark grades keep the subject lit. No film grain. No AI-generated backgrounds.
- Lead-in captions centred in the chest band read better than lines pinned to an edge.
- Big words behind the head are the signature move, only when readable.
- Portuguese and English are first-class: the plan, the captions and the prompts work in both.
