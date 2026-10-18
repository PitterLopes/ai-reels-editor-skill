#!/usr/bin/env python3
"""Synthesize the skill's sound effects (no third-party audio): whoosh, pop, click, thump, sparkle.
Mono 48 kHz 16-bit WAV, deterministic (seeded). Usage: python3 sfx.py <out_dir>"""
import math
import os
import random
import struct
import sys
import wave

SR = 48000


def env(t, attack, tau):
    return min(t / attack, 1.0) * math.exp(-max(t - attack, 0.0) / tau)


def lowpass(samples, cutoff_fn):
    out, y = [], 0.0
    for i, x in enumerate(samples):
        fc = cutoff_fn(i / SR)
        a = 1.0 - math.exp(-2 * math.pi * fc / SR)
        y += a * (x - y)
        out.append(y)
    return out


def highpass(samples, fc):
    out, y, prev = [], 0.0, 0.0
    a = math.exp(-2 * math.pi * fc / SR)
    for x in samples:
        y = a * (y + x - prev)
        prev = x
        out.append(y)
    return out


def noise(n, seed):
    r = random.Random(seed)
    return [r.uniform(-1, 1) for _ in range(n)]


def whoosh(d=0.55):
    n = int(d * SR)
    x = lowpass(noise(n, 1), lambda t: 300 + 5000 * (t / d) ** 2)
    x = highpass(x, 250)
    return [v * math.sin(math.pi * min(i / n, 1.0)) ** 1.6 for i, v in enumerate(x)]


def pop(d=0.3):
    n, ph, out = int(d * SR), 0.0, []
    for i in range(n):
        t = i / SR
        f = 320 * (0.7 + 0.3 * (1 - math.exp(-t / 0.012)))
        ph += 2 * math.pi * f / SR
        out.append((math.sin(ph) + 0.2 * math.sin(2 * ph)) * env(t, 0.002, 0.07))
    return out


def click(d=0.09):
    n = int(d * SR)
    x = highpass(noise(n, 3), 1800)
    return [v * env(i / SR, 0.0008, 0.012) * 0.9 for i, v in enumerate(x)]


def thump(d=0.6):
    n, ph, out = int(d * SR), 0.0, []
    crack = highpass(noise(n, 5), 1200)
    for i in range(n):
        t = i / SR
        f = 48 + 110 * math.exp(-t / 0.03)
        ph += 2 * math.pi * f / SR
        v = math.sin(ph) * env(t, 0.002, 0.22) + crack[i] * env(t, 0.0008, 0.03) * 0.35
        out.append(math.tanh(1.5 * v))
    return out


def sparkle(d=0.9):
    n = int(d * SR)
    out = [0.0] * n
    for k, (f, t0) in enumerate(((2093, 0.0), (2637, 0.06), (3136, 0.12), (4186, 0.2))):
        for i in range(int(t0 * SR), n):
            t = i / SR - t0
            out[i] += 0.25 * math.sin(2 * math.pi * f * t) * env(t, 0.002, 0.16)
    return out


def write(path, samples, gain=0.8):
    peak = max(1e-6, max(abs(s) for s in samples))
    data = b''.join(struct.pack('<h', int(max(-1, min(1, s / peak * gain)) * 32767)) for s in samples)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data)


ALL = {'whoosh': whoosh, 'pop': pop, 'click': click, 'thump': thump, 'sparkle': sparkle}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, fn in ALL.items():
        write(os.path.join(out, name + '.wav'), fn())
        print('wrote', os.path.join(out, name + '.wav'))
