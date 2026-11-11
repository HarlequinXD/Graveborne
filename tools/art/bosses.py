"""Chapter bosses, the townsfolk, story items and props, painted in the same style as actors.py.

BOSSES maps name -> (painter, canvas w, canvas h, world width, world height, lift)."""
import numpy as np
from canvas import Canvas
from common import value_noise
from actors import _person, _noise_tex

BONE, BONE_D, OLD_BONE = "d9d0b4", "a39a7c", "a8987a"
TEAL, TEAL_E = "48bba6", "64d2ba"
VIO, VIO_E = "ab6dd5", "e2b4f4"


def _skull(c, cx, cy, s=1.0, tone=BONE, eyes=TEAL, eye_e=TEAL_E, jaw_open=0):
    c.ellipse(cx, cy, 11 * s, 12 * s, tone, amb=0.6, k=0.6)
    c.ellipse(cx, cy + 11 * s + jaw_open, 7.5 * s, 4.5 * s, BONE_D if tone == BONE else tone)
    for ex in (cx - 4.5 * s, cx + 4.5 * s):
        c.ellipse(ex, cy + 1 * s, 3.6 * s, 3.2 * s, "0b0a0e", flat=True)
        c.ellipse(ex, cy + 1 * s, 1.6 * s, 1.6 * s, eyes, flat=True, emissive=eye_e)
        c.glow(ex, cy + 1 * s, 3 * s, eyes, 0.4)
    c.poly([(cx - 1 * s, cy + 5 * s), (cx + 1 * s, cy + 5 * s), (cx, cy + 8 * s)], "15131a", amb=1.0)
    for tx in np.arange(cx - 5 * s, cx + 6 * s, 2 * s):
        c.rect(tx, cy + 11 * s + jaw_open, tx + 1 * s, cy + 13 * s + jaw_open, "f4efe0")


# ------------------------------------------------------------- the Sexton
def sexton(frame="idle"):
    """The bell-ringer who died at his post: hunched in a rotted cassock, ringing the dead awake."""
    c = Canvas(96, 128)
    bob = 1 if frame == "idle2" else 0
    atk = frame == "attack"
    robe = "1d1a24"
    pts = [(46, 34 + bob), (62, 44 + bob), (70, 80), (74, 124), (60, 118), (50, 124), (40, 117), (24, 124), (28, 80), (32, 46 + bob)]
    r = c.poly(pts, robe, amb=1.0, grad=(-0.6, -0.3, 0.7))
    c.rgb[r & ((((c.xx - 48) * 0.6 + c.yy * 0.1) % 7) < 1.3)] *= 0.6
    c.rgb[r & (value_noise(128, 96, 5, 3, 2) > 0.72)] *= 0.5                      # moth-eaten holes
    c.rect(30, 70, 66, 74, "5c1618")                                             # rope belt
    c.line(40, 74, 36, 96, 1.6, "5c1618")
    # hunched hood and skull face
    c.ellipse(44, 30 + bob, 15, 14, "2a2533", amb=0.5, k=0.7)
    c.ellipse(44, 34 + bob, 10, 11, "0b0a0e", flat=True)
    _skull(c, 44, 33 + bob, 0.75)
    # the big bronze handbell
    hx, hy = (70, 64) if not atk else (66, 22)
    c.capsule(56, 50 + bob, hx - 2, hy + 4, 3.4, robe, 3)
    c.ellipse(hx - 2, hy + 4, 3.2, 3, OLD_BONE)
    c.line(hx, hy, hx, hy - 10, 2.6, "4a2e17")
    bell = c.poly([(hx - 4, hy + 2), (hx + 4, hy + 2), (hx + 11, hy + 22), (hx - 11, hy + 22)], "a26833", amb=1.0, grad=(-0.7, -0.3, 0.6))
    c.ellipse(hx, hy + 22, 11, 3, "6d4524")
    c.ellipse(hx, hy + 25, 2.5, 2.5, "3a2a1a")
    if atk:
        for k in range(3):
            c.line(hx + 14 + k * 4, hy + 6 + k * 6, hx + 20 + k * 4, hy + 2 + k * 6, 1.0, "e2b4f4", emissive=VIO_E)
    # left hand reaching, bony
    c.capsule(34, 50 + bob, 22, 70, 3.2, robe, 2.8)
    for k in (-2, 0, 2):
        c.line(22 + k, 70, 20 + k * 1.5, 78, 1.1, OLD_BONE)
    return c


