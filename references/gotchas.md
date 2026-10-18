# Gotchas (each one cost a render)

## Timing
- Concatenating segments leaves a start offset and variable frame timing; a background cutout then
  produces a different frame count and drifts (two speakers on screen after a cut). Always re-encode
  the cut to constant 30 fps (`ingest.py` does) and assert cutout frames == aroll frames (`cutout.py`).
- A `tl.set` at a rounded time fires one frame late: nudge 2 ms early (`build.py` does).
- `hyperframes snapshot` seeks approximately; only frames pulled from the final render prove a cut.
- Whisper word starts can be 0.1-0.3 s off and it invents a leading word at a cut. The pause cutter
  confirms silences with `silencedetect` (-40 dB, 0.08 s) before trimming.
- Editing the transcript does not move times: fix the text, keep `start`/`end`.

## Rendering (HyperFrames)
- Every `<video>` and `<audio>` needs an `id` and its own `data-track-index` when they overlap, or it
  renders frozen/silent.
- Never tween `autoAlpha`/`opacity` on an element that carries `data-start`: the framework forces
  opacity on active clips. Animate a wrapper div.
- `fromTo` renders its from-state immediately: pass `immediateRender:false` for anything hidden until
  its time, and set the initial state with `gsap.set` outside the timeline.
- `autoAlpha:1` overrides a CSS opacity on the same element (a 3% overlay becomes 100%).
- Lint rejects tweening `letterSpacing`; fake tracking with `scaleX`.
- CSS `-webkit-mask-image` does not survive the renderer; bake alpha into a VP9 WebM instead.
- Element ids cannot contain apostrophes; `build.py` generates ids, never text-derived ones.
- Heavy `backdrop-filter` on many elements can black out captures; the styles use it on at most two.
- Counters: tween a plain object and write `textContent` in `onUpdate`; it renders deterministically
  because the timeline is seeked, not played.

## Audio
- Phone takes often start the audio 20-30 ms after the image; `ingest.py` re-muxes so the cut video is
  aligned, and the composition uses `aroll.mp4` for both picture and sound.
- Synthesized SFX are mono 48 kHz WAV; keep them short (< 0.8 s) and at 0.7 of their base level.

## Tools
- Node 22+ for HyperFrames; `hf.py` finds one (nvm, Homebrew, PATH) or says what to install.
- The first transcription downloads the Whisper model (~0.5 GB for `small`); the first cutout downloads
  the segmentation model (~170 MB).
- Apple Silicon runs the cutout on CoreML; elsewhere it is CPU and 2-4× slower.
- Google Fonts only serves woff2 to a browser user agent; `setup.py` sends one and keeps the latin block.
