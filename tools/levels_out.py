"""Builds floor 2 (prison grounds + the Ashen Wood) and floor 3 (the town of Hollowmere).

  python3 tools/levels_out.py app/src/main/assets [preview_dir]
"""
import os
import sys
import numpy as np


class Grid:
    def __init__(self, w, h, fill="#"):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]

    def room(self, x0, y0, x1, y1, ch="."):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.g[y][x] = ch

    def put(self, x, y, ch):
        self.g[y][x] = ch

    def rows(self):
        return ["".join(r) for r in self.g]


def level2():
    m = Grid(26, 27)
    # the crypt's mausoleum to the north, a walled graveyard, a broken gate to the wood
    m.room(0, 0, 14, 3, "P")
    m.room(1, 4, 1, 9, "P"); m.room(13, 4, 13, 9, "P"); m.room(1, 9, 13, 9, "P")
    m.room(2, 4, 12, 8)
    m.put(7, 3, "Q")            # the door you came out of
    m.put(7, 9, ".")            # broken courtyard gate
    # winding paths through the Ashen Wood
    m.room(7, 10, 7, 13)
    m.room(3, 13, 11, 13)
    m.room(3, 14, 3, 18)        # side trail
    m.room(10, 14, 15, 18)      # grave clearing
    m.put(13, 13, "H")          # wayside shrine
    m.room(16, 16, 20, 16)
    m.room(20, 17, 20, 21)
    m.room(17, 21, 19, 21)
    m.room(17, 22, 17, 23)
    m.room(17, 23, 22, 23)
    # Hollowmere's palisade and gate on the southern edge
    m.room(14, 24, 25, 24, "F")
    m.put(22, 24, "S")
    lines = ["# Graveborne floor 2: the graveyard and the Ashen Wood",
             "NAME The Ashen Wood", "THEME forest",
             "WALL # tree tree tree2 tree tree3",
             "WALL P prison",
             "WALL Q pdoor",
             "WALL F palisade",
             "STAIRS towngate", "SHRINE shrine", "NEXT level3.txt",
             "MAP"] + m.rows() + ["END",
             "START 7 4 S",
             "PROP 3 5 grave", "PROP 5 6 grave", "PROP 9 6 grave", "PROP 11 5 grave", "PROP 6 7 grave", "PROP 8 7 grave",
             "PROP 3 7 grave", "PROP 11 7 grave", "PROP 4 8 grave", "PROP 10 8 grave",
             "MON 7 12 hound", "MON 3 17 hound", "MON 13 17 wraith", "MON 18 16 skeleton",
             "MON 20 19 hound", "MON 19 21 skeleton",
             "PROP 10 14 grave", "PROP 15 14 grave", "PROP 10 18 grave", "PROP 12 18 grave",
             "ITEM 3 18 potion", "ITEM 15 18 potion", "ITEM 5 13 bones"]
    return m, lines


def level3():
    m = Grid(17, 17, "#")
    for i in range(17):
        m.put(i, 0, "F"); m.put(i, 16, "F"); m.put(0, i, "F"); m.put(16, i, "F")
    m.room(8, 9, 8, 15)         # main street from the gate
    m.room(5, 4, 11, 8)         # square
    m.room(2, 6, 14, 6)         # cross street
    m.room(2, 2, 2, 10); m.room(14, 2, 14, 10)
    m.room(2, 2, 14, 2)         # north lane
    m.room(2, 10, 5, 10); m.room(11, 10, 14, 10)
    m.put(8, 3, "C")            # chapel
    m.put(11, 9, "H")           # the inn: rest here
    m.put(8, 16, "G")           # town gate behind you
    lines = ["# Graveborne floor 3: the town of Hollowmere",
             "NAME Hollowmere", "THEME town",
             "WALL # house house2 house house2",
             "WALL C chapel", "WALL F palisade", "WALL G towngate",
             "SHRINE inn", "STAIRS chapel",
             "MAP"] + m.rows() + ["END",
             "START 8 15 N",
             "NPC 8 13 guard HALT! THOSE EYES... YOU CAME FROM THE OUBLIETTE?|THE CURSE RAISED YOU TOO. THEN YOU'RE NO DIFFERENT FROM US.|SEE THE PRIEST BY THE CHAPEL. SHE KNOWS WHAT DIGS BENEATH HOLLOWMERE.",
             "NPC 10 8 innkeeper DEAD OR NOT, COIN IS COIN. BUT TONIGHT REST IS FREE.|TAP THE INN DOOR BESIDE ME TO REST. THE CURSE CANNOT FOLLOW YOU INSIDE.",
             "NPC 9 4 priest FOUR WHO SHOULD BE DUST. THE CURSE CHOSE WELL.|IT BLEEDS UP FROM THE BARROWS BELOW MY CHAPEL, A WOUND THAT NEVER CLOSES.|REST, RISEN ONES. WHEN THE CRYPT DOOR OPENS, YOU MUST GO DOWN.",
             "PROP 8 6 well", "PROP 5 4 lamppost", "PROP 11 4 lamppost", "PROP 5 8 lamppost",
             "DECO 2 1 S chains"]
    return m, [l for l in lines if not l.startswith("DECO")]


if __name__ == "__main__":
    out = sys.argv[1]
    for name, (m, lines) in (("level2.txt", level2()), ("level3.txt", level3())):
        open(os.path.join(out, name), "w").write("\n".join(lines) + "\n")
        print(name); print("\n".join(m.rows()))
        if len(sys.argv) > 2:
            from PIL import Image
            col = {"#": (30, 60, 30), ".": (150, 140, 120), "P": (90, 80, 100), "Q": (40, 30, 50), "F": (120, 70, 30),
                   "S": (80, 200, 180), "H": (140, 80, 200), "C": (180, 180, 200), "G": (200, 120, 40)}
            img = np.array([[col.get(c, (255, 0, 255)) for c in r] for r in m.g], np.uint8)
            Image.fromarray(img).resize((m.w * 12, m.h * 12), Image.NEAREST).save(os.path.join(sys.argv[2], name + ".png"))
