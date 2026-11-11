"""Crypt set for floor 1, painted in the same style as textures.py:
the iron crypt gate, the lever hidden in the tomb carvings, the burial-niche wall that
sinks away into a secret passage, plain burial niches, an ossuary wall of skulls, and the
underside of the sarcophagus lid you wake beneath."""
import numpy as np
from common import hexrgb, value_noise, Rng
from textures import stone_wall, _frame_mask, _voussoirs, SURFACES, T


def _g():
    return np.mgrid[0:T, 0:T].astype(np.float32)


def _skull(alb, emi, cx, cy, s=1.0, glow=False, tone="d9d0b4"):
    yy, xx = _g()
    cr = ((xx - cx) / (6.5 * s)) ** 2 + ((yy - cy) / (6 * s)) ** 2 < 1
    jaw = (np.abs(xx - cx) < 3.6 * s) & (yy > cy + 3 * s) & (yy < cy + 8 * s)
    m = cr | jaw
    base = hexrgb(tone)
    sh = np.clip((xx - cx + 2 * s) / (8 * s), 0, 1)
    alb[m] = (base * (1 - 0.4 * sh[..., None]))[m]
    for ex in (cx - 2.6 * s, cx + 2.6 * s):
        e = ((xx - ex) ** 2 + (yy - cy - 0.5 * s) ** 2) < (1.9 * s) ** 2
        alb[e] = hexrgb("0b0a0e")
        if glow:
            emi[e & (((xx - ex) ** 2 + (yy - cy - 0.5 * s) ** 2) < (0.9 * s) ** 2)] = hexrgb("48bba6")
    alb[(np.abs(xx - cx) < 0.9 * s) & (yy > cy + 2 * s) & (yy < cy + 4 * s)] = hexrgb("15131a")
    for tx in np.arange(cx - 2.5 * s, cx + 2.6 * s, 1.7 * s):
        alb[int(cy + 5 * s):int(cy + 6.2 * s), int(tx)] = hexrgb("3a3149")
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    alb[edge] = alb[edge] * 0.5
    return m


def crypt_gate(seed=101):
    """Ornate iron gate in a dressed-stone arch: spear-tipped bars, scrollwork, chained shut."""
    alb, emi, a = stone_wall(seed=7)
    om = _frame_mask(inner_w=72, inner_top=20, spring=44)
    alb = _voussoirs(alb, om, seed)
    yy, xx = _g()
    n = value_noise(T, T, 3, seed, 2)
    iron = hexrgb("36404c") * (0.8 + 0.4 * n[..., None])
    m = np.zeros((T, T), bool)
    bars_x = [34, 44, 54, 64, 74, 84, 94]
    for bx in bars_x:
        m |= (np.abs(xx - bx) < 2.2) & om
        # spear tips
        tip = (np.abs(xx - bx) < 4.2 - (34 - yy) * 0.45) & (yy > 26) & (yy < 36) & om
        m |= tip
    for by in (40, 100):
        m |= (np.abs(yy - by) < 2.6) & om
    # scrollwork between the cross bars
    for sx in (39, 59, 79):
        for cy_, flip in ((52, 1), (88, -1)):
            r = np.hypot(xx - sx - 5, yy - cy_)
            m |= (np.abs(r - 5) < 1.0) & ((yy - cy_) * flip > -2) & om
    # a hanging chain and padlock holding it shut
    for k in range(6):
        cy_ = 56 + k * 4
        ring = (np.abs(np.hypot((xx - 64) * (1.6 if k % 2 else 0.8), yy - cy_) - 2.4) < 0.9)
        m |= ring
    lock = (np.abs(xx - 64) < 5) & (yy > 80) & (yy < 90)
    shackle = (np.abs(np.hypot(xx - 64, yy - 80) - 3.4) < 1) & (yy < 80)
    m |= lock | shackle
    alb = np.where(m[..., None], iron, alb)
    for bx in bars_x:
        alb[om & (np.abs(xx - bx + 1) < 0.6)] = hexrgb("8497ab")
    alb[lock] = hexrgb("6a5a3a")
    alb[lock & (yy < 82)] = hexrgb("a88a50")
    alb[(np.abs(xx - 64) < 0.8) & (yy > 84) & (yy < 88)] = hexrgb("0b0a0e")
    rust = m & (value_noise(T, T, 4, seed + 3, 2) > 0.6)
    alb[rust] = alb[rust] * 0.55 + hexrgb("7b1b1d") * 0.35
    a = np.where(om & ~m, 0.0, 1.0).astype(np.float32)
    return alb, emi, a


LEVER_BOX = (40, 6, 88, 54)


