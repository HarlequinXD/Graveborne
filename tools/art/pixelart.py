"""The paint-over pass: turns a pre-rendered base into full-colour pixel art.

Textures are first painted down into the 16 colours.  Every colour sits on a
material ramp (stone, wood, moss, blood, curse, spectral); torchlight moves a pixel
down its own ramp, so stone stays stone and wood stays wood.  Between two ramp
steps we use a 2x2 checker dither, the EGA way.  Stray pixels are cleaned and each
piece gets a dark ink outline."""
import numpy as np

# Full-colour ramps, painted the pixel-art way: shadows shift cool/violet,
# highlights shift warm toward the torch.  Every ramp starts at black.
RAMP_ANCHORS = {
    "stone": ["0c0912", "2a2236", "5d5369", "9b919c", "e8dfd2"],
    "wood": ["0c0706", "321b10", "78431f", "c58644", "f8e0a6"],
    "moss": ["070a06", "1d2a13", "446022", "7b993e", "c8d484"],
    "blood": ["0d0406", "330c10", "7b1b1d", "c54830", "f2a46a"],
    "steel": ["07090d", "1b2330", "425167", "7c8e9f", "d2dce2"],
    "bone": ["0d0b08", "302a20", "6c614a", "ad9f81", "f0e6cc"],
    "fire": ["3a0e06", "9a300a", "e26a16", "fcc65a", "ffffff"],
    "curse": ["0a0612", "25103b", "572584", "9752c9", "e2b4f4"],
    "spectral": ["03100f", "0c332e", "217267", "48bba6", "d0f8ec"],
}
RAMP_LEN = 12


def _ramp(anchors, n):
    a = np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for h in anchors], np.float32)
    t = np.linspace(0, len(a) - 1, n)
    lo = np.floor(t).astype(int).clip(0, len(a) - 2)
    f = (t - lo)[:, None]
    return a[lo] * (1 - f) + a[lo + 1] * f


_cols = [np.zeros(3, np.float32)]
RAMPS = []
for name, anc in RAMP_ANCHORS.items():
    r = [0]
    for c in _ramp(anc, RAMP_LEN):
        _cols.append(np.round(c)); r.append(len(_cols) - 1)
    RAMPS.append(r)
PAL = np.array(_cols, np.float32)
NCOL = len(PAL)
PAL16 = PAL  # legacy name
INK = RAMPS[0][2]  # deep violet-black ink
PREF = np.ones(NCOL, np.float32)
for c in RAMPS[0][1:]:
    PREF[c] = 0.55
RAMP_OF = {}
for ri, r in enumerate(RAMPS):
    for p, c in enumerate(r):
        if c not in RAMP_OF:
            RAMP_OF[c] = (ri, p)

WTS = np.array([0.30, 0.59, 0.11], np.float32) * 3
BAYER2 = np.array([[0.2, 0.6], [0.8, 0.4]], np.float32)


def nearest(rgb):
    """Nearest palette colour, with stone preferred for greys so walls stay stone."""
    diff = rgb[..., None, :] - PAL
    d = (diff * diff * WTS).sum(-1) * PREF
    return d.argmin(-1)


def cleanup(idx, mask):
    """Replace orphan pixels (no 4-neighbour of the same colour) with the local majority."""
    h, w = idx.shape
    P = np.pad(idx, 1, mode="edge")
    M = np.pad(mask, 1, mode="constant")
    n = [P[0:h, 1:w + 1], P[2:h + 2, 1:w + 1], P[1:h + 1, 0:w], P[1:h + 1, 2:w + 2]]
    nm = [M[0:h, 1:w + 1], M[2:h + 2, 1:w + 1], M[1:h + 1, 0:w], M[1:h + 1, 2:w + 2]]
    same = sum(((a == idx) & m).astype(int) for a, m in zip(n, nm))
    diag = [P[0:h, 0:w], P[0:h, 2:w + 2], P[2:h + 2, 0:w], P[2:h + 2, 2:w + 2]]
    dsame = sum((a == idx).astype(int) for a in diag)
    orphan = (same == 0) & mask & (dsame < 2)
    out = idx.copy()
    if orphan.any():
        stack = np.stack(n, -1)
        best = stack[..., 0].copy()
        bestc = np.zeros_like(idx)
        for k in range(4):
            c = sum((stack[..., j] == stack[..., k]).astype(int) for j in range(4))
            upd = c > bestc
            best = np.where(upd, stack[..., k], best)
            bestc = np.where(upd, c, bestc)
        out = np.where(orphan & (bestc >= 2), best, out)
    return out


def paint_texture(rgb, emissive=None):
    """Paint an RGB albedo down to palette indices; returns (idx, glow) where glow is
    0..1 self-light (flames, spectral fire, sigils) from the emissive layer."""
    idx = nearest(rgb)
    glow = np.zeros(rgb.shape[:2], np.float32)
    if emissive is not None:
        el = (emissive * WTS / 3).sum(-1) / 255.0
        strong = el > 0.33
        eidx = nearest(np.clip(emissive, 0, 255))
        idx = np.where(strong, eidx, idx)
        glow = np.clip(el * 1.6, 0, 1.2)
    idx = cleanup(idx, np.ones(idx.shape, bool))
    return idx, glow


_ramp_ix = np.zeros(NCOL, np.int32); _ramp_pos = np.zeros(NCOL, np.int32)
for c, (r, p) in RAMP_OF.items():
    _ramp_ix[c] = r; _ramp_pos[c] = p
_ramp_tab = np.zeros((len(RAMPS), RAMP_LEN + 2), np.int32)
_ramp_len = np.array([len(r) for r in RAMPS])
for ri, r in enumerate(RAMPS):
    _ramp_tab[ri, :len(r)] = r
    _ramp_tab[ri, len(r):] = r[-1]


def light_indices(idx, steps, ox=0, oy=0):
    """Move each pixel along its material ramp by `steps` (negative = darker)."""
    r = _ramp_ix[idx]
    p = _ramp_pos[idx].astype(np.float32)
    fp = p + steps
    # dark ramp floor: everything bottoms out at ink then black
    fp = np.clip(fp, 0, _ramp_len[r] - 1)
    lo = np.floor(fp).astype(np.int32)
    frac = fp - lo
    h, w = idx.shape
    yy, xx = np.mgrid[0:h, 0:w]
    th = BAYER2[(yy + oy) % 2, (xx + ox) % 2]
    # dither only around the middle of a step; keep flat clusters elsewhere
    up = frac > (0.5 + (th - 0.5) * 0.5)
    pos = np.clip(lo + up, 0, _ramp_len[r] - 1)
    return _ramp_tab[r, pos]


def finish(idx, mask, outline=True):
    idx = cleanup(idx, mask)
    if outline:
        h, w = mask.shape
        M = np.pad(mask, 1, mode="constant")
        edge = mask & ~(M[0:h, 1:w + 1] & M[2:h + 2, 1:w + 1] & M[1:h + 1, 0:w] & M[1:h + 1, 2:w + 2])
        idx = np.where(edge & (idx != 0), INK, idx)
    out = np.zeros(idx.shape + (4,), np.uint8)
    out[..., :3] = PAL[idx].astype(np.uint8)
    out[..., 3] = np.where(mask, 255, 0)
    return out, idx