# ------------------------------------------------------- the Hanged Captain
def captain(frame="idle"):
    """Captain of the Watch, hanged from his own tower: noose still on, rope cut, sabre drawn."""
    c = Canvas(104, 144)
    bob = 2 if frame == "idle2" else 0
    atk = frame == "attack"
    cx = 52
    # cut rope dangling from the noose
    c.line(cx + 2, 4, cx + 1, 36 + bob, 2.4, "8a6a3a")
    c.line(cx + 3, 4, cx + 2, 36 + bob, 0.8, "b28d52")
    # tattered cloak behind
    cl = c.poly([(cx - 18, 52 + bob), (cx + 18, 52 + bob), (cx + 26, 128), (cx + 12, 120), (cx, 132), (cx - 12, 122), (cx - 26, 128)],
                "3a0d11", amb=1.0, grad=(-0.5, -0.4, 0.6))
    c.rgb[cl & (value_noise(144, 104, 6, 21, 2) > 0.7)] *= 0.5
    # legs, dangling a little off the ground
    for s in (-1, 1):
        hx = cx + s * 7
        c.capsule(hx, 98 + bob, hx + s * 2, 116 + bob, 3.2, BONE, 2.6)
        c.capsule(hx + s * 2, 116 + bob, hx + s * 1, 132 + bob, 2.6, BONE, 2.2)
        c.ellipse(hx + s * 1, 134 + bob, 5, 3, "2d2933")                      # boots
    # rusted breastplate over the ribs
    bp = c.ellipse(cx, 70 + bob, 17, 22, "6a5240", amb=0.5, k=0.8)
    _noise_tex(c, bp, 0.6, 11)
    c.rgb[bp & (value_noise(144, 104, 4, 12, 2) > 0.6)] = np.array([123, 60, 29], np.float32)
    c.line(cx, 50 + bob, cx, 90 + bob, 1.2, "3a2a1a")
    c.rect(cx - 16, 88 + bob, cx + 16, 92 + bob, "2d2933")                     # sword belt
    # pauldrons
    for s in (-1, 1):
        c.ellipse(cx + s * 16, 52 + bob, 8, 6, "56667a", amb=0.5, k=0.8)
    # noose knot and crooked neck
    c.capsule(cx, 44 + bob, cx + 3, 52 + bob, 3, BONE)
    c.ellipse(cx + 4, 46 + bob, 5, 4, "8a6a3a")
    _skull(c, cx + 3, 30 + bob, 0.95)
    # captain's helm with a broken plume
    hx, hy_ = (c.xx - cx - 3) / 13, (c.yy - 24 - bob) / 9
    hm = (hx * hx + hy_ * hy_ <= 1) & (c.yy < 24 + bob)
    c._put(hm, c.shade("425167", hx * 0.9, hy_ * 0.9, 0.6, 0.7))
    c.line(cx + 3, 16 + bob, cx - 10, 4 + bob, 3, "6e181b")
    # arms and sabre
    c.capsule(cx - 18, 54 + bob, cx - 24, 80 + bob, 3, BONE, 2.5)
    if not atk:
        c.capsule(cx + 18, 54 + bob, cx + 24, 80 + bob, 3, BONE, 2.5)
        c.line(cx + 25, 82 + bob, cx + 40, 126, 3.6, "8497ab")
        c.line(cx + 25.6, 82 + bob, cx + 40.6, 126, 1.0, "d2dce2")
        c.line(cx + 20, 82 + bob, cx + 30, 80 + bob, 2.6, "be8041")
    else:
        c.capsule(cx + 18, 54, cx + 30, 30, 3, BONE, 2.5)
        c.line(cx + 30, 30, cx - 20, 10, 4.0, "8497ab")
        c.line(cx + 30, 29, cx - 20, 9, 1.0, "d2dce2")
        for k in range(4):
            c.line(cx - 16 + k * 3, 14 + k * 5, cx - 26 + k * 4, 26 + k * 6, 1.0, "b1aaac")
    return c


