"""Walls and floors for the later chapters: the Ossuary Mines, the Barrows of the First Kings,
the Wardens' Keep and the Wound itself. Same contract as textures.py: (albedo, emissive, alpha)."""
import numpy as np
from common import hexrgb, value_noise, Rng
from textures import stone_wall, T
from textures_out import cliff, _grid, _blank
from textures_crypt import _skull


def mine_wall(seed=701):
    """Raw rock held up by timber props: a cross beam and two posts."""
    alb, emi, a = cliff(seed)
    a[:] = 1
    yy, xx = _grid()
    n = value_noise(T, T, 12, seed, 3)
    rock = hexrgb("4a4352") * (0.7 + 0.5 * n[..., None])
    top = yy < 24
    alb[top] = rock[top]
    wood = hexrgb("5a3a1e")
    for px in (14, 104):
        m = (xx >= px) & (xx < px + 12)
        g = (0.8 + 0.3 * np.sin(yy / 3 + px))[..., None]
        alb[m] = (wood * g)[m]
        alb[m & ((xx == px) | (xx == px + 11))] *= 0.5
    beam = (yy >= 12) & (yy < 24)
    alb[beam] = (wood * (0.85 + 0.25 * np.sin(xx / 4))[..., None])[beam]
    alb[beam & ((yy == 12) | (yy == 23))] *= 0.5
    # an oil lamp hung on the post
    lamp = ((xx - 58) ** 2 / 9 + (yy - 40) ** 2 / 16) < 1
    alb[lamp] = hexrgb("f0a040"); emi[lamp] = hexrgb("ffd27a")
    alb[(np.abs(xx - 58) < 0.8) & (yy > 24) & (yy < 36)] = hexrgb("2d2933")
    return alb, emi, a


def bone_wall(seed=711):
    """Mine galleries packed floor to ceiling with the bones the town moved out of its graveyards."""
    alb, emi, a = _blank("221d26")
    rng = Rng(seed)
    yy, xx = _grid()
    # long bones stacked in courses
    for row in range(10):
        y = 6 + row * 12
        if row % 3 == 1:
            for cx in range(8, T, 16):
                _skull(alb, emi, cx + (row % 2) * 6, y, s=0.75, tone=["d9d0b4", "a8987a", "bfb294"][rng.i(0, 2)])
            continue
        for x0 in range(-10, T, 22):
            x = x0 + rng.i(0, 8)
            tone = hexrgb(["d9d0b4", "a8987a", "bfb294", "8e8064"][rng.i(0, 3)])
            m = (np.abs(yy - y) < 2.6) & (xx >= x) & (xx < x + 20)
            alb[m] = tone * (0.75 + 0.35 * ((yy[m] - y + 3) / 6))[..., None] if False else tone * 0.95
            for ex in (x, x + 19):
                k = ((xx - ex) ** 2 + (yy - y) ** 2) < 12
                alb[k] = tone
            alb[(np.abs(yy - y - 2) < 0.6) & (xx >= x) & (xx < x + 20)] *= 0.6
    alb *= (0.8 + 0.3 * value_noise(T, T, 6, seed, 2))[..., None]
    return alb, emi, a


def barrow_wall(seed=721):
    """The first kings' barrows: huge undressed megaliths, roots pushing through, old carvings."""
    alb, emi, a = _blank("16131a")
    rng = Rng(seed)
    yy, xx = _grid()
    n = value_noise(T, T, 10, seed, 4)
    stones = [(0, 0, 70, 62), (70, 0, 58, 50), (0, 62, 46, 66), (46, 62, 82, 66), (70, 50, 58, 12)]
    for (x0, y0, w, h) in stones:
        cx, cy = x0 + w / 2, y0 + h / 2
        m = (((xx - cx) / (w / 2 - 2)) ** 4 + ((yy - cy) / (h / 2 - 2)) ** 4) < 1
        base = hexrgb(["4d4a44", "56524a", "47443f"][rng.i(0, 2)])
        sh = np.clip((xx - cx) / w + (yy - cy) / h, -1, 1)
        alb[m] = (base * (0.75 + 0.45 * n[..., None]) * (1 - 0.3 * sh[..., None]))[m]
    # spiral carvings on the big stone
    r = np.hypot(xx - 34, yy - 30); t = np.arctan2(yy - 30, xx - 34)
    spiral = (np.abs(((r - t * 3) % 9) - 4.5) < 0.9) & (r < 22)
    alb[spiral] *= 0.55
    # roots
    for _ in range(5):
        x, y = rng.u(0, T), 0.0
        w = rng.u(1.5, 3.5)
        while y < rng.u(50, 128):
            m = ((xx - x) ** 2 + (yy - y) ** 2) < w * w
            alb[m] = hexrgb("3a2a1a")
            x += rng.u(-1.2, 1.2); y += 1.5; w = max(0.8, w - 0.02)
    moss = value_noise(T, T, 7, seed + 3, 3) > 0.7
    alb[moss] = alb[moss] * 0.5 + hexrgb("2e3d1c") * 0.5
    return alb, emi, a


