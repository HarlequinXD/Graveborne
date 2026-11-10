"""Shared art helpers for Graveborne.

Everything the game shows is quantised to one fixed palette with the same
ordered dither, so walls, monsters, portraits and UI all read as one hand-made set.
"""
import numpy as np
from PIL import Image

HEX = [
    # darks
    "000000", "0b0a0e", "15131a",
    # stone ramp (cool, faintly violet)
    "211e26", "2d2933", "3a3541", "48434f", "58525e", "6b6570", "807a83", "979097", "b1aaac", "cdc6c2",
    # torch / wood ramp
    "1f140e", "33200f", "4a2e17", "653f1f", "84552a", "a56f37", "c98f47", "e8b45e", "ffd98a", "fff3c8",
    # moss
    "1b2414", "2e3d1c", "4a5e2a", "6f8540",
    # blood / rust
    "330b0e", "5c1618", "8c2420", "c03a2a", "e8643a",
    # curse violet + spectral teal
    "1e0f30", "3c1d5c", "6a34a0", "1f5f5a", "35a596", "7fe8d2", "d6fff6",
    # steel
    "36404c", "56667a", "8497ab", "bccbd8",
    # bone / pale flesh
    "6e6650", "a39a7c", "d9d0b4", "f4efe0",
    "ffffff",
]
PAL = np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for h in HEX], dtype=np.float32)

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) + 0.5) / 16.0 - 0.5


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def quantize(rgb, alpha=None, spread=22.0, ox=0, oy=0):
    """rgb float HxWx3 (0..255) -> uint8 RGBA quantised to PAL with ordered dither.
    ox/oy anchor the dither pattern so sprites composited on screen share one grid."""
    h, w, _ = rgb.shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = BAYER4[(yy + oy) % 4, (xx + ox) % 4][..., None] * spread
    c = np.clip(rgb + d, 0, 255)
    # weighted nearest colour (perceptual-ish)
    wts = np.array([0.30, 0.59, 0.11], dtype=np.float32) * 3
    diff = c[:, :, None, :] - PAL[None, None, :, :]
    dist = (diff * diff * wts).sum(-1)
    idx = dist.argmin(-1)
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = PAL[idx].astype(np.uint8)
    if alpha is None:
        out[..., 3] = 255
    else:
        out[..., 3] = np.where(alpha >= 0.5, 255, 0)
        out[out[..., 3] == 0, :3] = 0
    return out


def save(arr, path):
    Image.fromarray(arr).save(path, optimize=True)


class Rng:
    def __init__(self, seed):
        self.r = np.random.default_rng(seed)

    def u(self, a=0.0, b=1.0):
        return float(self.r.uniform(a, b))

    def i(self, a, b):
        return int(self.r.integers(a, b + 1))


def value_noise(h, w, scale, seed, octaves=3):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(1, int(scale / (2 ** o)))
        gh, gw = h // s + 2, w // s + 2
        g = rng.random((gh, gw)).astype(np.float32)
        yy = np.arange(h) / s
        xx = np.arange(w) / s
        y0 = yy.astype(int); x0 = xx.astype(int)
        fy = (yy - y0)[:, None]; fx = (xx - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        v = a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
        out += v * amp; tot += amp; amp *= 0.5
    return out / tot


# ---- torchlight model shared by every pre-rendered element ----
TORCH = np.array([1.0, 0.86, 0.66], np.float32)
AMBIENT = np.array([0.035, 0.03, 0.055], np.float32)


def light_at(d):
    """Brightness of the party's torch at distance d (cells)."""
    d = np.asarray(d, np.float32)
    f = np.exp(-0.62 * np.maximum(d - 0.55, 0.0))
    f = np.where(d > 4.6, f * np.clip((5.2 - d) / 0.6, 0, 1), f)
    return f


def lit(rgb, d, face=1.0, emissive=None):
    """Apply torch falloff (and per-face shade) to albedo rgb; emissive adds unlit glow."""
    L = light_at(d)[..., None] * face
    out = rgb * (TORCH * L + AMBIENT)
    if emissive is not None:
        out = out + emissive
    return out
