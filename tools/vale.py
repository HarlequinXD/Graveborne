"""Builds the open world: Hollowmere and the vale around it.

  python3 tools/vale.py app/src/main/assets [preview.png]

The opening chapters are linear: the Crypt, then the graveyard and the Ashen Wood trail
(level1, level2). The trail ends at Hollowmere's north gate, and from there the game opens up.
The town is a hub of side streets, alleys, courtyards and a central square, and its four
gates lead out into an 80 x 64 vale you can wander in any order:
  north   the wood edge (the trail back to the graveyard) and the High Moor with the Hanged Watch
  east    the mine road, the Mine Cliffs, and south of it the Pyre Fields
  west    the deep Ashen Wood: Gibbet Hill, the wayside shrine, Hunter's Hollow
  south   the river with three bridges, the Black Mire and the Drowned Barrow, the Wardens' Keep
Later dungeons wait sealed at the edges."""
import sys
import os
from collections import deque

W, H = 80, 64
g = [["#"] * W for _ in range(H)]
lines = []


def put(x, y, ch):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = ch


def rect(x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, ch)


def frame(x0, y0, x1, y1, ch):
    for x in range(x0, x1 + 1):
        put(x, y0, ch); put(x, y1, ch)
    for y in range(y0, y1 + 1):
        put(x0, y, ch); put(x1, y, ch)


def path(points, ch=","):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                put(x, y, ch)


# ======================================================== HOLLOWMERE (the hub)
TX0, TY0, TX1, TY1 = 26, 18, 54, 44
rect(TX0, TY0, TX1, TY1, "F")
rect(TX0 + 1, TY0 + 1, TX1 - 1, TY1 - 1, "h")
frame(29, 21, 51, 41, ":")                  # the ring lane inside the palisade
path([(40, 19), (40, 43)], ":")             # high street, north gate to south gate
path([(27, 31), (53, 31)], ":")             # cross street, west gate to east gate
rect(36, 28, 44, 34, ":")                   # the town square
# side streets
path([(33, 21), (33, 26)], ":"); path([(33, 33), (33, 41)], ":")
path([(47, 21), (47, 41)], ":")
path([(29, 25), (40, 25)], ":"); path([(44, 37), (51, 37)], ":")
path([(29, 37), (36, 37)], ":")
# alleys, dead ends and courtyards make the streets feel lived in
path([(36, 22), (36, 24)], ":")                         # tanners' alley
path([(44, 22), (44, 27)], ":")                         # chapel lane
rect(48, 33, 50, 35, ":"); put(47, 34, ":")             # well court
rect(30, 27, 32, 29, ":"); put(33, 28, "h")             # market yard off the ring
path([(43, 38), (43, 40)], ":")                         # gravediggers' alley
rect(37, 38, 39, 40, ":")                               # the old stocks yard
path([(38, 35), (38, 37)], ":")
# gates: each is a gap in the palisade flanked by gate towers
for (gx, gy, horiz) in [(40, TY0, True), (40, TY1, True), (TX0, 31, False), (TX1, 31, False)]:
    put(gx, gy, ":")
    if horiz:
        put(gx - 1, gy, "G"); put(gx + 1, gy, "G")
    else:
        put(gx, gy - 1, "G"); put(gx, gy + 1, "G")
put(39, 27, "C")        # the chapel, north face of the square
put(45, 30, "I")        # the Lantern inn, east side of the square
put(35, 32, "B")        # the boarded hall of the Gravewardens

# ======================================================== the vale around it
frame(0, 0, W - 1, H - 1, "r")
# north: the wood edge, road back to the graveyard trail
path([(40, 17), (40, 6)])
put(40, 5, "Z")                                          # where the trail from the graveyard comes out
rect(36, 9, 44, 13, ".")                                 # the crossroads glade outside the north gate
path([(36, 11), (25, 11), (25, 9)])                     # onto the moor
path([(44, 11), (56, 11), (56, 14)])                    # the mine road branches from here too
# the High Moor (north-west): wide open, broken by tors
rect(4, 2, 25, 10, ".")
for (x, y) in [(7, 4), (8, 4), (13, 7), (19, 3), (20, 3), (22, 8), (10, 9), (16, 5)]:
    put(x, y, "r")
for (x, y) in [(5, 8), (24, 4)]:
    put(x, y, "#")
rect(11, 1, 17, 1, "P"); put(14, 1, "Q")                # the Hanged Watch
# east: the mine road and the Mine Cliffs (north-east)
path([(55, 31), (66, 31), (66, 14), (56, 14)])
path([(66, 14), (70, 14), (70, 10)])
rect(58, 1, 78, 9, "r")
rect(64, 3, 76, 8, ".")
frame(63, 2, 77, 9, "r")
put(70, 9, ","); put(70, 2, "Q")                         # mine mouth on the cliff face
for (x, y) in [(66, 5), (72, 6), (74, 4)]:
    put(x, y, "r")
