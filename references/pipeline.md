# Pipeline and files

```
<project>/
  source.json          where the original is, its size, fps, duration (never modified)
  assets/aroll.mp4     normalized cut: 1080x1920, 30 fps CFR, pauses removed, AAC audio
  work/cuts.json       the pauses removed (source in/out -> cut time), for traceability
  words.json           [{text,start,end}] on the cut video (hyperframes transcribe, whisper)
  assets/subject.webm  the speaker cut out (VP9 + alpha), only for styles that need it
  head.json            head top / x-span / body box every 0.5 s, from the cutout alpha
  plan.json            the edit, written by the AI (draft_plan.py -> edited -> validate_plan.py)
  plan.resolved.json   the plan with positions resolved by the validator
  brand.json           accent, fonts, logo (copied from template/brand.json, edited per user)
  index.html           the HyperFrames composition written by build.py (never edit by hand)
  assets/fonts/        OFL fonts fetched by setup.py; assets/sfx/ synthesized by setup.py
  renders/             every version; work/check.jpg the QA sheet
```

Steps, each one script, each idempotent (re-running overwrites its own outputs only):
1. `ingest.py <project> <video> [--lang pt] [--keep-pauses] [--pause 0.6] [--air 0.2]`
2. `cutout.py <project>` (optional) then `headpos.py <project>`
3. `draft_plan.py <project> --style <name>` → edit `plan.json` → `validate_plan.py <project>`
4. `build.py <project> [--safe]` → `hf.py <project> lint|snapshot|render ...`
5. `check.py <project> <render.mp4> [--phone]`

`hf.py` runs the pinned HyperFrames (`npx --yes hyperframes@0.8.172`) from the project folder with Node
22+, on any OS, so the skill never depends on what `npx` resolves to in the user's shell.

Timing on an M1 Mac for a 60 s clip: ingest 20 s, transcribe 30-60 s, cutout 5-8 min, build 1 s,
render 60-90 s. For 3 minutes multiply; the cutout is the slow step, run it in the background while you
plan.
