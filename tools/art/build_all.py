"""Bakes every view piece into sprite atlases for the game.

  python3 tools/art/build_all.py app/src/main/assets

Outputs atlas0.png, atlas1.png, ... and atlas.txt:
  name sheet x y w h ox oy
Face/backdrop sprites: (ox, oy) is the top-left inside the 128x128 view.
Billboards (monsters/items): (ox, oy) is the top-left relative to the anchor
(screen centre column of the cell, horizon row)."""
import os
import sys
import numpy as np
from multiprocessing import Pool
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import view
from view import face_sprite, backdrop_sprite, torch_steps, RX, RY, SS, NEAR
from pixelart import paint_texture, light_indices, finish, NCOL

CAM = 1.2  # camera stands 0.3 cell behind the centre -> +1.2 quarter units

WALLISH = ["wall", "chains", "sconce", "sigil", "door", "locked", "arch", "stairs", "shrine", "bars", "exit"]
OUTDOOR = ["tree", "tree2", "tree3", "prison", "prisonwin", "pdoor", "palisade", "towngate", "house", "house2", "inn", "chapel"]
OUT_MONSTERS = ["skeleton", "wraith", "ghoul", "hound", "priest", "guard", "innkeeper"]
NEAR_ONLY = ["switch", "switch_on", "bed", "bed1", "bed2", "bed3", "door1", "door2", "door3"]


def view_keys(maxdx, maxdz):
    keys = set()
    for dz in range(0, maxdz + 1):
        for dx in range(-maxdx, maxdx + 1):
            for sz in range(4):
                keys.add((4 * dx, 4 * dz - sz))
            for sx in (-2, 2):
                keys.add((4 * dx - sx, 4 * dz))
    return sorted(keys)


def visible(side, X4, Zq):
    cx, cz = X4 / 4.0, (Zq + CAM) / 4.0
    if not side:
        zf = cz - 0.5
        return zf > NEAR and abs(cx) - 0.5 < zf * 1.02
    if abs(cx) <= 0.5:
        return False
    xp = abs(cx) - 0.5
    zfar = cz + 0.5
    return zfar > NEAR and xp < zfar * 1.02


