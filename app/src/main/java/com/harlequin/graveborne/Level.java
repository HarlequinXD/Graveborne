package com.harlequin.graveborne;

import java.util.ArrayList;
import java.util.HashMap;

/** A dungeon floor: a grid of cells plus per-face decorations, monsters and items. */
public final class Level {
    public static final int N = 0, E = 1, S = 2, W = 3;
    public static final int[] DX = {0, 1, 0, -1};
    public static final int[] DY = {-1, 0, 1, 0};
    public static final String DIRS = "NESW";

    // cell types
    public static final char WALL = '#', FLOOR = '.', DOOR = 'D', LOCKED = 'L', BARS = 'B',
            SECRET = 'X', STAIRS = 'S', SHRINE = 'H', OPEN = 'O';

    public String name = "";
    public String theme = "dungeon";
    /** Start inside the sarcophagus behind the start cell (floor 1 only). */
    public boolean intro;
    public String stairsKind = "stairs", shrineKind = "shrine", next = null;
    public final HashMap<Character, String[]> wallKinds = new HashMap<>();
    /** Ground cells beyond '.': char -> floor texture (dirt road, cobbles, water...). */
    public final HashMap<Character, String> floorKinds = new HashMap<>();
    /** Ground you can see but not walk on (water). */
    public final java.util.HashSet<Character> blocked = new java.util.HashSet<>();
    /** Shrine-like cells (rest and revive): char -> face texture. */
    public final HashMap<Character, String> shrineKinds = new HashMap<>();
    /** Cells that lead to another map: key y*w+x -> {file, tx, ty, dir}. */
    public final HashMap<Integer, String[]> exits = new HashMap<>();
    /** Text shown when you examine a cell: key y*w+x. */
    public final HashMap<Integer, String> notes = new HashMap<>();
    /** Named regions: name, music, step sound. */
    public final ArrayList<Area> areas = new ArrayList<>();

    public static final class Area {
        public int x0, y0, x1, y1;
        public String name, music, step;
    }
    public int w, h;
    public char[][] cell;
    /** door opening progress 0..1 per cell (only used while opening). */
    public float[][] doorAnim;
    /** decorations: key = (y*w+x)*4+dir. */
    public final HashMap<Integer, String> deco = new HashMap<>();
    public int startX, startY, startDir;
    public final ArrayList<Monster> monsters = new ArrayList<>();
    public final ArrayList<Item> items = new ArrayList<>();
    public boolean[][] seen;

