# Graveborne

A portrait-mode, step-by-step first-person dungeon crawler for Android, in the spirit of
80s/90s crawlers. Four warriors are resurrected by an eternal curse and must fight their
way out of the Oubliette.

## How it looks
* The 128x128 view is real-time 3D built from tiles, drawn like Game Boy Advance 3D
  (Driv3r, Asterix & Obelix XXL) and the PS1 (`Renderer3D.java`): textured triangles with
  perspective-correct texture mapping, vertices snapped to whole pixels (geometry wobbles
  as you move), per-vertex torch light, 4x4 ordered dithering on
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
You wake inside a sarcophagus, the stone lid inches from your face. Tap to heave it
aside and climb out into the tomb chamber, facing a chained iron crypt gate. A lever is
hidden behind the skull carved into the plaque above your sarcophagus: haul it down and a
wall of burial niches sinks into the floor, off to your left, opening a secret passage.

## The world
The opening is linear, then the game opens up.
1. **The Crypt** (linear): climb out of your sarcophagus, find the hidden lever, escape through the burial halls and climb the stairs into moonlight.
2. **The Ashen Wood trail** (linear): the walled graveyard by the crypt's mausoleum, then a winding forest trail to Hollowmere's north gate.
3. **Hollowmere and the vale** (open world, `tools/vale.py`, 80 x 64 cells): the town is the hub. It has a ring lane, side streets, alleys, courtyards, a market yard, the chapel and the Lantern inn on the central square, and four guarded gates. Each gate opens onto the wilds, and the wilds loop around the town, so every region can be reached from every gate:
   - **North**: the North Road back to the graveyard trail, and the High Moor with the Hanged Watch.
   - **East**: the Mine Road to the Mine Cliffs; the Pyre Fields to the south-east.
   - **West**: the deep Ashen Wood, with Gibbet Hill, the Wayside Shrine and Hunter's Hollow.
   - **South**: the River Hollow and its three bridges, the Black Mire with the Drowned Barrow, and the ruined Wardens' Keep.

   The Watch, the mine, the Barrow and the Keep are sealed for now; they are the later chapters' dungeons. Region names show as you enter them, and the map zooms out in the open world.

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
