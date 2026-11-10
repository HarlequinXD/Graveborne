# Graveborne

A portrait-mode, step-by-step first-person dungeon crawler for Android, in the spirit of
80s/90s crawlers. Four warriors are resurrected by an eternal curse and must fight their
way out of the Oubliette.

## How it looks
* The 128x128 view is composed from **pre-rendered sprites**, not a 3D engine. Every wall,
  door, decoration, monster and item piece is baked by `tools/art` from one set of
  hand-tuned textures, one torchlight model and one palette, so every screen matches.
* Each piece is then **painted over as pixel art**: about 110 colours on nine hue-shifted
  material ramps, flat colour clusters, ink outlines and light retro dithering.
* Pieces exist at every quarter-cell offset, so stepping animates through 4 frames,
  strafing through 2, and turning pans between the two facings.

## Controls
* Pad: turn left / forward / turn right, strafe left / back / strafe right (hold to keep walking).
* Tap the view (or the hand button) to use what is in front: press bricks, open doors, pray at shrines.
* Tap a warrior's weapon to strike. Aldric and Brann fight from the front row, Sera's spear
  reaches from behind, Vesh's crossbow shoots down the corridor.
* Left column: map, grave blood (healing), keys.

## The start
You wake in a cell facing the barred door. Behind you one brick is loose; the stone bed
slab is in the right-hand wall. Press the brick and the bed sinks away into a secret passage.

## Building
* APK: GitHub Actions (`.github/workflows/android.yml`) builds `Graveborne-debug`.
* Art: `python3 tools/art/build_all.py app/src/main/assets` (numpy + Pillow), about 1 minute.
* Floor 1: `python3 tools/level1.py app/src/main/assets/level1.txt`.
* Desktop screenshots: compile the core plus `tools/desktop/Harness.java` with `javac` and run a script
  (see the header of Harness.java).
