"""Outdoor surfaces: the prison's outer walls, the Ashen Wood and the town of Hollowmere.
Same contract as textures.py: (albedo, emissive, alpha) 128x128."""
import numpy as np
from common import hexrgb, value_noise, Rng
from textures import _frame_mask, _voussoirs, stone_wall, T


def _grid():
    return np.mgrid[0:T, 0:T].astype(np.float32)


def _blank(col="000000"):
    alb = np.zeros((T, T, 3), np.float32); alb[:] = hexrgb(col)
    return alb, np.zeros((T, T, 3), np.float32), np.ones((T, T), np.float32)


# ------------------------------------------------------------------- forest
def _foliage(alb, a, yy, xx, seed, top_min, top_max, cols, density=1.0):
    """Leafy canopy with a ragged top edge (alpha) so the sky shows through."""
    rng = Rng(seed)
    edge = top_min + (top_max - top_min) * value_noise(T, T, 9, seed, 3)[0]
    n = value_noise(T, T, 3, seed + 1, 3)
    clump = value_noise(T, T, 7, seed + 2, 2)
    canopy_bottom = top_max + 26
    m = (yy >= edge[None, :]) & (yy < canopy_bottom + 10 * clump)
    # holes in the canopy
    holes = (value_noise(T, T, 5, seed + 3, 2) > 0.74 - 0.1 * (1 - density)) & (yy < top_max + 8)
    a[(yy < edge[None, :]) | holes] = 0.0
    shade = 0.55 + 0.6 * clump + 0.25 * (n - 0.5)
    # leaves lit from above: lighter on top of clumps
    top_light = np.clip(1.0 - (yy - edge[None, :]) / 22.0, 0, 1) * 0.35
    c0, c1 = hexrgb(cols[0]), hexrgb(cols[1])
    mix = np.clip((shade + top_light - 0.5) * 1.4, 0, 1)[..., None]
    col = c0 * (1 - mix) + c1 * mix
    alb[m] = col[m]
    return m


def _trunk(alb, yy, xx, x0, w, lean, col, seed, roots=True):
    n = value_noise(T, T, 2, seed, 2)
    stripes = value_noise(T, T, 1, seed + 5, 1)
    cx = x0 + lean * (T - yy) / T
    flare = np.where(yy > 100, (yy - 100) * 0.35, 0) if roots else 0
    half = w / 2 + flare
    m = np.abs(xx - cx) < half
    rel = (xx - cx) / np.maximum(half, 1)
    shade = 0.95 - 0.55 * rel - 0.25 * rel * rel  # lit from the left
    bark = hexrgb(col) * shade[..., None] * (0.75 + 0.45 * n[..., None])
    grooves = ((xx - cx + 3 * stripes) % 5) < 1.3
    bark = np.where(grooves[..., None], bark * 0.6, bark)
    alb[m] = bark[m]
    return m


