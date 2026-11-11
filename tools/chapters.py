"""Builds chapters 3 to 11 of Graveborne's linear campaign, each with its story built in:
chapter cards, spoken scenes on the cells where they happen, bosses, levers, gated exits.

  python3 tools/chapters.py app/src/main/assets [preview_dir]

Chapters 1 and 2 (the Crypt, the Graveyard and the Ashen Wood) are built by level1.py and
levels_out.py. The run is one road: each chapter's exit leads into the next.

Scene lines: "NAME: words" is spoken by NAME, anything else is narration. '|' separates pages."""
import os
import sys
from collections import deque


class Map:
    def __init__(self, w, h, fill="#"):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]
        self.lines = []

    def rect(self, x0, y0, x1, y1, ch="."):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.g[y][x] = ch

    def path(self, pts, ch="."):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                for y in range(min(y0, y1), max(y0, y1) + 1):
                    self.g[y][x] = ch

    def put(self, x, y, ch):
        self.g[y][x] = ch

    def frame(self, x0, y0, x1, y1, ch):
        for x in range(x0, x1 + 1):
            self.g[y0][x] = ch; self.g[y1][x] = ch
        for y in range(y0, y1 + 1):
            self.g[y][x0] = ch; self.g[y][x1] = ch

    def add(self, *ls):
        self.lines += list(ls)

    def scene(self, x, y, *pages):
        self.lines.append(f"SCENE {x} {y} " + "|".join(pages))

    def text(self, header):
        return "\n".join(header + ["MAP"] + ["".join(r) for r in self.g] + ["END"] + self.lines) + "\n"