# east: the Pyre Fields (south-east)
rect(58, 20, 77, 44, ".")
for (x, y) in [(61, 23), (69, 26), (74, 22), (63, 36), (71, 40), (59, 42), (75, 33)]:
    put(x, y, "r")
for (x, y) in [(66, 21), (60, 30), (72, 30), (66, 43)]:
    put(x, y, "#")
path([(66, 31), (66, 45)])
# west: the deep Ashen Wood, open clearings joined by trails
path([(25, 31), (18, 31), (18, 26), (11, 26)])          # west gate trail
rect(14, 16, 22, 22, ".")                               # Gibbet Hill
for (x, y) in [(14, 16), (22, 16), (14, 22), (18, 19)]:
    put(x, y, "#")
path([(18, 23), (18, 25)])
rect(3, 23, 10, 29, ".")                                # the shrine clearing
put(6, 22, "H")
path([(6, 30), (6, 40), (14, 40)])
rect(12, 36, 18, 42, ".")                               # Hunter's Hollow
path([(18, 31), (18, 36)])
path([(22, 20), (24, 20), (24, 14), (25, 11)])          # back up to the moor
path([(15, 42), (15, 47)])
for (x, y) in [(5, 25), (9, 28), (15, 39)]:
    put(x, y, "#")
# south: the river, three bridges
path([(40, 45), (40, 47)])
rect(2, 46, 77, 47, ".")                                # the near bank
for x in range(1, W - 1):
    put(x, 48, "~"); put(x, 49, "~")
for bx in (15, 40, 66):
    put(bx, 48, ","); put(bx, 49, ",")
for (x, y) in [(8, 46), (27, 47), (51, 46), (74, 47)]:
    put(x, y, "#")
# south-west: the Black Mire
rect(2, 50, 37, 62, ".")
for (x0, y0, x1, y1) in [(5, 52, 9, 54), (16, 56, 20, 58), (26, 51, 29, 53), (31, 57, 35, 59), (9, 59, 11, 61)]:
    rect(x0, y0, x1, y1, "~")
for (x, y) in [(13, 51), (23, 55), (30, 55), (4, 57), (36, 51)]:
    put(x, y, "#")
rect(19, 61, 25, 62, "P"); put(22, 61, "Q")            # the Drowned Barrow
# south-east: the Wardens' Keep
path([(40, 50), (40, 52), (54, 52)])
path([(66, 50), (66, 52)])
rect(54, 51, 74, 61, ".")
frame(54, 51, 74, 61, "P")
for (x, y) in [(54, 52), (66, 51), (74, 56), (60, 61)]:
    put(x, y, ".")                                      # breaches in the curtain wall
rect(61, 56, 67, 61, "P"); put(64, 56, "Q")             # the keep's doors
frame(0, 0, W - 1, H - 1, "r")