    public static Level parse(String src) {
        Level lv = new Level();
        ArrayList<String> rows = new ArrayList<>();
        boolean inMap = false;
        for (String raw : src.split("\n")) {
            String line = raw.replace("\r", "");
            if (inMap) {
                if (line.trim().equals("END")) { inMap = false; continue; }
                rows.add(line);
                continue;
            }
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] p = line.split("\\s+");
            switch (p[0]) {
                case "NAME": lv.name = line.substring(5).trim(); break;
                case "MAP": inMap = true; break;
                case "THEME": lv.theme = p[1]; break;
                case "INTRO": lv.intro = true; break;
                case "STAIRS": lv.stairsKind = p[1]; break;
                case "SHRINE":
                    if (p.length >= 3) lv.shrineKinds.put(p[1].charAt(0), p[2]);
                    else { lv.shrineKind = p[1]; lv.shrineKinds.put(SHRINE, p[1]); }
                    break;
                case "FLOOR":
                    lv.floorKinds.put(p[1].charAt(0), p[2]);
                    if (p.length >= 4 && p[3].equals("block")) lv.blocked.add(p[1].charAt(0));
                    break;
                case "EXIT": lv.pendingExit.add(p); break;
                case "NOTE": lv.pendingNote.add(new String[]{p[1], p[2], line.split("\\s+", 4)[3]}); break;
                case "AREA": {
                    Area a = new Area();
                    a.x0 = Integer.parseInt(p[1]); a.y0 = Integer.parseInt(p[2]);
                    a.x1 = Integer.parseInt(p[3]); a.y1 = Integer.parseInt(p[4]);
                    a.music = p[5]; a.step = p[6];
                    a.name = line.split("\\s+", 8)[7];
                    lv.areas.add(a);
                    break;
                }
                case "NEXT": lv.next = p[1]; break;
                case "WALL": {
                    String[] k = new String[p.length - 2];
                    System.arraycopy(p, 2, k, 0, k.length);
                    lv.wallKinds.put(p[1].charAt(0), k);
                    break;
                }
                case "PROP": {
                    Item it = new Item(p[3], Integer.parseInt(p[1]), Integer.parseInt(p[2]));
                    it.prop = true;
                    lv.items.add(it);
                    break;
                }
                case "NPC": {
                    Monster m = new Monster(p[3], Integer.parseInt(p[1]), Integer.parseInt(p[2]));
                    m.lines = line.split("\\s+", 5)[4].split("\\|");
                    lv.monsters.add(m);
                    break;
                }
                case "START":
                    lv.startX = Integer.parseInt(p[1]); lv.startY = Integer.parseInt(p[2]);
                    lv.startDir = DIRS.indexOf(p[3].charAt(0));
                    break;
                case "DECO":
                    lv.pendingDeco.add(p);
                    break;
                case "MON":
                    lv.monsters.add(new Monster(p[3], Integer.parseInt(p[1]), Integer.parseInt(p[2])));
                    break;
                case "ITEM":
                    lv.items.add(new Item(p[3], Integer.parseInt(p[1]), Integer.parseInt(p[2])));
                    break;
                default: break;
            }
        }
        lv.h = rows.size();
        lv.w = rows.get(0).length();
        lv.cell = new char[lv.h][lv.w];
        lv.doorAnim = new float[lv.h][lv.w];
        lv.seen = new boolean[lv.h][lv.w];
        for (int y = 0; y < lv.h; y++)
            for (int x = 0; x < lv.w; x++)
                lv.cell[y][x] = x < rows.get(y).length() ? rows.get(y).charAt(x) : WALL;
        for (String[] p : lv.pendingDeco)
            lv.setDeco(Integer.parseInt(p[1]), Integer.parseInt(p[2]), DIRS.indexOf(p[3].charAt(0)), p[4]);
        lv.pendingDeco.clear();
        for (String[] p : lv.pendingExit)
            lv.exits.put(Integer.parseInt(p[2]) * lv.w + Integer.parseInt(p[1]), new String[]{p[3], p[4], p[5], p[6]});
        for (String[] p : lv.pendingNote)
            lv.notes.put(Integer.parseInt(p[1]) * lv.w + Integer.parseInt(p[0]), p[2]);
        if (lv.shrineKinds.isEmpty()) lv.shrineKinds.put(SHRINE, lv.shrineKind);
        return lv;
    }

    private final ArrayList<String[]> pendingDeco = new ArrayList<>();
    private final ArrayList<String[]> pendingExit = new ArrayList<>();
    private final ArrayList<String[]> pendingNote = new ArrayList<>();

    public String[] exitAt(int x, int y) {
        if (x < 0 || y < 0 || x >= w || y >= h) return null;
        return exits.get(y * w + x);
    }

    public String noteAt(int x, int y) {
        if (x < 0 || y < 0 || x >= w || y >= h) return null;
        return notes.get(y * w + x);
    }

    public Area areaAt(int x, int y) {
        for (Area a : areas) if (x >= a.x0 && x <= a.x1 && y >= a.y0 && y <= a.y1) return a;
        return null;
    }

    public boolean isShrine(int x, int y) { return shrineKinds.containsKey(at(x, y)); }

    /** Floor texture for a cell, or null for the theme's default ground. */
    public String floorKind(int x, int y) { return floorKinds.get(at(x, y)); }

    public char at(int x, int y) {
        if (x < 0 || y < 0 || x >= w || y >= h) return WALL;
        return cell[y][x];
    }

    public boolean passable(int x, int y) {
        char c = at(x, y);
        if (!open(x, y) || blocked.contains(c)) return false;
        for (Item it : items) if (it.prop && it.x == x && it.y == y) return false;
        return true;
    }

    /** Is the grid cell open ground (props stand on open ground but block walking)? */
    public boolean open(int x, int y) {
        char c = at(x, y);
        return c == FLOOR || c == OPEN || floorKinds.containsKey(c);
    }

    /** Solid blocks are drawn as cubes (walls, closed doors, bars...). */
    public boolean solid(int x, int y) {
        return !open(x, y);
    }

    public String deco(int x, int y, int dir) { return deco.get((y * w + x) * 4 + dir); }

    public void setDeco(int x, int y, int dir, String k) {
        int key = (y * w + x) * 4 + dir;
        if (k == null) deco.remove(key); else deco.put(key, k);
    }

    /** Doors, bars and stairs show their face only along the axis where they have open neighbours. */
    public boolean faceOnAxis(int x, int y, int dir) {
        int nx = x + DX[dir], ny = y + DY[dir];
        return open(nx, ny);
    }

    public boolean outdoor() { return !theme.equals("dungeon"); }

    /** Plain wall kind for a cell character, varied per face so forests and streets don't repeat. */
    public String wallKind(char c, int x, int y, int dir) {
        String[] k = wallKinds.get(c);
        if (k == null) k = wallKinds.get('#');
        if (k == null || k.length == 0) return "wall";
        int hsh = (x * 73856093) ^ (y * 19349663) ^ (dir * 83492791);
        hsh ^= hsh >>> 13;
        return k[Math.floorMod(hsh, k.length)];
    }

    /** Texture kind for one face of a solid cell, or null if nothing to draw. */
    public String faceKind(int x, int y, int dir) {
        char c = at(x, y);
        String d = deco(x, y, dir);
        String plain = d != null ? d : wallKind(c, x, y, dir);
        switch (c) {
            case DOOR: {
                if (!faceOnAxis(x, y, dir)) return plain;
                float a = doorAnim[y][x];
                if (a <= 0) return "door";
                int st = Math.min(3, 1 + (int) (a * 3));
                return "door" + st;
            }
            case LOCKED: return faceOnAxis(x, y, dir) ? "locked" : plain;
            case BARS: return faceOnAxis(x, y, dir) ? "bars" : plain;
            case STAIRS: return faceOnAxis(x, y, dir) ? stairsKind : plain;
            default:
                if (shrineKinds.containsKey(c)) return faceOnAxis(x, y, dir) ? shrineKinds.get(c) : plain;
                return plain;
        }
    }

    public Item propAt(int x, int y) {
        for (Item it : items) if (it.prop && it.x == x && it.y == y) return it;
        return null;
    }

    public Monster monsterAt(int x, int y) {
        for (Monster m : monsters) if (m.alive() && m.x == x && m.y == y) return m;
        return null;
    }

    public Item itemAt(int x, int y) {
        for (Item it : items) if (!it.prop && it.x == x && it.y == y) return it;
        return null;
    }
}
