package com.harlequin.graveborne;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;

/**
 * Real-time 3D tile renderer for the 128x128 view, in the style of Game Boy Advance 3D
 * (Driv3r, Asterix &amp; Obelix XXL) and the PS1: every grid cell is built from textured
 * quads, drawn as triangles with
 *  - perspective-correct texture mapping,
 *  - vertices snapped to whole pixels (no sub-pixel precision, so geometry jitters),
 *  - per-vertex (Gouraud) torch light, stepping each texel along its colour ramp,
 *  - heavy 4x4 ordered dithering on the light ramps and a 15-bit colour pass.
 */
public final class Renderer3D {
    public static final int V = 128;
    private static final float FOCAL = 64f;        // 90 degree field of view
    private static final float EYE_STAND = 0.5f;
    /** Eye height in cells (0.5 standing; lower while climbing out of the sarcophagus). */
    public float eye = EYE_STAND;
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

    private static final float[] BAYER4 = {
            0 / 16f, 8 / 16f, 2 / 16f, 10 / 16f,
            12 / 16f, 4 / 16f, 14 / 16f, 6 / 16f,
            3 / 16f, 11 / 16f, 1 / 16f, 9 / 16f,
            15 / 16f, 7 / 16f, 13 / 16f, 5 / 16f};

    private int shadePixel(int i, int x, int y) {
        short idx = pIdx[i];
        float th = BAYER4[(y & 3) * 4 + (x & 3)] + 1 / 32f;
        int c;
        if (idx < 0) c = pDirect[i];
        else {
            float st = pSteps[i], g = pGlow[i];
            if (g > 0) st = Math.max(st, st * (1 - Math.min(g, 1f)) + g * 2.4f);
            int r = rampOf[idx];
            float fp = posOf[idx] + st;
            int len = rampLen[r];
            if (fp < 0) fp = 0;
            if (fp > len - 1) fp = len - 1;
            int lo = (int) fp;
            // full ordered dither between ramp steps: every gradient gets the pattern
            int pos = lo + ((fp - lo) > th ? 1 : 0);
            if (pos > len - 1) pos = len - 1;
            c = pal[rampTab[r][pos]];
        }
        // 15-bit colour (5 bits per channel) with the same ordered dither, like the GBA
        int r = (c >> 16) & 255, gg = (c >> 8) & 255, b = c & 255;
        int bias = (int) (th * 8);
        r = Math.min(255, (r + bias) & ~7); gg = Math.min(255, (gg + bias) & ~7); b = Math.min(255, (b + bias) & ~7);
        return 0xff000000 | (r << 16) | (gg << 8) | b;
    }

    // ---------------------------------------------------------- geometry
    private static final float NEAR = 0.06f;
    private float cx, cy, fx, fy, rx, ry;
    private boolean outdoor;

    /** Camera-space vertex: x right, y up (world height), z forward, plus u, v, light steps. */
    private final float[][] poly = new float[16][6];
    private final float[][] clip = new float[16][6];
    private int polyN;

    private void vtx(int k, float wx, float wh, float wy, float u, float v, float bias) {
        float dx = wx - cx, dy = wy - cy;
        float[] p = poly[k];
        p[0] = dx * rx + dy * ry;
        p[1] = wh;
        p[2] = dx * fx + dy * fy;
        p[3] = u; p[4] = v;
        float d = (float) Math.sqrt(dx * dx + dy * dy);
        p[5] = torch(d, outdoor) + bias;
    }

    /** Draw a world quad (4 verts already in poly[0..3]) with texture t. */
    private void quad(int t, int flash) {
        // clip against the near plane (Sutherland-Hodgman)
        int n = 0;
        for (int i = 0; i < 4; i++) {
            float[] a = poly[i], b = poly[(i + 1) & 3];
            boolean ina = a[2] >= NEAR, inb = b[2] >= NEAR;
            if (ina) System.arraycopy(a, 0, clip[n++], 0, 6);
            if (ina != inb) {
                float k = (NEAR - a[2]) / (b[2] - a[2]);
                float[] o = clip[n++];
                for (int j = 0; j < 6; j++) o[j] = a[j] + (b[j] - a[j]) * k;
            }
        }
        if (n < 3) return;
        // project and snap to whole pixels: no sub-pixel precision -> vertex wobble
        for (int i = 0; i < n; i++) {
            float[] p = clip[i];
            float z = p[2];
            sxv[i] = Math.round(V / 2f + p[0] / z * FOCAL);
            syv[i] = Math.round(V / 2f - (p[1] - eye) / z * FOCAL);
        }
        for (int i = 1; i + 1 < n; i++) tri(0, i, i + 1, t, flash);
    }

    private final int[] sxv = new int[16], syv = new int[16];

