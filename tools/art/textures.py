"""Hand-tuned 128x128 surface paintings.  Each returns (albedo RGB float, emissive RGB float, alpha float).
Walls tile horizontally so neighbouring cells join without seams."""
import numpy as np
from common import hexrgb, value_noise, Rng

T = 128


def _blank():
    return np.zeros((T, T, 3), np.float32), np.zeros((T, T, 3), np.float32), np.ones((T, T), np.float32)


def stone_wall(seed=7):
    rng = Rng(seed)
    alb, emi, a = _blank()
    mortar = hexrgb("1a171f")
    alb[:] = mortar
    n1 = value_noise(T, T, 16, seed + 1, 4)
    n2 = value_noise(T, T, 4, seed + 2, 2)
    rows = [26, 25, 27, 24, 26]
    y = 0
    bricks = []
    for r, rh in enumerate(rows):
        x = rng.i(0, 30) if r % 2 else rng.i(10, 22)
        x0 = x
        while x < x0 + T:
            bw = rng.i(30, 48)
            if x + bw > x0 + T - 18:
                bw = x0 + T - x
            bricks.append((x, y, bw, rh))
            x += bw
        y += rh
    yy, xx = np.mgrid[0:T, 0:T]
    tones = ["58525e", "625c66", "6b6570", "5d5560", "6a6168", "54505c"]
    for (bx, by, bw, bh) in bricks:
        base = hexrgb(tones[rng.i(0, len(tones) - 1)]) * rng.u(0.9, 1.08)
        warm = rng.u(-3, 3)
        base = base + np.array([warm, warm * 0.5, -warm * 0.3])
        lx = (xx - bx) % T
        ly = yy - by
        inside = (lx >= 1) & (lx < bw - 1) & (ly >= 1) & (ly < bh - 1)
        # rounded / chipped corners
        cx = np.minimum(lx - 1, bw - 2 - lx); cy = np.minimum(ly - 1, bh - 2 - ly)
        chip = (np.minimum(cx, cy) < 2 + 3 * n2) & (np.minimum(cx, cy) < 1.2 + 4 * (n2 - 0.35))
        m = inside & ~((cx < 3) & (cy < 3) & (cx + cy < 2 + 4 * n2))
        col = base[None, None, :] * (0.82 + 0.36 * n1[..., None]) + (n2[..., None] - 0.5) * 18
        # bevel: lit from above (torch is near eye level, painted light comes from up-left)
        top = (ly < 4); left = (lx < 3); bot = (ly > bh - 5); right = (lx > bw - 4)
        shade = np.ones((T, T), np.float32)
        shade = np.where(top, 1.22, shade)
        shade = np.where(left & ~top, 1.10, shade)
        shade = np.where(bot, 0.62, shade)
        shade = np.where(right & ~bot, 0.78, shade)
        col = col * shade[..., None]
        alb[m] = col[m]
    # cracks
    for _ in range(7):
        x = rng.u(0, T); y = rng.u(0, T); ang = rng.u(0, 6.28)
        for s in range(rng.i(10, 26)):
            ang += rng.u(-0.6, 0.6)
            x = (x + np.cos(ang)) % T; y = min(max(y + np.sin(ang), 0), T - 1)
            xi, yi = int(x), int(y)
            alb[yi, xi] = alb[yi, xi] * 0.45
            if yi + 1 < T:
                alb[yi + 1, xi] = np.minimum(alb[yi + 1, xi] * 1.06, 255)
    # moss and damp near the floor and in mortar
    mn = value_noise(T, T, 10, seed + 9, 3)
    moss_mask = (mn + (yy / T) * 0.55 > 0.98) & (alb.sum(-1) < 420)
    mcol = np.where((n2 > 0.5)[..., None], hexrgb("4a5e2a"), hexrgb("2e3d1c"))
    alb[moss_mask] = alb[moss_mask] * 0.3 + mcol[moss_mask] * 0.7
    # grime gradient
    g = 1.0 - 0.28 * (yy / T) ** 2 - 0.12 * (1 - yy / T) ** 6
    alb *= g[..., None]
    return alb, emi, a


