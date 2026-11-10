"""Monsters and floor items, painted large then pre-rendered at every distance."""
import numpy as np
from canvas import Canvas
from common import value_noise

MW, MH = 96, 128   # monster canvas = 0.75 x 1.0 cell


def _noise_tex(c, m, amt, seed, scale=3):
    n = value_noise(c.h, c.w, scale, seed, 2)
    c.rgb[m] *= (1 - amt / 2 + amt * n[m])[:, None]


# ------------------------------------------------------------------ skeleton
def skeleton(frame="idle"):
    c = Canvas(MW, MH)
    bone, bone_d = "d9d0b4", "a39a7c"
    bob = 1 if frame == "idle2" else 0
    atk = frame == "attack"
    # legs
    for s in (-1, 1):
        hx = 48 + s * 7
        c.capsule(hx, 90, hx + s * 3, 106, 3.2, bone, 2.6)
        c.capsule(hx + s * 3, 106, hx + s * 2, 122, 2.6, bone, 2.2)
        c.ellipse(hx + s * 2, 106, 3.5, 3, bone)
        c.ellipse(hx + s * 2 + s * 3, 124, 6, 2.6, bone_d)
    # tattered loincloth
    c.poly([(36, 84 + bob), (60, 84 + bob), (58, 102), (54, 96), (50, 104), (45, 95), (40, 101)], "5c1618", amb=1.0, grad=(-0.6, -0.8, 0.6))
    # pelvis
    c.ellipse(48, 86 + bob, 13, 6, bone)
    c.ellipse(43, 87 + bob, 3, 2.5, "15131a", flat=True)
    c.ellipse(53, 87 + bob, 3, 2.5, "15131a", flat=True)
    # spine
    for i in range(5):
        c.ellipse(48, 72 + bob + i * 3, 2.6, 1.6, bone)
    # ribcage
    rc = c.ellipse(48, 58 + bob, 15, 15, bone)
    for i, yy in enumerate(range(48, 72, 5)):
        gap = (np.abs(c.yy - (yy + bob) - 2) < 1.2) & rc & (np.abs(c.xx - 48) > 2.5)
        c.rgb[gap] = np.array([21, 19, 26], np.float32)
    c.capsule(48, 46 + bob, 48, 70 + bob, 2.2, bone)
    inner = c.ellipse(48, 60 + bob, 4, 9, "15131a", flat=True) if False else None
    # shoulders
    c.capsule(34, 46 + bob, 62, 46 + bob, 3.0, bone)
    # left arm with round shield
    c.capsule(34, 47 + bob, 28, 64 + bob, 3, bone, 2.5)
    c.capsule(28, 64 + bob, 30, 78 + bob, 2.5, bone, 2.2)
    sh = c.ellipse(26, 72 + bob, 12, 14, "56667a", amb=0.6, k=0.7)
    _noise_tex(c, sh, 0.5, 5)
    rim = sh & ~(((c.xx - 26) / 10) ** 2 + ((c.yy - 72 - bob) / 12) ** 2 <= 1)
    c.rgb[rim] = np.array([132, 151, 171], np.float32)
    c.ellipse(26, 72 + bob, 3, 3, "8497ab")
    rust = sh & (value_noise(MH, MW, 4, 9, 2) > 0.6)
    c.rgb[rust] = c.rgb[rust] * 0.4 + np.array([123, 27, 29]) * 0.5
    # right arm + sword
    if not atk:
        c.capsule(62, 47 + bob, 68, 64 + bob, 3, bone, 2.5)
        c.capsule(68, 64 + bob, 70, 80 + bob, 2.5, bone, 2.2)
        c.ellipse(70, 81 + bob, 3, 3, bone)
        c.line(70, 80 + bob, 82, 40 + bob, 4.2, "8497ab")
        c.line(70.6, 80 + bob, 82.6, 40 + bob, 1.2, "d2dce2")
        c.line(64, 79 + bob, 77, 83 + bob, 3, "653f1f")
        c.line(70, 81 + bob, 68, 88 + bob, 2.6, "4a2e17")
    else:
        c.capsule(62, 47, 70, 32, 3, bone, 2.5)
        c.capsule(70, 32, 62, 18, 2.5, bone, 2.2)
        c.ellipse(61, 17, 3, 3, bone)
        c.line(60, 17, 24, 6, 4.4, "8497ab")
        c.line(60, 16, 24, 5, 1.2, "d2dce2")
        c.line(58, 11, 63, 23, 3, "653f1f")
        for k in range(4):  # motion streak
            c.line(26 + k * 2, 10 + k * 5, 18 + k * 4, 24 + k * 6, 1.0, "b1aaac")
    # skull
    c.ellipse(48, 26 + bob, 11, 12, bone, amb=0.6, k=0.6)
    c.ellipse(48, 37 + bob, 7.5, 4.5, bone_d)
    for ex in (43.5, 52.5):
        c.ellipse(ex, 27 + bob, 3.6, 3.2, "0b0a0e", flat=True)
        c.ellipse(ex, 27 + bob, 1.6, 1.6, "48bba6", flat=True, emissive="64d2ba")
    c.poly([(47, 31 + bob), (49, 31 + bob), (48, 34 + bob)], "15131a", amb=1.0)
    for tx in range(43, 54, 2):
        c.rect(tx, 37 + bob, tx + 1, 39 + bob, "f4efe0")
    # dented helm
    hx, hy_ = (c.xx - 48) / 12.5, (c.yy - 22 - bob) / 9
    hm = (hx * hx + hy_ * hy_ <= 1) & (c.yy < 20 + bob)
    c._put(hm, c.shade("425167", hx * 0.9, hy_ * 0.9, 0.6, 0.7))
    c.rgb[(c.yy >= 20 + bob) & (c.yy < 22 + bob) & (np.abs(c.xx - 48) < 13) & (c.a > 0)] = np.array([86, 102, 122], np.float32)
    c.glow(43.5, 27 + bob, 3, "48bba6", 0.4)
    c.glow(52.5, 27 + bob, 3, "48bba6", 0.4)
    return c