# ------------------------------------------------------- the Drowned Knight
def drowned(frame="idle"):
    """One of the barrow kings' guard, two centuries under the mire: bloated, weed-hung, still armoured."""
    c = Canvas(112, 144)
    bob = 1 if frame == "idle2" else 0
    atk = frame == "attack"
    cx = 56
    flesh = "6f7f6a"
    # heavy legs in greaves
    for s in (-1, 1):
        c.capsule(cx + s * 10, 96, cx + s * 12, 132, 6.5, "3f4a4f", 5.5)
        c.ellipse(cx + s * 12, 134, 8, 4, "232a2e")
    # mail skirt
    sk = c.poly([(cx - 22, 88 + bob), (cx + 22, 88 + bob), (cx + 26, 110), (cx - 26, 110)], "4b5a5c", amb=1.0, grad=(-0.5, -0.4, 0.5))
    c.rgb[sk & (((c.xx + c.yy) % 3) < 1)] *= 0.7
    # bloated body under a green-black cuirass
    body = c.ellipse(cx, 70 + bob, 26, 26, "2e3f3a", amb=0.45, k=0.8)
    _noise_tex(c, body, 0.6, 31)
    c.rgb[body & (value_noise(144, 112, 5, 32, 2) > 0.62)] = np.array([84, 112, 74], np.float32)   # verdigris
    # barnacles
    for (bx, by) in [(cx - 12, 62), (cx + 8, 76), (cx - 4, 84), (cx + 15, 58), (cx - 18, 78)]:
        c.ellipse(bx, by + bob, 2.6, 2.2, "c8c0a6")
        c.ellipse(bx, by + bob, 1, 1, "2d2933", flat=True)
    # pauldrons
    for s in (-1, 1):
        c.ellipse(cx + s * 24, 50 + bob, 11, 9, "3f4a4f", amb=0.5, k=0.8)
    # swollen grey head in an open bascinet
    c.ellipse(cx, 34 + bob, 14, 15, flesh, amb=0.5, k=0.7)
    for ex in (cx - 5, cx + 5):
        c.ellipse(ex, 34 + bob, 3.2, 2.6, "dfe8d8", flat=True, emissive="c2f5e6")
        c.ellipse(ex, 34 + bob, 1.2, 1.2, "1d675d", flat=True, emissive=TEAL_E)
    c.ellipse(cx, 44 + bob, 6, 3 + (2 if atk else 0), "17121f", flat=True)
    hx, hy_ = (c.xx - cx) / 17, (c.yy - 30 - bob) / 16
    hm = (hx * hx + hy_ * hy_ <= 1) & ((c.yy < 24 + bob) | (np.abs(c.xx - cx) > 12))
    c._put(hm, c.shade("4b5a5c", hx * 0.9, hy_ * 0.9, 0.5, 0.8))
    # weeds hanging off everything, dripping teal water
    rng = np.random.default_rng(5)
    for k in range(10):
        wx = cx + rng.uniform(-26, 26); wy = rng.uniform(22, 90)
        c.line(wx, wy + bob, wx + rng.uniform(-3, 3), wy + rng.uniform(8, 20) + bob, 1.3, "2e4a22")
    for k in range(6):
        dx = cx + rng.uniform(-24, 24); dy = rng.uniform(70, 130)
        c.ellipse(dx, dy, 1, 1.6, "8ee5cf", flat=True, emissive="64d2ba")
    # greatsword
    if not atk:
        c.line(cx + 30, 70, cx + 34, 136, 5, "6a7f86")
        c.line(cx + 30.8, 70, cx + 34.8, 136, 1.2, "a8bcc0")
        c.line(cx + 22, 70, cx + 40, 68, 3.4, "523a20")
        c.capsule(cx + 24, 52 + bob, cx + 30, 68, 5, "3f4a4f", 4)
    else:
        c.capsule(cx + 24, 52, cx + 18, 20, 5, "3f4a4f", 4)
        c.line(cx + 18, 22, cx - 34, 4, 5.4, "6a7f86")
        c.line(cx + 18, 21, cx - 34, 3, 1.2, "a8bcc0")
    c.capsule(cx - 24, 52 + bob, cx - 28, 84, 5, "3f4a4f", 4)
    return c


