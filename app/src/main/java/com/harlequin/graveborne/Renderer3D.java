package com.harlequin.graveborne;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;

/**
 * Real-time 3D tile renderer for the 128x128 view. Every grid cell is a textured block
 * (walls, doors and their details are painted on the faces); floors, ceilings and the
 * night sky are textured too. Lighting works like the painted art: each pixel's colour
 * slides along its material ramp with the torch's falloff, with a light 2x2 dither.
 */
public final class Renderer3D {
    public static final int V = 128;
    private static final float FOCAL = 64f;        // 90 degree field of view
    private static final float EYE = 0.5f;
    public final Gfx out = new Gfx(V, V);

    // palette and ramps
    private int[] pal;
    private int[] rampOf, posOf, rampLen;
    private int[][] rampTab;
    private final HashMap<Integer, Integer> colToIdx = new HashMap<>();

    // textures: 128x128 palette indices (-1 = see-through) and glow 0..255
    private final HashMap<String, Integer> texId = new HashMap<>();
    private short[][] tex;
    private byte[][] glow;
    private boolean[] texAlpha;
    private static final int T = 128;

    private static final class Spr {
        short[] idx; byte[] glow; int w, h; float ww, wh, lift;
    }
    private final HashMap<String, Spr> sprites = new HashMap<>();
    private int[] sky;   // two 512x64 panoramas (forest, town), direct colours

    // per-pixel frame buffers
    private final short[] pIdx = new short[V * V];
    private final float[] pSteps = new float[V * V];
    private final float[] pGlow = new float[V * V];
    private final int[] pDirect = new int[V * V];
    private final float[] depth = new float[V * V];

    public Renderer3D(Atlas.Loader ld) {
        loadPalette(ld.text("pal3d.txt"));
        loadTextures(ld);
        loadSprites(ld);
        int[] sz = new int[2];
        sky = ld.image("sky3d.png", sz);
    }

    private void loadPalette(String src) {
        String[] lines = src.split("\n");
        int li = 0;
        int nr = Integer.parseInt(lines[li++].trim().split(" ")[1]);
        rampTab = new int[nr][];
        rampLen = new int[nr];
        for (int r = 0; r < nr; r++) {
            String[] p = lines[li++].trim().split(" ");
            rampTab[r] = new int[p.length];
            for (int k = 0; k < p.length; k++) rampTab[r][k] = Integer.parseInt(p[k]);
            rampLen[r] = p.length;
        }
        int nc = Integer.parseInt(lines[li++].trim().split(" ")[1]);
        pal = new int[nc]; rampOf = new int[nc]; posOf = new int[nc];
        for (int i = 0; i < nc; i++) {
            String[] p = lines[li++].trim().split(" ");
            pal[i] = 0xff000000 | Integer.parseInt(p[0], 16);
            rampOf[i] = Integer.parseInt(p[1]);
            posOf[i] = Integer.parseInt(p[2]);
            if (!colToIdx.containsKey(pal[i] & 0xffffff)) colToIdx.put(pal[i] & 0xffffff, i);
        }
    }

    private short toIdx(int argb) {
        if ((argb >>> 24) < 128) return -1;
        Integer i = colToIdx.get(argb & 0xffffff);
        return (short) (i == null ? 0 : i);
    }

    private void loadTextures(Atlas.Loader ld) {
        String[] names = ld.text("tex3d.txt").trim().split("\n");
        int[] sz = new int[2];
        int[] px = ld.image("tex3d.png", sz);
        int sw = sz[0];
        int[] gp = ld.image("tex3d_glow.png", sz);
        tex = new short[names.length][];
        glow = new byte[names.length][];
        texAlpha = new boolean[names.length];
        for (int i = 0; i < names.length; i++) {
            texId.put(names[i].trim(), i);
            int ox = (i % 8) * T, oy = (i / 8) * T;
            short[] t = new short[T * T];
            byte[] g = new byte[T * T];
            for (int y = 0; y < T; y++)
                for (int x = 0; x < T; x++) {
                    int c = px[(oy + y) * sw + ox + x];
                    t[y * T + x] = toIdx(c);
                    if (t[y * T + x] < 0) texAlpha[i] = true;
                    g[y * T + x] = (byte) (gp[(oy + y) * sw + ox + x] & 255);
                }
            tex[i] = t; glow[i] = g;
        }
    }