def flagstone_floor(seed=21):
    rng = Rng(seed)
    alb = np.zeros((T, T, 3), np.float32)
    alb[:] = hexrgb("15131a")
    n1 = value_noise(T, T, 20, seed, 4)
    n2 = value_noise(T, T, 5, seed + 3, 2)
    yy, xx = np.mgrid[0:T, 0:T]
    # 2x2 big slabs per cell, slightly irregular
    cuts_x = [0, 62 + rng.i(-4, 4), T]
    for j in range(2):
        cy0, cy1 = (0, 64) if j == 0 else (64, T)
        offs = rng.i(-10, 10)
        cxs = [0, 64 + offs, T]
        for i in range(2):
            x0, x1 = cxs[i], cxs[i + 1]
            m = (xx > x0 + 1) & (xx < x1 - 2) & (yy > cy0 + 1) & (yy < cy1 - 2)
            base = hexrgb(["4d4853", "534d58", "48434f", "57515b"][rng.i(0, 3)])
            col = base * (0.78 + 0.4 * n1[..., None]) + (n2[..., None] - 0.5) * 16
            edge = (yy < cy0 + 4) | (xx < x0 + 4)
            col = np.where(edge[..., None], col * 1.15, col)
            far_edge = (yy > cy1 - 5) | (xx > x1 - 5)
            col = np.where(far_edge[..., None], col * 0.7, col)
            alb[m] = col[m]
    # stains
    st = value_noise(T, T, 24, seed + 8, 3)
    alb = np.where((st > 0.66)[..., None], alb * 0.72 + hexrgb("33200f") * 0.12, alb)
    for _ in range(14):
        x, y = rng.i(0, T - 3), rng.i(0, T - 3)
        alb[y:y + 2, x:x + 2] *= 0.6
    return alb


def ceiling(seed=33):
    rng = Rng(seed)
    alb = np.zeros((T, T, 3), np.float32)
    alb[:] = hexrgb("15131a")
    n1 = value_noise(T, T, 14, seed, 4)
    yy, xx = np.mgrid[0:T, 0:T]
    for j in range(4):
        y0 = j * 32
        off = rng.i(0, 40)
        x = -off
        while x < T:
            w = rng.i(36, 56)
            m = ((xx - x) % T < w - 2) & ((xx - x) % T >= 1) & (yy > y0 + 1) & (yy < y0 + 30)
            if x + w > T:
                pass
            base = hexrgb(["3a3541", "403a46", "35313c"][rng.i(0, 2)])
            col = base * (0.75 + 0.45 * n1[..., None])
            alb[m] = col[m]
            x += w
    # wooden cross beam along the cell edge
    beam = (yy < 10) | (yy > T - 6)
    bn = value_noise(T, T, 3, seed + 4, 2)
    wood = hexrgb("4a2e17") * (0.8 + 0.4 * bn[..., None]) * np.where(((yy % 4) == 0)[..., None], 0.8, 1.0)
    alb[beam] = wood[beam]
    alb[yy == 10] *= 0.4
    return alb


def _frame_mask(inner_w=74, inner_top=24, spring=58):
    """Stone archway opening (True inside the opening)."""
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    cx = T / 2 - 0.5
    r = inner_w / 2
    rect = (np.abs(xx - cx) < r) & (yy >= spring)
    arch = ((xx - cx) ** 2 + ((yy - spring) * (r / (spring - inner_top))) ** 2) < r * r
    return (rect | (arch & (yy < spring))) & (yy < T - 6)


def _voussoirs(alb, open_mask, seed):
    """Paint dressed stone blocks around an opening."""
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    from scipy_free import dilate
    ring = dilate(open_mask, 9) & ~open_mask
    cx = T / 2 - 0.5
    ang = np.arctan2(yy - 58, xx - cx)
    seg = np.floor((ang + np.pi) / (np.pi / 9)).astype(int)
    n = value_noise(T, T, 6, seed, 2)
    base = hexrgb("807a83") * (0.8 + 0.3 * n[..., None])
    tone = 0.92 + 0.12 * ((seg % 3) / 2.0)
    col = base * tone[..., None]
    above = yy < 58
    sidecut = (~above) & (((yy - 58) % 18) < 1.5)
    seam = above & (np.abs(((ang + np.pi) % (np.pi / 9))) < 0.03)
    col = np.where((seam | sidecut)[..., None], hexrgb("211e26"), col)
    inner = dilate(open_mask, 2) & ~open_mask
    col = np.where(inner[..., None], col * 0.55, col)
    alb[ring] = col[ring]
    outer = dilate(open_mask, 10) & ~dilate(open_mask, 9)
    alb[outer] = hexrgb("1a171f")
    return alb


