"""Pre-renders the dungeon view pieces (wall faces, floor/ceiling backdrops) and
paints them over as full-colour pixel art.

View geometry: 128x128 window, focal length 64 px, eye height 0.5 of a 1-unit cell,
camera stands 0.3 behind the centre of its cell.  A piece is keyed by the
quarter-cell position of its cell centre relative to the camera, so the same
sprites serve standing, stepping and strafing frames."""
import numpy as np
from pixelart import paint_texture, light_indices, finish

V = 128
F = 64.0
NEAR = 0.06
SS = 4  # supersamples per axis
CAM_BACK = 0.3

# torchlight in ramp steps: 0 at ~0.9 cells, about one step darker per extra cell
def torch_steps(d):
    return np.minimum(0.7, -(d - 0.9) * 1.75)


def torch_steps_out(d):
    """Outdoors the moon keeps distant shapes faintly visible instead of black."""
    return np.maximum(np.minimum(0.6, -(d - 0.9) * 1.05), -4.2)


LIGHT = {"dungeon": torch_steps, "out": torch_steps_out}
THEME_OF_GROUND = {"dungeon": "floor", "forest": "grass", "town": "cobble"}

FACE_FRONT = 0.0
FACE_SIDE = -1.1
FLOOR = -0.5
CEIL = -1.9

_tex_cache = {}


def tex(kind):
    if kind not in _tex_cache:
        from textures import SURFACES, flagstone_floor, ceiling
        from textures_out import OUT_SURFACES, forest_floor, cobbles
        if kind == "floor":
            alb, emi, a = flagstone_floor(), None, None
        elif kind == "ceil":
            alb, emi, a = ceiling(), None, None
        elif kind == "grass":
            alb, emi, a = forest_floor(), None, None
        elif kind == "cobble":
            alb, emi, a = cobbles(), None, None
        elif kind in OUT_SURFACES:
            alb, emi, a = OUT_SURFACES[kind]()
        else:
            alb, emi, a = SURFACES[kind]()
        idx, glow = paint_texture(alb, emi)
        _tex_cache[kind] = (idx, glow, a)
    return _tex_cache[kind]


def _rays():
    o = (np.arange(SS) + 0.5) / SS
    py, px = np.mgrid[0:V, 0:V]
    rx = (px[..., None, None] + o[None, None, None, :] - V / 2) / F
    ry = (V / 2 - (py[..., None, None] + o[None, None, :, None])) / F
    return np.broadcast_to(rx, (V, V, SS, SS)), np.broadcast_to(ry, (V, V, SS, SS))


RX, RY = _rays()


def _sample(t, u, v):
    T = t.shape[0]
    iu = np.clip((u * T).astype(int), 0, T - 1)
    iv = np.clip((v * T).astype(int), 0, T - 1)
    return t[iv, iu]


def _resolve(kind, u, v, dist, valid, face_bias, light="dungeon"):
    """Majority colour of the supersamples (keeps clean pixel-art clusters), then light it."""
    idx_t, glow_t, a_t = tex(kind)
    si = _sample(idx_t, u, v)
    sg = _sample(glow_t, u, v)
    sa = _sample(a_t, u, v) if a_t is not None else np.ones(u.shape, np.float32)
    w = valid & (sa > 0.5)
    cov = w.mean(axis=(2, 3))
    from pixelart import NCOL
    oh = np.zeros(si.shape[:2] + (NCOL,), np.float32)
    flat_i = si.reshape(si.shape[0], si.shape[1], -1)
    flat_w = w.reshape(w.shape[0], w.shape[1], -1).astype(np.float32)
    for c in np.unique(flat_i):
        oh[..., c] = ((flat_i == c) * flat_w).sum(-1)
    idx = oh.argmax(-1)
    n = np.maximum(flat_w.sum(-1), 1)
    glow = (sg.reshape(flat_w.shape) * flat_w).sum(-1) / n
    d = (np.where(w, dist, 0).reshape(flat_w.shape)).sum(-1) / n
    steps = LIGHT[light](d) + face_bias
    steps = np.maximum(steps, steps * (1 - np.clip(glow, 0, 1)) + glow * 2.4)
    lit = light_indices(idx, steps)
    return lit, cov >= 0.5, d


def render_face(kind, side, X4, Z4, light="dungeon"):
    """One face of the block whose centre is (X4/4, Z4/4) cells from the camera.
    side=False: near (front) face; side=True: the face turned towards the view axis."""
    cx, cz = X4 / 4.0, Z4 / 4.0
    if not side:
        zf = cz - 0.5
        if zf <= NEAR:
            return None
        x = RX * zf
        y = 0.5 + RY * zf
        u = x - (cx - 0.5)
        v = 1.0 - y
        valid = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
        dist = np.sqrt(x * x + zf * zf)
        bias = FACE_FRONT
    else:
        if cx - 0.5 > 0:
            xp = cx - 0.5
        elif cx + 0.5 < 0:
            xp = cx + 0.5
        else:
            return None
        with np.errstate(divide="ignore", invalid="ignore"):
            z = xp / RX
        z = np.where(np.isfinite(z), z, -1)
        y = 0.5 + RY * z
        u = z - (cz - 0.5) if xp < 0 else (cz + 0.5) - z
        v = 1.0 - y
        valid = (z > NEAR) & (z >= cz - 0.5) & (z < cz + 0.5) & (v >= 0) & (v < 1)
        dist = np.sqrt(xp * xp + z * z)
        bias = FACE_SIDE
    if not valid.any():
        return None
    return _resolve(kind, u, v, dist, valid, bias, light)


def face_sprite(kind, side, X4, Z4, light="dungeon"):
    r = render_face(kind, side, X4, Z4, light)
    if r is None:
        return None
    idx, mask, d = r
    if not mask.any():
        return None
    rgba, idx = finish(idx, mask)
    if (idx[mask] == 0).all():
        return None  # entirely in darkness
    return rgba


_sky_cache = {}


def sky_indices(theme, facing=0):
    key = (theme, facing)
    if key not in _sky_cache:
        from textures_out import sky
        col, emi = sky(theme, facing=facing)
        idx, _ = paint_texture(col + emi, emi)
        _sky_cache[key] = idx
    return _sky_cache[key]


def backdrop_sprite(fx, fz, theme="dungeon", facing=0):
    """Floor and ceiling for camera fraction (fx, fz) in cells."""
    with np.errstate(divide="ignore"):
        s = np.where(RY < 0, -0.5 / np.minimum(RY, -1e-6), 0.5 / np.maximum(RY, 1e-6))
    x = RX * s
    z = s
    wx = x + fx
    wz = z + fz - CAM_BACK
    u = (wx + 0.5) % 1.0
    v = 1.0 - ((wz + 0.5) % 1.0)
    dist = np.sqrt(x * x + z * z)
    valid = np.ones(u.shape, bool)
    if theme == "dungeon":
        fl, fm, _ = _resolve("floor", u, v, dist, valid & (RY < 0), FLOOR)
        ce, cm, _ = _resolve("ceil", u, v, dist, valid & (RY >= 0), CEIL)
        idx = np.where(fm, fl, ce)
    else:
        fl, fm, _ = _resolve(THEME_OF_GROUND[theme], u, v, dist, valid & (RY < 0), FLOOR, "out")
        idx = np.where(fm, fl, sky_indices(theme, facing))
    rgba, _ = finish(idx, np.ones(idx.shape, bool), outline=False)
    return rgba