# =================================================================== Chapter III
def hollowmere(night=False):
    """The town. In Chapter III you walk up from the gate to the chapel; in Chapter IX it is under siege."""
    m = Map(21, 27, "h")
    m.frame(0, 0, 20, 26, "F")
    m.path([(10, 25), (10, 15)])                       # the gate road
    m.rect(7, 10, 13, 14)                              # the square
    m.path([(10, 9), (10, 4)])                         # chapel road
    m.rect(8, 2, 12, 3)                                # chapel yard
    m.put(10, 1, "C")                                  # the chapel door
    m.put(14, 11, "I")                                 # the Lantern inn, on the square
    # side streets
    m.path([(14, 13), (18, 13), (18, 5), (11, 5)])     # tanners' row, loops back to the chapel road
    m.path([(9, 20), (3, 20), (3, 16)])                # widow's alley, a dead end
    m.path([(6, 12), (2, 12), (2, 7), (5, 7)])         # market lane and the shuttered stalls
    m.rect(9, 23, 11, 25)                              # the gate yard
    m.put(10, 26, "G")
    header = ["NAME Hollowmere", "THEME town",
              "WALL h house house2 house house2", "WALL F palisade", "WALL G towngate", "WALL C chapel",
              "SHRINE I inn"]
    if not night:
        header = ["# Graveborne Chapter III: Hollowmere", "CHAPTER III Hollowmere"] + header
        m.add("START 10 25 N",
              "EXIT 10 1 level4.txt 2 17 N",
              "NOTE 10 26 THE GATE IS BARRED BEHIND YOU.",
              "NOTE 6 7 THE MARKET STALLS ARE SHUTTERED. A SIGN: CLOSED UNTIL THE MOON TURNS.",
              "NPC 11 24 guard GO ON UP TO THE CHAPEL. THE PRIEST WILL KNOW WHAT TO DO WITH YOU.|AND KEEP YOUR HANDS OFF YOUR WEAPONS IN MY TOWN.",
              "NPC 13 12 innkeeper DEAD OR NOT, COIN IS COIN. THE CRYPT'S GRAVE GOODS SPEND LIKE ANY OTHER.|TAP THE INN DOOR BESIDE ME TO REST. THE CURSE CANNOT FOLLOW YOU INSIDE.",
              "NPC 9 2 priest FIND THE RECORD IN THE UNDERCROFT. THE DOOR IS UNBARRED.|WHATEVER RINGS THAT BELL, IT IS NOT THE SEXTON. NOT ANY MORE.",
              "NPC 3 16 townsman MY HUSBAND WENT TO THE PYRES LAST WINTER. I WATCHED HIM BURN, SO HE COULD NOT COME BACK.|AND STILL I LEAVE THE DOOR UNLATCHED AT NIGHT.",
              "NPC 18 6 townsman WARDENS? THE ONES FROM THE SONGS? MY GRANDDA SAID YOU'D COME.|HE SAID TO RUN WHEN YOU DID.",
              "PROP 10 12 well", "PROP 7 10 lamppost", "PROP 13 14 lamppost", "PROP 8 3 lamppost",
              "MON 2 8 hound", "ITEM 2 9 potion", "ITEM 3 17 potion")
        m.scene(10, 25,
                "The gate groans shut behind you. Lanterns, smoke, the smell of the living. Hollowmere.",
                "GUARD: HALT! STAND IN THE LIGHT WHERE I CAN SEE YOU.",
                "GUARD: THOSE EYES... TEAL, NOT VIOLET. YOU CAME OUT OF THE WARDENS' CRYPT.",
                "GUARD: MY GRANDMOTHER SANG OF FOUR WHO RISE FROM THAT TOMB WHEN THE MOON TURNS. I NEVER BELIEVED HER.",
                "GUARD: THE PRIEST KEEPS THE OLD SONGS. HER CHAPEL IS AT THE TOP OF THE TOWN. GO.")
        m.scene(10, 14,
                "Every shutter in the square is closed. Behind them people are praying. Pyre smoke drifts over the roofs.",
                "BRANN: THEY'RE AFRAID OF US.",
                "SERA: THEY SHOULD BE. THEY CHAINED US IN.",
                "ALDRIC: THEY DID WHAT THEY HAD TO. WE KEEP OUR OATH ANYWAY.")
        m.scene(2, 11, "VESH: A HOUND GOT OVER THE PALISADE. VIOLET EYES. THE WOUND'S OWN.")
        m.scene(10, 3,
                "PRIEST: ALDRIC. BRANN. SERA. VESH. I KNOW YOUR FACES FROM THE CHAPEL GLASS.",
                "PRIEST: I AM THE LAST WHO KEEPS THE GRAVEWARDENS' SONGS. THE ORDER ITSELF IS DUST.",
                "PRIEST: THE WOUND BLEEDS UP FROM THE BARROWS UNDER THIS CHAPEL. YOU SEALED IT ONCE. YOU HAVE SEALED IT AGAIN AND AGAIN.",
                "ALDRIC: THEN SHOW US THE WAY DOWN, AND WE WILL SEAL IT AGAIN.",
                "PRIEST: NO. EVERY SEALING COSTS YOUR LIVES, AND EVERY TIME IT WAKES AGAIN. THE SONGS SAY THE CIRCLE CAN BE BROKEN. NOT HOW.",
                "PRIEST: THE ORDER'S LAST ABBOT LEFT A RECORD IN THE UNDERCROFT, BENEATH MY CHAPEL. NO ONE HAS GONE DOWN SINCE THE BURIALS STOPPED.",
                "PRIEST: AND SOMETHING DOWN THERE STILL RINGS THE BURIAL BELL. I HAVE UNBARRED THE DOOR. FIND THE RECORD.")
        return m, header
    # ---------------------------------------------------------------- Chapter IX
    header = ["# Graveborne Chapter IX: The Violet Night", "CHAPTER IX The Violet Night", "TOUGH 3"] + header
    m.add("START 10 25 N",
          "EXIT 10 1 level10.txt 12 23 N clear",
          "WAVES 10 13",
          "NPC 8 10 guard HOLD THE SQUARE! FOR HOLLOWMERE!",
          "NPC 13 12 innkeeper I'VE A CLEAVER AND A GRUDGE. COME ON, THEN!",
          "NPC 9 2 priest THE CHAPEL STANDS WHILE YOU STAND.",
          "NPC 7 14 townsman WE CHAINED YOU IN. AND HERE YOU ARE, FIGHTING FOR US.",
          "NPC 13 10 townsman FOR THE WARDENS!",
          "PROP 10 12 well", "PROP 7 10 lamppost", "PROP 13 14 lamppost",
          "PROP 3 16 pyre", "PROP 18 7 pyre",
          "ITEM 9 13 potion", "ITEM 11 11 potion", "ITEM 18 12 potion", "ITEM 4 20 potion",
          "WAVETEXT 1 GUARD: HERE THEY COME, UP THE GATE ROAD!",
          "WAVETEXT 2 INNKEEPER: GHOULS IN THE WIDOW'S ALLEY! AND THE MARKET LANE!",
          "WAVETEXT 3 PRIEST: WRAITHS OVER THE ROOFTOPS! HOLD THE CHAPEL ROAD!",
          "WAVETEXT 4 VESH: EVERYTHING IT HAS LEFT. HERE IT COMES.",
          )
    waves = {1: [("skeleton", 10, 22), ("skeleton", 10, 24), ("hound", 10, 20), ("hound", 10, 18), ("skeleton", 10, 23)],
             2: [("ghoul", 3, 18), ("ghoul", 4, 20), ("ghoul", 2, 9), ("hound", 2, 11), ("ghoul", 7, 20)],
             3: [("wraith", 10, 5), ("wraith", 18, 9), ("skeleton", 15, 13), ("wraith", 11, 5), ("skeleton", 18, 11)],
             4: [("ghoul", 10, 22), ("wraith", 3, 17), ("skeleton", 17, 13), ("hound", 2, 8), ("skeleton", 10, 20),
                 ("wraith", 10, 6), ("ghoul", 18, 6), ("hound", 10, 24)]}
    for wv, ms in waves.items():
        for t, x, y in ms:
            m.add(f"MON {x} {y} {t} {wv}")
    m.scene(10, 25,
            "Hollowmere is burning. The violet moon hangs low over the roofs, and the dead are coming out of the ash.",
            "GUARD: WARDENS! THEY'RE OVER THE PALISADE! WE CAN'T HOLD THEM WITHOUT YOU!",
            "ALDRIC: THE SQUARE. EVERY ROAD MEETS THERE. WE HOLD THE SQUARE.")
    m.add("AFTERBOSS The dead stop coming. Dawn will not rise under this moon, but the town is still standing."
          "|GUARD: WE CHAINED YOU IN. AND YOU CAME BACK FOR US."
          "|PRIEST: YOU HAVE ALL FOUR STONES. I SEE IT IN YOUR FACES. YOU KNOW WHAT THEY ARE FOR NOW."
          "|ALDRIC: WE KNOW. I KNOW WHAT I DID."
          "|PRIEST: THEN TAKE THIS. THE KEY TO THE BARROW GATE BENEATH MY CHAPEL. THE ONE DOOR I WOULD NOT OPEN."
          "|PRIEST: WHATEVER YOU CHOOSE DOWN THERE, HOLLOWMERE WILL REMEMBER YOU.")
    return m, header