lines += [
    "# Graveborne: Hollowmere and the vale (open world, generated by tools/vale.py)",
    "NAME The Hollowmere Vale", "THEME forest",
    "WALL # tree tree tree2 tree tree3",
    "WALL Z tree3",
    "WALL r cliff",
    "WALL P prison",
    "WALL Q pdoor",
    "WALL F palisade",
    "WALL G towngate",
    "WALL h house house2 house house2",
    "WALL B house2",
    "WALL C chapel",
    "FLOOR , path",
    "FLOOR : cobble",
    "FLOOR ~ water block",
    "SHRINE H shrine",
    "SHRINE I inn",
    "MAP"] + ["".join(r) for r in g] + ["END",
    "START 40 19 S",
    "EXIT 40 5 level2.txt 22 23 N",
    # regions: listed smallest first so they win where they overlap
    "AREA 36 28 44 34 town step_cobble The Square",
    "AREA 26 18 54 44 town step_cobble Hollowmere",
    "AREA 14 16 22 22 forest step_grass Gibbet Hill",
    "AREA 3 22 10 29 forest step_grass The Wayside Shrine",
    "AREA 12 36 18 42 forest step_grass Hunter's Hollow",
    "AREA 33 5 47 17 forest step_grass The North Road",
    "AREA 2 1 25 11 forest step_grass The High Moor",
    "AREA 58 1 78 10 forest step_grass The Mine Cliffs",
    "AREA 48 11 72 19 forest step_grass The Mine Road",
    "AREA 55 20 78 45 forest step_grass The Pyre Fields",
    "AREA 1 12 25 45 forest step_grass The Ashen Wood",
    "AREA 1 46 78 49 forest step_grass The River Hollow",
    "AREA 2 50 37 62 forest step_grass The Black Mire",
    "AREA 38 50 78 62 forest step_grass The Wardens' Keep",
    # sealed ways onward (later chapters)
    "NOTE 14 1 THE WATCHTOWER DOOR IS BARRED FROM WITHIN. SOMETHING CREAKS ON A ROPE BEHIND IT.",
    "NOTE 70 2 A ROCKFALL CHOKES THE MINE MOUTH. BONES JUT FROM THE RUBBLE.",
    "NOTE 22 61 BLACK WATER FILLS THE BARROW MOUTH TO THE LINTEL.",
    "NOTE 64 56 THE KEEP'S DOORS ARE CHAINED WITH THE GRAVEWARDENS' SEAL.",
    "NOTE 39 27 THE CHAPEL IS BARRED. NOT YET.",
    "NOTE 35 32 THE GRAVEWARDENS' HALL. BOARDED UP SINCE BEFORE ANYONE CAN REMEMBER.",
    "NOTE 33 28 A MARKET STALL, SHUTTERED. A SIGN: CLOSED UNTIL THE MOON TURNS.",
    # signposts
    "NOTE 41 42 A SIGNPOST: SOUTH GATE. THE RIVER, THE MIRE, THE OLD KEEP.",
    "NOTE 39 20 A SIGNPOST: NORTH GATE. THE GRAVEYARD ROAD AND THE MOOR.",
    "NOTE 28 30 A SIGNPOST: WEST GATE. THE ASHEN WOOD. KEEP TO THE TRAILS.",
    "NOTE 52 30 A SIGNPOST: EAST GATE. THE MINES AND THE PYRE FIELDS.",
    "NOTE 45 10 A SIGNPOST: THE MINES EAST. THE MOOR WEST. HOLLOWMERE SOUTH.",
    # the townsfolk
    "NPC 41 21 guard HALT! THOSE EYES... YOU CAME OUT OF THE WARDENS' CRYPT.|THE OLD SONGS SAY FOUR RISE FROM THAT TOMB WHEN THE MOON TURNS VIOLET. I NEVER BELIEVED THEM.|THE PRIEST IS AT THE CHAPEL ON THE SQUARE. FOUR GATES OUT OF TOWN. NONE OF THEM SAFE.",
    "NPC 44 29 innkeeper DEAD OR NOT, COIN IS COIN. BUT TONIGHT REST IS FREE.|TAP THE INN DOOR BESIDE ME TO REST. THE CURSE CANNOT FOLLOW YOU INSIDE.",
    "NPC 38 28 priest FOUR WHO SHOULD BE DUST. THE CURSE CHOSE WELL.|IT BLEEDS UP FROM THE BARROWS BELOW MY CHAPEL, A WOUND THAT NEVER CLOSES.|SEALING IT ONLY STARTS THE CIRCLE AGAIN. FIND THE GRAVEWARDENS' MARKS IN THE VALE, AND I WILL OPEN THE WAY.",
    "NPC 29 32 guard WEST GATE. THE WOOD EATS THE CARELESS.|THE OLD TRAILS STILL RUN TO GIBBET HILL AND THE HUNTER'S HOLLOW.",
    "NPC 51 32 guard EAST GATE. THE MINERS WALLED THEMSELVES IN.|SMOKE STILL RISES FROM THE PYRE FIELDS. NOBODY LIGHTS IT.",
    "NPC 39 41 guard SOUTH GATE. THREE BRIDGES CROSS THE RIVER.|THE WEST ONE TO THE MIRE. THE EAST ONE TO THE KEEP. THE MIDDLE ONE TO BOTH.",
    "PROP 40 31 well", "PROP 49 34 well",
    "PROP 36 28 lamppost", "PROP 44 34 lamppost", "PROP 36 34 lamppost",
    "PROP 29 21 lamppost", "PROP 51 41 lamppost", "PROP 29 41 lamppost", "PROP 51 21 lamppost",
]
for (x, y) in [(15, 18), (21, 18), (16, 21), (4, 24), (9, 24), (8, 47), (12, 53), (24, 59), (34, 52), (38, 9), (42, 13)]:
    lines.append(f"PROP {x} {y} grave")
