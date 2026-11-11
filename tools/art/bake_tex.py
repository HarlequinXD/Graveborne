"""Bakes everything the real-time 3D tile renderer needs.

  python3 tools/art/bake_tex.py app/src/main/assets

Outputs
  tex3d.png / tex3d_glow.png / tex3d.txt   wall, floor and ground textures (painted, unlit), 128x128 tiles
  spr3d.png / spr3d_glow.png / spr3d.txt   monsters, items, props (painted, unlit, outlined)
  sky3d.png                                 512x64 night-sky panoramas: forest row 0, town row 1
  pal3d.txt                                 palette colours with their material ramp and position
  atlas*.png / atlas.txt                    portraits and UI icons
All colour comes from the same palette; the game lights it by stepping along the ramps."""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixelart import paint_texture, finish, PAL, RAMPS, RAMP_OF
import textures as TX
import textures_crypt as TC
import textures_out as TO
import actors
import portraits
import ui
from build_all import pack


def rgba_of(idx, alpha):
    out = np.zeros(idx.shape + (4,), np.uint8)
    out[..., :3] = PAL[idx].astype(np.uint8)
    out[..., 3] = np.where(alpha, 255, 0)
    return out


def main():
    out = sys.argv[1]
    # ---------------------------------------------------------- textures
    names, tiles, glows = [], [], []

    def add(name, alb, emi, a):
        idx, glow = paint_texture(alb, emi)
        names.append(name)
        tiles.append(rgba_of(idx, a > 0.5 if a is not None else np.ones(idx.shape, bool)))
        glows.append((np.clip(glow, 0, 1) * 255).astype(np.uint8))

    for k, f in TX.SURFACES.items():
        add(k, *f())
    for k, f in TO.OUT_SURFACES.items():
        add(k, *f())
    add("floor", TX.flagstone_floor(), None, None)
    add("ceil", TX.ceiling(), None, None)
    add("grass", TO.forest_floor(), None, None)
    add("cobble", TO.cobbles(), None, None)
    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    sheet = np.zeros((rows * 128, cols * 128, 4), np.uint8)
    gsheet = np.zeros((rows * 128, cols * 128), np.uint8)
    for i, (t, g) in enumerate(zip(tiles, glows)):
        y, x = (i // cols) * 128, (i % cols) * 128
        sheet[y:y + 128, x:x + 128] = t
        gsheet[y:y + 128, x:x + 128] = g
    Image.fromarray(sheet).save(os.path.join(out, "tex3d.png"), optimize=True)
    Image.fromarray(gsheet).save(os.path.join(out, "tex3d_glow.png"), optimize=True)
    with open(os.path.join(out, "tex3d.txt"), "w") as f:
        f.write("\n".join(names) + "\n")

    # ----------------------------------------------------------- sprites
    items = []

    def add_sprite(name, c, ww, wh, lift=0.0):
        idx, glow = paint_texture(c.rgb, c.emi)
        mask = c.a > 0.5
        rgba, _ = finish(idx, mask)
        ys, xs = np.where(mask)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        # keep the card's full extent so world size maps 1:1 to the canvas
        items.append((name, rgba, (np.clip(glow, 0, 1) * 255).astype(np.uint8), ww, wh, lift))

    for name, fn in actors.MONSTERS.items():
        for fr in actors.FRAMES:
            if name in ("priest", "guard", "innkeeper") and fr == "attack":
                continue
            add_sprite(f"m:{name}:{fr}", fn(fr), 0.75, 1.0, 0.04 if name == "wraith" else 0.0)
    for name, fn in actors.ITEMS.items():
        add_sprite(f"i:{name}", fn(), 0.5, 0.25)
    for name, (fn, ww, wh) in actors.PROPS.items():
        add_sprite(f"o:{name}", fn(), ww, wh)
    # shelf pack
    W = 1024
    x = y = rowh = 0
    place = []
    for it in sorted(items, key=lambda t: -t[1].shape[0]):
        h, w = it[1].shape[:2]
        if x + w > W:
            x = 0; y += rowh + 1; rowh = 0
        place.append((it, x, y)); x += w + 1; rowh = max(rowh, h)
    H = y + rowh
    ss = np.zeros((H, W, 4), np.uint8); sg = np.zeros((H, W), np.uint8)
    lines = []
    for (name, rgba, glow, ww, wh, lift), x, y in place:
        h, w = rgba.shape[:2]
        ss[y:y + h, x:x + w] = rgba; sg[y:y + h, x:x + w] = glow
        lines.append(f"{name} {x} {y} {w} {h} {ww} {wh} {lift}")
    Image.fromarray(ss).save(os.path.join(out, "spr3d.png"), optimize=True)
    Image.fromarray(sg).save(os.path.join(out, "spr3d_glow.png"), optimize=True)
    with open(os.path.join(out, "spr3d.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    # --------------------------------------------------------------- sky
    rows_ = []
    for theme in ("forest", "town"):
        strip = []
        for facing in range(4):
            col, emi = TO.sky(theme, facing=facing)
            idx, _ = paint_texture(col + emi, emi)
            strip.append(PAL[idx][:64].astype(np.uint8))
        rows_.append(np.concatenate(strip, 1))
    Image.fromarray(np.concatenate(rows_, 0)).save(os.path.join(out, "sky3d.png"), optimize=True)

    # ----------------------------------------------------------- palette
    with open(os.path.join(out, "pal3d.txt"), "w") as f:
        f.write(f"RAMPS {len(RAMPS)}\n")
        for r in RAMPS:
            f.write(" ".join(str(c) for c in r) + "\n")
        f.write(f"COLORS {len(PAL)}\n")
        for i, c in enumerate(PAL):
            ri, pos = RAMP_OF[i]
            f.write("%02x%02x%02x %d %d\n" % (int(c[0]), int(c[1]), int(c[2]), ri, pos))

    # ------------------------------------------------- portraits and icons
    res = [(f"p:{n}", portraits.render(n), 0, 0) for n in portraits.PORTRAITS]
    res += [(f"ui:{k}", v, 0, 0) for k, v in ui.icons().items()]
    lid_alb, lid_emi, _ = TC.lid_underside()
    lid_idx, _ = paint_texture(lid_alb, lid_emi)
    res.append(("ui:lid", rgba_of(lid_idx, np.ones(lid_idx.shape, bool)), 0, 0))
    for f_ in os.listdir(out):
        if f_.startswith("atlas") and f_.endswith(".png"):
            os.remove(os.path.join(out, f_))
    pack(res, out)
    print("textures", len(names), "sprites", len(items))


if __name__ == "__main__":
    main()