def tree(variant=0, seed=301):
    alb, emi, a = _blank("0f160b")
    yy, xx = _grid()
    deep = value_noise(T, T, 6, seed, 3)
    alb[:] = (hexrgb("0f160b") * (0.6 + 0.8 * deep[..., None]))
    # far trunks in the gloom
    for k, fx in enumerate((18, 57, 96, 118)):
        _trunk(alb, yy, xx, fx + 6 * np.sin(seed + k), 7, 3, "1a0e0a", seed + 20 + k, roots=False)
    if variant == 0:
        trunks = [(30, 20, -6, "4b3a2a"), (84, 26, 5, "52402c")]
        cols = ("17210f", "4e6a27")
    elif variant == 1:
        trunks = [(22, 14, 3, "b8b0a0"), (64, 12, -4, "c8c0ae"), (104, 16, 2, "a8a092")]
        cols = ("212f14", "627f31")
    else:
        trunks = [(60, 24, -10, "3a3026")]
        cols = ("17210f", "2f431a")
    for (x0, w, lean, col) in trunks:
        m = _trunk(alb, yy, xx, x0, w, lean, col, seed + x0)
        if variant == 1:  # birch marks
            marks = m & (value_noise(T, T, 2, seed + x0, 1) > 0.7) & (((yy + x0) % 9) < 2)
            alb[marks] = hexrgb("1a1611")
    if variant == 2:
        # twisted dead branches reaching up, and a hanging iron cage
        for (bx, by, ex, ey) in ((60, 60, 20, 20), (62, 50, 104, 14), (58, 80, 12, 64), (64, 70, 118, 50)):
            for t in np.linspace(0, 1, 60):
                px_, py_ = bx + (ex - bx) * t, by + (ey - by) * t - 8 * np.sin(t * 3)
                r = 4 * (1 - t) + 1
                m = (xx - px_) ** 2 + (yy - py_) ** 2 < r * r
                alb[m] = hexrgb("3a3026") * (0.7 + 0.3 * (xx[m] < px_))[:, None]
        alb[(np.abs(xx - 100) < 0.8) & (yy > 18) & (yy < 40)] = hexrgb("36404c")
        cage = (np.abs(xx - 100) < 9) & (yy > 40) & (yy < 66)
        bars = cage & ((((xx - 91) % 4) < 1.2) | (np.abs(yy - 40) < 1.5) | (np.abs(yy - 65) < 1.5))
        alb[bars] = hexrgb("56667a")
        # a skull inside the cage
        sk = ((xx - 100) ** 2 / 16 + (yy - 58) ** 2 / 12) < 1
        alb[sk & ~bars] = hexrgb("d9d0b4")
    canopy = _foliage(alb, a, yy, xx, seed + 7, 2 if variant != 2 else 30, 22 if variant != 2 else 60, cols,
                      density=1.0 if variant != 2 else 0.4)
    if variant == 2:
        a[:] = np.where(yy < 70, np.where(alb.sum(-1) > 0, a, 0), a)
    # undergrowth: ferns and roots
    ferns = (yy > 96 + 14 * value_noise(T, T, 6, seed + 9, 2)) & (value_noise(T, T, 3, seed + 10, 2) > 0.35)
    fcol = np.where((value_noise(T, T, 2, seed + 11, 1) > 0.5)[..., None], hexrgb("3d561f"), hexrgb("212f14"))
    alb[ferns] = fcol[ferns]
    alb[yy > 122] *= 0.6
    return alb, emi, a


def _ashlar(alb, yy, xx, seed, rows=4, base="4b4558"):
    rng = Rng(seed)
    n1 = value_noise(T, T, 12, seed, 4)
    h = T // rows
    alb[:] = hexrgb("17121f")
    for r in range(rows):
        off = rng.i(0, 40) if r % 2 else rng.i(0, 10)
        x = -off
        while x < T:
            w = rng.i(38, 60)
            m = ((xx - x) % T < w - 2) & ((xx - x) % T >= 0) & (yy > r * h + 1) & (yy < (r + 1) * h - 1)
            m = (xx >= x) & (xx < x + w - 2) & (yy > r * h + 1) & (yy < (r + 1) * h - 1)
            tone = rng.u(0.85, 1.1)
            col = hexrgb(base) * tone * (0.8 + 0.4 * n1[..., None])
            col = np.where((yy < r * h + 4)[..., None], col * 1.15, col)
            col = np.where((yy > (r + 1) * h - 5)[..., None], col * 0.7, col)
            alb[m] = col[m]
            x += w
    # weather streaks
    st = value_noise(T, T, 3, seed + 4, 2)
    streak = (st > 0.62) & (((xx * 7) % 13) < 3)
    alb[streak] *= 0.75
    return alb