# =================================================================== Chapter IV
def undercroft():
    m = Map(22, 20)
    m.rect(1, 13, 4, 17)                      # the stair hall
    m.path([(2, 12), (2, 6)])
    m.path([(2, 5), (14, 5)])
    m.rect(6, 14, 9, 17); m.put(5, 15, "D")   # the sexton's vault
    m.rect(7, 1, 10, 3); m.put(8, 4, "D")     # ossuary
    m.put(15, 5, "L")
    m.path([(16, 5), (17, 5), (17, 9)])
    m.rect(11, 10, 20, 18)                    # the belfry vault
    m.put(21, 14, "S")
    m.put(2, 18, "S")
    header = ["# Graveborne Chapter IV: The Chapel Undercroft", "CHAPTER IV The Chapel Undercroft",
              "NAME The Chapel Undercroft", "THEME dungeon", "STAIRS stairs", "TOUGH 1"]
    m.add("START 2 17 N",
          "NOTE 2 18 THE STAIR UP TO THE CHAPEL. YOU HAVE WORK DOWN HERE.",
          "EXIT 21 14 level5.txt 12 24 N boss+letter",
          "DECO 1 12 E loculi", "DECO 3 12 W loculi", "DECO 1 9 E ossuary", "DECO 3 8 W loculi",
          "DECO 5 6 N sconce", "DECO 11 6 N sconce", "DECO 10 2 W ossuary", "DECO 9 18 N loculi",
          "DECO 11 9 S sigil", "DECO 18 9 S sconce", "DECO 13 19 N loculi", "DECO 21 11 W ossuary",
          "MON 3 14 skeleton", "MON 2 7 skeleton", "MON 8 15 ghoul", "MON 9 2 ghoul", "MON 12 5 wraith",
          "MON 17 7 skeleton",
          "BOSS 16 14 sexton",
          "ITEM 7 16 key", "ITEM 8 1 potion", "ITEM 6 17 potion", "ITEM 19 17 letter", "ITEM 12 17 potion",
          "PROP 13 11 bell", "PROP 4 16 coffin", "PROP 9 14 coffin", "PROP 19 11 coffin")
    m.scene(2, 17,
            "The undercroft smells of lime and old bones. Somewhere below, a bell tolls. Once. Twice.",
            "VESH: NO ONE HAS RUNG A BURIAL BELL IN THIS TOWN FOR A GENERATION.",
            "BRANN: SOMEONE'S RINGING IT NOW.")
    m.scene(7, 16, "SERA: THE SEXTON'S KEY. HE KEPT EVERY DOOR DOWN HERE LOCKED, EVEN FROM THE DEAD.")
    m.scene(14, 5, "Beyond an iron door, the bell is louder. Each toll shakes dust from the vaults.")
    m.scene(17, 9,
            "THE SEXTON: ANOTHER BURIAL? GOOD. GOOD. THE BELL MUST RING FOR EVERY ONE. EVERY ONE.",
            "ALDRIC: HE DIED AT HIS POST, AND HE NEVER STOPPED RINGING.",
            "THE SEXTON: THE DEAD COME WHEN I RING. COME DOWN, LITTLE WARDENS. LIE DOWN.")
    m.add("AFTERBOSS The Sexton's bell cracks on the flagstones. For the first time in a generation, the undercroft is silent."
          "|VESH: THERE, ON THE BIER IN THE CORNER. SEALED PAGES, UNDER WAX.")
    m.scene(19, 17,
            "The abbot's hand, shaking, two hundred years old:",
            "\"TO THE FOUR, IF YOU RISE AND FIND THIS. I HID YOUR OATH-STONES. FORGIVE ME, THOUGH I DO NOT DESERVE IT.\"",
            "\"THE WOUND CAN BE UNMADE, NOT ONLY SEALED. FOUR MUST BREAK THE OATHS THEY SWORE, UPON THE STONES THEY SWORE THEM ON.\"",
            "\"I PUT EACH STONE WHERE ITS WARDEN FIRST BLED FOR HOLLOWMERE: THE WATCHTOWER ON THE MOOR. THE BARROW IN THE MIRE. THE DEEP MINES. OUR OWN KEEP.\"",
            "SERA: WHY WOULD THE ABBOT HIDE THEM FROM US?",
            "ALDRIC: ...I DON'T KNOW.",
            "VESH: THE WATCHTOWER FIRST. I STOOD GUARD THERE AS A BOY. THE OLD BELL STAIR COMES OUT ON THE MOOR ROAD.")
    return m, header