def keep_wall(seed=731):
    """The Gravewardens' keep: dressed stone with a torn order banner (the seven-point sigil struck through)."""
    alb, emi, a = stone_wall(seed=19)
    yy, xx = _grid()
    ban = (xx > 40) & (xx < 88) & (yy > 10) & (yy < 96 + 8 * np.sin(xx / 5))
    n = value_noise(T, T, 5, seed, 2)
    alb[ban] = (hexrgb("2a1242") * (0.7 + 0.5 * n[..., None]))[ban]
    alb[ban & (n > 0.75)] = hexrgb("16131a")
    r = np.hypot(xx - 64, yy - 46); t = np.arctan2(yy - 46, xx - 64)
    star = (r < 14 * (0.6 + 0.4 * np.abs(np.cos(t * 3.5)))) & ban
    alb[star] = hexrgb("be8041")
    alb[(np.abs((xx - 64) - (yy - 46)) < 2) & (r < 18) & ban] = hexrgb("6e181b")   # struck through
    alb[(yy > 8) & (yy < 12) & (xx > 36) & (xx < 92)] = hexrgb("4a2e17")
    return alb, emi, a


def wound_wall(seed=741):
    """The Wound's chamber: rock turned to violet flesh, veined and faintly glowing."""
    alb, emi, a = _blank("2a0f2e")
    yy, xx = _grid()
    n = value_noise(T, T, 4, seed, 2)
    alb[:] = hexrgb("4a1752") * (0.7 + 0.4 * n[..., None])
    folds = np.sin(xx / 9 + 4 * value_noise(T, T, 4, seed + 1, 2)) > 0.75
    alb[folds] *= 0.55
    vn = value_noise(T, T, 3, seed + 2, 2)
    veins = np.abs(vn - 0.5) < 0.012
    alb[veins] = hexrgb("c08ce0"); emi[veins] = hexrgb("7a3eaa")
    # half-swallowed bones
    for (cx, cy) in [(30, 90), (96, 40), (70, 104)]:
        _skull(alb, emi, cx, cy, s=0.9, tone="a8987a")
    return alb, emi, a


def wound_floor(seed=751):
    yy, xx = _grid()
    n = value_noise(T, T, 10, seed, 4)
    alb = hexrgb("3a1240") * (0.8 + 0.25 * value_noise(T, T, 4, seed + 5, 2)[..., None])
    vn = value_noise(T, T, 3, seed + 1, 2)
    alb[np.abs(vn - 0.5) < 0.01] = hexrgb("8a4aa8")
    return alb


def barrow_floor(seed=761):
    yy, xx = _grid()
    n = value_noise(T, T, 12, seed, 4)
    alb = hexrgb("3b352c") * (0.7 + 0.5 * n[..., None])
    rng = Rng(seed)
    for _ in range(30):
        x, y = rng.i(0, T - 6), rng.i(0, T - 4)
        alb[y:y + 3, x:x + 5] = hexrgb("5a554c") * rng.u(0.8, 1.2)
    return alb


STORY_SURFACES = {"mine": mine_wall, "bonewall": bone_wall, "barrow": barrow_wall, "keep": keep_wall, "wound": wound_wall}
STORY_FLOORS = {"woundfloor": wound_floor, "barrowfloor": barrow_floor}