# --------------------------------------------------------------------- ghoul
def ghoul(frame="idle"):
    c = Canvas(MW, MH)
    flesh, flesh_d = "9aa58a", "5f6a52"
    atk = frame == "attack"
    bob = 1 if frame == "idle2" else 0
    # legs, bent
    for s in (-1, 1):
        c.capsule(48 + s * 9, 92, 48 + s * 15, 106, 5, flesh_d, 4)
        c.capsule(48 + s * 15, 106, 48 + s * 11, 122, 4, flesh_d, 3)
        c.ellipse(48 + s * 13, 124, 7, 3, "4a5e2a")
    c.poly([(34, 86), (62, 86), (64, 100), (56, 96), (50, 102), (44, 97), (33, 100)], "33200f", amb=1.0, grad=(-0.5, -0.8, 0.6))
    # hunched torso
    t = c.capsule(48, 56 + bob, 48, 84, 14, flesh, 9, amb=0.5, k=0.7)
    _noise_tex(c, t, 0.35, 11, 4)
    for i in range(5):
        rib = t & (np.abs(c.yy - (58 + bob + i * 5)) < 0.9) & (np.abs(c.xx - 48) > 3) & (np.abs(c.xx - 48) < 12 - i)
        c.rgb[rib] *= 0.55
    c.capsule(48, 84, 48, 88, 3, flesh_d)
    c.ellipse(48, 52 + bob, 17, 8, flesh, amb=0.5, k=0.7)  # shoulders hunched up
    # long arms
    if not atk:
        for s in (-1, 1):
            c.capsule(48 + s * 15, 54 + bob, 48 + s * 24, 80 + bob, 4.5, flesh, 3.5)
            c.capsule(48 + s * 24, 80 + bob, 48 + s * 22, 104 + bob, 3.5, flesh, 3)
            for k in (-2, 0, 2):
                c.line(48 + s * 22 + k, 104 + bob, 48 + s * 22 + k * 2, 113 + bob, 1.3, "d9d0b4")
    else:
        for s in (-1, 1):
            c.capsule(48 + s * 15, 54, 48 + s * 30, 40, 4.5, flesh, 3.5)
            c.capsule(48 + s * 30, 40, 48 + s * 22, 20, 3.5, flesh, 3)
            for k in (-2, 0, 2):
                c.line(48 + s * 22 + k, 20, 48 + s * 18 + k * 2, 10, 1.3, "d9d0b4")
    # head, thrust forward and low
    hy = 44 + bob + (4 if atk else 0)
    hd = c.ellipse(48, hy, 11, 11, flesh, amb=0.55, k=0.6)
    _noise_tex(c, hd, 0.3, 13)
    c.ellipse(48, hy - 6, 10, 5, "3a3541", amb=0.6)  # lank hair
    for s in (-1, 1):
        c.line(48 + s * 6, hy - 6, 48 + s * 10, hy + 6, 1.4, "2d2933")
    for ex in (44, 52):
        c.ellipse(ex, hy, 2.6, 2.2, "fcc65a", flat=True, emissive="fcc65a")
    mouth = c.ellipse(48, hy + 6, 6, 3.5 + (2 if atk else 0), "330c10", flat=True)
    for tx in range(43, 53, 2):
        c.line(tx + 0.5, hy + 4, tx + 0.5, hy + 6, 1.0, "f0e6cc")
    c.glow(44, hy, 3, "f8ab3a", 0.5)
    c.glow(52, hy, 3, "f8ab3a", 0.5)
    # blood
    blood = (value_noise(MH, MW, 3, 17, 2) > 0.66) & (c.a > 0) & (c.yy > hy + 4) & (c.yy < 70)
    c.rgb[blood] = c.rgb[blood] * 0.3 + np.array([123, 27, 29]) * 0.7
    return c