def door(locked=False, seed=41):
    alb, emi, a = stone_wall(seed=7)
    om = _frame_mask()
    alb = _voussoirs(alb, om, seed)
    yy, xx = np.mgrid[0:T, 0:T]
    n = value_noise(T, T, 3, seed + 2, 3)
    grain = value_noise(T, T, 2, seed + 5, 1)
    plank = ((xx - 27) // 12)
    tone = np.choose(np.clip(plank, 0, 5) % 3, [0.95, 1.05, 0.88])
    wood = hexrgb("653f1f") * tone[..., None] * (0.75 + 0.5 * n[..., None]) * (0.92 + 0.16 * grain[..., None])
    seams = ((xx - 27) % 12 == 0)
    wood = np.where(seams[..., None], hexrgb("1f140e"), wood)
    # iron straps
    straps = ((yy > 40) & (yy < 47)) | ((yy > 92) & (yy < 99))
    iron = hexrgb("36404c") * (0.85 + 0.3 * n[..., None])
    iron = np.where(((yy == 41) | (yy == 93))[..., None], hexrgb("8497ab"), iron)
    iron = np.where(((yy == 46) | (yy == 98))[..., None], hexrgb("15131a"), iron)
    wood = np.where(straps[..., None], iron, wood)
    for sy in (43, 95):
        for sx in range(32, 98, 9):
            wood[sy:sy + 2, sx:sx + 2] = hexrgb("bccbd8")
    # ring pull
    cy, cx = 70, 84
    rr = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    ring = (rr > 4.0) & (rr < 6.2) & (yy > cy - 2)
    wood = np.where(ring[..., None], hexrgb("8497ab"), wood)
    wood[cy - 4:cy - 1, cx - 2:cx + 2] = hexrgb("36404c")
    # shadow under the arch
    sh = np.clip(1.0 - (yy - 24) / 70.0, 0, 1)
    wood = wood * (1 - 0.35 * sh[..., None] * (yy < 50)[..., None])
    if locked:
        plate = (np.abs(yy - 72) < 8) & (np.abs(xx - 44) < 6)
        wood = np.where(plate[..., None], hexrgb("a56f37") * (0.8 + 0.4 * n[..., None]), wood)
        wood[68:72, 43:46] = hexrgb("0b0a0e")
        wood[72:77, 44:45] = hexrgb("0b0a0e")
        wood[64, 39:50] = hexrgb("ffd98a")
    alb[om] = wood[om]
    return alb, emi, a


def arch(seed=41):
    alb, emi, a = stone_wall(seed=7)
    om = _frame_mask()
    alb = _voussoirs(alb, om, seed)
    a = np.where(om, 0.0, 1.0).astype(np.float32)
    return alb, emi, a


def stairs(seed=55):
    alb, emi, a = stone_wall(seed=7)
    om = _frame_mask()
    alb = _voussoirs(alb, om, seed)
    yy, xx = np.mgrid[0:T, 0:T]
    inside = np.zeros((T, T, 3), np.float32)
    inside[:] = hexrgb("0b0a0e")
    # steps going down and away into darkness
    steps = [(122, 112, 1.0), (112, 103, 0.72), (103, 96, 0.5), (96, 90, 0.34), (90, 85, 0.22), (85, 81, 0.13)]
    for (y1, y0, br) in steps:
        m = (yy >= y0) & (yy < y1)
        col = hexrgb("807a83") * br
        col = np.where((yy == y0)[..., None], hexrgb("b1aaac") * br, col)
        inside[m] = col if np.ndim(col) == 1 else col[m]
    # walls of the stairwell
    side = (np.abs(xx - 63.5) > 30 - (122 - yy) * 0.25) & (yy > 70)
    inside[side] = hexrgb("2d2933")
    alb[om] = inside[om]
    return alb, emi, a


def shrine(seed=61):
    alb, emi, a = stone_wall(seed=7)
    om = _frame_mask(inner_w=60, inner_top=30, spring=60) & (np.mgrid[0:T, 0:T][0] < 104)
    alb = _voussoirs(alb, om, seed)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    niche = np.zeros((T, T, 3), np.float32)
    niche[:] = hexrgb("15131a")
    niche[yy > 90] = hexrgb("2d2933")
    # altar slab
    slab = (yy > 86) & (yy < 104) & (np.abs(xx - 63.5) < 24)
    niche[slab] = hexrgb("6b6570")
    niche[(yy > 86) & (yy < 89) & (np.abs(xx - 63.5) < 24)] = hexrgb("979097")
    # skull
    sk = ((xx - 63.5) ** 2 / 81 + (yy - 72) ** 2 / 64) < 1
    jaw = (np.abs(xx - 63.5) < 6) & (yy > 76) & (yy < 86)
    skull = sk | jaw
    niche[skull] = hexrgb("d9d0b4")
    shade = np.clip((xx - 58) / 14, 0, 1)
    niche[skull] = niche[skull] * (1 - 0.35 * shade[skull][:, None])
    for ex in (59.5, 67.5):
        e = ((xx - ex) ** 2 + (yy - 72) ** 2) < 6.5
        niche[e] = hexrgb("0b0a0e")
        emi[e] = hexrgb("35a596") * 1.1
        emi[((xx - ex) ** 2 + (yy - 72) ** 2) < 1.6] = hexrgb("d6fff6")
    niche[(np.abs(xx - 63.5) < 1.5) & (yy > 75) & (yy < 79)] = hexrgb("15131a")
    for tx in range(58, 70, 3):
        niche[83:85, tx:tx + 2] = hexrgb("f4efe0")
    # spectral candles
    for cx in (44, 83):
        niche[(np.abs(xx - cx) < 2.5) & (yy > 76) & (yy < 87)] = hexrgb("cdc6c2")
        fl = ((xx - cx) ** 2 * 2.2 + (yy - 72) ** 2 * 0.6) < 12
        emi[fl] = hexrgb("7fe8d2")
        emi[((xx - cx) ** 2 * 3 + (yy - 73) ** 2) < 3] = hexrgb("ffffff")
    # glow on niche
    g = np.exp(-((xx - 63.5) ** 2 + (yy - 76) ** 2) / 500.0)
    emi += (hexrgb("35a596") * 0.35 * g[..., None]) * om[..., None]
    alb[om] = niche[om]
    return alb, emi, a


def deco_chains(seed=71):
    alb, emi, a = stone_wall(seed=7)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    for (cx, top, length) in ((40, 18, 64), (88, 18, 70)):
        # bolt plate
        alb[top - 3:top + 4, cx - 4:cx + 5] = hexrgb("36404c")
        alb[top - 3, cx - 4:cx + 5] = hexrgb("8497ab")
        y = top + 4
        k = 0
        while y < top + length:
            if k % 2 == 0:
                ring = (((xx - cx) ** 2) / 4 + ((yy - y - 3) ** 2) / 12 < 1.4) & (((xx - cx) ** 2) / 4 + ((yy - y - 3) ** 2) / 12 > 0.45)
            else:
                ring = (np.abs(xx - cx) < 1) & (yy >= y) & (yy < y + 6)
            alb[ring] = hexrgb("56667a")
            alb[ring & (xx < cx)] = hexrgb("8497ab")
            y += 5; k += 1
        # shackle
        rr = np.sqrt((xx - cx) ** 2 + (yy - y - 6) ** 2)
        sh = (rr > 4) & (rr < 7) & (yy > y)
        alb[sh] = hexrgb("56667a")
        alb[sh & (xx < cx - 1)] = hexrgb("8497ab")
        # rust drip on the wall
        drip = (np.abs(xx - cx - 2) < 1.2) & (yy > top + 4) & (yy < top + length + 20)
        alb[drip] = alb[drip] * 0.7 + hexrgb("5c1618") * 0.25
    return alb, emi, a


def deco_sconce(seed=81):
    alb, emi, a = stone_wall(seed=7)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    cx = 63.5
    # soot on the wall above
    soot = np.exp(-((xx - cx) ** 2) / 120 - ((yy - 30) ** 2) / 300)
    alb *= (1 - 0.7 * soot)[..., None]
    # warm wash from the flame
    glow = np.exp(-((xx - cx) ** 2 + (yy - 44) ** 2) / 900.0)
    emi += hexrgb("e8b45e")[None, None, :] * 0.55 * glow[..., None] * (alb.sum(-1) / 300.0)[..., None]
    # iron bracket and cup
    alb[(np.abs(xx - cx) < 2) & (yy > 56) & (yy < 80)] = hexrgb("36404c")
    alb[(np.abs(xx - cx) < 5) & (yy > 76) & (yy < 82)] = hexrgb("36404c")
    cup = (np.abs(xx - cx) < 8 - (yy - 48) * 0.25) & (yy > 48) & (yy < 58)
    alb[cup] = hexrgb("56667a"); alb[cup & (xx < cx - 2)] = hexrgb("8497ab")
    # torch handle
    alb[(np.abs(xx - cx) < 3) & (yy > 40) & (yy < 50)] = hexrgb("4a2e17")
    # flame
    f = ((xx - cx) ** 2 * (1.0 + (44 - yy) * 0.05) / 22 + (yy - 36) ** 2 / 110) < 1
    f &= yy < 46
    core = ((xx - cx) ** 2 / 6 + (yy - 39) ** 2 / 30) < 1
    emi[f] = hexrgb("e8643a") * 1.0
    emi[f & (yy > 30)] = hexrgb("e8b45e")
    emi[core] = hexrgb("fff3c8")
    alb[f] = 0
    return alb, emi, a


def deco_sigil(seed=91):
    alb, emi, a = stone_wall(seed=7)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    cx, cy = 63.5, 60
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    th = np.arctan2(yy - cy, xx - cx)
    m = (np.abs(r - 34) < 1.3) | (np.abs(r - 27) < 0.9)
    # pentagram-ish curse star (7 points)
    pts = [(cx + 27 * np.cos(-np.pi / 2 + k * 2 * np.pi / 7), cy + 27 * np.sin(-np.pi / 2 + k * 2 * np.pi / 7)) for k in range(7)]
    for k in range(7):
        x0, y0 = pts[k]; x1, y1 = pts[(k + 3) % 7]
        dx, dy = x1 - x0, y1 - y0
        L = np.hypot(dx, dy)
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / (L * L), 0, 1)
        dist = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
        m |= dist < 0.9
    # runes between the rings
    for k in range(14):
        ang = k * 2 * np.pi / 14
        rx, ry = cx + 30.5 * np.cos(ang), cy + 30.5 * np.sin(ang)
        m |= (np.abs(xx - rx) < 0.8) & (np.abs(yy - ry) < 2.2)
        if k % 2:
            m |= (np.abs(yy - ry + 1) < 0.7) & (np.abs(xx - rx) < 1.8)
    carve = m
    alb[carve] = hexrgb("15131a")
    emi[carve] = hexrgb("6a34a0") * 1.0
    halo = np.exp(-((r - 31) ** 2) / 40.0) * 0.28
    emi += hexrgb("6a34a0")[None, None, :] * halo[..., None]
    # blood drips from the lowest point
    for dx_ in (-6, 2, 9):
        d = (np.abs(xx - cx - dx_) < 1.1) & (yy > cy + 30) & (yy < cy + 44 + dx_)
        alb[d] = hexrgb("5c1618")
    return alb, emi, a