# =================================================================== Chapter V
def hanged_watch():
    m = Map(25, 26, "r")
    # the moor: open ground, broken by tors
    m.rect(2, 14, 22, 24)
    for (x, y) in [(4, 15), (5, 15), (16, 18), (20, 22), (3, 22), (9, 23), (14, 15), (21, 16)]:
        m.put(x, y, "r")
    for (x, y) in [(18, 23), (8, 15), (19, 19)]:
        m.put(x, y, "#")
    m.path([(12, 24), (12, 20), (6, 20), (6, 16), (12, 16), (12, 13)], ",")
    # the tower compound
    m.frame(6, 2, 18, 12, "P")
    m.rect(7, 7, 17, 11, ";")                  # courtyard
    m.rect(7, 3, 17, 6, "P")
    m.rect(9, 3, 15, 5, ";")                   # the inner keep
    m.put(12, 6, "X")                           # sealed inner door
    m.put(12, 12, ";")                          # the broken gate
    m.put(12, 2, "Q")                           # postern down the far side of the ridge
    header = ["# Graveborne Chapter V: The Hanged Watch", "CHAPTER V The Hanged Watch",
              "NAME The Hanged Watch", "THEME forest", "TOUGH 1",
              "WALL # tree tree2 tree3", "WALL r cliff", "WALL P prison prisonwin prison", "WALL Q pdoor", "WALL X prison",
              "FLOOR , path", "FLOOR ; floor"]
    m.add("START 12 24 N",
          "EXIT 12 2 level6.txt 2 21 E boss+stone",
          "LEVER 18 9 W open 12 6",
          "PROP 6 18 hanged", "PROP 7 21 hanged", "PROP 11 17 hanged", "PROP 13 14 hanged",
          "PROP 8 8 hanged", "PROP 16 8 hanged", "PROP 9 4 hanged", "PROP 15 4 hanged",
          "MON 9 20 hound", "MON 5 17 hound", "MON 12 15 skeleton", "MON 17 21 skeleton",
          "MON 9 10 skeleton", "MON 15 10 skeleton", "MON 14 9 skeleton",
          "MON 10 8 hound",
          "BOSS 12 4 captain",
          "ITEM 12 3 stone", "ITEM 3 23 potion", "ITEM 17 11 potion", "ITEM 20 14 potion", "ITEM 7 7 potion",
          "SHRINE H shrine")
    m.put(2, 13, "H")
    m.scene(12, 24,
            "The moor road climbs into a cold wind. On the ridge stands the Hanged Watch, a broken tower with shapes swinging from its walls.",
            "VESH: MY FIRST POST. I WAS FOURTEEN. I LEARNED TO SHOOT FROM THOSE WALLS.",
            "BRANN: LOOKS LIKE THE TOWN FOUND ANOTHER USE FOR THEM.")
    m.scene(6, 19,
            "SERA: THE TOWN HANGED THE RISEN FROM THE WATCH, THE LAST TIME. THEY'RE STILL MOVING.",
            "ALDRIC: THERE'S A GRAVE SHRINE IN THE ROCKS TO THE WEST. PRAY THERE BEFORE THE TOWER.")
    m.scene(12, 11,
            "VESH: THE INNER DOOR IS WINCHED SHUT. THERE'S A LEVER ON THE EAST WALL. I USED TO HAUL IT FOR THE CAPTAIN.")
    m.scene(12, 6,
            "THE HANGED CAPTAIN: VESH. MY BEST BOY. YOU LEFT YOUR POST.",
            "VESH: CAPTAIN ORREN. I'M SORRY.",
            "THE HANGED CAPTAIN: THEY HANGED ME FROM MY OWN TOWER. NOW I KEEP THE WATCH FOREVER. STAND YOUR POST, BOY. FOREVER.")
    m.add("AFTERBOSS The Captain's rope goes slack at last.|VESH: REST, CAPTAIN. I'LL TAKE THE WATCH FROM HERE.")
    m.scene(12, 3,
            "Vesh closes his hand around the Oath-stone. A memory comes back with it, sharp as a bolt.",
            "VESH: THE BARROWS. THE FIRST TIME. WE WERE LOSING. ALL FOUR OF US WERE GOING TO DIE DOWN THERE, WITH THE WOUND STILL OPEN.",
            "ALDRIC: BUT WE SEALED IT.",
            "VESH: DID WE? I DON'T REMEMBER HOW.",
            "SERA: THE BARROW IN THE MIRE IS NEXT. THAT ONE IS MINE. THE POSTERN DOOR LEADS DOWN THE FAR SIDE OF THE RIDGE.")
    return m, header