def prison_ext(window=False, seed=331):
    alb, emi, a = _blank()
    yy, xx = _grid()
    alb = _ashlar(alb, yy, xx, seed)
    # moss creeping up from the ground
    mn = value_noise(T, T, 8, seed + 2, 3)
    moss = (mn + yy / T * 0.6 > 1.05)
    alb[moss] = alb[moss] * 0.4 + hexrgb("3d561f") * 0.6
    if window:
        win = (np.abs(xx - 64) < 12) & (yy > 30) & (yy < 62)
        archtop = ((xx - 64) ** 2 + (yy - 42) ** 2 < 144) & (yy < 42)
        w = (win & (yy >= 42)) | archtop
        frame = (np.abs(xx - 64) < 16) & (yy > 26) & (yy < 66) & ~w
        alb[frame & (((yy > 62)) | (np.abs(xx - 64) > 12))] = hexrgb("7f7585")
        alb[w] = hexrgb("0c0706")
        glow = np.exp(-((xx - 64) ** 2 + (yy - 50) ** 2) / 200.0)
        emi[w] = (hexrgb("a26833") * glow[..., None] * 0.9)[w]
        for bx in (57, 64, 71):
            alb[w & (np.abs(xx - bx) < 1.2)] = hexrgb("4d5c71")
            emi[w & (np.abs(xx - bx) < 1.2)] = 0
        alb[(np.abs(yy - 64) < 2) & (np.abs(xx - 64) < 17)] = hexrgb("958b97")
    return alb, emi, a


def prison_door(seed=341):
    alb, emi, a = prison_ext(False, seed)
    om = _frame_mask(inner_w=70, inner_top=26, spring=56)
    alb = _voussoirs(alb, om, seed)
    yy, xx = _grid()
    inside = np.zeros((T, T, 3), np.float32); inside[:] = hexrgb("0c0912")
    for (y1, y0, br) in ((122, 112, 0.5), (112, 104, 0.35), (104, 98, 0.22), (98, 93, 0.12)):
        m = (yy >= y0) & (yy < y1)
        inside[m] = hexrgb("685e72") * br
    alb[om] = inside[om]
    return alb, emi, a


def palisade(seed=351):
    alb, emi, a = _blank("1a0e0a")
    yy, xx = _grid()
    n = value_noise(T, T, 2, seed, 2)
    rng = Rng(seed)
    x = 0
    while x < T:
        w = rng.i(13, 17)
        cx = x + w / 2
        tip = 6 + rng.i(0, 8)
        log = (xx >= x) & (xx < x + w - 1) & (yy > tip + np.abs(xx - cx) * 1.2)
        rel = (xx - cx) / (w / 2)
        shade = 0.95 - 0.5 * rel
        col = hexrgb("6b3c1c") * rng.u(0.8, 1.1) * shade[..., None] * (0.75 + 0.45 * n[..., None])
        alb[log] = col[log]
        x += w
    a[alb.sum(-1) < 40] = 0
    a[yy > 20] = 1.0
    alb[(a > 0) & (alb.sum(-1) < 40)] = hexrgb("0c0706")
    for by in (40, 92):
        band = (np.abs(yy - by - 2 * np.sin(xx / 6)) < 2)
        alb[band] = hexrgb("a7997c") * (0.8 + 0.3 * n[band][:, None])
    return alb, emi, a