SURFACES = {
    "wall": stone_wall,
    "chains": deco_chains,
    "sconce": deco_sconce,
    "sigil": deco_sigil,
    "door": lambda: door(False),
    "locked": lambda: door(True),
    "arch": arch,
    "stairs": stairs,
    "shrine": shrine,
}


# ---------------------------------------------------------------- prison set

def bars(seed=101):
    """Cell door: iron bars in a dressed stone frame; see-through between bars."""
    alb, emi, a = stone_wall(seed=7)
    om = _frame_mask(inner_w=70, inner_top=22, spring=40)
    alb = _voussoirs(alb, om, seed)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    a = np.where(om, 0.0, 1.0).astype(np.float32)
    n = value_noise(T, T, 3, seed, 2)
    iron = hexrgb("425167") * (0.85 + 0.3 * n[..., None])
    barx = [36, 46, 56, 66, 76, 86]
    m = np.zeros((T, T), bool)
    for bx in barx:
        b = (np.abs(xx - bx - 1) < 2.6) & om
        m |= b
        hi = (np.abs(xx - bx) < 0.8) & om
        alb[hi] = hexrgb("8497ab")
    for by in (46, 92):
        band = (np.abs(yy - by) < 3) & om
        m |= band
    alb = np.where((m & ~((np.abs(((xx - 35) % 10) - 1) < 0.8) & om))[..., None], np.where(m[..., None], iron, alb), alb)
    for bx in barx:
        hi = (np.abs(xx - bx) < 0.8) & om
        alb[hi] = hexrgb("8497ab")
    for by in (46, 92):
        alb[(np.abs(yy - by + 2) < 0.7) & om] = hexrgb("8497ab")
        alb[(np.abs(yy - by - 2) < 0.7) & om] = hexrgb("1b2330")
        for bx in barx:
            alb[int(by) - 1:int(by) + 2, bx:bx + 3] = hexrgb("bccbd8")
    # rust streaks
    rust = m & (value_noise(T, T, 4, seed + 3, 2) > 0.62)
    alb[rust] = alb[rust] * 0.5 + hexrgb("7b1b1d") * 0.45
    # lock box on the right-hand bar band
    lb = (np.abs(xx - 82) < 6) & (np.abs(yy - 69) < 7)
    alb[lb] = hexrgb("36404c"); alb[lb & (yy < 64)] = hexrgb("8497ab")
    alb[(np.abs(xx - 82) < 1.2) & (np.abs(yy - 70) < 3)] = hexrgb("0b0a0e")
    m |= lb
    a = np.where(om & ~m, 0.0, 1.0).astype(np.float32)
    return alb, emi, a