    /** Textured triangle, perspective-correct, from pixel-snapped corners. */
    private void tri(int a, int b, int c, int t, int flash) {
        int x0 = sxv[a], y0 = syv[a], x1 = sxv[b], y1 = syv[b], x2 = sxv[c], y2 = syv[c];
        long area = (long) (x1 - x0) * (y2 - y0) - (long) (x2 - x0) * (y1 - y0);
        if (area == 0) return;
        if (Math.abs(area) > 4_000_000) return;
        int minX = Math.max(0, Math.min(x0, Math.min(x1, x2))), maxX = Math.min(V - 1, Math.max(x0, Math.max(x1, x2)));
        int minY = Math.max(0, Math.min(y0, Math.min(y1, y2))), maxY = Math.min(V - 1, Math.max(y0, Math.max(y1, y2)));
        if (minX > maxX || minY > maxY) return;
        float inv = 1f / area;
        float[] A = clip[a], B = clip[b], C = clip[c];
        short[] tt = t >= 0 ? tex[t] : null;
        byte[] gg = t >= 0 ? glow[t] : null;
        for (int y = minY; y <= maxY; y++) {
            float py = y + 0.5f;
            for (int x = minX; x <= maxX; x++) {
                float px = x + 0.5f;
                float w0 = ((x1 - px) * (y2 - py) - (x2 - px) * (y1 - py)) * inv;
                float w1 = ((x2 - px) * (y0 - py) - (x0 - px) * (y2 - py)) * inv;
                float w2 = 1 - w0 - w1;
                if (w0 < 0 || w1 < 0 || w2 < 0) continue;
                int i = y * V + x;
                // perspective-correct: interpolate 1/z and attribute/z, then divide back
                float iz = w0 / A[2] + w1 / B[2] + w2 / C[2];
                float z = 1f / iz;
                if (z >= depth[i]) continue;
                float u = (w0 * A[3] / A[2] + w1 * B[3] / B[2] + w2 * C[3] / C[2]) * z;
                float v = (w0 * A[4] / A[2] + w1 * B[4] / B[2] + w2 * C[4] / C[2]) * z;
                short px_;
                int tu, tv;
                if (tt != null) {
                    tu = ((int) Math.floor(u * T)) & (T - 1);
                    tv = ((int) Math.floor(v * T)) & (T - 1);
                    px_ = tt[tv * T + tu];
                } else {
                    tu = Math.min(curSpr.w - 1, Math.max(0, (int) (u * curSpr.w)));
                    tv = Math.min(curSpr.h - 1, Math.max(0, (int) (v * curSpr.h)));
                    px_ = curSpr.idx[tv * curSpr.w + tu];
                }
                if (px_ < 0) continue;
                pIdx[i] = px_;
                pSteps[i] = (w0 * A[5] / A[2] + w1 * B[5] / B[2] + w2 * C[5] / C[2]) * z;
                pGlow[i] = ((tt != null ? gg[tv * T + tu] : curSpr.glow[tv * curSpr.w + tu]) & 255) / 255f;
                depth[i] = z;
                flashPix[i] = flash != 0;
            }
        }
    }

    private Spr curSpr;

    private float lam(float nx, float ny, float qx, float qy) {
        // light falls off on faces seen at a glancing angle (torch is at the camera)
        float dx = qx - cx, dy = qy - cy;
        float d = (float) Math.sqrt(dx * dx + dy * dy) + 1e-4f;
        float c = Math.abs((dx * nx + dy * ny) / d);
        return -(1 - c) * 1.6f;
    }