def town_gate(seed=361):
    alb, emi, a = palisade(seed)
    yy, xx = _grid()
    n = value_noise(T, T, 2, seed + 1, 2)
    g = (np.abs(xx - 64) < 34) & (yy > 30)
    planks = hexrgb("522d17") * (0.8 + 0.4 * n[..., None]) * np.where((((xx - 30) % 10) < 1)[..., None], 0.55, 1.0)
    alb[g] = planks[g]
    alb[g & (np.abs(xx - 64) < 1)] = hexrgb("1a0e0a")
    for by in (48, 96):
        s = g & (np.abs(yy - by) < 3)
        alb[s] = hexrgb("2d3849")
        alb[s & (yy < by - 1)] = hexrgb("627286")
    # little roof over the gate
    roof = (yy > 18) & (yy < 30) & (np.abs(xx - 64) < 42 - (30 - yy) * 0.8)
    alb[roof] = (hexrgb("41384d") * np.where((((xx // 4) + (yy // 3)) % 2 == 0)[..., None], 1.0, 0.8))[roof]
    a[roof] = 1.0
    # two lanterns
    for lx in (24, 104):
        alb[(np.abs(xx - lx) < 1) & (yy > 36) & (yy < 46)] = hexrgb("2d3849")
        lm = (np.abs(xx - lx) < 5) & (yy > 46) & (yy < 60)
        alb[lm] = hexrgb("2d3849")
        core = (np.abs(xx - lx) < 3) & (yy > 48) & (yy < 58)
        emi[core] = hexrgb("fdd687")
        emi += hexrgb("e77b22")[None, None, :] * 0.45 * np.exp(-((xx - lx) ** 2 + (yy - 53) ** 2) / 260.0)[..., None]
    return alb, emi, a


# --------------------------------------------------------------------- town
def _house_base(seed, plaster="cbbfa6"):
    alb, emi, a = _blank()
    yy, xx = _grid()
    n = value_noise(T, T, 6, seed, 3)
    # stone footing
    foot = yy > 92
    alb[foot] = _ashlar(np.zeros_like(alb), yy, xx, seed + 1, rows=8, base="544a60")[foot]
    # plaster with timber frame
    pl = (yy > 22) & (yy <= 92)
    alb[pl] = (hexrgb(plaster) * (0.82 + 0.25 * n[..., None]))[pl]
    stain = value_noise(T, T, 10, seed + 2, 3) > 0.62
    alb[pl & stain] *= 0.85
    beam = hexrgb("381f11")
    for bx in (2, 42, 86, 125):
        alb[pl & (np.abs(xx - bx) < 3)] = beam
    alb[(np.abs(yy - 24) < 3)] = beam
    alb[(np.abs(yy - 90) < 3)] = beam
    alb[(np.abs(yy - 56) < 2) & pl] = beam
    for (x0, x1) in ((4, 40), (88, 124)):
        for t in np.linspace(0, 1, 50):
            x_ = x0 + (x1 - x0) * t; y_ = 26 + 28 * t
            alb[(np.abs(xx - x_) < 2) & (np.abs(yy - y_) < 2)] = beam
    # roof eave: dark tiles with a ragged top against the sky
    roof = yy <= 22
    tiles = hexrgb("3a0d11") * np.where(((((xx + (yy // 6) * 5) // 10) % 2) == 0)[..., None], 0.9, 1.1)
    tiles = np.where(((yy % 6) < 1)[..., None], tiles * 0.5, tiles)
    alb[roof] = tiles[roof]
    alb[np.abs(yy - 21) < 1.5] = hexrgb("1b070a")
    a[yy < 4 + 3 * value_noise(T, T, 4, seed + 3, 1)] = 0
    return alb, emi, a, yy, xx


def _window(alb, emi, yy, xx, cx, cy, lit, w=14, h=18):
    m = (np.abs(xx - cx) < w / 2) & (np.abs(yy - cy) < h / 2)
    alb[(np.abs(xx - cx) < w / 2 + 2) & (np.abs(yy - cy) < h / 2 + 2)] = hexrgb("381f11")
    if lit:
        alb[m] = 0
        g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / 90.0)
        emi[m] = (hexrgb("f09c3b") * (0.7 + 0.5 * g[..., None]))[m]
    else:
        alb[m] = hexrgb("0e121a")
    mull = m & ((np.abs(xx - cx) < 1) | (np.abs(yy - cy) < 1))
    alb[mull] = hexrgb("381f11"); emi[mull] = 0
    # shutters
    for s in (-1, 1):
        sh = (np.abs(xx - (cx + s * (w / 2 + 6))) < 5) & (np.abs(yy - cy) < h / 2 + 1)
        alb[sh] = (hexrgb("2f431a") * np.where((((yy - cy) % 4) < 1)[..., None], 0.6, 1.0))[sh]


def _door(alb, emi, yy, xx, cx, w=26):
    m = (np.abs(xx - cx) < w / 2) & (yy > 66) & (yy < 124)
    top = ((xx - cx) ** 2 + (yy - 70) ** 2 < (w / 2) ** 2) & (yy <= 70) & (yy > 56)
    d = m | top
    alb[((np.abs(xx - cx) < w / 2 + 3) & (yy > 70) & (yy < 124)) | (((xx - cx) ** 2 + (yy - 70) ** 2 < (w / 2 + 3) ** 2) & (yy <= 70))] = hexrgb("41384d")
    n = value_noise(T, T, 2, int(cx), 2)
    wood = hexrgb("6b3c1c") * (0.75 + 0.4 * n[..., None]) * np.where((((xx - cx) % 6) < 1)[..., None], 0.55, 1.0)
    alb[d] = wood[d]
    alb[d & (np.abs(yy - 80) < 1.5)] = hexrgb("2d3849")
    alb[d & (np.abs(yy - 110) < 1.5)] = hexrgb("2d3849")
    alb[(np.abs(xx - cx - w / 2 + 5) < 1.5) & (np.abs(yy - 96) < 1.5)] = hexrgb("be8041")


def house(variant=0, seed=371):
    alb, emi, a, yy, xx = _house_base(seed + variant * 7, plaster=["cbbfa6", "b9a98c"][variant % 2])
    if variant == 0:
        _window(alb, emi, yy, xx, 24, 40, False)
        _window(alb, emi, yy, xx, 104, 40, True)
        _window(alb, emi, yy, xx, 64, 74, False, w=18, h=12)
    else:
        _window(alb, emi, yy, xx, 64, 40, True)
        _door(alb, emi, yy, xx, 36)
        _window(alb, emi, yy, xx, 98, 106, False, w=12, h=10)
    return alb, emi, a


def inn(seed=391):
    alb, emi, a, yy, xx = _house_base(seed, plaster="d8ccb1")
    _window(alb, emi, yy, xx, 24, 40, True)
    _window(alb, emi, yy, xx, 104, 40, True)
    _door(alb, emi, yy, xx, 64, w=30)
    # hanging sign with a tankard
    alb[(np.abs(yy - 54) < 1.2) & (xx > 84) & (xx < 112)] = hexrgb("2d3849")
    sign = (xx > 88) & (xx < 112) & (yy > 58) & (yy < 76)
    alb[sign] = hexrgb("864f26")
    alb[sign & ((xx < 90) | (xx > 109) | (yy < 60) | (yy > 73))] = hexrgb("381f11")
    mug = (xx > 95) & (xx < 104) & (yy > 62) & (yy < 72)
    alb[mug] = hexrgb("d39f5f")
    alb[(xx > 95) & (xx < 104) & (yy > 61) & (yy < 64)] = hexrgb("f0e6cc")
    alb[(np.abs(xx - 105.5) < 1.2) & (yy > 64) & (yy < 70)] = hexrgb("d39f5f")
    # lantern by the door
    lm = (np.abs(xx - 40) < 3) & (yy > 66) & (yy < 76)
    emi[lm] = hexrgb("fdd687")
    emi += hexrgb("e77b22")[None, None, :] * 0.35 * np.exp(-((xx - 40) ** 2 + (yy - 71) ** 2) / 200.0)[..., None]
    return alb, emi, a


def chapel(seed=401):
    alb, emi, a = _blank()
    yy, xx = _grid()
    alb = _ashlar(alb, yy, xx, seed, rows=6, base="685e72")
    # tall pointed stained-glass window
    w = (np.abs(xx - 64) < 14) & (yy > 34) & (yy < 104)
    tip = (np.abs(xx - 64) < 14 - (34 - yy) * 0.7) & (yy <= 34) & (yy > 14)
    win = w | tip
    frame = (np.abs(xx - 64) < 18) & (yy > 10) & (yy < 108) & ~win
    frame &= (np.abs(xx - 64) < 18 - np.clip(34 - yy, 0, 99) * 0.7)
    alb[frame] = hexrgb("958b97")
    alb[win] = 0
    lead = ((((xx - 64) + (yy * 0.6)) % 9) < 1.2) | ((((xx - 64) - (yy * 0.6)) % 9) < 1.2)
    glass = np.where(((xx - 64 + 40) // 7 % 3 == 0)[..., None], hexrgb("7a3eaa"),
                     np.where(((yy // 9) % 2 == 0)[..., None], hexrgb("369a89"), hexrgb("be442e")))
    emi[win & ~lead] = (glass * 0.85)[win & ~lead]
    alb[win & lead] = hexrgb("17121f")
    return alb, emi, a


def exit_stairs(seed=421):
    """Dungeon exit: stairs climbing up toward pale moonlight."""
    alb, emi, a = stone_wall(seed=7)
    om = _frame_mask()
    alb = _voussoirs(alb, om, seed)
    yy, xx = _grid()
    inside = np.zeros((T, T, 3), np.float32)
    inside[:] = hexrgb("1e0d30")
    moon = np.clip(1 - (yy - 24) / 70, 0, 1)
    em = np.zeros((T, T, 3), np.float32)
    em[:] = hexrgb("6dccb9") * (moon ** 2)[..., None] * 0.55
    steps = [(122, 114), (110, 103), (99, 93), (89, 84), (80, 76), (72, 69)]
    for i, (y1, y0) in enumerate(steps):
        m = (yy >= y0) & (yy < y1) & (np.abs(xx - 63.5) < 30 - i * 2)
        inside[m] = hexrgb("958b97") * (0.55 + 0.08 * i)
        inside[m & (yy < y0 + 2)] = hexrgb("ccc3be")
        em[m] *= 0.3
    alb[om] = inside[om]
    emi[om] = em[om]
    return alb, emi, a


OUT_SURFACES = {
    "tree": lambda: tree(0),
    "tree2": lambda: tree(1, 311),
    "tree3": lambda: tree(2, 321),
    "prison": lambda: prison_ext(False),
    "prisonwin": lambda: prison_ext(True),
    "pdoor": prison_door,
    "palisade": palisade,
    "towngate": town_gate,
    "house": lambda: house(0),
    "house2": lambda: house(1),
    "inn": inn,
    "chapel": chapel,
    "exit": exit_stairs,
}


# ----------------------------------------------------------------- grounds
def forest_floor(seed=501):
    yy, xx = _grid()
    n1 = value_noise(T, T, 10, seed, 4)
    n2 = value_noise(T, T, 3, seed + 1, 2)
    alb = hexrgb("2f431a") * (0.6 + 0.6 * n1[..., None])
    dirt = value_noise(T, T, 16, seed + 2, 3) > 0.55
    alb[dirt] = (hexrgb("4b4333") * (0.7 + 0.5 * n2[..., None]))[dirt]
    blades = (n2 > 0.62) & ~dirt
    alb[blades] = hexrgb("4e6a27")
    leaves = (value_noise(T, T, 2, seed + 3, 1) > 0.84)
    alb[leaves] = np.where((n1[leaves] > 0.35)[:, None], hexrgb("6b3c1c"), hexrgb("6e181b"))
    return alb


def cobbles(seed=511):
    yy, xx = _grid()
    rng = Rng(seed)
    alb = np.zeros((T, T, 3), np.float32); alb[:] = hexrgb("17121f")
    n = value_noise(T, T, 3, seed, 2)
    for r in range(8):
        off = (r % 2) * 8
        for c in range(9):
            cx = c * 16 + off - 8 + rng.u(-1.5, 1.5); cy = r * 16 + 8 + rng.u(-1.5, 1.5)
            for dy in (-T, 0, T):
                for dx in (-T, 0, T):
                    m = ((xx - cx - dx) / 7.2) ** 2 + ((yy - cy - dy) / 6.6) ** 2 < 1
                    if not m.any():
                        continue
                    base = hexrgb(["685e72", "5d5369", "726677", "7f7585"][rng.i(0, 3)])
                    rel = (yy - cy - dy) / 6.6
                    col = base * (1.1 - 0.35 * rel[..., None]) * (0.85 + 0.3 * n[..., None])
                    alb[m] = col[m]
    return alb


def sky(theme, seed=521, facing=0):
    """Night sky painted in screen space for the 128x128 view (top half), with a
    silhouette on the horizon: treeline for the wood, rooftops for the town."""
    V = 128
    yy, xx = np.mgrid[0:V, 0:V].astype(np.float32)
    t = np.clip(yy / 64.0, 0, 1)
    top, mid, hor = hexrgb("0a0612"), hexrgb("1e0d30"), hexrgb("165048")
    col = np.where((t < 0.6)[..., None], top * (1 - t[..., None] / 0.6) + mid * (t[..., None] / 0.6),
                   mid * (1 - (t[..., None] - 0.6) / 0.4) + hor * ((t[..., None] - 0.6) / 0.4))
    emi = np.zeros_like(col)
    rng = np.random.default_rng(seed + facing * 17)
    for _ in range(46):
        sx, sy = rng.integers(0, V), rng.integers(0, 44)
        b = rng.uniform(0.4, 1.0)
        emi[sy, sx] = hexrgb("d0f8ec") * b
    # the moon, ringed by a violet curse halo
    if facing == 0:  # the moon hangs in the north
        mx, my = 34, 20
        r = np.hypot(xx - mx, yy - my)
        halo = np.exp(-((r - 13) ** 2) / 20.0) * 0.5
        emi += hexrgb("7a3eaa")[None, None, :] * halo[..., None]
        moon = r < 8.5
        crater = value_noise(V, V, 3, seed, 2)
        emi[moon] = (hexrgb("e8dfd2") * (0.85 + 0.25 * crater[..., None]) * (1 - 0.25 * np.clip((xx - mx) / 9, 0, 1))[..., None])[moon]
    # clouds
    cl = value_noise(V, V, 14, seed + 1 + facing * 5, 3)
    cloud = (cl > 0.6) & (yy > 10) & (yy < 50)
    col[cloud] = col[cloud] * 0.6 + hexrgb("41384d") * 0.4
    emi[cloud] *= 0.3
    # horizon silhouette
    if theme == "forest":
        ridge = 52 + 9 * value_noise(V, V, 6, seed + 2 + facing * 7, 3)[0] - 6 * (np.abs(((xx[0] * 0.7) % 9) - 4.5) < 2)
        sil = yy >= ridge[None, :]
        col[sil] = hexrgb("07090d"); emi[sil] = 0
    elif theme == "town":
        rng2 = np.random.default_rng(seed + 3 + facing * 11)
        h = np.full(V, 58.0)
        x = 0
        while x < V:
            w = int(rng2.integers(10, 22)); top_ = 44 + rng2.integers(0, 10)
            for i in range(w):
                if x + i < V:
                    peak = top_ + abs(i - w / 2) * 0.9
                    h[x + i] = min(h[x + i], peak)
            if rng2.random() < 0.3 and x + w // 2 < V:
                h[x + w // 2] = top_ - 9  # chimney / spire
                if x + w // 2 + 1 < V: h[x + w // 2 + 1] = top_ - 9
            x += w
        sil = yy >= h[None, :]
        col[sil] = hexrgb("0c0912"); emi[sil] = 0
        for _ in range(7):
            wx, wy = rng2.integers(4, V - 4), rng2.integers(52, 62)
            if yy[wy, wx] >= h[wx] + 2:
                emi[wy:wy + 2, wx:wx + 2] = hexrgb("f09c3b")
    return col, emi
