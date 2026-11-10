import numpy as np, sys
from PIL import Image
from common import quantize, lit
from textures import SURFACES, flagstone_floor, ceiling
tiles = []
for k, f in SURFACES.items():
    alb, emi, a = f()
    rgb = alb * 0.95 + emi
    q = quantize(rgb, a)
    tiles.append(q)
for f in (flagstone_floor, ceiling):
    tiles.append(quantize(f()))
W = 4
rows = (len(tiles) + W - 1) // W
sheet = np.zeros((rows * 130, W * 130, 4), np.uint8); sheet[..., 3] = 255; sheet[..., :3] = 40
for i, t in enumerate(tiles):
    y, x = (i // W) * 130 + 1, (i % W) * 130 + 1
    sheet[y:y + 128, x:x + 128] = np.where(t[..., 3:] > 0, t, sheet[y:y + 128, x:x + 128])
Image.fromarray(sheet).resize((sheet.shape[1] * 2, sheet.shape[0] * 2), Image.NEAREST).save(sys.argv[1])
