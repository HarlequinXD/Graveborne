"""Graveborne's scores. Each track is a seamless loop (the reverb tail is folded back
onto the start). Run: python3 tools/audio/compose.py <out_dir> [track ...]"""
import os
import sys
import subprocess
import numpy as np
from synth import *  # noqa

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
        "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def n(name):
    """'A4' -> midi"""
    p, o = name[:-1], int(name[-1])
    return 12 * (o + 1) + NOTE[p]


CHORDS = {  # root, intervals
    "m": (0, 3, 7), "M": (0, 4, 7), "sus": (0, 5, 7), "m7": (0, 3, 7, 10), "7": (0, 4, 7, 10),
}


def chord(sym, octave=3):
    root = sym.rstrip("mM7sus") or sym
    qual = sym[len(root):] or "M"
    r = 12 * (octave + 1) + NOTE[root]
    return [r + i for i in CHORDS[qual]]


class Track:
    def __init__(self, bpm, bars, beats=4):
        self.bpm, self.beat = bpm, 60.0 / bpm
        self.L = int(bars * beats * self.beat * SR)
        self.tail = int(SR * 4)
        self.dry = np.zeros((self.L + self.tail, 2))
        self.send = np.zeros(self.L + self.tail)

    def add(self, sig, beat, gain=1.0, p=0.0, send=0.4):
        i = int(beat * self.beat * SR)
        if i >= self.L:
            return
        sig = sig * gain
        end = min(i + len(sig), len(self.send))
        sig = sig[:end - i]
        self.dry[i:end] += pan(sig, p)
        self.send[i:end] += sig * send

    def note(self, inst, m, beat, dur_beats, gain=1.0, p=0.0, send=0.4, **kw):
        self.add(inst(midi(m), dur_beats * self.beat, **kw), beat, gain, p, send)

    def render(self, size=1.0, wet=0.5, damp=0.35):
        rv = reverb(self.send, size=size, wet=1.0, damp=damp)[: len(self.send)]
        mix = self.dry + rv * wet
        # fold the tail so the loop is seamless
        out = mix[: self.L].copy()
        out[: self.tail] += mix[self.L: self.L + self.tail]
        out = soft_clip(normalize(out, 0.95)) * 0.9
        return out


def save_ogg(stereo, path, q=4):
    import wave
    tmp = path + ".wav"
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    with wave.open(tmp, "wb") as w:
        w.setnchannels(pcm.shape[1] if pcm.ndim == 2 else 1)
        w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", str(q), path], check=True)
    os.remove(tmp)


def melody(tr, inst, notes, start_beat, gain, p=0.0, send=0.45, **kw):
    """notes: list of (name or None, beats)"""
    b = start_beat
    for nm, d in notes:
        if nm:
            tr.note(inst, n(nm), b, d * 1.05, gain, p, send, **kw)
        b += d
    return b


def arp(tr, chord_notes, start, beats, step=0.5, pattern=(0, 1, 2, 1), gain=0.25, p=0.3, oct_up=12, bright=0.5):
    k = 0
    b = start
    while b < start + beats - 1e-6:
        idx = pattern[k % len(pattern)]
        m = chord_notes[idx % len(chord_notes)] + (oct_up if idx >= len(chord_notes) else 0) + 12
        tr.note(pluck, m, b, 2.0, gain * (1.0 if k % 4 == 0 else 0.8), p, 0.5, bright=bright)
        b += step; k += 1


# ===================================================================== tracks
def title():
    tr = Track(66, 16)
    prog = ["Dm", "Bb", "Gm", "A", "Dm", "Bb", "C", "A", "F", "C", "Dm", "Bb", "Gm", "A", "Dm", "Dm"]
    for bar, c in enumerate(prog):
        b = bar * 4
        notes = chord(c, 3)
        for k, m in enumerate(notes):
            tr.note(choir, m + 12, b, 4.2, 0.22, -0.4 + 0.4 * k, 0.6, vowel="ah" if bar % 4 < 2 else "oo")
        tr.note(cello, notes[0] - 12, b, 4.0, 0.45, 0.0, 0.3)
        arp(tr, notes, b, 4, step=0.5, pattern=(0, 1, 2, 3, 2, 1), gain=0.12, p=0.45)
        if bar % 4 == 0:
            tr.note(bell, n("D5"), b, 6, 0.25, -0.3, 0.7)
        if bar % 2 == 0:
            tr.note(bell, n("D3"), b, 6, 0.35, 0.2, 0.6)
    mel = [("A4", 2), ("F4", 1), ("G4", 1), ("A4", 1.5), ("Bb4", .5), ("A4", 1), ("G4", 1), ("F4", 2), ("E4", 1), ("D4", 1), ("E4", 4),
           ("C5", 2), ("A4", 1), ("F4", 1), ("G4", 2), ("E4", 2), ("F4", 1), ("G4", 1), ("A4", 1), ("D5", 1), ("D5", 3), ("C5", 1),
           ("Bb4", 2), ("A4", 1), ("G4", 1), ("A4", 2), ("E4", 2), ("D4", 4)]
    melody(tr, strings, mel, 16, 0.32, 0.1, 0.5)
    melody(tr, flute, [(a, d) for a, d in mel[11:]], 32 + 0.0, 0.18, -0.2, 0.5)
    for k in range(8):
        tr.note(timpani, n("A1"), 60 + k * 0.5, 1.0, 0.18 + 0.05 * k, 0, 0.3)
    return tr.render(size=1.2, wet=0.6)


