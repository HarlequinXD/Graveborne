"""Graveborne sound effects, all synthesised. Run: python3 tools/audio/sfx.py <out_dir>"""
import os
import sys
import numpy as np
from synth import *  # noqa
from compose import save_ogg, n

R = np.random.default_rng(21)


def fit(x, dur):
    k = int(dur * SR)
    if len(x) >= k:
        return x[:k]
    return np.concatenate([x, np.zeros(k - len(x))])


def mix(*parts, dur=None):
    L = max(len(p) for p in parts) if dur is None else int(dur * SR)
    out = np.zeros(L)
    for p in parts:
        p = p[:L]
        out[:len(p)] += p
    return out


def at(x, sec, total):
    out = np.zeros(int(total * SR))
    i = int(sec * SR)
    e = min(len(out), i + len(x))
    out[i:e] += x[:e - i]
    return out


def edecay(dur, k):
    return np.exp(-t_(dur) * k)


def room(x, size=0.4, wet=0.25):
    y = reverb(x, size=size, wet=wet)
    return y.mean(-1)[: len(x) + int(SR * 0.6 * size)]


def burst(dur, lo, hi, k):
    return bandpass(noise(dur), lo, hi) * edecay(dur, k)


def thump(f0=70, dur=0.25, k=14, drop=2.0):
    t = t_(dur)
    f = f0 * (1 + drop * np.exp(-t * 40))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * k)


def metal(freq, dur=0.6, k=8, partials=(1, 2.32, 4.25, 6.63, 9.38)):
    t = t_(dur)
    return sum(np.sin(2 * np.pi * freq * p * t + R.uniform(0, 6)) / (1 + i) for i, p in enumerate(partials)) * np.exp(-t * k)