# ------------------------------------------------------- the Bone Colossus
def colossus(frame="idle"):
    """Built by the Wound from ten thousand bones the town moved out of its graveyards."""
    W, H = 160, 192
    c = Canvas(W, H)
    bob = 2 if frame == "idle2" else 0
    atk = frame == "attack"
    cx = 80
    rng = np.random.default_rng(77)

    def heap(x0, y0, rx, ry, n, seed):
        rr = np.random.default_rng(seed)
        for _ in range(n):
            a = rr.uniform(0, 2 * np.pi); d = np.sqrt(rr.uniform(0, 1))
            x, y = x0 + np.cos(a) * rx * d, y0 + np.sin(a) * ry * d
            if rr.uniform() < 0.35:
                c.ellipse(x, y, 4.5, 4.2, [BONE, OLD_BONE, BONE_D][rr.integers(0, 3)], amb=0.5, k=0.7)
                c.ellipse(x - 1.5, y, 1.2, 1.2, "15131a", flat=True)
                c.ellipse(x + 1.5, y, 1.2, 1.2, "15131a", flat=True)
            else:
                L = rr.uniform(6, 14); t = rr.uniform(0, np.pi)
                c.capsule(x, y, x + np.cos(t) * L, y + np.sin(t) * L, 2.0, [BONE, OLD_BONE, BONE_D][rr.integers(0, 3)], 1.6)

    # legs: stumpy pillars of bone
    for s in (-1, 1):
        heap(cx + s * 26, 160, 14, 26, 70, 10 + s)
    # torso
    heap(cx, 108 + bob, 46, 40, 260, 3)
    # ribcage chest with the grave-fire core
    for i in range(5):
        y = 92 + i * 9 + bob
        c.capsule(cx - 24, y, cx, y - 4, 2.6, BONE)
        c.capsule(cx + 24, y, cx, y - 4, 2.6, BONE)
    c.ellipse(cx, 108 + bob, 10, 12, "1d675d", flat=True, emissive="64d2ba")
    c.ellipse(cx, 108 + bob, 5, 6, "c2f5e6", flat=True, emissive="d0f8ec")
    c.glow(cx, 108 + bob, 22, TEAL, 0.9)
    # great arms
    for s in (-1, 1):
        ax = cx + s * 46
        if atk and s == 1:
            heap(ax - 6, 54, 10, 30, 60, 40)
            heap(ax - 20, 22, 16, 14, 50, 41)
        else:
            heap(ax, 112 + bob, 11, 34, 70, 20 + s)
            heap(ax + s * 4, 152 + bob, 16, 12, 50, 30 + s)    # fists of skulls
    # head: one giant skull
    _skull(c, cx, 58 + bob, 1.9, tone=OLD_BONE, jaw_open=4 if atk else 0)
    for s in (-1, 1):
        c.capsule(cx + s * 18, 44 + bob, cx + s * 34, 26 + bob, 3.2, BONE_D, 2)    # horns of femurs
    return c