    private void loadSprites(Atlas.Loader ld) {
        int[] sz = new int[2];
        int[] px = ld.image("spr3d.png", sz);
        int sw = sz[0];
        int[] gp = ld.image("spr3d_glow.png", sz);
        for (String line : ld.text("spr3d.txt").split("\n")) {
            line = line.trim();
            if (line.isEmpty()) continue;
            String[] p = line.split(" ");
            Spr s = new Spr();
            int x0 = Integer.parseInt(p[1]), y0 = Integer.parseInt(p[2]);
            s.w = Integer.parseInt(p[3]); s.h = Integer.parseInt(p[4]);
            s.ww = Float.parseFloat(p[5]); s.wh = Float.parseFloat(p[6]); s.lift = Float.parseFloat(p[7]);
            s.idx = new short[s.w * s.h]; s.glow = new byte[s.w * s.h];
            for (int y = 0; y < s.h; y++)
                for (int x = 0; x < s.w; x++) {
                    s.idx[y * s.w + x] = toIdx(px[(y0 + y) * sw + x0 + x]);
                    s.glow[y * s.w + x] = (byte) (gp[(y0 + y) * sw + x0 + x] & 255);
                }
            sprites.put(p[0], s);
        }
    }

    private int tid(String kind) {
        Integer i = texId.get(kind);
        if (i == null) i = texId.get("wall");
        return i;
    }

    // ------------------------------------------------------------- lighting
    private static float torch(float d, boolean outdoor) {
        if (outdoor) return Math.max(Math.min(0.6f, -(d - 0.9f) * 1.05f), -4.2f);
        return Math.min(0.7f, -(d - 0.9f) * 1.75f);
    }

    private static final float[] BAYER = {0.2f, 0.6f, 0.8f, 0.4f};

    private int shadePixel(int i, int x, int y) {
        short idx = pIdx[i];
        if (idx < 0) return pDirect[i];
        float st = pSteps[i], g = pGlow[i];
        if (g > 0) st = Math.max(st, st * (1 - Math.min(g, 1f)) + g * 2.4f);
        int r = rampOf[idx];
        float fp = posOf[idx] + st;
        int len = rampLen[r];
        if (fp < 0) fp = 0;
        if (fp > len - 1) fp = len - 1;
        int lo = (int) fp;
        float frac = fp - lo;
        float th = BAYER[(y & 1) * 2 + (x & 1)];
        int pos = lo + (frac > 0.5f + (th - 0.5f) * 0.5f ? 1 : 0);
        if (pos > len - 1) pos = len - 1;
        return pal[rampTab[r][pos]];
    }

    // --------------------------------------------------------------- render
    private static final class Hit {
        float perp, u; int tex; float lam;
    }
    private final Hit[] hits = new Hit[24];
    { for (int i = 0; i < hits.length; i++) hits[i] = new Hit(); }