def voice(f0, dur, vowel="ah", glide=0.0, rough=0.0):
    t = t_(dur)
    f = f0 * (1 + glide * t / dur) * (1 + rough * lowpass(noise(dur), 30) * 3)
    src = np.zeros_like(t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    for k in range(1, 40):
        src += np.sin(k * ph) / k
    F = {"ah": [(700, 1.0), (1220, 0.5), (2600, 0.2)], "uh": [(500, 1.0), (1000, 0.4), (2400, 0.1)],
         "oo": [(320, 1.0), (800, 0.4), (2500, 0.1)], "ee": [(300, 0.8), (2300, 0.5), (3000, 0.2)]}[vowel]
    return sum(g * bandpass(src, a * 0.85, a * 1.15) for a, g in F)


def sweep_noise(dur, f0, f1, q=0.5):
    """Noise through a state-variable band-pass sweeping f0->f1 (whooshes, swishes)."""
    x = noise(dur)
    N = len(x)
    out = np.zeros(N)
    low = band = 0.0
    damp = min(2.0, q * 2)
    for i in range(N):
        fc = f0 * (f1 / f0) ** (i / N)
        f = 2 * np.sin(np.pi * min(fc, SR / 6) / SR)
        high = x[i] - low - damp * band
        band += f * high
        low += f * band
        out[i] = band
    return out * 0.7


# ------------------------------------------------------------------- library
def step_stone():
    x = mix(thump(85, 0.18, 30, 1.0) * 0.8, burst(0.12, 900, 3500, 45) * 0.5, at(burst(0.06, 1200, 4000, 60) * 0.25, 0.05, 0.2))
    return room(x, 0.5, 0.3)


def step_grass():
    x = mix(highpass(noise(0.22), 2500) * edecay(0.22, 16) * (lowpass(noise(0.22), 60) * 4 + 0.5) * 0.5,
            thump(70, 0.12, 30, 0.5) * 0.4)
    return x


def step_cobble():
    return room(mix(thump(110, 0.14, 35, 0.8) * 0.6, burst(0.05, 1500, 5000, 80) * 0.6), 0.3, 0.15)


def turn():
    s = sweep_noise(0.28, 700, 2400, 0.8) * np.hanning(int(0.28 * SR)) * 0.6
    return s


def bump():
    return room(mix(thump(60, 0.3, 12, 1.0), burst(0.1, 200, 900, 30) * 0.6), 0.4, 0.2)


def click():
    x = mix(burst(0.02, 2000, 7000, 200) * 1.0, at(burst(0.15, 300, 1500, 25) * 0.6, 0.03, 0.3), at(thump(90, 0.2, 18) * 0.7, 0.05, 0.3))
    return room(x, 0.6, 0.3)


def grind():
    d = 2.8
    t = t_(d)
    shape = np.clip(t / 0.4, 0, 1) * np.clip((d - t) / 0.8, 0, 1)
    rough = lowpass(noise(d), 18) * 3 + 1
    body = lowpass(noise(d), 700) * rough * 0.9
    rumble = np.sin(2 * np.pi * (42 + 6 * lowpass(noise(d), 3)) * t) * 0.8
    crunch = sum(at(burst(0.08, 600, 3000, 40), R.uniform(0.2, 2.4), d) for _ in range(9)) * 0.6
    return room((body + rumble + crunch) * shape, 0.9, 0.35)


def thud():
    return room(mix(thump(48, 0.9, 5, 1.5) * 1.0, burst(0.4, 100, 800, 9) * 0.7), 1.0, 0.4)


def thud_soft():
    return room(mix(thump(70, 0.4, 10, 1.0) * 0.7, burst(0.2, 150, 1000, 18) * 0.4), 0.6, 0.3)


def door():
    d = 0.9
    t = t_(d)
    f = 260 + 120 * np.sin(t * 9) + 60 * lowpass(noise(d), 12) * 5
    creak = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25
    creak = bandpass(creak, 400, 2500) * (lowpass(np.abs(noise(d)), 40) * 3) * np.clip(t / 0.1, 0, 1) * np.clip((d - t) / 0.2, 0, 1)
    chain = sum(at(metal(R.uniform(1800, 2600), 0.15, 30) * 0.15, R.uniform(0.05, 0.8), d) for _ in range(10))
    return room(creak + chain, 0.6, 0.3)


def unlock():
    return room(mix(metal(2400, 0.08, 60) * 0.5, at(metal(1900, 0.1, 50) * 0.5, 0.12, 0.4), at(thump(150, 0.15, 30) * 0.5, 0.2, 0.4)), 0.4, 0.2)


def locked():
    return room(sum(at(mix(metal(1500, 0.08, 50) * 0.4, burst(0.05, 800, 3000, 70) * 0.4), k * 0.11, 0.45) for k in range(3)), 0.4, 0.2)


def bars():
    return room(sum(at(metal(R.uniform(500, 800), 0.5, 9) * 0.35, k * 0.09 + R.uniform(0, 0.03), 0.9) for k in range(5)), 0.7, 0.35)


def key():
    return room(sum(at(metal(R.uniform(2600, 3600), 0.3, 18) * 0.3, k * 0.07, 0.6) for k in range(4)), 0.4, 0.3)


def pickup():
    return room(mix(metal(3100, 0.4, 12, (1, 2.7, 5.1)) * 0.4, at(bell(midi(n("E6")), 0.6) * 0.25, 0.05, 0.7)), 0.5, 0.3)


def drink():
    return mix(*[at(lowpass(noise(0.12), 600) * np.hanning(int(0.12 * SR)) * 0.8 + voice(110, 0.12, "oo") * 0.05, k * 0.22, 0.8) for k in range(3)])


def _chord_swell(notes, dur, vowel="ah", gain=0.25):
    return sum(choir(midi(m), dur, vowel) * gain for m in notes)


def shrine():
    x = mix(_chord_swell([n("D4"), n("F#4"), n("A4"), n("D5")], 2.4, "ah", 0.18), at(bell(midi(n("A5")), 2.0) * 0.3, 0.1, 2.4))
    return room(x, 1.2, 0.5)


def rest():
    x = mix(_chord_swell([n("G3"), n("B3"), n("D4")], 2.4, "oo", 0.2), at(bell(midi(n("G5")), 1.6) * 0.2, 0.0, 2.4),
            at(bell(midi(n("D5")), 1.6) * 0.2, 0.4, 2.4))
    return room(x, 1.0, 0.4)


def levelup():
    x = mix(*[at(bell(midi(m), 1.2) * 0.3, k * 0.12, 1.8) for k, m in enumerate([n("A4"), n("C5"), n("E5"), n("A5")])],
            at(_chord_swell([n("A3"), n("C4"), n("E4")], 1.4, "ah", 0.15), 0.3, 1.8))
    return room(x, 1.0, 0.4)


def rise():
    s = _chord_swell([n("D3"), n("A3"), n("D4")], 2.0, "oo", 0.25)
    s = s * np.linspace(0, 1, len(s)) ** 2
    return room(mix(s, at(bell(midi(n("D4")), 1.5) * 0.4, 1.6, 3.2)), 1.2, 0.5)


def start():
    return room(mix(bell(midi(n("D3")), 3.0) * 0.6, _chord_swell([n("D3"), n("A3"), n("F4")], 2.0, "ah", 0.2), timpani(midi(n("D2")), 2.0) * 0.5), 1.4, 0.5)


def stairs():
    return mix(*[at(step_stone() * (0.6 + 0.1 * k), k * 0.22, 1.5) for k in range(5)],
               bandpass(noise(1.5), 300, 1200) * np.linspace(0, 0.25, int(1.5 * SR)))


def gate():
    return mix(door() * 1.2, at(thud(), 0.7, 2.2))


def talk():
    return voice(140, 0.18, "uh", glide=0.15) * env(int(0.18 * SR), 0.02, 0.05, 0.8, 0.06) * 0.4


def swing():
    s = sweep_noise(0.22, 600, 3000, 0.6)
    return s * np.hanning(len(s)) * 0.8


def whoosh():
    s = sweep_noise(0.3, 2500, 500, 0.7)
    return s * np.hanning(len(s)) * 0.6


def xbow():
    tw = pluck(110, 0.4, bright=0.9, decay=0.99) * 1.2
    return mix(burst(0.02, 2000, 8000, 200) * 0.8, tw, at(whoosh() * 0.6, 0.03, 0.5))


def hit_sword():
    return room(mix(burst(0.08, 1500, 7000, 40) * 0.8, metal(1300, 0.4, 14) * 0.3, thump(120, 0.15, 25) * 0.6), 0.4, 0.2)


def hit_axe():
    return room(mix(thump(80, 0.25, 15, 1.5) * 1.0, burst(0.15, 400, 2500, 22) * 0.8, metal(700, 0.2, 25) * 0.2), 0.4, 0.2)


def hit_spear():
    return room(mix(burst(0.05, 2000, 6000, 60) * 0.6, thump(140, 0.15, 25) * 0.7, at(lowpass(noise(0.1), 900) * edecay(0.1, 30) * 0.5, 0.03, 0.2)), 0.4, 0.2)


def hit_xbow():
    return room(mix(thump(160, 0.12, 30) * 0.8, burst(0.05, 1000, 4000, 70) * 0.6), 0.4, 0.2)


def _clatter(count, spread, dur):
    return sum(at(mix(burst(0.04, 900, 4000, 90) * R.uniform(0.3, 0.8), thump(R.uniform(200, 500), 0.05, 60) * 0.3),
                  R.uniform(0, spread), dur) for _ in range(count))


def hurt_skeleton():
    return room(_clatter(6, 0.15, 0.35), 0.5, 0.3)


def die_skeleton():
    return room(mix(_clatter(22, 0.9, 1.3), at(thump(90, 0.3, 12) * 0.6, 0.6, 1.3)), 0.6, 0.35)


def growl_skeleton():
    return room(_clatter(10, 0.5, 0.7) * 0.7, 0.6, 0.35)


def atk_skeleton():
    return mix(swing(), at(metal(900, 0.3, 14) * 0.25, 0.15, 0.5))


def hurt_ghoul():
    return room(voice(95, 0.35, "ah", glide=-0.2, rough=0.4) * env(int(0.35 * SR), 0.01, 0.1, 0.7, 0.1) * 0.7, 0.5, 0.3)


def die_ghoul():
    return room(voice(110, 1.0, "uh", glide=-0.6, rough=0.6) * env(int(1.0 * SR), 0.02, 0.2, 0.7, 0.4) * 0.8, 0.6, 0.35)


def growl_ghoul():
    return room(voice(70, 0.9, "oo", glide=0.1, rough=0.8) * env(int(0.9 * SR), 0.2, 0.2, 0.8, 0.3) * 0.7, 0.6, 0.35)


def atk_ghoul():
    return mix(voice(120, 0.3, "ah", glide=0.2, rough=0.5) * env(int(0.3 * SR), 0.01, 0.1, 0.7, 0.1) * 0.6, at(swing() * 0.7, 0.05, 0.4))


def _wail(f0, dur, glide):
    t = t_(dur)
    f = f0 * (1 + glide * t / dur) * (1 + 0.03 * np.sin(2 * np.pi * 6 * t))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return (s * 0.5 + highpass(noise(dur), 3000) * 0.15) * env(len(t), 0.08, 0.1, 0.8, dur * 0.4)


def hurt_wraith():
    return room(_wail(900, 0.5, -0.3), 1.0, 0.5)


def die_wraith():
    return room(_wail(1100, 1.6, -0.75) * 0.9, 1.4, 0.6)


def growl_wraith():
    return room(mix(_wail(500, 1.2, 0.2) * 0.5, bandpass(noise(1.2), 1500, 5000) * env(int(1.2 * SR), 0.4, 0.2, 0.6, 0.4) * 0.4), 1.2, 0.6)


def atk_wraith():
    return room(mix(whoosh(), _wail(700, 0.4, -0.4) * 0.5), 1.0, 0.5)


def hurt_hound():
    t = t_(0.25)
    f = 900 * np.exp(-t * 4)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + voice(400, 0.25, "ee") * 0.3) * env(len(t), 0.005, 0.05, 0.7, 0.1)


