# Graveborne

A portrait-mode, step-by-step first-person dungeon crawler for Android, in the spirit of
80s/90s crawlers. Four warriors are resurrected by an eternal curse and must fight their
way out of the Oubliette.

## How it looks
* The 128x128 view is real-time 3D built from tiles, drawn like Game Boy Advance 3D
  (Driv3r, Asterix & Obelix XXL) and the PS1 (`Renderer3D.java`): textured triangles with
  affine texture mapping (textures bend on near walls and floors), vertices snapped to whole
  pixels (geometry wobbles as you move), per-vertex torch light, 4x4 ordered dithering on
  the light ramps and a dithered 15-bit colour pass.
* Doors, the bed slab, cell bars, chains, sconces, sigils, shrines, stairs, trees and
  house fronts are painted onto the wall textures (`tools/art`), full-colour pixel art on
  nine material ramps. Bars, archways, rising doors, tree canopies and rooftops are see-through.
* Torchlight slides each pixel down its own colour ramp with a light 2x2 dither, so the
  3D view keeps the painted look. Monsters, items and props are lit sprites.
* Movement stays on the grid (step, strafe, 90 degree turns, no free-look); the camera
  glides between cells and turns smoothly.

## Controls
* Pad: turn left / forward / turn right, strafe left / back / strafe right (hold to keep walking).
* Tap the view (or the hand button) to use what is in front: press bricks, open doors, pray at shrines.
* Tap a warrior's weapon to strike. Aldric and Brann fight from the front row, Sera's spear
  reaches from behind, Vesh's crossbow shoots down the corridor.
* Left column: map, grave blood (healing), keys.

## The start
You wake in a cell facing the barred door. Behind you one brick is loose; the stone bed
slab is in the right-hand wall. Press the brick and the bed sinks away into a secret passage.

## The journey so far
1. **The Oubliette**: escape the cell through the secret passage, find the key, climb the stairs into moonlight.
2. **The Ashen Wood**: the prison grounds, then winding forest paths, a grave clearing and a wayside shrine.
3. **Hollowmere**: a lantern-lit town. Talk to the guard, the innkeeper and the priest, and rest at the inn.

## Sound
Everything is synthesised by `tools/audio`: scores for the title, dungeon, forest and town
(seamless loops), a death lament, and about 50 effects (footsteps per ground, doors, the
grinding wall, weapons, each monster's cries, pickups, shrines). Regenerate with
`python3 tools/audio/compose.py app/src/main/assets/music` and
`python3 tools/audio/sfx.py app/src/main/assets/sfx` (needs ffmpeg with libvorbis).

## Building
* APK: GitHub Actions (`.github/workflows/android.yml`) builds `Graveborne-debug`.
* Art: `python3 tools/art/bake_tex.py app/src/main/assets` (numpy + Pillow), a few seconds.
* Floor 1: `python3 tools/level1.py app/src/main/assets/level1.txt`; floors 2-3: `python3 tools/levels_out.py app/src/main/assets`.
* Desktop screenshots: compile the core plus `tools/desktop/Harness.java` with `javac` and run a script
  (see the header of Harness.java).