    /**
     * @param camX camera x in cells (cell x spans x..x+1)
     * @param camY camera y in cells (y grows southward)
     * @param ang facing angle in radians, 0 = north, PI/2 = east
     */
    public void render(Level lv, float camX, float camY, float ang, float time, int flashMode) {
        outdoor = lv.outdoor();
        cx = camX; cy = camY;
        fx = (float) Math.sin(ang); fy = (float) -Math.cos(ang);
        rx = (float) Math.cos(ang); ry = (float) Math.sin(ang);
        int skyRow = lv.theme.equals("town") ? 1 : 0;
        // background: sky outdoors (upper half), black elsewhere
        for (int y = 0; y < V; y++)
            for (int x = 0; x < V; x++) {
                int i = y * V + x;
                depth[i] = 1e9f;
                pIdx[i] = -1;
                if (outdoor && y < 64) {
                    float camx = (x + 0.5f - V / 2f) / (V / 2f);
                    double a = ang + Math.atan(camx);
                    int sx = (int) Math.floor((a + Math.PI / 4) / (2 * Math.PI) * 512) & 511;
                    pDirect[i] = sky[(skyRow * 64 + y) * 512 + sx];
                } else pDirect[i] = 0xff000000;
            }
        int floorT = tid(outdoor ? (lv.theme.equals("town") ? "cobble" : "grass") : "floor");
        int ceilT = tid("ceil");
        int R = 8;
        int x0 = (int) Math.floor(cx) - R, x1 = (int) Math.floor(cx) + R;
        int y0 = (int) Math.floor(cy) - R, y1 = (int) Math.floor(cy) + R;
        for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++) {
                // rough frustum cull on the cell centre
                float dx = x + 0.5f - cx, dy = y + 0.5f - cy;
                float z = dx * fx + dy * fy, xs = dx * rx + dy * ry;
                if (z < -1.2f || Math.abs(xs) > z + 1.6f || z > R + 0.5f) continue;
                // floor and ceiling under every cell: see-through walls (bars, opening doors,
                // the sliding bed wall, tree canopies) reveal the ground inside the block
                vtx(0, x, 0, y + 1, 0, 1, -0.5f); vtx(1, x + 1, 0, y + 1, 1, 1, -0.5f);
                vtx(2, x + 1, 0, y, 1, 0, -0.5f); vtx(3, x, 0, y, 0, 0, -0.5f);
                quad(floorT, 0);
                if (!outdoor) {
                    vtx(0, x, 1, y, 0, 0, -1.9f); vtx(1, x + 1, 1, y, 1, 0, -1.9f);
                    vtx(2, x + 1, 1, y + 1, 1, 1, -1.9f); vtx(3, x, 1, y + 1, 0, 1, -1.9f);
                    quad(ceilT, 0);
                }
                if (lv.open(x, y)) {
                    if (lv.at(x, y) == Level.OPEN) {
                        // archway frames on the open door's axis faces
                        for (int d = 0; d < 4; d++) if (lv.faceOnAxis(x, y, d)) faceQuad(lv, x, y, d, tid("arch"), true);
                    }
                    continue;
                }
                for (int d = 0; d < 4; d++) {
                    int nx = x + Level.DX[d], ny = y + Level.DY[d];
                    if (!lv.open(nx, ny)) continue;
                    faceQuad(lv, x, y, d, tid(lv.faceKind(x, y, d)), false);
                }
            }
        drawSprites(lv);
        int[] o = out.px;
        for (int y = 0; y < V; y++)
            for (int x = 0; x < V; x++) {
                int i = y * V + x;
                int c = shadePixel(i, x, y);
                if (flashPix[i]) c = 0xff000000 | ((((c >> 16) & 255) + 510) / 3 << 16) | ((((c >> 8) & 255) + 510) / 3 << 8) | (((c & 255) + 460) / 3);
                o[i] = c;
            }
        java.util.Arrays.fill(flashPix, false);
    }

    /** One face of cell (x,y) pointing in direction d, textured so u runs left-to-right as seen from outside. */
    private void faceQuad(Level lv, int x, int y, int d, int t, boolean inset) {
        // corners on the cell edge, ordered left -> right as seen by someone facing the face
        float ax, ay, bx, by, nx = Level.DX[d], ny = Level.DY[d];
        switch (d) {
            case Level.N: ax = x + 1; ay = y; bx = x; by = y; break;
            case Level.S: ax = x; ay = y + 1; bx = x + 1; by = y + 1; break;
            case Level.E: ax = x + 1; ay = y + 1; bx = x + 1; by = y; break;
            default: ax = x; ay = y; bx = x; by = y + 1; break;
        }
        // back-face cull: camera must be on the outside of the face
        float side = (cx - ax) * nx + (cy - ay) * ny;
        if (side <= 0) {
            if (!inset) return;
        }
        float qx = (ax + bx) / 2, qy = (ay + by) / 2;
        float b = lam(nx, ny, qx, qy);
        // seen from the face's front, the viewer looks along -n; "left" is corner a
        vtx(0, ax, 0, ay, 0, 1, b); vtx(1, bx, 0, by, 1, 1, b);
        vtx(2, bx, 1, by, 1, 0, b); vtx(3, ax, 1, ay, 0, 0, b);
        quad(t, 0);
    }

    private final boolean[] flashPix = new boolean[V * V];

    private void drawSprites(Level lv) {
        for (Item it : lv.items) billboard((it.prop ? "o:" : "i:") + it.type, it.x + 0.5f, it.y + 0.5f, 0);
        for (Monster m : lv.monsters) {
            if (!m.alive()) continue;
            billboard("m:" + m.type + ":" + m.frame(), m.wx() + 0.5f, m.wy() + 0.5f, m.hitFlash > 0 ? 1 : 0);
        }
    }

    private void billboard(String key, float wx, float wy, int flash) {
        Spr sp = sprites.get(key);
        if (sp == null) {
            int c = key.lastIndexOf(':');
            if (key.startsWith("m:") && c > 2) sp = sprites.get(key.substring(0, c) + ":idle");
            if (sp == null) return;
        }
        float dx = wx - cx, dy = wy - cy;
        if (dx * fx + dy * fy < NEAR) return;
        // a camera-facing card: corners offset along the camera's right vector
        float hw = sp.ww / 2;
        float lx = wx - rx * hw, ly = wy - ry * hw, rxw = wx + rx * hw, ryw = wy + ry * hw;
        float b = 0.25f;
        vtx(0, lx, sp.lift, ly, 0, 1, b); vtx(1, rxw, sp.lift, ryw, 1, 1, b);
        vtx(2, rxw, sp.lift + sp.wh, ryw, 1, 0, b); vtx(3, lx, sp.lift + sp.wh, ly, 0, 0, b);
        curSpr = sp;
        quad(-1, flash);
    }
}