    /**
     * @param cx camera x in cells (cell x spans x..x+1)
     * @param cy camera y in cells (y grows southward)
     * @param ang facing angle in radians, 0 = north, PI/2 = east
     */
    public void render(Level lv, float cx, float cy, float ang, float time, int flashMode) {
        boolean outdoor = lv.outdoor();
        float fx = (float) Math.sin(ang), fy = (float) -Math.cos(ang);
        float rx = (float) Math.cos(ang), ry = (float) Math.sin(ang);
        int skyRow = lv.theme.equals("town") ? 1 : 0;
        int floorT = tid(outdoor ? (lv.theme.equals("town") ? "cobble" : "grass") : "floor");
        int ceilT = tid("ceil");
        // ---- floor, ceiling, sky
        for (int y = 0; y < V; y++) {
            float yoff = y + 0.5f - V / 2f;
            boolean below = yoff > 0;
            for (int x = 0; x < V; x++) {
                int i = y * V + x;
                float camx = (x + 0.5f - V / 2f) / (V / 2f);
                if (!below && outdoor) {
                    double a = ang + Math.atan(camx);
                    int sx = (int) Math.floor((a + Math.PI / 4) / (2 * Math.PI) * 512) & 511;
                    pIdx[i] = -1;
                    pDirect[i] = sky[(skyRow * 64 + Math.min(63, y)) * 512 + sx];
                    depth[i] = 1e9f;
                    continue;
                }
                float perp = EYE * FOCAL / Math.abs(yoff);
                float wx = cx + (fx + rx * camx) * perp, wy = cy + (fy + ry * camx) * perp;
                int t = below ? floorT : ceilT;
                int tu = (int) ((wx - (float) Math.floor(wx)) * T) & (T - 1);
                int tv = (int) ((wy - (float) Math.floor(wy)) * T) & (T - 1);
                pIdx[i] = tex[t][tv * T + tu];
                pGlow[i] = 0;
                float d = perp * (float) Math.sqrt(1 + camx * camx);
                pSteps[i] = torch(d, outdoor) + (below ? -0.5f : -1.9f);
                depth[i] = perp;
            }
        }
        // ---- walls: DDA per column, gathering see-through faces until an opaque one
        for (int x = 0; x < V; x++) {
            float camx = (x + 0.5f - V / 2f) / (V / 2f);
            float dx = fx + rx * camx, dy = fy + ry * camx;
            float dlen = (float) Math.sqrt(dx * dx + dy * dy);
            int mx = (int) Math.floor(cx), my = (int) Math.floor(cy);
            float ddx = dx == 0 ? 1e9f : Math.abs(1 / dx), ddy = dy == 0 ? 1e9f : Math.abs(1 / dy);
            int sx = dx > 0 ? 1 : -1, sy = dy > 0 ? 1 : -1;
            float tx = (dx > 0 ? (mx + 1 - cx) : (cx - mx)) * ddx;
            float ty = (dy > 0 ? (my + 1 - cy) : (cy - my)) * ddy;
            int nh = 0;
            for (int step = 0; step < 40 && nh < hits.length; step++) {
                int side;
                if (tx < ty) { tx += ddx; mx += sx; side = 0; } else { ty += ddy; my += sy; side = 1; }
                float perp = side == 0 ? tx - ddx : ty - ddy;
                if (perp > 12) break;
                int face; float u;
                if (side == 0) {
                    float hy = cy + dy * perp;
                    u = hy - (float) Math.floor(hy);
                    face = sx > 0 ? Level.W : Level.E;
                    if (sx < 0) u = 1 - u;
                } else {
                    float hx = cx + dx * perp;
                    u = hx - (float) Math.floor(hx);
                    face = sy > 0 ? Level.N : Level.S;
                    if (sy > 0) u = 1 - u;
                }
                float lam = side == 0 ? Math.abs(dx) / dlen : Math.abs(dy) / dlen;
                char c = lv.at(mx, my);
                if (lv.solid(mx, my)) {
                    int t = tid(lv.faceKind(mx, my, face));
                    Hit h = hits[nh++];
                    h.perp = perp; h.u = u; h.tex = t; h.lam = lam;
                    if (!texAlpha[t]) break;
                } else if (c == Level.OPEN && lv.faceOnAxis(mx, my, face)) {
                    Hit h = hits[nh++];
                    h.perp = perp; h.u = u; h.tex = tid("arch"); h.lam = lam;
                }
            }
            for (int k = nh - 1; k >= 0; k--) {
                Hit h = hits[k];
                if (h.perp < 0.02f) continue;
                float size = FOCAL / h.perp;
                float top = V / 2f - (1 - EYE) * size, bot = V / 2f + EYE * size;
                int y0 = Math.max(0, (int) Math.ceil(top - 0.5f)), y1 = Math.min(V, (int) Math.ceil(bot - 0.5f));
                int tu = Math.min(T - 1, (int) (h.u * T));
                short[] tt = tex[h.tex];
                byte[] gg = glow[h.tex];
                float d = h.perp * (float) Math.sqrt(1 + camx * camx);
                float st = torch(d, outdoor) - (1 - h.lam) * 1.6f;
                for (int y = y0; y < y1; y++) {
                    int tv = (int) ((y + 0.5f - top) / size * T);
                    if (tv < 0) tv = 0; else if (tv >= T) tv = T - 1;
                    short v = tt[tv * T + tu];
                    if (v < 0) continue;
                    int i = y * V + x;
                    pIdx[i] = v;
                    pGlow[i] = (gg[tv * T + tu] & 255) / 255f;
                    pSteps[i] = st;
                    depth[i] = h.perp;
                }
            }
        }
        // ---- sprites (monsters, items, props), far to near, depth tested per pixel
        drawSprites(lv, cx, cy, fx, fy, rx, ry, outdoor);
        // ---- resolve colours
        int[] o = out.px;
        for (int y = 0; y < V; y++)
            for (int x = 0; x < V; x++) {
                int i = y * V + x;
                o[i] = shadePixel(i, x, y);
                if (flashPix[i]) {
                    int c = o[i];
                    o[i] = 0xff000000 | ((((c >> 16) & 255) + 510) / 3 << 16) | ((((c >> 8) & 255) + 510) / 3 << 8) | (((c & 255) + 460) / 3);
                }
            }
        Arrays.fill(flashPix, false);
    }

