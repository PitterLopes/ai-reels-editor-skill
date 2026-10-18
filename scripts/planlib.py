"""Plan rules shared by draft_plan.py, validate_plan.py and build.py."""
SIZES = {'sm': 84, 'sm2': 56, 'md': 150, 'big': 236, 'xl': 220, 'huge': 300}
BIG = ('card', 'stat', 'compare')
SAFE = {'top': 220, 'bottom': 1470, 'side': 35, 'right_col_x': 980, 'right_col_y': 1155}
CHEST_TOPS = (1010, 1100)      # alternating lead-in lines
TOP_SLOT = 240


def head_at(head, t):
    """nearest head sample at t, or None."""
    if not head:
        return None
    best = min(head, key=lambda s: abs(s['t'] - t))
    return best if best.get('head_top') is not None else None


def head_range(head, t0, t1):
    tops = [s['head_top'] for s in (head or []) if t0 - .25 <= s['t'] <= t1 + .25 and s.get('head_top') is not None]
    return (min(tops), max(tops)) if tops else None


def behind_top(head_top, size):
    """baseline 30% of the x-height below the head top: the bottom ~30% of the glyphs may be covered."""
    return int(head_top + 0.15 * size - 0.72 * size)


def resolve(plan, head, dur):
    """Fill positions, demote unreadable behind-head words, collect errors/warnings. Returns (plan, errors, warnings)."""
    errors, warnings = [], []
    beats = plan.get('beats', [])
    chest_k = 0
    for i, b in enumerate(beats):
        typ = b.get('type')
        t = float(b.get('t', -1))
        if t < 0 or t > dur:
            errors.append(f'beat {i} ({typ}): t={t} outside the video (0..{dur:.2f})'); continue
        if typ in ('line', 'word', *BIG):
            end = float(b.get('end', 0))
            if end <= t + 0.3:
                errors.append(f'beat {i} ({typ} "{b.get("text", b.get("title", ""))}"): end must be > t + 0.3')
            b['end'] = min(end, dur)
        if typ == 'line':
            b.setdefault('slot', 'chest'); b.setdefault('size', 'sm2' if len(b.get('text', '')) > 16 else 'sm')
            if b['slot'] == 'chest':
                b['top'] = CHEST_TOPS[chest_k % 2]; chest_k += 1
            else:
                b['top'] = TOP_SLOT
        elif typ == 'word':
            size = b.get('size', 'md')
            if size not in SIZES:
                errors.append(f'beat {i}: unknown size {size}'); size = 'md'
            S = SIZES[size]
            slot = b.get('slot', 'chest')
            if slot == 'behind':
                rng = head_range(head, t, b['end'])
                if not rng:
                    warnings.append(f'beat {i} "{b.get("text")}": no head.json sample (no cutout?) -> top'); slot = 'top'
                elif rng[1] - rng[0] > 60:
                    warnings.append(f'beat {i} "{b.get("text")}": head moves {rng[1] - rng[0]} px -> chest'); slot = 'chest'
                elif len(b.get('text', '')) > 9:
                    warnings.append(f'beat {i} "{b.get("text")}": too long for behind -> chest'); slot = 'chest'
                else:
                    b['top'] = max(180, behind_top(rng[0], S))
            if slot == 'chest':
                b['top'] = 1040 if S >= 150 else CHEST_TOPS[0]
            elif slot == 'top':
                b['top'] = TOP_SLOT
            b['slot'] = slot
            if b['top'] + S * 0.9 > SAFE['bottom']:
                errors.append(f'beat {i} "{b.get("text")}": below the safe zone (y {b["top"] + S * 0.9:.0f} > 1470)')
        elif typ == 'cut':
            z = float(b.get('zoom', 1.18))
            if not 1.0 <= z <= 1.9:
                errors.append(f'beat {i}: zoom {z} outside 1.0..1.9')
            b['zoom'] = z
            h = head_at(head, t)
            b.setdefault('cx', 0.5 if not h or not h.get('head_x') else round(sum(h['head_x']) / 2 / 1080, 3))
            b.setdefault('cy', 0.38 if not h else round(min(0.6, (h['head_top'] + 220) / 1920), 3))
        elif typ == 'punch':
            pass
        elif typ == 'card':
            if not b.get('title') or not isinstance(b.get('items'), list):
                errors.append(f'beat {i}: card needs title and items')
            elif len(b['items']) > 4:
                errors.append(f'beat {i}: card has {len(b["items"])} items; max 4 (it would cover the speaker) — split it')
            if len(str(b.get('title', ''))) > 34:
                warnings.append(f'beat {i}: card title has {len(b["title"])} chars; over 2 lines it pushes the speaker')
            for it in b.get('items', []):
                it.setdefault('t', t)
        elif typ == 'stat':
            if 'to' not in b:
                errors.append(f'beat {i}: stat needs "to"')
        elif typ == 'compare':
            for side in ('a', 'b'):
                if not isinstance(b.get(side), dict) or 'label' not in b[side] or 'value' not in b[side]:
                    errors.append(f'beat {i}: compare needs a/b with label and value')
        else:
            errors.append(f'beat {i}: unknown type {typ}')
    # overlaps and pacing
    timed = [b for b in beats if b.get('type') in ('line', 'word', *BIG) and 'end' in b]
    chest = sorted([b for b in timed if b['type'] == 'line' and b.get('slot') == 'chest'], key=lambda b: b['t'])
    for p, q in zip(chest, chest[1:]):
        if q['t'] < p['end'] - 0.05:
            warnings.append(f'lines overlap in chest at {q["t"]:.2f}: "{p.get("text")}" / "{q.get("text")}" (trimmed)')
            p['end'] = q['t']
    bigs = sorted([b for b in timed if b['type'] in BIG or (b['type'] == 'word' and b.get('size') in ('xl', 'huge', 'big'))],
                  key=lambda b: b['t'])
    def band(b):
        # vertical space a big beat takes: cards live in the top band; a word takes its own line
        if b['type'] in BIG:
            return (110, 900 if b['type'] == 'card' else 620)
        top = b.get('top', CHEST_TOPS[0])
        return (top, top + SIZES.get(b.get('size', 'md'), 150) * 0.95)
    for i, p in enumerate(bigs):
        for q in bigs[i + 1:]:
            if q['t'] >= p['end']:
                break
            pb, qb = band(p), band(q)
            if qb[0] < pb[1] and pb[0] < qb[1]:
                errors.append(f'big beats overlap at {q["t"]:.2f} ({p["type"]} "{p.get("text", p.get("title", ""))}" / '
                              f'{q["type"]} "{q.get("text", q.get("title", ""))}"): same place, same time')
    for p, q in zip(bigs, bigs[1:]):
        if p['end'] <= q['t'] < p['t'] + 4:
            warnings.append(f'big beats only {q["t"] - p["t"]:.1f} s apart at {q["t"]:.2f}')
    cuts = sorted(float(b['t']) for b in beats if b.get('type') == 'cut')
    for p, q in zip(cuts, cuts[1:]):
        if q - p < 6:
            warnings.append(f'reframes only {q - p:.1f} s apart at {q:.2f}')
    if dur > 60 and bigs and len(bigs) > dur / 5:
        warnings.append(f'{len(bigs)} big beats in {dur:.0f} s: more than one every 5 s reads as clutter')
    plan['beats'] = sorted(beats, key=lambda b: float(b['t']))
    return plan, errors, warnings