SW = (46, 50, 82, 75)  # the loose brick: x0, y0, x1, y1


def _tally(alb, x0, y0, groups, seed):
    rng = Rng(seed)
    x = x0
    for g in range(groups):
        for k in range(4):
            yo = rng.i(-1, 1)
            alb[y0 + yo:y0 + yo + 9, x] = alb[y0 + yo:y0 + yo + 9, x] * 0.45
            alb[y0 + yo:y0 + yo + 9, x + 1] = np.minimum(alb[y0 + yo:y0 + yo + 9, x + 1] * 1.25, 255)
            x += 3
        for k in range(12):
            xx_ = x - 13 + k
            yy_ = y0 + 7 - int(k * 0.55)
            alb[yy_, xx_] = alb[yy_, xx_] * 0.45
        x += 5
    return alb


def switch_wall(pressed=False, seed=111):
    alb, emi, a = stone_wall(seed=7)
    x0, y0, x1, y1 = SW
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    n = value_noise(T, T, 5, seed, 3)
    # clear the area and draw mortar around one odd brick
    box = (xx >= x0 - 2) & (xx < x1 + 2) & (yy >= y0 - 2) & (yy < y1 + 2)
    alb[box] = hexrgb("15131a")
    brick = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    base = hexrgb("6f6872") * (0.85 + 0.3 * n[..., None])
    if not pressed:
        col = base.copy()
        col = np.where((yy < y0 + 3)[..., None], col * 1.25, col)
        col = np.where((xx < x0 + 2)[..., None], col * 1.12, col)
        col = np.where((yy > y1 - 4)[..., None], col * 0.62, col)
        col = np.where((xx > x1 - 3)[..., None], col * 0.75, col)
        # worn, polished by old hands
        rub = np.exp(-((xx - (x0 + x1) / 2) ** 2 + (yy - (y0 + y1) / 2) ** 2) / 60.0)
        col = col * (1 + 0.18 * rub[..., None])
    else:
        col = base * 0.62
        col = np.where((yy < y0 + 6)[..., None], hexrgb("15131a") * 1.5, col)
        col = np.where((xx < x0 + 4)[..., None], hexrgb("211e26"), col)
    alb[brick] = col[brick]
    # a faint hairline crack running into the brick and a smear of old blood
    for i in range(10):
        alb[y0 - 8 + i, x0 + 4 + (i // 3)] *= 0.5
    smear = ((xx - x1 + 4) ** 2 / 12 + (yy - y1 + 8) ** 2 / 30) < 1
    alb[smear] = alb[smear] * 0.6 + hexrgb("5c1618") * 0.35
    # prisoner's tally marks scratched beside it
    alb = _tally(alb, 12, 34, 3, seed)
    alb = _tally(alb, 88, 90, 2, seed + 1)
    return alb, emi, a


def _bed_slab(alb, drop, seed):
    """Stone bed slab built into the wall, lowered by `drop` px."""
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    n = value_noise(T, T, 6, seed, 3)
    top0, top1, fr1 = 74 + drop, 84 + drop, 100 + drop
    x0, x1 = 8, 120
    topm = (yy >= top0) & (yy < top1) & (xx >= x0 + (top1 - yy) * 0.6) & (xx < x1 - (top1 - yy) * 0.6)
    frontm = (yy >= top1) & (yy < fr1) & (xx >= x0) & (xx < x1)
    stone = hexrgb("807a83") * (0.85 + 0.25 * n[..., None])
    # shadow below the slab on the wall
    sh = (yy >= fr1) & (yy < fr1 + 7) & (xx >= x0) & (xx < x1)
    alb[sh] = alb[sh] * 0.35
    alb[topm] = (stone * 1.15)[topm]
    alb[frontm] = (stone * 0.82)[frontm]
    alb[(np.abs(yy - top1) < 1) & (xx >= x0) & (xx < x1)] = hexrgb("cdc6c2")
    alb[(np.abs(yy - fr1 + 1) < 1) & (xx >= x0) & (xx < x1)] = hexrgb("211e26")
    for jx in (40, 82):
        alb[(np.abs(xx - jx) < 0.8) & frontm] = hexrgb("2d2933")
    # threadbare blanket and straw
    bl = topm & (xx > 30) & (xx < 92)
    bn = value_noise(T, T, 3, seed + 4, 2)
    blanket = hexrgb("5c1618") * (0.75 + 0.5 * bn[..., None])
    blanket = np.where((((xx - 30) // 6) % 2 == 0)[..., None], blanket * 0.85, blanket)
    alb[bl] = blanket[bl]
    hang = (yy >= top1) & (yy < top1 + 9 - (np.abs(xx - 61) > 22) * 4) & (xx > 32) & (xx < 90)
    alb[hang] = (blanket * 0.7)[hang]
    straw = topm & ((xx < 30) | (xx > 92)) & (bn > 0.45)
    alb[straw] = hexrgb("c98f47") * (0.7 + 0.5 * n[straw][:, None])
    return alb


def bed_wall(stage=0, seed=121):
    """stage 0: closed. 1..3: slab sinking and the wall drawing back (secret passage)."""
    alb, emi, a = stone_wall(seed=7)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    om = _frame_mask(inner_w=82, inner_top=20, spring=50)
    if stage >= 1:
        # cracks tracing the hidden doorway
        ring = _frame_mask(inner_w=84, inner_top=19, spring=50) & ~_frame_mask(inner_w=80, inner_top=21, spring=50)
        alb[ring] = hexrgb("0b0a0e")
        dust = (value_noise(T, T, 2, seed + stage, 1) > 0.8) & (yy > 100) & (yy < 112)
        alb[dust] = hexrgb("b1aaac")
    if stage >= 2:
        rise = {2: 78, 3: 34}[stage]
        hole = om & (yy > rise)
        a = np.where(hole, 0.0, 1.0).astype(np.float32)
        # the retracting stone edge
        lip = om & (np.abs(yy - rise) < 2.5)
        alb[lip] = hexrgb("2a2236")
    drop = {0: 0, 1: 8, 2: 22, 3: 40}[stage]
    alb = _bed_slab(alb, drop, seed)
    if stage >= 2:
        slab = (yy >= 74 + drop) & (yy < 100 + drop)
        a = np.where(slab & (xx >= 8) & (xx < 120), 1.0, a).astype(np.float32)
    return alb, emi, a


def door_rising(stage, seed=41):
    """Door lifting into the arch: stage 1..3 = 25/55/85 % raised."""
    alb, emi, a = door(False, seed)
    base_alb, _, _ = arch(seed)
    om = _frame_mask()
    lift = {1: 26, 2: 56, 3: 86}[stage]
    shifted = np.zeros_like(alb)
    shifted[:T - lift] = alb[lift:]
    yy = np.mgrid[0:T, 0:T][0]
    keep = om & (yy < (T - 6) - lift)
    out = base_alb.copy()
    out[keep] = shifted[keep]
    a = np.where(om & ~keep, 0.0, 1.0).astype(np.float32)
    # dark slot the door slides into
    return out, emi, a


SURFACES.update({
    "bars": bars,
    "switch": lambda: switch_wall(False),
    "switch_on": lambda: switch_wall(True),
    "bed": lambda: bed_wall(0),
    "bed1": lambda: bed_wall(1),
    "bed2": lambda: bed_wall(2),
    "bed3": lambda: bed_wall(3),
    "door1": lambda: door_rising(1),
    "door2": lambda: door_rising(2),
    "door3": lambda: door_rising(3),
})