def dungeon():
    tr = Track(52, 24)
    L = 24 * 4
    tr.note(pad, n("A1"), 0, L, 0.4, -0.2, 0.5, bright=400)
    tr.note(pad, n("E2"), 0, L, 0.25, 0.2, 0.5, bright=500)
    prog = ["Am", "Bb", "Am", "Gm", "Am", "F", "Gm", "Am", "Bb", "Gm", "F", "E"]
    r = np.random.default_rng(3)
    for i, c in enumerate(prog):
        b = i * 8
        notes = chord(c, 3)
        tr.note(strings, notes[0] - 12, b, 8, 0.25, -0.3, 0.6, bright=700)
        tr.note(strings, notes[2] - 12, b + 2, 6, 0.15, 0.3, 0.6, bright=700)
        # sparse harp figures
        for k in range(r.integers(3, 6)):
            bb = b + float(r.integers(0, 14)) * 0.5
            m = notes[r.integers(0, 3)] + 12 * int(r.integers(1, 3))
            tr.note(pluck, m, bb, 3, 0.2, float(r.uniform(-0.7, 0.7)), 0.8, bright=0.35, decay=0.997)
        if i % 4 == 0:
            for k, m in enumerate(notes):
                tr.note(choir, m + 12, b + 1, 7, 0.12, -0.5 + 0.5 * k, 0.8, vowel="oo")
            tr.note(timpani, n("A1"), b, 3, 0.4, 0, 0.5)
    # water drips in the dark
    for k in range(26):
        bb = float(r.uniform(0, L - 2))
        tr.note(bell, int(r.integers(84, 96)), bb, 1.5, 0.05, float(r.uniform(-0.8, 0.8)), 1.0, ratio=1.0, idx=0.3)
    # a low cello lament in the middle
    lam = [("A2", 4), ("C3", 2), ("B2", 2), ("A2", 4), ("G2", 4), ("F2", 6), ("E2", 2), ("A2", 8)]
    melody(tr, cello, lam, 32, 0.32, 0.0, 0.5)
    melody(tr, cello, lam, 64, 0.28, 0.1, 0.5)
    return tr.render(size=1.6, wet=0.75, damp=0.45)


def forest():
    tr = Track(80, 32)
    prog = ["Em", "A", "Em", "D", "C", "D", "Em", "Em", "G", "D", "Em", "A", "C", "D", "Bm", "Em"]
    for i, c in enumerate(prog):
        b = i * 8
        notes = chord(c, 3)
        for k, m in enumerate(notes):
            tr.note(pad, m + 12, b, 8.2, 0.12, -0.5 + 0.5 * k, 0.5, bright=1400)
        tr.note(cello, notes[0] - 12, b, 4, 0.3, 0, 0.3)
        tr.note(cello, notes[2] - 12, b + 4, 4, 0.25, 0, 0.3)
        arp(tr, notes, b, 8, step=0.5, pattern=(0, 2, 3, 1, 2, 0, 3, 2), gain=0.13, p=0.4, bright=0.6)
        if i >= 4:
            for bt in range(8):
                hit = 0.5 if bt % 4 == 0 else (0.25 if bt % 2 == 0 else 0.1)
                tr.add(frame_drum(0.5, 95 if bt % 4 == 0 else 140, hit), b + bt, 0.5, 0.0, 0.3)
    A = [("E5", 2), ("D5", 1), ("B4", 1), ("A4", 1), ("B4", 1), ("D5", 2), ("E5", 1), ("F#5", 1), ("E5", 1), ("D5", 1), ("B4", 4)]
    B = [("G5", 1), ("F#5", 1), ("E5", 1), ("D5", 1), ("E5", 2), ("B4", 1), ("A4", 1), ("B4", 1), ("D5", 1), ("E5", 1), ("F#5", 1), ("E5", 4)]
    b = 32
    for ph in (A, B, A, B):
        b = melody(tr, flute, ph, b, 0.3, 0.15, 0.5)
        b += 0
    melody(tr, flute, [("B5", 8), ("A5", 8), ("G5", 8), ("E5", 8)], 96, 0.16, -0.2, 0.7)
    # crickets
    r = np.random.default_rng(11)
    for k in range(60):
        bb = float(r.uniform(0, 127)); f = float(r.uniform(4200, 5200)); pp = float(r.uniform(-0.9, 0.9))
        for j in range(3):
            t = t_(0.03)
            tr.add(np.sin(2 * np.pi * f * t) * np.hanning(len(t)) * 0.04, bb + j * 0.1, 1.0, pp, 0.2)
    return tr.render(size=1.0, wet=0.45)