# --------------------------------------------------------- the Last Abbot
def abbot(frame="idle"):
    """The abbot who hid the Oath-stones, risen to guard his secret."""
    c = Canvas(104, 144)
    bob = -3 if frame == "idle2" else 0
    atk = frame == "attack"
    cx = 52
    robe = "e3dccb"
    pts = [(cx, 40 + bob), (cx + 18, 52 + bob), (cx + 26, 100 + bob), (cx + 30, 134 + bob), (cx + 14, 126 + bob), (cx, 136 + bob),
           (cx - 14, 126 + bob), (cx - 30, 134 + bob), (cx - 26, 100 + bob), (cx - 18, 52 + bob)]
    r = c.poly(pts, robe, amb=1.0, grad=(-0.7, -0.3, 0.7))
    c.rgb[r & ((((c.xx - cx) * 0.6 + c.yy * 0.1) % 7) < 1.3)] *= 0.75
    c.rgb[r & (value_noise(144, 104, 5, 41, 2) > 0.7)] *= 0.6            # grave stains
    # violet stole with the seven-pointed sigil
    for s in (-1, 1):
        c.poly([(cx + s * 6, 50 + bob), (cx + s * 12, 50 + bob), (cx + s * 12, 128 + bob), (cx + s * 6, 128 + bob)], "4a1f6a", amb=1.0)
    c.ellipse(cx, 90 + bob, 6, 6, "c08ce0", flat=True, emissive=VIO_E)
    c.glow(cx, 90 + bob, 14, "7a3eaa", 0.8)
    hem = r & (c.yy > 118 + bob)
    c.emi[hem] = np.array([90, 40, 130], np.float32) * np.clip((c.yy[hem] - 118 - bob) / 18, 0, 1)[:, None]
    # skeletal face under a tall mitre
    _skull(c, cx, 34 + bob, 0.8, eyes=VIO, eye_e=VIO_E)
    c.poly([(cx - 12, 26 + bob), (cx + 12, 26 + bob), (cx + 8, 2 + bob), (cx, -2 + bob), (cx - 8, 2 + bob)], "e3dccb", amb=1.0, grad=(-0.6, -0.4, 0.5))
    c.line(cx, 4 + bob, cx, 24 + bob, 1.6, "be8041")
    c.line(cx - 6, 12 + bob, cx + 6, 12 + bob, 1.6, "be8041")
    # crozier
    sx = cx + 26
    hand_y = 70 if not atk else 52
    c.line(sx, 140, sx, 14 + (0 if not atk else -10), 2.6, "8a6a3a")
    c.capsule(sx, 14 - (10 if atk else 0), sx - 8, 6 - (10 if atk else 0), 2.4, "be8041", 2)
    c.ellipse(sx - 8, 9 - (10 if atk else 0), 3, 3, "c08ce0", flat=True, emissive=VIO_E)
    c.capsule(cx + 16, 54 + bob, sx, hand_y, 4, robe, 3)
    # open hand casting
    hy = 66 if not atk else 40
    c.capsule(cx - 16, 54 + bob, cx - 26, hy, 4, robe, 3)
    for k in (-2, 0, 2):
        c.line(cx - 26 + k, hy, cx - 28 + k * 1.6, hy - 8, 1.2, OLD_BONE, emissive="ab6dd5" if atk else None)
    c.glow(cx - 27, hy - 4, 8 if atk else 5, "7a3eaa", 0.9 if atk else 0.5)
    return c


