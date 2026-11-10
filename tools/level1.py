"""Builds floor 1 (The Oubliette) from room rectangles into app/src/main/assets/level1.txt
and writes a top-down preview PNG.

Legend: # wall  . floor  D door  L locked door  B cell bars  X secret wall (bed)
        S stairs down  H grave shrine (wall)"""
import sys
import numpy as np

W, H = 18, 18
g = [["#"] * W for _ in range(H)]


def room(x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = "."


def put(x, y, ch):
    g[y][x] = ch


# prison block
room(1, 12, 16, 12)                 # cell corridor
for cx in (2, 5, 8, 13):
    room(cx, 14, cx, 14)
    put(cx, 13, "B")
put(9, 14, "X")                     # bed wall that slides away
room(10, 14, 10, 16)                # secret tunnel
room(10, 16, 15, 16)
room(15, 13, 15, 16)
# west: guard room and the way north
room(1, 6, 6, 10)
put(3, 11, "D")
room(4, 2, 4, 5)
room(4, 2, 7, 2)
room(8, 1, 11, 5)                   # sigil hall
# east wing behind the locked door
room(11, 6, 16, 10)
put(12, 11, "L")
put(13, 5, "H")
put(16, 5, "S")

lines = ["# Graveborne floor 1: The Oubliette", "NAME The Oubliette", "MAP"]
lines += ["".join(r) for r in g]
lines += ["END",
          "START 8 14 N",
          # the cell: loose brick behind you, bed slab on your right, chains on the left
          "DECO 8 15 N switch",
          "DECO 9 14 W bed",
          "DECO 7 14 E chains",
          "DECO 2 15 N chains",
          "DECO 13 15 N chains",
          "DECO 7 11 S sconce",
          "DECO 14 11 S sconce",
          "DECO 0 8 E sconce",
          "DECO 7 4 E chains",
          "DECO 9 0 S sigil",
          "DECO 10 8 E sigil",
          "DECO 12 5 S sconce",
          "DECO 16 11 N chains",
          "MON 12 16 ghoul",
          "MON 6 12 skeleton",
          "MON 2 8 skeleton",
          "MON 5 9 skeleton",
          "MON 10 3 wraith",
          "MON 14 8 ghoul",
          "MON 15 9 wraith",
          "ITEM 13 16 potion",
          "ITEM 2 7 key",
          "ITEM 9 5 potion",
          "ITEM 11 1 potion",
          "ITEM 5 14 bones",
          "ITEM 13 14 bones",
          "ITEM 2 14 bones",
          ]
open(sys.argv[1], "w").write("\n".join(lines) + "\n")

if len(sys.argv) > 2:
    from PIL import Image
    col = {"#": (40, 34, 50), ".": (150, 140, 150), "D": (150, 90, 40), "L": (220, 160, 60), "B": (120, 140, 170),
           "X": (200, 60, 60), "S": (80, 200, 180), "H": (140, 80, 200)}
    img = np.array([[col[c] for c in r] for r in g], np.uint8)
    img[14, 8] = (255, 255, 255)
    Image.fromarray(img).resize((W * 16, H * 16), Image.NEAREST).save(sys.argv[2])
    print("\n".join("".join(r) for r in g))