    private final boolean[] flashPix = new boolean[V * V];
    private final ArrayList<float[]> sprList = new ArrayList<>();
    private final ArrayList<Object> sprRef = new ArrayList<>();

    private void drawSprites(Level lv, float cx, float cy, float fx, float fy, float rx, float ry, boolean outdoor) {
        sprList.clear(); sprRef.clear();
        String suf = "";
        for (Item it : lv.items) {
            String key = (it.prop ? "o:" : "i:") + it.type;
            addSprite(key, it.x + 0.5f, it.y + 0.5f, cx, cy, fx, fy, rx, ry, 0);
        }
        for (Monster m : lv.monsters) {
            if (!m.alive()) continue;
            addSprite("m:" + m.type + ":" + m.frame(), m.wx() + 0.5f, m.wy() + 0.5f, cx, cy, fx, fy, rx, ry, m.hitFlash > 0 ? 1 : 0);
        }
        // sort far to near
        Integer[] order = new Integer[sprList.size()];
        for (int i = 0; i < order.length; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> Float.compare(sprList.get(b)[0], sprList.get(a)[0]));
        for (int oi : order) {
            float[] s = sprList.get(oi);
            Spr sp = (Spr) sprRef.get(oi);
            float z = s[0], xs = s[1];
            boolean flash = s[2] > 0;
            float scale = FOCAL / z;
            float scx = V / 2f + xs * scale;
            float w = sp.ww * scale, h = sp.wh * scale;
            float bottom = V / 2f + (EYE - sp.lift) * scale;
            float top = bottom - h, left = scx - w / 2;
            int x0 = Math.max(0, (int) Math.ceil(left - 0.5f)), x1 = Math.min(V, (int) Math.ceil(left + w - 0.5f));
            int y0 = Math.max(0, (int) Math.ceil(top - 0.5f)), y1 = Math.min(V, (int) Math.ceil(bottom - 0.5f));
            float st = torch((float) Math.hypot(z, xs), outdoor) + 0.25f;
            for (int x = x0; x < x1; x++) {
                int u = (int) ((x + 0.5f - left) / w * sp.w);
                if (u < 0 || u >= sp.w) continue;
                for (int y = y0; y < y1; y++) {
                    int i = y * V + x;
                    if (z >= depth[i]) continue;
                    int v = (int) ((y + 0.5f - top) / h * sp.h);
                    if (v < 0 || v >= sp.h) continue;
                    short c = sp.idx[v * sp.w + u];
                    if (c < 0) continue;
                    pIdx[i] = c;
                    pSteps[i] = st;
                    pGlow[i] = (sp.glow[v * sp.w + u] & 255) / 255f;
                    depth[i] = z;
                    flashPix[i] = flash;
                }
            }
        }
    }

    private void addSprite(String key, float wx, float wy, float cx, float cy, float fx, float fy, float rx, float ry, int flash) {
        Spr sp = sprites.get(key);
        if (sp == null) {
            int c = key.lastIndexOf(':');
            if (key.startsWith("m:") && c > 2) sp = sprites.get(key.substring(0, c) + ":idle");
            if (sp == null) return;
        }
        float relx = wx - cx, rely = wy - cy;
        float z = relx * fx + rely * fy;
        if (z < 0.2f || z > 9f) return;
        float xs = relx * rx + rely * ry;
        if (Math.abs(xs) > z * 1.3f + 1) return;
        sprList.add(new float[]{z, xs, flash});
        sprRef.add(sp);
    }
}
