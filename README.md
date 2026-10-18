# AI Reels Editor — a Claude Code skill that edits talking-head videos into motion-graphics Reels

**English** · [Português](README.pt-BR.md)

`reels-editor` is a [Claude Code](https://claude.com/claude-code) skill (also usable with the Claude Agent SDK) that turns a raw talking-head take into an **edited vertical video for Instagram Reels, TikTok and YouTube Shorts**: silence cuts, kinetic captions, words that appear *behind* the speaker, hard reframes (no in-and-out zoom), presentation cards, animated numbers and synthesized sound effects — rendered with [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP, open source).

The key idea: **the AI does not write animation code per video.** It writes a short *plan* (what to show, when, in which slot), the plan is validated in code, and a fixed, measured **style** turns it into a composition. Twenty styles are specified in [`references/styles.md`](references/styles.md); three are implemented today (`impact`, `card`, `data`).

> Built for the [Scriptroom](https://scriptroom.online) app ("AI script writer + teleprompter"). This repository is the open, chat-testable version of that editing concept.

## What you get

- **Cuts**: pauses above 0.6 s removed, 0.2 s of air kept, frame-accurate (CFR 30 fps).
- **Transcript with word timings** (Whisper, local) → captions never say a word that was not spoken.
- **Speaker cutout** (optional, `hyperframes remove-background`) so big words can sit **between the speaker and the background**.
- **Head tracking** from the alpha mask: words behind the head land where the head is, per second.
- **Safe zone** for Reels (top 220 px, bottom 1470 px, right column) respected by every element.
- **Hard reframes held** (1.0 → 1.18 → 1.0): never a zoom that goes in and comes back.
- **Presentation cards** (the speaker becomes a framed card, bullet points appear with the voice), **stat** and **compare** cards.
- **Synthesized SFX** (whoosh, pop, click, thump, sparkle) on their own lanes at ≤ 0.7 gain — no third-party sound libraries redistributed.
- **QA from the final render**: a contact sheet of frames at every beat, audio peaks, a 720p phone copy.

## Install

```bash
git clone https://github.com/PitterLopes/ai-reels-editor-skill ~/.claude/skills/reels-editor
cd ~/.claude/skills/reels-editor
python3 scripts/setup.py     # checks ffmpeg, node 22+, python 3.9+; fetches fonts (OFL), GSAP, synthesizes SFX
```

Requirements: `ffmpeg`/`ffprobe`, Node 22+ (HyperFrames is fetched by `npx`, pinned), Python 3.9+. The first `hyperframes transcribe` downloads a Whisper model.

Then, in Claude Code, say something like:

> *Edit this take as a Reel in the impact style: `~/Videos/take.mov`*

The skill reads [`SKILL.md`](SKILL.md) and runs the pipeline below.

## Pipeline

```
ingest.py   video → assets/aroll.mp4 (1080×1920, 30 fps, pauses cut) + words.json + work/cuts.json
cutout.py   (optional) → assets/subject.webm      headpos.py → head.json
draft_plan.py --style impact → plan.json          (the AI then refines the plan: big words, cards, stats)
validate_plan.py → plan.resolved.json             (slots, overlaps, safe zone, spoken-word check)
build.py → index.html                             hf.py lint / snapshot / render
check.py render.mp4 --phone → work/check.jpg      (look at the frames before delivering)
```

Every step is a small Python script in [`scripts/`](scripts/); the plan schema is in [`references/plan.md`](references/plan.md); layout rules in [`references/layout.md`](references/layout.md); things that bit us in [`references/gotchas.md`](references/gotchas.md).

## Styles

| Family | Styles |
|---|---|
| A — Words | Impact, Typewriter, Highlight, Stack, Glitch |
| B — Cards | Card, Steps, Checklist, Versus, Quote |
| C — Data | Data, Counter, Chart, Timeline, Map |
| D — Scene | Backdrop, Split, Frame, Window, Cinema |
| E — Brand | Minimal, Editorial, Neon, Paper, Studio |

Full specs (values, when to use, what it needs from the take): [`references/styles.md`](references/styles.md).

## Why not a prompt per video?

We tried. Two prototypes where the model wrote the animation code scored 3/10 with the person who had to post the video, cost US$ 7 each and took 25 minutes. Fixed styles with exact values + a short validated plan is what gives a consistent, professional result in minutes — and what makes the same pipeline run on a server for an app.

## License

MIT. Fonts are fetched at setup under the SIL Open Font License; HyperFrames is Apache-2.0; GSAP under its own license (free for most uses — check [gsap.com/licensing](https://gsap.com/licensing)).

Keywords: ai video editing, claude code skill, reels editor, tiktok editor, youtube shorts, auto captions, kinetic typography, talking head video, motion graphics, hyperframes, gsap, ffmpeg, whisper, opusclip alternative, submagic alternative, edição de vídeo com IA.
