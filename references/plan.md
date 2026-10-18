# plan.json: the only thing the AI writes

The plan describes the content of the edit in seconds on the **cut video** (`assets/aroll.mp4`). The
style renders it. `draft_plan.py` writes a first version from the transcript; the editor (you) refines it;
`validate_plan.py` checks it and resolves positions.

```json
{
  "version": 1,
  "style": "impact",
  "language": "pt",
  "brand": {"accent": "#FAE67A", "ink": "#0B0B14", "display": "Inter Tight", "serif": "DM Serif Display", "text": "Inter"},
  "beats": [
    {"type": "line", "t": 0.00, "end": 1.84, "text": "todo mundo fala", "slot": "chest"},
    {"type": "word", "t": 1.48, "end": 3.10, "text": "claude", "size": "xl", "slot": "behind"},
    {"type": "word", "t": 2.40, "end": 3.10, "text": "vídeos.", "size": "big", "slot": "chest", "accent": true},
    {"type": "cut", "t": 3.10, "zoom": 1.18},
    {"type": "punch", "t": 9.40},
    {"type": "card", "t": 12.3, "end": 19.9, "kicker": "o que muda", "title": "Três pontos",
     "items": [{"t": 13.1, "text": "Planejar a semana", "mark": "check"},
               {"t": 15.0, "text": "Escolhas possíveis"},
               {"t": 17.2, "text": "Acompanhar", "mark": "cross"}]},
    {"type": "stat", "t": 24.5, "end": 29.0, "label": "por mensagem", "prefix": "R$ ", "from": 0, "to": 0.32, "decimals": 2, "bar": 1.0},
    {"type": "compare", "t": 31.0, "end": 37.0, "title": "Oferta vs aviso",
     "a": {"label": "Marketing", "value": "R$ 0,32", "num": 0.32, "bad": true},
     "b": {"label": "Utilidade", "value": "R$ 0,035", "num": 0.035, "good": true}, "ratio": "9×"}
  ]
}
```

## Beat types
| type | required | what it does |
|---|---|---|
| `line` | t, end, text | caption line (lead-in), `slot` chest (default) or top; `size` sm (default) or sm2 for long lines |
| `word` | t, end, text, size | punch word; `slot` behind (needs cutout + head.json), chest, top; `accent` true = brand color |
| `cut` | t | hard reframe held until the next `cut`; `zoom` 1.0-1.9 (default 1.18); `cx`,`cy` 0-1 (default head) |
| `punch` | t | soft punch `1.05 -> 1` on a cut of the source (no reframe) |
| `card` | t, end, title, items | presentation card (style `card`); items have `t`, `text`, optional `mark` check/cross; `kicker` optional |
| `stat` | t, end, label, to | animated number (style `data`); `from` default 0, `prefix`, `suffix`, `decimals`, `bar` 0-1 |
| `compare` | t, end, a, b | two rows with bars (style `data`); `num` scales the bars; `ratio` pill optional |

Times are seconds on the cut video. `end` must be > `t` + 0.3. Text is what was said (fix the transcript
first). Words in `word`/`line` beats must exist in `words.json` within ±0.6 s of `t` (validation warns).

## Rules the validator enforces
- **Safe zone** (layout.md): no text box above y 220 (behind-head words may start at 180, the glyphs sit
  lower), none below 1470, 35 px sides, right column clear below 1155.
- **Behind-the-head words** need `head.json`; the top is computed from the head top (layout.md). If the
  head moves more than 60 px during the word, or coverage would exceed 30% of the glyph height, the word
  is demoted to `chest` with a WARNING.
- **No overlaps** in the same slot: two `line` beats cannot overlap in `chest`; `word` and `card`/`stat`/
  `compare` beats cannot overlap each other (lines may run under a card at reduced size).
- **Pacing** (warnings): big beats (`word` xl/huge, `card`, `stat`, `compare`) at least 4 s apart; at
  most one every 6-10 s in videos over 60 s; `cut` beats at least 6 s apart.
- **Coverage**: every spoken second should have a `line` within 3 s before it (captions say what was
  said); gaps are listed.

## Editing the draft well (the creative work)
- Choose 1 punch word per sentence at most; the one that carries the stake (money, loss, number, name).
- `behind` only for short words (≤ 8 letters) with a still head; otherwise `chest` with `size: big`.
- A `card` when the speech names a list; a `stat` when it says a number; a `compare` when it contrasts
  two things. One of these per script block is plenty.
- Reframes (`cut`) at the start of a sentence, never mid-word; alternate 1.0 and 1.15-1.3.
- Remove lines that repeat the card's text; the card is the caption there.
- Long videos: silence is a tool. 30-40% of the video with nothing but the speaker and small captions is
  normal for 2-3 minutes.
