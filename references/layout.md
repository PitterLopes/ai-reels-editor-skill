# Layout (1080x1920)

## Reels safe zone (hard)
- Top 220 px clear (platform header).
- Bottom 450 px clear: nothing below **y = 1470** (username, caption, audio row).
- 35 px clear left and right.
- Right 100 px column clear from **y = 1155** down (like / comment / share).
TikTok and Shorts are similar enough; this zone is the intersection that works on the three.

`build.py --safe` draws the unsafe area in red. Snapshot with it, render without it (the build writes
`index.html` fresh each time; the guide only exists with the flag).

## Slots
- `chest`: centred lines over the chest band, y 950-1300, never over the face.
- `top`: centred, y 240-600 (below the header, above the eyes for a typical framing).
- `behind`: behind the head (z-order below the cutout), top computed from `head.json`.
- Cards (`card`, `stat`, `compare`): top band x 60-1020, y 90-690 in `data`; in `card` style the speaker
  moves down and the card uses y 120-900.

## Behind-the-head words (readability)
`headpos.py` samples the cutout alpha every 0.5 s: head top `y`, head x-span, body box.
For a word at font-size S with line-height .9: baseline ≈ top + 0.72·S, x-height ≈ 0.5·S.
Target: the baseline sits 30% of the x-height below the head top, so at most the bottom ~30% of the
glyphs is covered: `top = head_top + 0.15·S − 0.72·S`. Example: head top 400, S = 220 → top ≈ 275.
If the head moves more than 60 px during the word, use `chest` instead.

## Reframes
A `cut` beat scales the stage around the head (`cx`, `cy` default from `head.json`, else 0.5/0.38) and
holds. Punch-ins above 1.4 need a 4K source to stay sharp; `ingest.py` keeps the original resolution in
`work/source.json` so the plan can be checked against it.

## Cut timing
Beat times that must land on an exact frame are nudged 2 ms early (`t − 0.002`) inside `build.py`, so a
`tl.set` lands on the first frame of the new shot instead of one frame late.
