package com.harlequin.graveborne;

import java.util.HashMap;

/** Sprite atlas baked by tools/art/build_all.py. */
public final class Atlas {
    /** Platform image/text loading (Android assets or desktop files). */
    public interface Loader {
        /** Returns ARGB pixels; size[0]=w, size[1]=h. */
        int[] image(String name, int[] size);
        String text(String name);
    }

    public static final class Sheet {
        public final int[] px; public final int w, h;
        Sheet(int[] px, int w, int h) { this.px = px; this.w = w; this.h = h; }
    }

    public static final class Sprite {
        public final Sheet sheet; public final int x, y, w, h, ox, oy;
        Sprite(Sheet s, int x, int y, int w, int h, int ox, int oy) {
            this.sheet = s; this.x = x; this.y = y; this.w = w; this.h = h; this.ox = ox; this.oy = oy;
        }
    }

    private final HashMap<String, Sprite> map = new HashMap<>(4096);

    public Atlas(Loader ld) {
        String idx = ld.text("atlas.txt");
        HashMap<Integer, Sheet> sheets = new HashMap<>();
        for (String line : idx.split("\n")) {
            line = line.trim();
            if (line.isEmpty()) continue;
            String[] p = line.split(" ");
            int si = Integer.parseInt(p[1]);
            Sheet sh = sheets.get(si);
            if (sh == null) {
                int[] sz = new int[2];
                int[] px = ld.image("atlas" + si + ".png", sz);
                sh = new Sheet(px, sz[0], sz[1]);
                sheets.put(si, sh);
            }
            map.put(p[0], new Sprite(sh, Integer.parseInt(p[2]), Integer.parseInt(p[3]), Integer.parseInt(p[4]),
                    Integer.parseInt(p[5]), Integer.parseInt(p[6]), Integer.parseInt(p[7])));
        }
    }

    public Sprite get(String name) { return map.get(name); }

    public int size() { return map.size(); }
}