mons = [("hound", 40, 8), ("skeleton", 30, 11),
        ("hound", 12, 5), ("skeleton", 18, 9), ("hound", 22, 3),
        ("skeleton", 60, 14), ("hound", 66, 22), ("skeleton", 68, 6), ("skeleton", 73, 5),
        ("wraith", 62, 27), ("wraith", 70, 36), ("skeleton", 64, 40), ("wraith", 75, 25),
        ("hound", 21, 31), ("wraith", 18, 17), ("skeleton", 20, 21), ("ghoul", 7, 27), ("ghoul", 14, 38), ("hound", 6, 35),
        ("skeleton", 30, 46), ("hound", 55, 47),
        ("ghoul", 7, 50), ("ghoul", 20, 53), ("ghoul", 28, 56), ("wraith", 14, 60), ("ghoul", 33, 61),
        ("skeleton", 58, 54), ("skeleton", 70, 54), ("wraith", 64, 53), ("hound", 48, 52)]
for t, x, y in mons:
    lines.append(f"MON {x} {y} {t}")
for (x, y) in [(10, 2), (19, 22), (3, 29), (12, 42), (76, 8), (77, 44), (3, 61), (73, 60), (50, 35), (37, 40), (30, 29)]:
    lines.append(f"ITEM {x} {y} potion")
for (x, y) in [(17, 37), (65, 4), (62, 43), (36, 60)]:
    lines.append(f"ITEM {x} {y} bones")

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def flood(start, walk, blocked=()):
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in N4:
            n = (x + dx, y + dy)
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and g[n[1]][n[0]] in walk and n not in blocked:
                seen.add(n); q.append(n)
    return seen


def check():
    blocked = {(int(p[1]), int(p[2])) for p in (l.split() for l in lines) if p and p[0] in ("PROP", "NPC")}
    seen = flood((40, 19), set(".,:"), blocked)
    bad = []
    for l in lines:
        p = l.split()
        if not p:
            continue
        if p[0] in ("MON", "ITEM", "PROP", "NPC"):
            x, y = int(p[1]), int(p[2])
            if g[y][x] not in ".,:":
                bad.append(("not on ground", l[:40]))
            elif p[0] in ("MON", "ITEM") and (x, y) not in seen:
                bad.append(("unreachable", l[:40]))
        if p[0] in ("NOTE", "EXIT"):
            x, y = int(p[1]), int(p[2])
            if not any((x + dx, y + dy) in seen for dx, dy in N4):
                bad.append(("can't reach", l[:50]))
    for ch, name in (("H", "shrine"), ("I", "inn")):
        for y in range(H):
            for x in range(W):
                if g[y][x] == ch and not any((x + dx, y + dy) in seen for dx, dy in N4):
                    bad.append(("can't reach", name))
    return bad, seen


def routes():
    """Which town gates lead to each region, walking outside the palisade only."""
    gates = {"north": (40, 17), "south": (40, 45), "west": (25, 31), "east": (55, 31)}
    targets = {"moor": (14, 2), "mines": (70, 3), "pyre": (66, 30), "gibbet": (18, 20), "shrine": (6, 23),
               "hollow": (15, 40), "mire": (22, 60), "keep": (64, 55)}
    res = {k: [] for k in targets}
    for gname, s in gates.items():
        seen = flood(s, set(".,"))
        for k, t in targets.items():
            if t in seen:
                res[k].append(gname)
    return res


if __name__ == "__main__":
    out = sys.argv[1]
    bad, seen = check()
    for b in bad:
        print("PROBLEM", b)
    for k, v in routes().items():
        print(f"{k:8s} reached from gates: {', '.join(v) or 'NONE'}")
    open(os.path.join(out, "vale.txt"), "w").write("\n".join(lines) + "\n")
    print("walkable cells reachable:", len(seen))
    if len(sys.argv) > 2:
        import numpy as np
        from PIL import Image
        col = {"#": (28, 52, 24), "Z": (60, 90, 40), "r": (90, 84, 96), ".": (120, 140, 80), ",": (150, 120, 80),
               ":": (170, 160, 140), "~": (30, 80, 100), "P": (110, 104, 120), "Q": (40, 30, 50), "F": (120, 70, 30),
               "G": (200, 120, 40), "h": (150, 110, 80), "B": (100, 70, 60), "C": (200, 200, 230), "I": (240, 180, 60),
               "H": (140, 80, 200)}
        img = np.array([[col.get(c, (255, 0, 255)) for c in r] for r in g], np.uint8)
        for l in lines:
            p = l.split()
            if p and p[0] == "MON":
                img[int(p[2]), int(p[1])] = (220, 40, 40)
            if p and p[0] == "NPC":
                img[int(p[2]), int(p[1])] = (255, 255, 255)
            if p and p[0] == "ITEM":
                img[int(p[2]), int(p[1])] = (60, 220, 220)
        Image.fromarray(img).resize((W * 10, H * 10), Image.NEAREST).save(sys.argv[2])