# =================================================================== Chapter VI
def drowned_barrow():
    m = Map(23, 24, "#")
    m.rect(1, 14, 21, 22)                     # the mire
    for (x0, y0, x1, y1) in [(4, 15, 6, 17), (15, 19, 18, 21), (8, 20, 10, 22), (17, 15, 19, 16), (12, 18, 13, 19)]:
        m.rect(x0, y0, x1, y1, "~")
    for (x, y) in [(3, 19), (14, 15), (20, 19), (7, 18)]:
        m.put(x, y, "#")
    m.path([(1, 21), (5, 21), (5, 19), (11, 19), (11, 16), (12, 16), (12, 14)], ",")
    # the barrow, a mound of megaliths
    m.rect(1, 1, 21, 13, "b")
    m.path([(12, 13), (12, 9)], ";")           # the barrow mouth
    m.rect(5, 7, 20, 8, ";")                   # hall of the dead
    m.path([(6, 6), (6, 4)], "w")              # flooded way north
    m.rect(4, 2, 9, 3, ";")                    # sluice chamber
    m.path([(10, 2), (13, 2)], "w")            # flooded passage east
    m.rect(14, 2, 20, 5, ";")                  # the knight's chamber
    m.put(21, 3, "Q")
    m.put(22, 21, "#")
    header = ["# Graveborne Chapter VI: The Drowned Barrow", "CHAPTER VI The Drowned Barrow",
              "NAME The Drowned Barrow", "THEME forest", "TOUGH 2",
              "WALL # tree tree2 tree3", "WALL b barrow", "WALL Q pdoor",
              "FLOOR , path", "FLOOR ~ water block", "FLOOR ; barrowfloor roof", "FLOOR w water block roof",
              "SHRINE H shrine"]
    m.put(12, 10, ";")
    m.put(11, 13, "H")
    m.add("START 2 21 E",
          "EXIT 21 3 level7.txt 2 2 S boss+stone",
          "LEVER 21 7 W drain 6 4 6 6 ;",
          "LEVER 3 2 E drain 10 2 13 2 ;",
          "MON 8 19 ghoul", "MON 14 17 ghoul", "MON 18 18 hound", "MON 3 15 ghoul",
          "MON 9 8 skeleton", "MON 17 7 ghoul", "MON 19 8 skeleton", "MON 7 3 ghoul", "MON 5 2 wraith",
          "BOSS 17 3 drowned",
          "ITEM 20 5 stone", "ITEM 20 14 potion", "ITEM 5 8 potion", "ITEM 9 2 potion", "ITEM 2 16 potion",
          "PROP 7 15 grave", "PROP 16 14 grave", "PROP 10 7 coffin", "PROP 15 8 coffin")
    m.scene(2, 21,
            "The mire stinks of rot and still water. Pale lights drift over the pools.",
            "SERA: I HELD THE LINE AT THE BARROW MOUTH WHILE THE OTHERS WENT DOWN. SHIELDS LOCKED. NOTHING GOT PAST ME.",
            "BRANN: AND THEN?",
            "SERA: AND THEN I DON'T REMEMBER.")
    m.scene(12, 14, "SERA: HERE. THIS IS WHERE I STOOD.", "ALDRIC: THERE'S A SHRINE CUT INTO THE MOUND, JUST BESIDE THE MOUTH.")
    m.scene(6, 7,
            "Black water fills the passage north. Somewhere along the hall, old sluice gates creak.",
            "BRANN: THE BARROW-BUILDERS FLOODED THEIR OWN HALLS. THERE'LL BE A LEVER TO DRAIN THEM.")
    m.scene(13, 2,
            "THE DROWNED KNIGHT: ...SPEARWARDEN. YOU HELD THE MOUTH AGAINST US. WE REMEMBER YOU.",
            "SERA: THE BARROW KINGS' GUARD. I PUT YOU IN THE WATER MYSELF.",
            "THE DROWNED KNIGHT: AND THE WATER GAVE US BACK.")
    m.add("AFTERBOSS The Drowned Knight sinks to his knees, and the water takes him again.")
    m.scene(20, 5,
            "SERA: I REMEMBER NOW. THE OTHERS WENT DOWN, AND ALDRIC WENT ON ALONE INTO THE DARK. HE WAS GONE A LONG TIME.",
            "SERA: WHEN HE CAME BACK HE HAD THAT RIBBON ON HIS HELM. VIOLET. AND THE DEAD STOPPED COMING.",
            "ALDRIC: I... DON'T REMEMBER ANY OF THAT.",
            "BRANN: THE MINES NEXT. MY STONE. MAYBE IT REMEMBERS FOR YOU.")
    return m, header


# =================================================================== Chapter VII
def ossuary_mines():
    m = Map(24, 24)
    m.path([(2, 2), (2, 10)], ",")
    m.path([(2, 10), (18, 10)], ",")
    m.path([(6, 11), (6, 15)], ",")
    m.rect(4, 16, 8, 18, ",")                  # the bone store
    m.path([(12, 9), (12, 5)], ",")
    m.rect(10, 2, 15, 4, ",")                  # old foreman's chamber
    m.put(19, 10, "L")
    m.path([(20, 10), (20, 14)], ",")
    m.rect(10, 15, 21, 21, ",")                # the deep seam
    m.put(22, 18, "S")
    m.put(1, 4, "H")
    header = ["# Graveborne Chapter VII: The Ossuary Mines", "CHAPTER VII The Ossuary Mines",
              "NAME The Ossuary Mines", "THEME dungeon", "TOUGH 2", "STAIRS stairs",
              "WALL # mine mine bonewall mine bonewall", "FLOOR , path"]
    m.add("START 2 2 S",
          "EXIT 22 18 level8.txt 12 22 N boss+stone",
          "MON 2 8 skeleton", "MON 8 10 skeleton", "MON 6 14 ghoul", "MON 5 17 ghoul", "MON 7 17 skeleton",
          "MON 12 6 wraith", "MON 14 3 skeleton", "MON 16 10 ghoul", "MON 20 13 skeleton",
          "BOSS 15 18 colossus",
          "ITEM 8 16 key", "ITEM 11 3 potion", "ITEM 4 18 potion", "ITEM 10 21 potion", "ITEM 21 15 potion",
          "ITEM 20 20 stone", "ITEM 14 4 bones", "ITEM 13 20 bones",
          "DECO 21 16 E sigil")
    m.scene(2, 2,
            "The barrow-breakers' mines. When the town stopped burying its dead, it dug up the old graveyards and packed the bones down here.",
            "BRANN: I WORKED THESE SEAMS BEFORE I TOOK THE OATH. BREAKING BARROWS FOR THE KING'S GOLD.",
            "BRANN: IN THE DEEPEST SEAM THERE WERE CARVINGS. THAT'S WHERE I LEARNED THE SIGIL.",
            "VESH: A SHRINE IN THE SHAFT WALL. THE ORDER KNEW WE'D COME THIS WAY.")
    m.scene(8, 16, "SERA: THE FOREMAN'S KEY, ON A HOOK BY THE BONES. THE DEEP SEAM WAS ALWAYS LOCKED.")
    m.scene(20, 14,
            "The bone heaps shift. Something stands up out of them: ten thousand bones, one body.",
            "BRANN: THE WOUND BUILT ITSELF A CHAMPION OUT OF HOLLOWMERE'S GRANDMOTHERS.")
    m.add("AFTERBOSS The Colossus comes apart in an avalanche of bone.")
    m.scene(20, 20,
            "Carved into the seam wall above the Oath-stone is the seven-pointed sigil, the same one on Brann's scalp.",
            "BRANN: I THOUGHT I CUT THIS INTO MY SKIN TO LEARN THE WOUND'S WAYS. I WAS WRONG.",
            "BRANN: IT'S A CONTRACT MARK. A SIGNATURE. AND THAT RIBBON ON YOUR HELM, ALDRIC, IS THE SAME MARK IN SILK.",
            "ALDRIC: ...THE KEEP. WHATEVER THIS IS, THE ABBOT KNEW. IT ENDS AT THE KEEP.")
    return m, header