def lever_wall(pulled=False, seed=111):
    """A carved memorial plaque with a skull relief; an iron lever hides in its shadowed niche."""
    alb, emi, a = stone_wall(seed=13)
    yy, xx = _g()
    x0, y0, x1, y1 = LEVER_BOX
    plaque = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    n = value_noise(T, T, 5, seed, 3)
    alb[plaque] = (hexrgb("6b6570") * (0.85 + 0.3 * n[..., None]))[plaque]
    alb[plaque & ((yy < y0 + 3) | (xx < x0 + 3))] *= 1.25
    alb[plaque & ((yy > y1 - 4) | (xx > x1 - 4))] *= 0.62
    edge = plaque & ~((xx >= x0 + 1) & (xx < x1 - 1) & (yy >= y0 + 1) & (yy < y1 - 1))
    alb[edge] = hexrgb("15131a")
    # carved border lines and a skull relief
    alb[plaque & ((np.abs(yy - (y0 + 7)) < 0.7) | (np.abs(yy - (y1 - 8)) < 0.7))] = hexrgb("2d2933")
    _skull(alb, emi, 64, 22, 1.4, tone="958b97")
    # worn inscription marks
    for k in range(8):
        alb[y1 - 5:y1 - 3, x0 + 6 + k * 5:x0 + 8 + k * 5] = hexrgb("2d2933")
    # the niche below the skull where the lever hides
    niche = (np.abs(xx - 64) < 9) & (yy > 34) & (yy < 46)
    alb[niche] = hexrgb("15131a")
    if not pulled:
        handle = (np.abs(xx - 64) < 1.4) & (yy > 30) & (yy < 42)
        knob = ((xx - 64) ** 2 + (yy - 30) ** 2) < 6
        alb[handle] = hexrgb("56667a"); alb[handle & (xx < 64)] = hexrgb("8497ab")
        alb[knob] = hexrgb("8497ab")
    else:
        handle = (np.abs(yy - 42) < 1.4) & (xx > 58) & (xx < 72)
        knob = ((xx - 72) ** 2 + (yy - 42) ** 2) < 6
        alb[handle] = hexrgb("56667a"); alb[knob] = hexrgb("8497ab")
    alb[(np.abs(xx - 64) < 2.5) & (yy > 42) & (yy < 45)] = hexrgb("36404c")
    # scratches where long-dead fingers searched for it
    for k in range(5):
        x = 50 + k * 6
        for t in range(10):
            alb[min(T - 1, 56 + t), x + t // 3] *= 0.6
    return alb, emi, a


def _niches(alb, emi, seed, rows=((22, 52), (64, 94)), cols=(18, 64, 110), with_bodies=True):
    """Arched burial niches cut into the wall, with wrapped bodies and skulls."""
    rng = Rng(seed)
    yy, xx = _g()
    for (ny0, ny1) in rows:
        for cx in cols:
            hw = 19
            niche = (np.abs(xx - cx) < hw) & (yy > ny0 + 8) & (yy < ny1)
            top = ((xx - cx) ** 2 / hw ** 2 + (yy - ny0 - 8) ** 2 / 8 ** 2 < 1) & (yy <= ny0 + 8)
            nm = (niche | top)
            frame = (np.abs(xx - cx) < hw + 3) & (yy > ny0 + 4) & (yy < ny1 + 3) & ~nm
            frame |= ((xx - cx) ** 2 / (hw + 3) ** 2 + (yy - ny0 - 8) ** 2 / 11 ** 2 < 1) & (yy <= ny0 + 8) & ~nm
            alb[frame] = hexrgb("7f7585")
            alb[frame & (yy > ny1)] = hexrgb("4b4458")
            alb[nm] = hexrgb("0f0d13")
            alb[nm & (yy < ny0 + 12)] = hexrgb("0a090d")
            if with_bodies:
                if rng.u() < 0.65:
                    # shroud-wrapped body lying along the niche
                    body = (((xx - cx) / (hw - 3)) ** 2 + ((yy - ny1 + 6) / 5.5) ** 2 < 1) & nm
                    alb[body] = hexrgb("a39a7c") * (0.8 + 0.3 * value_noise(T, T, 3, seed + int(cx), 2)[body][:, None])
                    for k in range(-14, 15, 5):
                        alb[body & (np.abs(xx - cx - k) < 0.8)] *= 0.7
                    _skull(alb, emi, cx - hw + 7, ny1 - 9, 0.75)
                else:
                    for k in range(3):
                        _skull(alb, emi, cx - 9 + k * 9, ny1 - 6, 0.7)
    return alb


def loculi(seed=131):
    alb, emi, a = stone_wall(seed=7)
    alb = _niches(alb, emi, seed)
    return alb, emi, a


def tomb_wall(stage=0, seed=141):
    """The burial-niche panel hiding the secret passage. Stages 1-3: it cracks free and
    sinks into the floor, opening from the top down."""
    alb, emi, a = stone_wall(seed=7)
    yy, xx = _g()
    om = _frame_mask(inner_w=84, inner_top=14, spring=46)
    drop = {0: 0, 1: 4, 2: 40, 3: 92}[stage]
    panel_alb = loculi(seed)[0]
    # the panel slides down: shift its picture by `drop`
    shifted = np.zeros_like(panel_alb)
    if drop < T:
        shifted[drop:] = panel_alb[:T - drop]
    alb = np.where(om[..., None], shifted, alb)
    if stage >= 1:
        ring = _frame_mask(inner_w=86, inner_top=13, spring=46) & ~_frame_mask(inner_w=82, inner_top=15, spring=46)
        alb[ring] = hexrgb("0b0a0e")
        dust = (value_noise(T, T, 2, seed + stage, 1) > 0.78) & (yy > 112) & om
        alb[dust] = hexrgb("b1aaac")
    if stage >= 2:
        hole = om & (yy < drop + 2)
        a = np.where(hole, 0.0, 1.0).astype(np.float32)
        alb[om & (np.abs(yy - drop - 2) < 2)] = hexrgb("2a2236")
    return alb, emi, a


def ossuary(seed=151):
    """A wall packed with skulls and long bones, the way the old ossuaries were stacked."""
    alb, emi, a = stone_wall(seed=7)
    yy, xx = _g()
    rng = Rng(seed)
    # bone rows
    for by in (30, 62, 94, 120):
        band = (np.abs(yy - by) < 4)
        alb[band] = hexrgb("a39a7c") * (0.8 + 0.3 * value_noise(T, T, 2, seed + by, 2)[band][:, None])
        for k in range(0, T, 9):
            knob = ((xx - k) ** 2 + (yy - by) ** 2) < 16
            alb[knob] = hexrgb("cdc4a8")
        alb[np.abs(yy - by - 4) < 0.8] = hexrgb("2d2933")
        alb[np.abs(yy - by + 4) < 0.8] = hexrgb("4b4458")
    # skull rows between them
    for row, cy in enumerate((14, 46, 78, 108)):
        off = 0 if row % 2 else 8
        for cx in range(4 + off, T, 16):
            _skull(alb, emi, cx, cy, rng.u(0.95, 1.1), tone=["d9d0b4", "c8bda0", "e2d9c0"][rng.i(0, 2)])
    gaps = (alb.sum(-1) > 0) & False
    return alb, emi, a


def lid_underside(seed=161):
    """What you see when you wake: the underside of your sarcophagus lid, inches away."""
    yy, xx = _g()
    n = value_noise(T, T, 14, seed, 4)
    n2 = value_noise(T, T, 3, seed + 1, 2)
    alb = hexrgb("41384d") * (0.7 + 0.5 * n[..., None]) * (0.9 + 0.2 * n2[..., None])
    # fingernail scratches from someone who woke here before
    rng = Rng(seed)
    for g in range(4):
        x0, y0 = rng.u(20, 100), rng.u(30, 90)
        for k in range(4):
            for t in range(18):
                x = int(x0 + k * 3 + t * 0.15); y = int(y0 + t)
                if 0 <= x < T and 0 <= y < T:
                    alb[y, x] = hexrgb("958b97")
                    if x + 1 < T:
                        alb[y, x + 1] = hexrgb("15131a")
    # carved inverted cross and an inscription, mirrored from this side
    alb[(np.abs(xx - 64) < 2) & (yy > 40) & (yy < 86)] = hexrgb("221b2c")
    alb[(np.abs(yy - 74) < 2) & (np.abs(xx - 64) < 13)] = hexrgb("221b2c")
    for k in range(10):
        alb[100:104, 30 + k * 7:33 + k * 7] = hexrgb("221b2c")
    emi = np.zeros_like(alb)
    return alb, emi, np.ones((T, T), np.float32)


CRYPT = {
    "bars": crypt_gate,
    "lever": lambda: lever_wall(False),
    "lever_on": lambda: lever_wall(True),
    "tomb": lambda: tomb_wall(0),
    "tomb1": lambda: tomb_wall(1),
    "tomb2": lambda: tomb_wall(2),
    "tomb3": lambda: tomb_wall(3),
    "loculi": loculi,
    "ossuary": ossuary,
}
SURFACES.update(CRYPT)
for old in ("switch", "switch_on", "bed", "bed1", "bed2", "bed3"):
    SURFACES.pop(old, None)
