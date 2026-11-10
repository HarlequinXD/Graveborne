"""UI icons painted at 4x and brought down with majority colour, plus ink outlines."""
import numpy as np
import canvas as cv
from pixelart import paint_texture, finish


def _down(c, size, outline=True):
    k = c.w // size
    idx, _ = paint_texture(c.rgb * 1.0 + c.emi * 0.8, c.emi)
    blk = idx.reshape(size, k, size, k).transpose(0, 2, 1, 3).reshape(size, size, k * k)
    ab = c.a.reshape(size, k, size, k).mean(axis=(1, 3)) >= 0.4
    out = np.zeros((size, size), np.int64)
    for y in range(size):
        for x in range(size):
            v, cnt = np.unique(blk[y, x], return_counts=True)
            out[y, x] = v[cnt.argmax()]
    # grow mask by one pixel for the ink outline
    if outline:
        m = ab.copy()
        p = np.pad(ab, 1)
        ring = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]) & ~ab
        from pixelart import INK
        out = np.where(ring, INK, out)
        ab = ab | ring
    rgba, _ = finish(out, ab, outline=False)
    return rgba


def _arrow(kind):
    S = 64
    c = cv.Canvas(S, S)
    bone = "e8dfd2"
    if kind == "fwd":
        c.poly([(32, 8), (54, 32), (40, 32), (40, 56), (24, 56), (24, 32), (10, 32)], bone, amb=1.0, grad=(-0.5, -0.5, 0.4))
    elif kind == "back":
        c.poly([(32, 56), (54, 32), (40, 32), (40, 8), (24, 8), (24, 32), (10, 32)], bone, amb=1.0, grad=(-0.5, -0.5, 0.4))
    elif kind == "left":
        c.poly([(8, 32), (32, 10), (32, 24), (56, 24), (56, 40), (32, 40), (32, 54)], bone, amb=1.0, grad=(-0.5, -0.5, 0.4))
    elif kind == "right":
        c.poly([(56, 32), (32, 10), (32, 24), (8, 24), (8, 40), (32, 40), (32, 54)], bone, amb=1.0, grad=(-0.5, -0.5, 0.4))
    elif kind in ("turnl", "turnr"):
        r = np.hypot(c.xx - 32, c.yy - 38)
        ang = np.arctan2(c.yy - 38, c.xx - 32)
        band = (r > 12) & (r < 22) & (ang < 0.2) & (ang > -np.pi + 0.15)
        c._put(band, c.shade(bone, (c.xx - 32) / 30, (c.yy - 38) / 30, 0.8, 0.3))
        c.poly([(-2 + 44, 44), (24 + 44, 44), (11 + 44, 60)] if False else [(36, 36), (63, 36), (50, 58)], bone, amb=0.9)
        if kind == "turnl":
            c = c.flip()
    return c


def _weapon(kind):
    S = 80
    c = cv.Canvas(S, S)
    if kind == "sword":
        c.line(16, 64, 62, 14, 8, "8497ab"); c.line(17, 62, 61, 15, 2.4, "d2dce2")
        c.line(10, 54, 26, 70, 6, "c58644"); c.line(8, 72, 18, 62, 6, "4a2e17"); c.ellipse(7, 73, 4, 4, "c58644")
    elif kind == "axe":
        c.line(14, 70, 58, 14, 6, "653f1f")
        c.poly([(42, 10), (70, 20), (66, 44), (46, 30)], "8497ab", amb=1.0, grad=(-0.6, -0.6, 0.5))
        c.line(70, 20, 66, 44, 2.5, "d2dce2")
    elif kind == "spear":
        c.line(10, 72, 58, 22, 5, "84552a")
        c.poly([(56, 16), (74, 6), (64, 24), (58, 28)], "8497ab", amb=1.0, grad=(-0.6, -0.6, 0.5))
        c.line(52, 26, 58, 32, 5, "7b1b1d")
    elif kind == "xbow":
        c.line(20, 64, 60, 24, 7, "653f1f")
        r = np.hypot(c.xx - 52, c.yy - 32)
        ang = np.arctan2(c.yy - 32, c.xx - 52)
        bow = (np.abs(r - 26) < 3) & (np.abs(ang - 2.36) < 1.1)
        c._put(bow, c.shade("425167", (c.xx - 52) / 30, (c.yy - 32) / 30, 0.7, 0.5))
        c.line(34, 8, 76, 50, 1.2, "d0d0c0")
        c.line(36, 48, 70, 14, 3, "c2b496")
    elif kind == "fist":
        c.ellipse(40, 40, 18, 15, "9aa6ae", amb=0.5, k=0.7)
        for k in range(4):
            c.ellipse(28 + k * 8, 30, 5, 6, "9aa6ae", amb=0.5, k=0.7)
    return c


def _small(kind):
    S = 48
    c = cv.Canvas(S, S)
    if kind == "potion":
        c.ellipse(24, 30, 14, 14, "c54830", amb=0.6, k=0.8)
        c.rect(18, 6, 30, 18, "7c8e9f"); c.rect(16, 2, 32, 8, "a56f37")
        c.ellipse(19, 26, 3, 5, "f2a46a", flat=True)
    elif kind == "key":
        c.ellipse(14, 24, 11, 11, "c58644", amb=0.6, k=0.7)
        c.ellipse(14, 24, 5, 5, "0b0a0e", flat=True); c.a[np.hypot(c.xx - 14, c.yy - 24) < 5] = 0
        c.line(24, 24, 44, 24, 6, "c58644"); c.rect(36, 26, 40, 36, "c58644"); c.rect(42, 26, 46, 33, "c58644")
    elif kind == "skull":
        c.ellipse(24, 20, 16, 16, "e8dfd2", amb=0.6, k=0.6)
        c.ellipse(24, 34, 10, 7, "c2b496", amb=0.6, k=0.6)
        for ex in (18, 30):
            c.ellipse(ex, 22, 5, 5, "0b0a0e", flat=True)
            c.ellipse(ex, 22, 2, 2, "48bba6", flat=True, emissive="8ee5cf")
    elif kind == "use":
        c.ellipse(24, 26, 14, 16, "9aa6ae", amb=0.5, k=0.7)
        for k in range(4):
            c.ellipse(13 + k * 7, 12, 3.5, 8, "9aa6ae", amb=0.5, k=0.7)
        c.ellipse(36, 30, 4, 9, "9aa6ae", amb=0.5, k=0.7, rot=0.6)
    elif kind == "map":
        c.poly([(6, 10), (18, 6), (30, 10), (42, 6), (42, 40), (30, 44), (18, 40), (6, 44)], "c2b496", amb=1.0, grad=(-0.5, -0.5, 0.4))
        c.line(12, 34, 22, 20, 2.5, "7b1b1d"); c.line(22, 20, 34, 26, 2.5, "7b1b1d")
        c.line(32, 14, 38, 20, 2.5, "330c10"); c.line(38, 14, 32, 20, 2.5, "330c10")
    return c


def icons():
    out = {}
    for k in ("fwd", "back", "left", "right", "turnl", "turnr"):
        out[f"arr_{k}"] = _down(_arrow(k), 16)
    for k in ("sword", "axe", "spear", "xbow", "fist"):
        out[f"wpn_{k}"] = _down(_weapon(k), 20)
    for k in ("potion", "key", "skull", "use", "map"):
        out[k] = _down(_small(k), 12)
    return out