# =================================================================== Chapter VIII
def wardens_keep():
    m = Map(25, 25, "#")
    m.rect(5, 19, 19, 23)                      # the approach
    m.path([(12, 23), (12, 18)], ",")
    for (x, y) in [(7, 21), (17, 20), (9, 23), (15, 22)]:
        m.put(x, y, "r")
    m.frame(3, 3, 21, 18, "P")
    m.rect(4, 12, 20, 17)                      # the courtyard
    m.put(12, 18, ",")
    m.put(4, 18, "."); m.put(20, 14, ".")      # breaches
    m.rect(4, 4, 20, 11, "k")
    m.rect(5, 6, 19, 10, ";")                  # the oath hall
    m.put(8, 8, "k"); m.put(16, 8, "k")        # pillars
    m.put(12, 11, "D")
    m.rect(9, 1, 15, 4, "k")
    m.rect(10, 1, 14, 4, ";")                  # chapter house
    m.put(12, 5, "L")
    m.put(12, 0, "Q")
    header = ["# Graveborne Chapter VIII: The Wardens' Keep", "CHAPTER VIII The Wardens' Keep",
              "NAME The Wardens' Keep", "THEME forest", "TOUGH 3",
              "WALL # tree tree2 tree3", "WALL r cliff", "WALL P prison prisonwin", "WALL k keep wall keep", "WALL Q pdoor",
              "FLOOR , path", "FLOOR ; floor roof", "SHRINE H shrine"]
    m.put(11, 18, "H")
    m.add("START 12 22 N",
          "EXIT 12 0 level9.txt 10 25 N boss+stone+letter",
          "MON 8 14 skeleton", "MON 16 15 skeleton", "MON 19 13 hound", "MON 5 16 ghoul",
          "MON 6 7 skeleton", "MON 18 7 skeleton", "MON 10 9 wraith", "MON 14 9 wraith",
          "BOSS 12 2 abbot",
          "ITEM 5 10 key", "ITEM 13 1 letter", "ITEM 11 1 stone",
          "ITEM 4 13 potion", "ITEM 19 6 potion", "ITEM 20 17 potion",
          "PROP 6 12 grave", "PROP 18 16 grave", "PROP 9 16 grave")
    m.scene(12, 22,
            "The Wardens' Keep, where the four swore their oaths two hundred years ago. Its banners hang in rags.",
            "ALDRIC: I KNELT IN THAT HALL. I SWORE ON A STONE BLACKER THAN THIS NIGHT.")
    m.scene(12, 16,
            "SERA: SOMEONE STRUCK THROUGH THE ORDER'S SIGIL ON EVERY BANNER.",
            "BRANN: SOMEONE WHO KNEW WHAT IT REALLY MEANT.")
    m.scene(12, 10, "VESH: THE CHAPTER HOUSE IS LOCKED. THE ABBOT'S STEWARD SLEPT IN THE WEST END OF THE HALL. HE KEPT THE KEY.")
    m.scene(12, 4,
            "THE LAST ABBOT: NO. NO, NOT YOU. YOU WERE NEVER MEANT TO COME HERE.",
            "ALDRIC: YOU HID OUR STONES, ABBOT. WHY?",
            "THE LAST ABBOT: BECAUSE WITHOUT YOU THIS TOWN DIES. I CHOSE HOLLOWMERE. I WOULD CHOOSE IT AGAIN.")
    m.add("AFTERBOSS The Last Abbot crumbles. His journal lies open on the lectern, beside the last Oath-stone.")
    m.scene(13, 1,
            "The abbot's journal:",
            "\"ALDRIC CAME BACK FROM THE BARROWS ALONE, WITH THE WOUND'S RIBBON ON HIS HELM. BEFORE HE DIED HE TOLD ME WHAT HE HAD DONE.\"",
            "\"HE STRUCK A BARGAIN WITH THE WOUND. LET THE FOUR RISE WHENEVER IT WAKES, AND THEY WILL FIGHT IT FOREVER. EACH TIME THEY SEAL IT, THEIR DEATHS FEED IT AGAIN.\"",
            "\"THE CURSE IS ETERNAL BECAUSE THEY ARE PART OF IT. BREAK THE OATHS AND THE PACT BREAKS. BUT THEN THE TOWN HAS NO CHAMPIONS. SO I HID THE STONES.\"")
    m.scene(11, 1,
            "Aldric lifts his Oath-stone, and the last memory comes back.",
            "ALDRIC: I REMEMBER. THE DARK. IT SPOKE TO ME IN MY OWN VOICE. WE WERE ALL GOING TO DIE.",
            "ALDRIC: SO I GAVE IT US. FOREVER. I THOUGHT IT WAS A VICTORY.",
            "BRANN: TWO HUNDRED YEARS OF DYING. YOU SIGNED US UP FOR IT.",
            "SERA: HE SAVED THE TOWN. AND HE DAMNED US. BOTH.",
            "VESH: THE WOUND WILL HAVE FELT THE STONES MOVE. IT KNOWS WE CAN END IT NOW.",
            "ALDRIC: THEN IT WILL GO FOR HOLLOWMERE. RUN.")
    return m, header


