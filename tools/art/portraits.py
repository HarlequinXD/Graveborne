"""Party portraits: four resurrected warriors, painted at 4x then brought down to 32x32 pixel art."""
import numpy as np
from canvas import Canvas
from common import value_noise, hexrgb

S = 128  # paint size; final 32


def _bg(c):
    g = np.clip(1 - np.hypot(c.xx - 64, c.yy - 50) / 110, 0, 1)
    c.rgb[:] = hexrgb("15101f") * (0.6 + 0.8 * g[..., None])


def _face(c, cx, cy, skin="9aa6ae", w=26, h=32, jaw=1.0):
    f = c.ellipse(cx, cy, w, h, skin, amb=0.5, k=0.65)
    c.ellipse(cx, cy + h * 0.55, w * 0.78 * jaw, h * 0.5, skin, amb=0.5, k=0.6)
    # sunken cheeks of the long dead
    for s in (-1, 1):
        ch = (((c.xx - cx - s * w * 0.55) / 7) ** 2 + ((c.yy - cy - 8) / 10) ** 2) < 1
        c.rgb[ch & f] *= 0.78
    return f


def _eyes(c, cx, cy, spread=11, col="64d2ba"):
    for s in (-1, 1):
        ex = cx + s * spread
        c.ellipse(ex, cy, 7, 4.5, "1c1626", flat=True)
        c.ellipse(ex, cy, 4, 3, col, flat=True, emissive=col)
        c.ellipse(ex - 1, cy - 1, 1.5, 1.2, "ffffff", flat=True, emissive="ffffff")
        c.glow(ex, cy, 7, "217267", 0.5)
        c.line(ex - 8, cy - 7, ex + 8, cy - 6 + s * 2, 3, "2a2236")  # brow


def _stitches(c, x0, y0, x1, y1, n=5):
    c.line(x0, y0, x1, y1, 1.6, "2a1520")
    for k in range(n):
        t = (k + 0.5) / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        dx, dy = (y1 - y0), -(x1 - x0)
        L = np.hypot(dx, dy) + 1e-6
        c.line(x - dx / L * 3, y - dy / L * 3, x + dx / L * 3, y + dy / L * 3, 1.4, "2a1520")


def _mouth(c, cx, cy, w=10):
    c.line(cx - w, cy, cx + w, cy + 1, 2.2, "2a1520")


