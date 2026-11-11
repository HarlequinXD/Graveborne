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
                case "SHRINE": lv.shrineKind = p[1]; break;
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
        return lv;
    }

    private final ArrayList<String[]> pendingDeco = new ArrayList<>();

    public char at(int x, int y) {
        if (x < 0 || y < 0 || x >= w || y >= h) return WALL;
        return cell[y][x];
    }

    public boolean passable(int x, int y) {
        char c = at(x, y);
        if (c != FLOOR && c != OPEN) return false;
        for (Item it : items) if (it.prop && it.x == x && it.y == y) return false;
        return true;
    }

    /** Is the grid cell open ground (props stand on open ground but block walking)? */
    public boolean open(int x, int y) {
        char c = at(x, y);
        return c == FLOOR || c == OPEN;
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
            case SHRINE: return faceOnAxis(x, y, dir) ? shrineKind : plain;
            default: return plain;
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
