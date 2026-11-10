"""Small offline synthesiser for Graveborne's music and sound effects (numpy + scipy)."""
import numpy as np
from scipy.signal import lfilter, butter, sosfilt

SR = 32000
rng = np.random.default_rng(7)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12.0)


def env(n, a=0.01, d=0.1, s=0.7, r=0.2, hold=None):
    """ADSR over n samples; hold = seconds before release (default: n - r)."""
    total = n / SR
    hold = total - r if hold is None else hold
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4),
                 np.where(t < a + d, 1 - (1 - s) * (t - a) / max(d, 1e-4), s))
    rel = np.clip((t - hold) / max(r, 1e-4), 0, 1)
    return e * (1 - rel)


def lowpass(x, fc, order=2):
    sos = butter(order, min(fc, SR / 2 * 0.95) / (SR / 2), "low", output="sos")
    return sosfilt(sos, x)


def highpass(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), "high", output="sos")
    return sosfilt(sos, x)


def bandpass(x, lo, hi, order=2):
    sos = butter(order, [lo / (SR / 2), min(hi, SR / 2 * 0.95) / (SR / 2)], "band", output="sos")
    return sosfilt(sos, x)


def additive(freq, dur, harmonics, phase_rand=True, vib=0.0, vib_rate=5.0):
    t = t_(dur)
    f = freq * (1 + vib * np.sin(2 * np.pi * vib_rate * t + rng.uniform(0, 6)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros_like(t)
    for k, amp in enumerate(harmonics, start=1):
        if freq * k > SR / 2 * 0.9:
            break
        out += amp * np.sin(k * ph + (rng.uniform(0, 6) if phase_rand else 0))
    return out


def saw(freq, dur, n=30, **kw):
    return additive(freq, dur, [1.0 / k for k in range(1, n + 1)], **kw)


def square(freq, dur, n=15, **kw):
    return additive(freq, dur, [(1.0 / k if k % 2 else 0.0) for k in range(1, n + 1)], **kw)


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


# ---------------------------------------------------------------- instruments
def pluck(freq, dur, bright=0.5, decay=0.996):
    """Karplus-Strong string (harp / lute)."""
    n = int(dur * SR)
    N = max(2, int(SR / freq))
    exc = lowpass(rng.uniform(-1, 1, N), 1500 + 6000 * bright)
    x = np.zeros(n); x[:N] = exc
    a = np.zeros(N + 2); a[0] = 1; a[N] = -0.5 * decay; a[N + 1] = -0.5 * decay
    y = lfilter([1.0], a, x)
    return y * env(n, 0.002, 0.05, 1.0, 0.08)


def pad(freq, dur, bright=900, detune=0.004, voices=3):
    out = np.zeros(int(dur * SR))
    for v in range(voices):
        out += saw(freq * (1 + detune * (v - (voices - 1) / 2)), dur, n=18, vib=0.002, vib_rate=0.3 + v * 0.1)
    out = lowpass(out / voices, bright)
    return out * env(len(out), min(1.2, dur * 0.4), 0.3, 0.85, min(1.5, dur * 0.4))


def choir(freq, dur, vowel="ah"):
    """Saw voices through vowel formants: a cold choir of the dead."""
    src = np.zeros(int(dur * SR))
    for v in range(4):
        src += saw(freq * (1 + 0.006 * (v - 1.5)), dur, n=40, vib=0.006, vib_rate=4.5 + v * 0.3)
    F = {"ah": [(700, 1.0), (1220, 0.5), (2600, 0.25)], "oo": [(320, 1.0), (800, 0.4), (2500, 0.1)],
         "eh": [(530, 1.0), (1840, 0.5), (2480, 0.2)]}[vowel]
    out = sum(g * bandpass(src, f * 0.88, f * 1.12) for f, g in F)
    return out * env(len(out), min(0.9, dur * 0.35), 0.2, 0.9, min(1.4, dur * 0.4)) * 1.6


def flute(freq, dur):
    s = additive(freq, dur, [1.0, 0.18, 0.06, 0.02], vib=0.007, vib_rate=5.2)
    breath = bandpass(noise(dur), freq * 0.8, freq * 3) * 0.12
    n = len(s)
    return (s + breath) * env(n, 0.06, 0.1, 0.8, 0.15)


def strings(freq, dur, bright=2200):
    out = np.zeros(int(dur * SR))
    for v in range(3):
        out += saw(freq * (1 + 0.003 * (v - 1)), dur, n=30, vib=0.005, vib_rate=5.5 + v * 0.4)
    out = lowpass(out / 3, bright)
    return out * env(len(out), min(0.25, dur * 0.3), 0.2, 0.8, min(0.4, dur * 0.3))


def bell(freq, dur, ratio=2.76, idx=3.0):
    t = t_(dur)
    mod = idx * np.exp(-t * 2.5) * np.sin(2 * np.pi * freq * ratio * t)
    car = np.sin(2 * np.pi * freq * t + mod)
    car += 0.3 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t * 3)
    return car * np.exp(-t * (1.6 + 200 / freq))


def cello(freq, dur):
    return strings(freq, dur, bright=900) * 1.2


def recorder(freq, dur):
    s = additive(freq, dur, [1.0, 0.35, 0.12, 0.05, 0.02], vib=0.004, vib_rate=5.8)
    return (s + bandpass(noise(dur), freq, freq * 4) * 0.06) * env(len(s), 0.03, 0.08, 0.75, 0.1)


def frame_drum(dur=0.6, pitch=110, hit=1.0):
    t = t_(dur)
    f = pitch * (1 + 1.2 * np.exp(-t * 30))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    slap = lowpass(noise(dur), 2500) * np.exp(-t * 45) * 0.5
    return (body + slap) * hit


def timpani(freq, dur=2.0):
    t = t_(dur)
    body = sum(a * np.sin(2 * np.pi * freq * r * t) for r, a in ((1, 1), (1.5, 0.4), (1.98, 0.25)))
    return (body * np.exp(-t * 2.2) + lowpass(noise(dur), 400) * np.exp(-t * 18) * 0.4)


def tambourine(dur=0.25):
    t = t_(dur)
    return highpass(noise(dur), 5000) * np.exp(-t * 22) * 0.6


# ------------------------------------------------------------------ effects
def _comb(x, d, g, damp=0.3):
    a = np.zeros(d + 1); a[0] = 1; a[d] = -g
    y = lfilter([1.0], a, x)
    return lowpass(y, 6000 * (1 - damp) + 1200)


def _allpass(x, d, g=0.5):
    b = np.zeros(d + 1); b[0] = -g; b[d] = 1
    a = np.zeros(d + 1); a[0] = 1; a[d] = -g
    return lfilter(b, a, x)


def reverb(x, size=1.0, wet=0.35, damp=0.35):
    """Stereo Schroeder reverb; x mono -> (n, 2)."""
    tail = int(SR * 2.5 * size)
    x = np.concatenate([x, np.zeros(tail)])
    outs = []
    for side, offs in ((0, 0), (1, 23)):
        combs = [1116, 1188, 1277, 1356, 1422, 1491]
        y = sum(_comb(x, int((c + offs) * size * SR / 44100), 0.84 - 0.02 * i, damp) for i, c in enumerate(combs)) / 6
        for ap in (556, 441, 341, 225):
            y = _allpass(y, int((ap + offs) * SR / 44100))
        outs.append(y)
    wetsig = np.stack(outs, -1)
    dry = np.stack([x, x], -1)
    return dry * (1 - wet) + wetsig * wet * 2.2


def pan(x, p):
    """p -1..1 -> stereo"""
    l = np.cos((p + 1) * np.pi / 4); r = np.sin((p + 1) * np.pi / 4)
    return np.stack([x * l, x * r], -1)


def normalize(x, peak=0.89):
    m = np.max(np.abs(x)) + 1e-9
    return x * (peak / m)


def soft_clip(x):
    return np.tanh(x * 1.1) / np.tanh(1.1)