def crop(rgba):
    a = rgba[..., 3] > 0
    if not a.any():
        return None
    ys, xs = np.where(a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return rgba[y0:y1, x0:x1], int(x0), int(y0)


def job_face(args):
    kind, side, X4, Zq, light = args
    s = face_sprite(kind, side, X4, Zq + CAM, light)
    if s is None:
        return None
    c = crop(s)
    if c is None:
        return None
    img, ox, oy = c
    return (f"f:{kind}:{'S' if side else 'F'}:{X4}:{Zq}", img, ox, oy)


def job_backdrop(args):
    theme, fx4, fz4, facing = args
    s = backdrop_sprite(fx4 / 4.0, fz4 / 4.0, theme, facing)
    key = f"bg:{theme}:{fx4}:{fz4}" if theme == "dungeon" else f"bg:{theme}{facing}:{fx4}:{fz4}"
    return (key, s, 0, 0)


# ---------------------------------------------------------------- billboards
_bb_cache = {}


def _bb_tex(group, name, frame):
    key = (group, name, frame)
    if key not in _bb_cache:
        import actors
        if group == "m":
            c = actors.MONSTERS[name](frame)
        elif group == "o":
            c = actors.PROPS[name][0]()
        else:
            c = actors.ITEMS[name]()
        idx, glow = paint_texture(c.rgb, c.emi)
        _bb_cache[key] = (idx, glow, c.a, c.w, c.h)
    return _bb_cache[key]


def billboard(group, name, frame, Zq, world_w, world_h, lift=0.0, light="dungeon"):
    """Upright card at the cell centre, feet on the floor (+lift)."""
    idx_t, glow_t, a_t, tw, th = _bb_tex(group, name, frame)
    d = (Zq + CAM) / 4.0
    x = RX * d
    y = 0.5 + RY * d
    u = (x + world_w / 2) / world_w
    v = 1.0 - (y - lift) / world_h
    valid = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
    if not valid.any():
        return None
    iu = np.clip((u * tw).astype(int), 0, tw - 1)
    iv = np.clip((v * th).astype(int), 0, th - 1)
    si = idx_t[iv, iu]; sg = glow_t[iv, iu]; sa = a_t[iv, iu]
    w = valid & (sa > 0.5)
    flat_i = si.reshape(128, 128, -1); flat_w = w.reshape(128, 128, -1).astype(np.float32)
    oh = np.zeros((128, 128, NCOL), np.float32)
    for c in np.unique(flat_i):
        oh[..., c] = ((flat_i == c) * flat_w).sum(-1)
    idx = oh.argmax(-1)
    n = np.maximum(flat_w.sum(-1), 1)
    glow = (sg.reshape(flat_w.shape) * flat_w).sum(-1) / n
    mask = flat_w.mean(-1) >= 0.5
    if not mask.any():
        return None
    steps = view.LIGHT[light](np.full((128, 128), d)) + 0.25
    steps = np.maximum(steps, steps * (1 - np.clip(glow, 0, 1)) + glow * 2.4)
    lit = light_indices(idx, steps)
    rgba, li = finish(lit, mask)
    if (li[mask] == 0).all():
        return None
    c = crop(rgba)
    if c is None:
        return None
    img, x0, y0 = c
    return img, x0 - 64, y0 - 64


def job_bb(args):
    group, name, frame, Zq, light = args
    suf = ":o" if light == "out" else ""
    if group == "m":
        r = billboard(group, name, frame, Zq, 0.75, 1.0, lift=0.0 if name != "wraith" else 0.04, light=light)
        key = f"m:{name}:{frame}:{Zq}{suf}"
    elif group == "o":
        import actors
        _, ww, wh = actors.PROPS[name]
        r = billboard(group, name, None, Zq, ww, wh, light=light)
        key = f"o:{name}:{Zq}"
    else:
        r = billboard(group, name, frame, Zq, 0.5, 0.25, light=light)
        key = f"i:{name}:{Zq}{suf}"
    if r is None:
        return None
    img, ox, oy = r
    return (key, img, ox, oy)


# -------------------------------------------------------------------- packer
def pack(items, out_dir, sheet_w=1024, sheet_h=1024):
    items = sorted(items, key=lambda t: (-t[1].shape[0], -t[1].shape[1]))
    sheets = []
    lines = []
    cur = None
    x = y = rowh = 0
    for name, img, ox, oy in items:
        h, w = img.shape[:2]
        if cur is None or x + w + 1 > sheet_w:
            x = 0; y += rowh + 1; rowh = 0
        if cur is None or y + h > sheet_h:
            cur = np.zeros((sheet_h, sheet_w, 4), np.uint8)
            sheets.append(cur)
            x = y = rowh = 0
        cur[y:y + h, x:x + w] = img
        lines.append(f"{name} {len(sheets) - 1} {x} {y} {w} {h} {ox} {oy}")
        x += w + 1
        rowh = max(rowh, h)
    for i, s in enumerate(sheets):
        used = np.where(s[..., 3].any(axis=1))[0]
        hh = int(used.max()) + 1 if len(used) else 1
        Image.fromarray(s[:hh]).save(os.path.join(out_dir, f"atlas{i}.png"), optimize=True)
    with open(os.path.join(out_dir, "atlas.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return len(sheets)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    jobs = []
    for kinds, light in ((WALLISH, "dungeon"), (OUTDOOR, "out")):
        for kind in kinds:
            for (X4, Zq) in view_keys(4, 5):
                for side in (False, True):
                    if visible(side, X4, Zq):
                        jobs.append((kind, side, X4, Zq, light))
    for kind in NEAR_ONLY:
        for (X4, Zq) in view_keys(1, 2):
            for side in (False, True):
                if visible(side, X4, Zq):
                    jobs.append((kind, side, X4, Zq, "dungeon"))
    print("faces:", len(jobs), flush=True)
    bb = []
    import actors
    for name in actors.MONSTERS:
        npc = name in ("priest", "guard", "innkeeper")
        lights = (["dungeon"] if name in ("skeleton", "wraith", "ghoul") else []) + (["out"] if name in OUT_MONSTERS else [])
        for light in lights:
            for fr in actors.FRAMES:
                if npc and fr == "attack":
                    continue
                for Zq in range(2, 22):
                    bb.append(("m", name, fr, Zq, light))
    for name in actors.ITEMS:
        for light in ("dungeon", "out"):
            for Zq in range(1, 22):
                bb.append(("i", name, None, Zq, light))
    for name in actors.PROPS:
        for Zq in range(1, 22):
            bb.append(("o", name, None, Zq, "out"))
    bgs = [(th, sx, sz, f) for th in ("dungeon", "forest", "town") for f in (range(1) if th == "dungeon" else range(4))
           for (sx, sz) in [(0, 0), (0, 1), (0, 2), (0, 3), (-2, 0), (2, 0)]]
    with Pool(int(os.environ.get("JOBS", "2"))) as pool:
        res = [r for r in pool.imap_unordered(job_face, jobs, chunksize=8) if r is not None]
        print("faces kept:", len(res), flush=True)
        res += [r for r in pool.map(job_backdrop, bgs)]
        res += [r for r in pool.imap_unordered(job_bb, bb, chunksize=8) if r is not None]
    # portraits and UI icons (flat, unlit)
    import portraits
    for n in portraits.PORTRAITS:
        res.append((f"p:{n}", portraits.render(n), 0, 0))
    import ui
    for name, img in ui.icons().items():
        res.append((f"ui:{name}", img, 0, 0))
    n = pack(res, out)
    print("sprites:", len(res), "sheets:", n)


if __name__ == "__main__":
    main()