# =================================================================== Chapter X
def barrows():
    m = Map(24, 26, "#")
    m.rect(9, 20, 15, 24)                      # the barrow mouth
    m.path([(12, 19), (12, 16)])
    m.rect(4, 12, 20, 15)                      # hall of the first kings
    m.put(12, 11, "X")                         # sealed gate
    m.rect(9, 7, 15, 10)                       # antechamber
    m.put(12, 6, "X")                          # the last gate
    m.rect(7, 1, 17, 5)                        # Hrodmar's throne
    m.put(12, 0, "S")
    m.path([(4, 11), (4, 9), (2, 9), (2, 5)])   # Vesh's ledges
    m.rect(2, 2, 5, 4)
    m.path([(20, 11), (20, 5)])                # Brann's seam
    m.rect(19, 2, 22, 4)
    header = ["# Graveborne Chapter X: The Barrows of the First Kings", "CHAPTER X The Barrows of the First Kings",
              "NAME The Barrows of the First Kings", "THEME dungeon", "TOUGH 4", "STAIRS stairs",
              "WALL # barrow", "WALL X barrow", "FLOOR . barrowfloor"]
    m.put(11, 24, "H")
    m.put(10, 20, "#")
    m.add("START 12 23 N",
          "EXIT 12 0 level11.txt 7 14 N boss",
          "LEVER 1 3 E open 12 11",
          "LEVER 23 3 W open 12 6",
          "MON 6 13 skeleton", "MON 18 14 skeleton", "MON 9 14 skeleton", "MON 15 13 skeleton",
          "MON 2 6 wraith", "MON 4 3 skeleton", "MON 20 7 ghoul", "MON 21 3 skeleton",
          "MON 10 8 skeleton", "MON 14 8 skeleton",
          "BOSS 12 2 hrodmar",
          "ITEM 2 2 potion", "ITEM 22 2 potion", "ITEM 15 23 potion", "ITEM 9 7 potion",
          "PROP 6 12 coffin", "PROP 10 12 coffin", "PROP 14 12 coffin", "PROP 18 12 coffin",
          "PROP 8 1 coffin", "PROP 16 1 coffin",
          "DECO 12 0 S sigil")
    m.scene(12, 23,
            "The barrow gate grinds shut behind you. You have been here before. Every time.",
            "SERA: THIS IS THE MOUTH. I STOOD RIGHT HERE, SHIELD UP, SPEAR OUT. I REMEMBER THE WEIGHT OF THEM.",
            "ALDRIC: THERE'S A SHRINE IN THE WALL. THE ORDER BUILT IT FOR OUR LAST NIGHT. PRAY.")
    m.scene(12, 15,
            "The first kings of Hollowmere lie in their stone beds. Their honour guard does not.",
            "BRANN: THE WAY ON IS SEALED. SAME AS LAST TIME. VESH FOUND ONE WAY THROUGH, I BROKE THE OTHER.")
    m.scene(3, 3, "VESH: MY LEDGES. I FOUND THE WINCH UP HERE THE FIRST TIME, AND CAME BACK TO GUIDE YOU.")
    m.scene(20, 3, "BRANN: AND HERE'S THE SEAM I BROKE TO LET US THROUGH. SAME CRACK. SAME ROCK. TWO HUNDRED YEARS.")
    m.scene(12, 7, "ALDRIC: BEYOND THAT GATE IS WHERE I WENT ON ALONE. INTO THE DARK. AND CAME BACK SOMETHING ELSE.")
    m.scene(12, 5,
            "KING HRODMAR: THE WARDENS. MY JAILERS. EVERY TIME YOU SEAL IT, I SLEEP. EVERY TIME IT WAKES, SO DO I.",
            "KING HRODMAR: I WAS THE FIRST IT RAISED. I WILL BE THE LAST STANDING.")
    m.add("AFTERBOSS King Hrodmar falls, and his honour guard fall with him. Behind the throne, steps lead down into violet light.")
    return m, header


# =================================================================== Chapter XI
def wound():
    m = Map(15, 16, "#")
    m.path([(7, 14), (7, 10)])
    m.rect(2, 2, 12, 9)
    for (x, y) in [(3, 3), (11, 3), (3, 8), (11, 8)]:
        m.put(x, y, "#")
    m.put(8, 12, "H")
    m.put(7, 1, "W")
    header = ["# Graveborne Chapter XI: The Wound", "CHAPTER XI The Wound",
              "NAME The Wound", "THEME dungeon", "TOUGH 4",
              "WALL # wound", "WALL W wound", "FLOOR . woundfloor"]
    m.add("START 7 14 N",
          "CHOICE 7 1",
          "BOSS 7 3 heart",
          "MON 4 6 wraith", "MON 10 6 wraith",
          "ITEM 7 13 potion", "ITEM 7 11 potion")
    m.scene(7, 14,
            "Violet light beats in the rock like a pulse. The walls are warm to the touch.",
            "VESH: IT KNOWS WE'RE COMING.",
            "SERA: GOOD.")
    m.scene(7, 9,
            "THE HEART OF THE WOUND: ALDRIC.",
            "The voice is Aldric's own.",
            "THE HEART OF THE WOUND: YOU KNOW THIS VOICE. YOU GAVE IT TO ME, DOWN HERE, WHEN YOU WERE AFRAID.",
            "THE HEART OF THE WOUND: SEAL ME. SLEEP. RISE AGAIN. HOLLOWMERE LIVES, AND YOU NEVER TRULY DIE. IS THAT NOT WHAT YOU WANTED?",
            "BRANN: DON'T LISTEN TO IT.",
            "ALDRIC: I'M NOT. NOT THIS TIME.")
    m.add("AFTERBOSS The Heart tears and falls still. Behind it the Wound still gapes in the rock, waiting for the old words."
          "|ALDRIC: THE WOUND. ALL FOUR STONES. WE CHOOSE NOW.")
    return m, header