# -------------------------------------------------------------------- wraith
def wraith(frame="idle"):
    c = Canvas(MW, MH)
    atk = frame == "attack"
    bob = -3 if frame == "idle2" else 0
    robe = "25103b"
    # wispy robe
    pts = [(48, 18 + bob), (64, 30 + bob), (70, 60 + bob), (74, 92 + bob), (66, 112 + bob), (60, 102 + bob),
           (54, 116 + bob), (48, 104 + bob), (42, 118 + bob), (36, 102 + bob), (30, 114 + bob), (22, 92 + bob),
           (26, 60 + bob), (32, 30 + bob)]
    r = c.poly(pts, robe, amb=1.0, grad=(-0.7, -0.4, 0.8))
    folds = r & ((((c.xx - 48) * 0.5 + c.yy * 0.12) % 6) < 1.2)
    c.rgb[folds] *= 0.6
    hem = r & (c.yy > 96 + bob)
    c.emi[hem] = np.array([33, 114, 103], np.float32) * np.clip((c.yy[hem] - 96 - bob) / 18, 0, 1)[:, None]
    # hood opening: darkness with eyes
    c.ellipse(48, 36 + bob, 10, 12, "0b0a0e", flat=True)
    hood = c.ellipse(48, 30 + bob, 15, 15, robe, amb=0.6, k=0.6) & ~((((c.xx - 48) / 10) ** 2 + ((c.yy - 38 - bob) / 13) ** 2) <= 1)
    for ex in (44, 52):
        c.ellipse(ex, 36 + bob, 2.4, 1.6, "8ee5cf", flat=True, emissive="c2f5e6")
    c.glow(48, 36 + bob, 9, "217267", 0.6)
    # skeletal hands reaching
    hy = 52 if not atk else 40
    spread = 18 if not atk else 30
    for s in (-1, 1):
        c.capsule(48 + s * 12, 48 + bob, 48 + s * spread, hy + 10 + bob, 4, robe, 3)
        hx = 48 + s * spread
        for k in (-2, 0, 2):
            c.line(hx + k, hy + 10 + bob, hx + k * 1.6 + s * 2, hy + 2 + bob - (3 if atk else 0), 1.2, "d0f8ec", emissive="48bba6")
        c.glow(hx, hy + 6 + bob, 7, "217267", 0.8)
    return c


# --------------------------------------------------------------------- items
IW, IH = 64, 32   # items: 0.5 x 0.25 cell, lying on the floor


def item_key():
    c = Canvas(IW, IH)
    c.ellipse(32, 30, 18, 3, "0b0a0e", flat=True)  # shadow
    c.a[(c.yy > 27)] = np.where(c.a[(c.yy > 27)] > 0, 0.6, 0)
    rg = c.ellipse(20, 20, 7, 6, "8497ab", amb=0.6, k=0.7)
    c.ellipse(20, 20, 3.5, 3, "0b0a0e", flat=True); c.a[(((c.xx - 20) / 3.5) ** 2 + ((c.yy - 20) / 3) ** 2) <= 1] = 0
    c.line(26, 20, 48, 20, 3, "8497ab")
    c.line(26, 19, 48, 19, 1, "d2dce2")
    c.rect(42, 21, 45, 26, "8497ab"); c.rect(46, 21, 49, 25, "8497ab")
    return c


def item_potion():
    c = Canvas(IW, IH)
    c.ellipse(32, 30, 10, 2.5, "0b0a0e", flat=True)
    c.ellipse(32, 22, 8, 8, "7b1b1d", amb=0.6, k=0.8, emissive=None)
    c.rect(29, 6, 35, 14, "425167")
    c.rect(28, 3, 36, 7, "84552a")
    c.ellipse(29, 19, 2, 3, "f2a46a", flat=True)
    c.glow(32, 22, 6, "c54830", 0.25)
    return c


def item_bones():
    c = Canvas(IW, IH)
    c.ellipse(32, 29, 24, 3, "0b0a0e", flat=True)
    c.capsule(12, 26, 40, 22, 2.5, "d9d0b4")
    c.capsule(24, 28, 50, 26, 2.2, "a39a7c")
    c.capsule(34, 24, 54, 18, 2.0, "d9d0b4")
    c.ellipse(46, 20, 7, 6.5, "d9d0b4")
    c.ellipse(43.5, 20, 1.8, 1.8, "0b0a0e", flat=True)
    c.ellipse(48.5, 20, 1.8, 1.8, "0b0a0e", flat=True)
    return c


MONSTERS = {"skeleton": skeleton, "ghoul": ghoul, "wraith": wraith}
FRAMES = ["idle", "idle2", "attack"]
ITEMS = {"key": item_key, "potion": item_potion, "bones": item_bones}
