"""Composites a sample view exactly the way the game does (backdrop + face sprites, far to near)."""
import sys
import numpy as np
from PIL import Image
from view import face_sprite, backdrop_sprite

MAP = [
    "#########",
    "####l####",
    "##.....##",
    "##h#.#t##",
    "##.#.#.##",
    "##...c###",
    "####.####",
]
KIND = {"#": "wall", "c": "chains", "t": "sconce", "g": "sigil", "d": "door", "l": "locked",
        "s": "stairs", "h": "shrine"}
SIDE_KIND = {"door": "wall", "locked": "wall", "shrine": "wall", "stairs": "wall"}


def compose(px, pz, sub_x=0, sub_z=0):
    """Camera in cell (px, pz) facing north (row index decreasing), offset by quarter steps."""
    img = backdrop_sprite(sub_x / 4.0, sub_z / 4.0)[..., :3].astype(np.float32)
    blocks = []
    for r, row in enumerate(MAP):
        for c, ch in enumerate(row):
            if ch in KIND:
                dx, dz = c - px, pz - r
                if dz < 0 or dz > 5 or abs(dx) > 5:
                    continue
                blocks.append((dz, abs(dx), dx, ch))
    blocks.sort(key=lambda b: (-b[0], -b[1]))
    for dz, adx, dx, ch in blocks:
        kind = KIND[ch]
        X4 = 4 * dx - sub_x
        Z4 = 4 * dz - sub_z + int(round(0.3 * 4)) * 0
        Z4f = 4 * dz - sub_z
        for side in (True, False):
            k = SIDE_KIND.get(kind, kind) if side else kind
            s = face_sprite(k, side, X4, Z4f + 1.2)  # +0.3 cell camera setback
            if s is None:
                continue
            a = s[..., 3:] > 0
            img = np.where(a, s[..., :3], img)
    return img.astype(np.uint8)


if __name__ == "__main__":
    out = sys.argv[1]
    frames = [compose(4, 5, 0, sz) for sz in (0, 1, 2, 3)]
    sheet = np.concatenate(frames, axis=1)
    Image.fromarray(np.concatenate([compose(4, 6), frames[0]], axis=1)).resize((1024, 512), Image.NEAREST).save(out)
    Image.fromarray(sheet).resize((sheet.shape[1] * 3, sheet.shape[0] * 3), Image.NEAREST).save(out.replace(".png", "_step.png"))
