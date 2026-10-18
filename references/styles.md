# Style catalog (20)

A style is a fixed, measured recipe in `scripts/build.py`: fonts, sizes, grade, motion, transitions,
sound. The plan (`plan.json`) only says *what* the video contains; the style decides *how it looks*.
The user's brand (`brand.json`: accent color, fonts, logo) is applied on top of any style, so two
creators using the same style do not look the same.

**Status:** `impact`, `card` and `data` are implemented. The other 17 are specified here so the plan
format and the build code can grow without changing the pipeline. Contributions welcome: one style = one
`render_<style>()` in `build.py` plus its entry below.

Legend: *needs cutout* = the speaker is cut out of the background (`cutout.py`), which costs
~5-8 s per second of video on Apple Silicon; plan the time.

## Family A: kinetic (letters in motion)
What the AI decides: which words pop and how big.

### 1. `impact` (implemented, needs cutout)
Giant lowercase words, the biggest ones **behind the head**; lead-in lines centred in the chest band;
one accent word per sentence in the brand color.
- Type: Inter Tight 900, lowercase, letter-spacing -.05em, line-height .9, white, soft shadow.
  Sizes: `sm` 84 (lead-in), `sm2` 56 (long lead-in), `md` 150, `big` 236, `xl` 220 (behind), `huge` 300.
- Grade: `contrast(1.06) saturate(.92) brightness(.98)`, soft-light cool/warm tone, light vignette,
  dark gradients top and bottom for legibility.
- Motion: each word blur-pops in on its frame (`scale 1.18, blur 18px -> 1, 0`, .22 s, expo.out);
  groups blur out (.14 s) and are hard-killed. Every hard cut gets a punch (`scale 1.05 -> 1`, .32 s).
- Sound: `pop` on xl/huge words, `whoosh` on reframes, all at 0.7 gain.

### 2. `headline` (spec)
Keyword in wide uppercase crossing the screen (slide through with motion blur), hard background color
cuts in the rhythm of speech (ink / accent / white), speaker on a cutout when the background is solid.
For launches and ads. *needs cutout* for the solid-background beats.

### 3. `strike` (spec)
The wrong word enters, gets struck through and replaced by the right one; the key sentence switches to
a serif italic. For myth-busting. No cutout.

### 4. `stamp` (spec)
Tilted stamps/pills with the spoken word, popping in with a click, 2-4 per sentence max. For lists of
mistakes and warnings. No cutout.

### 5. `typed` (spec)
Text appears letter by letter (one span per character, revealed with `tl.set`), code/terminal backdrop
cards. For tech and tutorials. No cutout.

## Family B: presentation (the speaker leaves the frame)
What the AI decides: which script blocks become a scene and what each scene shows.

### 6. `card` (implemented, no cutout)
When a `card` beat is active the speaker shrinks into a rounded frame with camera corners in the
bottom 62% of the frame, and a presentation card takes the top band: a kicker, a title and up to 5
items that light up on their spoken word (ticks/crosses optional). Outside card beats: full frame with
chest-band captions.
- Card: glass dark `rgba(12,12,20,.88)`, radius 32, 2 px border at 16% white, big soft shadow.
- Type: title DM Serif Display 92, items Inter 46, kicker Inter 600 32 uppercase tracked.
- Transition: stage scales to .62 and slides down in .45 s (power3.inOut); back the same way.
- Sound: `whoosh` on the transition, `click` on each item.

### 7. `avatar` (spec)
The speaker becomes a round avatar in the corner; the whole frame presents numbered steps. For
step-by-step. No cutout.

### 8. `layers3d` (spec, needs cutout)
Glass panels in perspective, elements passing behind and in front of the speaker, "depth" reveals. For
product showcases.

### 9. `scenes` (spec, needs cutout)
The original background is replaced per beat: city at night, solid brand color, neon grid. "One take,
three sets." For a static take that needs variety.

## Family C: editorial and cinema
What the AI decides: where to reframe and which sentence becomes a chapter title.

### 10. `studio` (spec, needs cutout)
Dark room, lit subject (the cutout gets its own lighter grade), tiny wide-tracked caps + big serif
words rising from a mask, slow push-ins instead of punches, wide/close alternation. For authority.

### 11. `warm` (spec)
Sepia/warm grade, serif italic in the accent color, small sparkles, soft vignette. For lifestyle,
aesthetics and wellness. No cutout.

### 12. `news` (spec)
Lower-third band with the name, a ticker, a source card and a date. For trending topics and politics.
No cutout.

### 13. `documentary` (spec)
Desaturated grade, small classic captions, serif chapter titles, very slow push-in. For stories and
cases. No cutout.

## Family D: data and B-roll
What the AI decides: which number, comparison or screen illustrates a sentence, only with numbers the
speaker said.

### 14. `data` (implemented, no cutout)
Glass cards in the top band (y 90-690) with animated numbers: `stat` (label, counter, bar) and `compare`
(two rows with bars, a "×" ratio pill), while the speaker stays full frame with chest-band captions.
- Card as in `card`; values in DM Serif Display 120, labels Inter 36.
- Counters tween a plain object and write `textContent`; bars grow from the left (`scaleX`), .9 s
  power3.out; the card slides in from y+40 with blur, out the same way.
- Sound: `click` on each value, `whoosh` on the card.

### 15. `checklist` (spec)
A process card with icons lighting up on speech, items ticked or crossed, numbered progress
("01/03"). For methods and stages. No cutout.

### 16. `appscreen` (spec)
Simulated chat, notification and app screens beside the speaker (built from the plan, never from
copied logos). For tools and services. No cutout.

### 17. `broll` (spec)
Cutaways to stock footage with the voice over and captions (`broll` beats name the scene; footage
comes from a licensed library the user configures). For explanations and health. No cutout.

## Family E: minimal
What the AI decides: little, only caption emphasis and zoom cadence.

### 18. `captions` (spec)
Word-by-word captions with highlight, one zoom per script block, nothing else. For speed. No cutout.

### 19. `clean` (spec)
Discreet captions and a source card for regulated professions (doctors, lawyers, accountants), where
heavy effects cost credibility. No cutout.

### 20. `podcast` (spec)
Alternating reframes, progress bar, name and @ in a lower third, a camera frame with REC. For interviews
and conversation. No cutout.

## Choosing for the user
- Opinion / hook-driven: `impact`. Lists and tips: `card`. Numbers, prices, comparisons: `data`.
- Long videos (2-3 min): fewer big beats per minute than a 25 s reel; the style's pacing rule in
  `plan.md` applies.
- Regulated professions: `clean` once implemented; until then `card` without accent words.