def town():
    tr = Track(96, 32)
    prog = ["G", "D", "Em", "C", "G", "D", "C", "D", "Em", "C", "G", "D", "Em", "C", "D", "D"] * 2
    for i, c in enumerate(prog):
        b = i * 4
        notes = chord(c, 3)
        arp(tr, notes, b, 4, step=0.5, pattern=(0, 1, 2, 3, 2, 1, 0, 2), gain=0.18, p=-0.35, bright=0.8)
        tr.note(cello, notes[0] - 12, b, 2, 0.32, 0.1, 0.3)
        tr.note(cello, notes[2] - 12, b + 2, 2, 0.26, 0.1, 0.3)
        tr.add(frame_drum(0.4, 120, 0.5), b, 0.45, 0, 0.2)
        tr.add(tambourine(), b + 1, 0.35, 0.4, 0.15)
        tr.add(tambourine(), b + 3, 0.35, 0.4, 0.15)
        if i in (0, 16):
            for k, m in enumerate(notes):
                tr.note(pad, m + 12, b, 16, 0.08, -0.4 + 0.4 * k, 0.5, bright=1600)
    A = [("B4", 2), ("D5", 1), ("B4", 1), ("A4", 2), ("G4", 2), ("G4", 1), ("A4", 1), ("B4", 1), ("D5", 1), ("E5", 2), ("D5", 2),
         ("B4", 2), ("A4", 1), ("G4", 1), ("A4", 2), ("B4", 1), ("A4", 1), ("G4", 2), ("E4", 2), ("D4", 4)]
    B = [("E5", 2), ("G5", 2), ("F#5", 1), ("E5", 1), ("D5", 2), ("C5", 2), ("E5", 2), ("D5", 2), ("B4", 2),
         ("A4", 1), ("B4", 1), ("C5", 2), ("B4", 1), ("A4", 1), ("G4", 2), ("A4", 2), ("A4", 4), (None, 4)]
    b = 0
    b = melody(tr, recorder, A, 16, 0.3, 0.2, 0.45)
    b = melody(tr, recorder, B, 48, 0.3, 0.2, 0.45)
    b = melody(tr, recorder, A, 80, 0.3, 0.2, 0.45)
    b = melody(tr, recorder, B, 112, 0.28, 0.2, 0.45)
    tr.note(bell, n("G5"), 64, 4, 0.18, -0.5, 0.7)
    tr.note(bell, n("D5"), 65, 4, 0.15, -0.5, 0.7)
    return tr.render(size=0.8, wet=0.35)


def death():
    tr = Track(60, 3)
    for k, m in enumerate(["D4", "C4", "Bb3", "A3"]):
        tr.note(choir, n(m), k * 1.5, 3, 0.4, -0.2, 0.7, vowel="oo")
        tr.note(choir, n(m) - 12, k * 1.5, 3, 0.3, 0.2, 0.7, vowel="oo")
    tr.note(timpani, n("D2"), 0, 3, 0.6, 0, 0.5)
    tr.note(bell, n("D3"), 6, 6, 0.5, 0, 0.8)
    # not a loop: render with the tail appended
    rv = reverb(tr.send, size=1.4, wet=1.0)[: len(tr.send)]
    mix = tr.dry + rv * 0.7
    return soft_clip(normalize(mix, 0.95)) * 0.9


TRACKS = {"title": title, "dungeon": dungeon, "forest": forest, "town": town, "death": death}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    names = sys.argv[2:] or list(TRACKS)
    for k in names:
        audio = TRACKS[k]()
        save_ogg(audio, os.path.join(out, k + ".ogg"), q=3)
        print(k, f"{len(audio) / SR:.1f}s", os.path.getsize(os.path.join(out, k + ".ogg")) // 1024, "KB", flush=True)