CHAPTERS = {
    "level3.txt": lambda: hollowmere(False),
    "level4.txt": undercroft,
    "level5.txt": hanged_watch,
    "level6.txt": drowned_barrow,
    "level7.txt": ossuary_mines,
    "level8.txt": wardens_keep,
    "level9.txt": lambda: hollowmere(True),
    "level10.txt": barrows,
    "level11.txt": wound,
}


# ------------------------------------------------------------------ validation
def validate(name, m, header):
    walk = set(".O")
    blocked = set()
    floor_of = {}
    for l in header:
        p = l.split()
        if p[0] == "FLOOR":
            floor_of[p[1]] = p[2]
            if "block" in p[3:]:
                blocked.add(p[1])
            else:
                walk.add(p[1])
    g = m.g
    W, H = m.w, m.h
    # cells that open in play: doors, locked doors, lever targets, drained water
    opens = set()
    for l in m.lines:
        p = l.split()
        if p[0] == "LEVER":
            if p[4] == "open":
                opens.add((int(p[5]), int(p[6])))
            else:
                x0, y0, x1, y1 = map(int, p[5:9])
                for y in range(y0, y1 + 1):
                    for x in range(x0, x1 + 1):
                        if g[y][x] in blocked:
                            opens.add((x, y))
    def ok(x, y):
        return 0 <= x < W and 0 <= y < H and (g[y][x] in walk or g[y][x] in "DL" or (x, y) in opens)
    props = set()
    for l in m.lines:
        p = l.split()
        if p[0] in ("PROP", "NPC"):
            props.add((int(p[1]), int(p[2])))
    start = next(tuple(map(int, l.split()[1:3])) for l in m.lines if l.startswith("START"))
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and ok(*n) and n not in props:
                seen.add(n); q.append(n)
    bad = []
    adj = lambda x, y: any((x + dx, y + dy) in seen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for l in m.lines:
        p = l.split()
        if p[0] in ("MON", "BOSS", "ITEM", "PROP", "NPC", "SCENE", "START", "WAVES"):
            x, y = int(p[1]), int(p[2])
            if not ok(x, y):
                bad.append(("not on floor", l[:50]))
            elif p[0] not in ("PROP", "NPC") and (x, y) not in seen:
                bad.append(("unreachable", l[:50]))
            if p[0] in ("PROP", "NPC") and not adj(x, y):
                bad.append(("boxed in", l[:50]))
        if p[0] in ("EXIT", "NOTE", "LEVER", "CHOICE"):
            x, y = int(p[1]), int(p[2])
            if ok(x, y) and p[0] != "LEVER":
                bad.append(("should be a wall", l[:50]))
            if p[0] == "LEVER":
                d = "NESW".index(p[3]); fx, fy = x + (0, 1, 0, -1)[d], y + (-1, 0, 1, 0)[d]
                if (fx, fy) not in seen:
                    bad.append(("lever face unreachable", l[:50]))
            elif not adj(x, y):
                bad.append(("can't reach", l[:50]))
    for y in range(H):
        for x in range(W):
            if g[y][x] in "HICS" and not adj(x, y) and g[y][x] in ("H", "I"):
                bad.append(("shrine unreachable", (x, y)))
    for b in bad:
        print(name, "PROBLEM", b)
    return not bad


if __name__ == "__main__":
    out = sys.argv[1]
    allok = True
    for name, fn in CHAPTERS.items():
        m, header = fn()
        allok &= validate(name, m, header)
        open(os.path.join(out, name), "w").write(m.text(header))
        if len(sys.argv) > 2:
            import numpy as np
            from PIL import Image
            col = {"#": (40, 34, 50), ".": (150, 140, 150), ",": (150, 120, 80), ";": (130, 125, 120), "~": (30, 80, 100),
                   "w": (30, 80, 100), "D": (150, 90, 40), "L": (220, 160, 60), "S": (80, 200, 180), "H": (140, 80, 200),
                   "X": (200, 60, 60), "Q": (40, 30, 50), "P": (110, 104, 120), "r": (90, 84, 96), "h": (150, 110, 80),
                   "F": (120, 70, 30), "G": (200, 120, 40), "C": (200, 200, 230), "I": (240, 180, 60), "b": (80, 76, 66),
                   "k": (100, 90, 110), "W": (170, 60, 200)}
            img = np.array([[col.get(c, (255, 0, 255)) for c in r] for r in m.g], np.uint8)
            for l in m.lines:
                p = l.split()
                if p[0] in ("MON",):
                    img[int(p[2]), int(p[1])] = (220, 40, 40)
                if p[0] == "BOSS":
                    img[int(p[2]), int(p[1])] = (255, 0, 160)
                if p[0] == "SCENE":
                    img[int(p[2]), int(p[1])] = (255, 230, 80)
                if p[0] == "ITEM":
                    img[int(p[2]), int(p[1])] = (60, 220, 220)
            Image.fromarray(img).resize((m.w * 10, m.h * 10), Image.NEAREST).save(os.path.join(sys.argv[2], name + ".png"))
    print("all chapters valid" if allok else "PROBLEMS FOUND")