def aldric():
    """Knight: open-faced great helm with nose guard, mail coif, steel pauldrons."""
    c = Canvas(S, S); _bg(c)
    c.ellipse(64, 132, 62, 30, "425167", amb=0.55, k=0.7)       # pauldrons
    for s in (-1, 1):
        c.ellipse(64 + s * 44, 112, 22, 16, "7c8e9f", amb=0.5, k=0.8)
    mail = c.ellipse(64, 92, 34, 30, "56667a", amb=0.6, k=0.5)
    ring = mail & ((((c.xx // 3) + (c.yy // 3)) % 2) == 0)
    c.rgb[ring] *= 0.7
    _face(c, 64, 62, w=22, h=26)
    _eyes(c, 64, 58, 10)
    _stitches(c, 50, 74, 60, 84, 3)
    _mouth(c, 64, 80, 8)
    helm = (((c.xx - 64) / 34) ** 2 + ((c.yy - 50) / 36) ** 2 <= 1)
    opening = (np.abs(c.xx - 64) < 20 - np.clip(c.yy - 70, 0, 99) * 0.2) & (c.yy > 46) & (c.yy < 96)
    hm = helm & ~opening
    nx, ny = (c.xx - 64) / 34, (c.yy - 50) / 36
    c._put(hm, c.shade("7c8e9f", nx * 0.9, ny * 0.9, 0.45, 0.8, rim=0.4))
    c._put(helm & (np.abs(c.xx - 64) < 3) & (c.yy > 40) & (c.yy < 72), c.shade("bccbd8", (c.xx - 64) / 3 * 0.8, ny * 0, 0.5, 0.7))
    c._put(helm & (np.abs(c.yy - 44) < 2.5) & ~opening, c.shade("d2dce2", nx, ny, 0.5, 0.6))
    for s in (-1, 1):  # rivets
        c.ellipse(64 + s * 26, 44, 2, 2, "d2dce2")
    # violet plume ribbon (the curse that raised him)
    c.poly([(64, 12), (90, 4), (104, 14), (84, 18)], "572584", amb=1.0, grad=(-0.5, -0.5, 0.6))
    return c


def brann():
    """Berserker: bald, curse-rune tattoo, braided beard, fur mantle, scarred eye."""
    c = Canvas(S, S); _bg(c)
    fur = c.ellipse(64, 128, 66, 32, "5f331a", amb=0.55, k=0.6)
    n = value_noise(c.h, c.w, 4, 3, 2)
    c.rgb[fur] *= (0.7 + 0.6 * n[fur])[:, None]
    c.ellipse(64, 126, 30, 20, "6c614a", amb=0.5, k=0.6)
    head = _face(c, 64, 58, skin="a4aaa2", w=28, h=34, jaw=1.05)
    # tattoo
    for k in range(3):
        c.line(52 + k * 12, 30, 58 + k * 6, 44, 2.2, "572584", emissive="451d6a")
    c.line(50, 36, 78, 36, 1.6, "572584", emissive="451d6a")
    _eyes(c, 64, 56, 12)
    # scar over the left eye, eye milky
    c.line(46, 40, 58, 72, 2.4, "5a2030")
    c.ellipse(52, 56, 4, 3, "c9c9c9", flat=True, emissive="6a6a6a")
    c.ellipse(64, 66, 4, 6, "a4aaa2", amb=0.5, k=0.7)       # nose
    # beard with braids
    beard = c.poly([(36, 66), (92, 66), (96, 92), (78, 116), (64, 120), (50, 116), (32, 92)], "7a3a1c", amb=1.0, grad=(-0.4, -0.8, 0.7))
    strands = beard & ((((c.xx - 64) * 0.7 + c.yy * 0.25) % 5) < 1.3)
    c.rgb[strands] *= 0.7
    c.ellipse(64, 78, 9, 3, "1c1626", flat=True)           # mouth in the beard
    for s in (-1, 1):
        for k in range(4):
            c.ellipse(64 + s * 12, 118 + k * 7, 4, 4, "8c4a22", amb=0.5, k=0.7)
        c.rect(64 + s * 12 - 4, 112, 64 + s * 12 + 4, 115, "c58644")
    return c


def sera():
    """Spearwarden: leather hood, pale hair, high collar, stitched jaw."""
    c = Canvas(S, S); _bg(c)
    c.ellipse(64, 130, 58, 30, "4a1015", amb=0.55, k=0.7)
    c.poly([(30, 100), (98, 100), (104, 128), (24, 128)], "6b2520", amb=1.0, grad=(-0.5, -0.6, 0.5))
    hood = c.ellipse(64, 56, 40, 50, "4a1015", amb=0.5, k=0.7)
    hair = c.poly([(34, 46), (94, 46), (98, 108), (84, 92), (44, 92), (30, 108)], "c2b8a6", amb=1.0, grad=(-0.6, -0.7, 0.6))
    strands = hair & (((c.xx * 0.9 + c.yy * 0.1) % 4) < 1.1)
    c.rgb[strands] *= 0.75
    _face(c, 64, 62, skin="b0b6bc", w=22, h=28, jaw=0.85)
    _eyes(c, 64, 60, 10, col="8ee5cf")
    c.ellipse(64, 70, 3, 5, "b0b6bc", amb=0.5, k=0.7)
    _stitches(c, 70, 78, 82, 70, 3)
    c.line(57, 81, 71, 81, 2.0, "5a2030")
    # fringe
    c.poly([(42, 40), (86, 40), (82, 52), (72, 46), (62, 54), (52, 46), (44, 54)], "d6cdb8", amb=1.0, grad=(-0.6, -0.8, 0.5))
    c.ellipse(64, 30, 32, 16, "4a1015", amb=0.5, k=0.7)
    # bronze clasp
    c.ellipse(64, 104, 6, 5, "c58644", amb=0.6, k=0.7)
    return c


def vesh():
    """Crossbowman: deep moss-green hood, scarf, half the face rotted to bone."""
    c = Canvas(S, S); _bg(c)
    c.ellipse(64, 130, 60, 30, "1d2a13", amb=0.6, k=0.7)
    c.line(30, 124, 100, 96, 6, "653f1f")  # crossbow strap
    hood = c.ellipse(64, 58, 42, 52, "293b18", amb=0.45, k=0.75)
    c.ellipse(64, 66, 27, 34, "07090d", flat=True)
    _face(c, 64, 66, skin="8f9aa0", w=20, h=26)
    # exposed skull on the right half
    half = (c.xx > 64) & ((((c.xx - 64) / 20) ** 2 + ((c.yy - 64) / 26) ** 2) < 1)
    nx, ny = (c.xx - 64) / 20, (c.yy - 64) / 26
    c._put(half, c.shade("e0d6bc", nx * 0.9, ny * 0.9, 0.55, 0.6))
    c.line(64, 42, 64, 92, 1.6, "2a1520")
    _eyes(c, 64, 62, 9)
    c.ellipse(74, 62, 6, 5, "0b0a0e", flat=True)
    c.ellipse(74, 62, 2.4, 2.4, "64d2ba", flat=True, emissive="8ee5cf")
    # scarf over the mouth
    c.poly([(40, 76), (88, 76), (92, 96), (36, 96)], "3a3541", amb=1.0, grad=(-0.5, -0.8, 0.6))
    c.line(40, 84, 90, 86, 1.4, "211e26")
    c.ellipse(64, 30, 36, 18, "293b18", amb=0.45, k=0.75)
    c.poly([(64, 6), (84, 30), (44, 30)], "293b18", amb=0.8)
    return c


PORTRAITS = {"aldric": aldric, "brann": brann, "sera": sera, "vesh": vesh}


PSIZE = 40


def render(name, out_size=PSIZE):
    """Paint at 4x into palette colours, then take the majority colour of each 4x4
    block: keeps crisp pixel-art clusters instead of a blurry average."""
    from pixelart import paint_texture, finish, cleanup
    import canvas as cv
    k = 4
    big = out_size * k
    orig = cv.Canvas.__init__

    def scaled_init(self, w, h):
        orig(self, big, big)
        self.xx *= S / big
        self.yy *= S / big
    cv.Canvas.__init__ = scaled_init
    try:
        c = PORTRAITS[name]()
    finally:
        cv.Canvas.__init__ = orig
    idx, _ = paint_texture(c.rgb * 1.05 + c.emi * 0.8, c.emi)
    blocks = idx.reshape(out_size, k, out_size, k).transpose(0, 2, 1, 3).reshape(out_size, out_size, k * k)
    out = np.zeros((out_size, out_size), np.int64)
    for y in range(out_size):
        for x in range(out_size):
            v, cnt = np.unique(blocks[y, x], return_counts=True)
            out[y, x] = v[cnt.argmax()]
    rgba, _ = finish(out, np.ones(out.shape, bool), outline=False)
    return rgba