# ---------------------------------------------------------- King Hrodmar
def hrodmar(frame="idle"):
    """The first of the dead the Wound ever raised: a barrow king in bronze, older than the town."""
    c = Canvas(128, 168)
    bob = 1 if frame == "idle2" else 0
    atk = frame == "attack"
    cx = 64
    bone = "b8a986"
    # royal cloak
    cl = c.poly([(cx - 24, 54 + bob), (cx + 24, 54 + bob), (cx + 36, 160), (cx + 18, 152), (cx, 164), (cx - 18, 152), (cx - 36, 160)],
                "4a0f14", amb=1.0, grad=(-0.5, -0.4, 0.6))
    c.rgb[cl & (value_noise(168, 128, 6, 51, 2) > 0.72)] *= 0.45
    # legs in bronze greaves
    for s in (-1, 1):
        c.capsule(cx + s * 9, 112, cx + s * 11, 160, 5, "8a5a24", 4.2)
        c.ellipse(cx + s * 11, 162, 7, 3.4, "4a2e17")
    # bronze scale coat
    coat = c.poly([(cx - 22, 52 + bob), (cx + 22, 52 + bob), (cx + 26, 118), (cx - 26, 118)], "9a6a2a", amb=1.0, grad=(-0.6, -0.4, 0.6))
    scales = coat & (((c.yy + (c.xx // 5) % 2 * 3) % 6) < 1.4)
    c.rgb[scales] *= 0.6
    c.rgb[coat & (value_noise(168, 128, 4, 52, 2) > 0.62)] = np.array([60, 110, 90], np.float32)   # verdigris
    c.rect(cx - 24, 104, cx + 24, 108, "4a2e17")
    for s in (-1, 1):
        c.ellipse(cx + s * 22, 54 + bob, 10, 8, "b07a32", amb=0.5, k=0.8)
    # skull with a bronze crown
    _skull(c, cx, 36 + bob, 1.05, tone=bone)
    c.rect(cx - 13, 20 + bob, cx + 13, 26 + bob, "d4a246")
    for k in range(-2, 3):
        c.poly([(cx + k * 6 - 3, 21 + bob), (cx + k * 6 + 3, 21 + bob), (cx + k * 6, 11 + bob)], "d4a246", amb=1.0, grad=(-0.5, -0.5, 0.5))
    c.ellipse(cx, 23 + bob, 2, 2, "c08ce0", flat=True, emissive=VIO_E)
    # long beard of grave-moss
    c.poly([(cx - 7, 50 + bob), (cx + 7, 50 + bob), (cx + 3, 66 + bob), (cx - 3, 66 + bob)], "4e5a3a", amb=1.0)
    # great axe
    if not atk:
        c.capsule(cx + 22, 56 + bob, cx + 30, 86, 4, bone, 3.4)
        c.line(cx + 34, 160, cx + 30, 20, 3.4, "4a2e17")
        c.poly([(cx + 30, 26), (cx + 52, 16), (cx + 56, 40), (cx + 30, 44)], "a8bcc0", amb=1.0, grad=(-0.6, -0.5, 0.5))
        c.poly([(cx + 30, 26), (cx + 16, 20), (cx + 16, 40), (cx + 30, 40)], "6a7f86", amb=1.0)
    else:
        c.capsule(cx + 22, 56, cx + 20, 22, 4, bone, 3.4)
        c.line(cx + 22, 26, cx - 46, 6, 3.6, "4a2e17")
        c.poly([(cx - 40, 2), (cx - 58, 20), (cx - 44, 30), (cx - 30, 14)], "a8bcc0", amb=1.0, grad=(-0.6, -0.5, 0.5))
        for k in range(4):
            c.line(cx - 50 + k * 4, 30 + k * 4, cx - 56 + k * 4, 44 + k * 5, 1.0, "b1aaac")
    c.capsule(cx - 22, 56 + bob, cx - 28, 92, 4, bone, 3.4)
    return c


# ------------------------------------------------------ the Heart of the Wound
def heart(frame="idle"):
    """The Wound's heart: a violet mass of veined flesh that beats, and speaks in Aldric's voice."""
    W, H = 144, 144
    c = Canvas(W, H)
    pulse = {"idle": 0.0, "idle2": 0.08, "attack": 0.14}[frame]
    cx, cy = 72, 64
    # tendrils rooting it into the floor
    rng = np.random.default_rng(9)
    for k in range(9):
        a0 = rng.uniform(-2.6, -0.5) if k % 2 else rng.uniform(0.5, 2.6)
        x0, y0 = cx + np.cos(a0) * 24, cy + 30
        xm, ym = cx + np.cos(a0) * 44, cy + 50
        x1, y1 = cx + np.cos(a0) * 60 + rng.uniform(-6, 6), 140
        if frame == "attack" and k < 3:
            x1, y1 = cx + rng.uniform(-60, 60), rng.uniform(4, 30)
        c.capsule(x0, y0, xm, ym, 5, "5a1f63", 3.5)
        c.capsule(xm, ym, x1, y1, 3.5, "4a1752", 1.5)
    # the heart itself
    s = 1 + pulse
    m = c.ellipse(cx, cy, 34 * s, 38 * s, "7a2a7e", amb=0.45, k=0.8)
    c.ellipse(cx - 14 * s, cy - 22 * s, 16 * s, 16 * s, "7a2a7e", amb=0.45, k=0.8)
    c.ellipse(cx + 14 * s, cy - 22 * s, 16 * s, 16 * s, "7a2a7e", amb=0.45, k=0.8)
    # veins
    vn = value_noise(H, W, 8, 61, 3)
    veins = (c.a > 0) & (np.abs(vn - 0.5) < 0.012)
    c.rgb[veins] = np.array([200, 120, 220], np.float32)
    c.emi[veins] = np.array([120, 60, 160], np.float32)
    dark = (c.a > 0) & (value_noise(H, W, 5, 62, 2) > 0.62)
    c.rgb[dark] *= 0.7
    # the seam it opens, like an eye
    c.ellipse(cx, cy + 4, 20 * s, 6 * s + pulse * 30, "0b0a0e", flat=True)
    c.ellipse(cx, cy + 4, 6, 4 + pulse * 18, "f0d8ff", flat=True, emissive="ffffff")
    c.glow(cx, cy + 4, 40, "7a3eaa", 1.0)
    # a violet ribbon caught on it, like the one on Aldric's helm
    c.line(cx + 22, cy - 30, cx + 36, cy - 10, 3, "c08ce0", emissive=VIO_E)
    c.line(cx + 36, cy - 10, cx + 30, cy + 12, 3, "c08ce0", emissive=VIO_E)
    return c


# ------------------------------------------------------------- townsfolk
def townsman(frame="idle"):
    c = Canvas(96, 128)
    bob = 1 if frame == "idle2" else 0
    _person(c, "4b4558", "2d2933", skin="c9a98c", hood="3a3149", bob=bob)
    for ex in (44.5, 51.5):
        c.ellipse(ex, 33 + bob, 1.3, 1.3, "1a1611", flat=True)
    # a torch held high
    c.ellipse(64, 60, 4, 3, "c9a98c")
    c.line(64, 62, 66, 30, 2.4, "522d17")
    c.ellipse(66, 26, 4, 6, "f0a040", flat=True, emissive="ffd27a")
    c.glow(66, 26, 12, "c86420", 0.9)
    return c


# ----------------------------------------------------------------- items
def item_stone():
    """An Oath-stone: black, carved with a warden's rune, veined with violet."""
    c = Canvas(64, 32)
    m = c.ellipse(32, 20, 12, 8, "2d2933", amb=0.5, k=0.8)
    c.rgb[m & (np.abs(value_noise(32, 64, 4, 71, 2) - 0.5) < 0.05)] = np.array([226, 180, 244], np.float32)
    c.line(28, 16, 36, 22, 1.4, "c08ce0", emissive=VIO_E)
    c.line(36, 16, 28, 22, 1.4, "c08ce0", emissive=VIO_E)
    c.glow(32, 19, 14, "7a3eaa", 0.8)
    return c


def item_letter():
    c = Canvas(64, 32)
    c.poly([(16, 14), (46, 10), (50, 26), (20, 28)], "d8ccb1", amb=1.0, grad=(-0.4, -0.3, 0.4))
    c.line(18, 18, 46, 15, 0.8, "786c54")
    c.line(19, 22, 46, 19, 0.8, "786c54")
    c.ellipse(34, 21, 4, 3.4, "8a1820", amb=0.5, k=0.7)
    return c


# ----------------------------------------------------------------- props
def prop_hanged():
    """A risen corpse still hanging from a gibbet rope, twitching."""
    c = Canvas(48, 128)
    c.line(24, 0, 24, 30, 1.8, "8a6a3a")
    c.ellipse(24, 32, 4, 3, "8a6a3a")
    c.ellipse(24, 26, 7, 8, OLD_BONE, amb=0.6, k=0.6)
    for ex in (21.5, 26.5):
        c.ellipse(ex, 26, 1.8, 1.6, "0b0a0e", flat=True)
        c.ellipse(ex, 26, 0.8, 0.8, TEAL, flat=True, emissive=TEAL_E)
    body = c.poly([(16, 36), (32, 36), (34, 80), (14, 80)], "4b4558", amb=1.0, grad=(-0.6, -0.4, 0.6))
    c.rgb[body & (value_noise(128, 48, 4, 81, 2) > 0.65)] *= 0.5
    for s in (-1, 1):
        c.capsule(24 + s * 9, 38, 24 + s * 11, 70, 2, OLD_BONE, 1.6)
        c.capsule(24 + s * 5, 80, 24 + s * 6, 108, 2.4, OLD_BONE, 2)
    return c


def prop_pyre():
    """A town pyre: stacked logs, white ash, embers that never quite go out."""
    c = Canvas(96, 96)
    for i in range(5):
        y = 86 - i * 9
        w = 36 - i * 5
        c.capsule(48 - w, y, 48 + w, y - 2, 4.2, ["5a3a1e", "4a2e17"][i % 2], 4)
    c.ellipse(48, 46, 18, 8, "c8c0b6")
    ember = (c.a > 0) & (value_noise(96, 96, 6, 91, 2) > 0.7) & (c.yy > 40)
    c.rgb[ember] = np.array([240, 120, 40], np.float32)
    c.emi[ember] = np.array([255, 150, 60], np.float32)
    c.glow(48, 60, 26, "c86420", 0.6)
    return c


def prop_bell():
    """The undercroft's great burial bell, fallen from its beam."""
    c = Canvas(96, 96)
    c.poly([(36, 20), (60, 20), (78, 86), (18, 86)], "8a5a24", amb=1.0, grad=(-0.7, -0.3, 0.6))
    c.ellipse(48, 20, 12, 5, "b07a32")
    c.ellipse(48, 86, 30, 6, "4a2e17")
    c.rgb[(c.a > 0) & (value_noise(96, 96, 4, 95, 2) > 0.62)] = np.array([60, 110, 90], np.float32)
    c.line(30, 60, 66, 60, 2, "d4a246")
    c.ellipse(48, 14, 6, 6, "4a2e17")
    return c


BOSSES = {
    "sexton": (sexton, 0.75, 1.0, 0.0),
    "captain": (captain, 0.8, 1.1, 0.06),
    "drowned": (drowned, 0.85, 1.1, 0.0),
    "colossus": (colossus, 1.25, 1.5, 0.0),
    "abbot": (abbot, 0.8, 1.1, 0.04),
    "hrodmar": (hrodmar, 0.95, 1.25, 0.0),
    "heart": (heart, 1.15, 1.15, 0.08),
}
NPCS = {"townsman": townsman}
ITEMS = {"stone": item_stone, "letter": item_letter}
PROPS = {"hanged": (prop_hanged, 0.375, 1.0), "pyre": (prop_pyre, 0.8, 0.8), "bell": (prop_bell, 0.8, 0.8)}