def die_hound():
    t = t_(0.9)
    f = 700 * np.exp(-t * 1.5)
    return room((np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + voice(300, 0.9, "oo", glide=-0.5) * 0.3) * env(len(t), 0.01, 0.2, 0.7, 0.4), 0.5, 0.3)


def growl_hound():
    return room(voice(85, 1.0, "uh", rough=1.2) * env(int(1.0 * SR), 0.15, 0.2, 0.8, 0.3) * 0.8, 0.5, 0.3)


def atk_hound():
    bark = voice(220, 0.15, "ah", glide=-0.3, rough=0.6) * env(int(0.15 * SR), 0.005, 0.04, 0.8, 0.05)
    snap = burst(0.03, 1500, 6000, 120)
    return mix(bark * 0.8, at(snap * 0.7, 0.12, 0.3))


def ouch():
    f0 = R.uniform(95, 130)
    return voice(f0, 0.28, "uh", glide=-0.25, rough=0.2) * env(int(0.28 * SR), 0.01, 0.08, 0.7, 0.1) * 0.7


def fall():
    return room(mix(voice(110, 1.1, "ah", glide=-0.5, rough=0.3) * env(int(1.1 * SR), 0.02, 0.3, 0.6, 0.4) * 0.6,
                    at(thump(60, 0.4, 10) * 0.8, 0.9, 1.4)), 0.7, 0.35)


SFX = {k: v for k, v in dict(globals()).items() if callable(v) and v.__module__ == __name__ and not k.startswith("_")
       and k not in ("fit", "mix", "at", "edecay", "room", "burst", "thump", "metal", "voice", "sweep_noise")}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    total = 0
    for name, fn in SFX.items():
        x = fn()
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.85
        fade = min(len(x), int(0.02 * SR))
        x[-fade:] *= np.linspace(1, 0, fade)
        save_ogg(np.stack([x, x], -1)[:, :1], os.path.join(out, name + ".ogg"), q=3)
        total += os.path.getsize(os.path.join(out, name + ".ogg"))
    print(len(SFX), "sfx", total // 1024, "KB")
