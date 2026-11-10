package com.harlequin.graveborne;

/**
 * Composes the 128x128 first-person view from pre-rendered sprites, far to near.
 * Pieces are keyed by the quarter-cell position of their cell relative to the camera,
 * so stepping (sz = 1..3 quarters forward) and strafing (sx = +-2 quarters) frames reuse
 * exactly the same art as standing still.
 */
public final class ViewRenderer {
    public static final int V = 128;
    private static final int MAX_DZ = 5, MAX_DX = 4;
    private final Atlas atlas;
    private String suffix = "";
    public final Gfx out = new Gfx(V, V);

    public ViewRenderer(Atlas atlas) { this.atlas = atlas; }

    private Atlas.Sprite face(String kind, boolean side, int x4, int zq) {
        String key = "f:" + kind + (side ? ":S:" : ":F:") + x4 + ":" + zq;
        Atlas.Sprite s = atlas.get(key);
        if (s == null && !kind.equals("wall")) {
            // special pieces only exist close up; far away they read as plain wall
            String base = kind.startsWith("door") ? "door" : "wall";
            s = atlas.get("f:" + base + (side ? ":S:" : ":F:") + x4 + ":" + zq);
        }
        return s;
    }

    /**
     * @param sx strafe offset in quarter cells toward the camera's right
     * @param sz forward offset in quarter cells
     */
    public void render(Level lv, int px, int py, int dir, int sx, int sz, float time) {
        Gfx g = out;
        String th = lv.outdoor() ? lv.theme + dir : lv.theme;
        Atlas.Sprite bg = atlas.get("bg:" + th + ":" + sx + ":" + sz);
        if (bg == null) bg = atlas.get("bg:" + th + ":0:0");
        suffix = lv.outdoor() ? ":o" : "";
        g.blit(bg, 0, 0);
        int fx = Level.DX[dir], fy = Level.DY[dir];
        int rdir = (dir + 1) & 3;
        int rx = Level.DX[rdir], ry = Level.DY[rdir];
        for (int dz = MAX_DZ; dz >= 0; dz--) {
            for (int a = MAX_DX; a >= 0; a--) {
                for (int sgn = -1; sgn <= 1; sgn += 2) {
                    if (a == 0 && sgn == 1) continue;
                    int dx = a * sgn;
                    int cx = px + fx * dz + rx * dx, cy = py + fy * dz + ry * dx;
                    int x4 = 4 * dx - sx, zq = 4 * dz - sz;
                    if (lv.solid(cx, cy)) {
                        if (dz == 0 && dx == 0) continue;
                        // side face toward the view axis
                        if (Math.abs(x4) > 2) {
                            int fd = x4 < 0 ? rdir : (dir + 3) & 3;
                            if (!lv.solid(cx + Level.DX[fd], cy + Level.DY[fd])) {
                                String k = lv.faceKind(cx, cy, fd);
                                Atlas.Sprite s = face(k, true, x4, zq);
                                if (s != null) g.blit(s, s.ox, s.oy);
                            }
                        }
                        int fd = (dir + 2) & 3;
                        if (!lv.solid(cx + Level.DX[fd], cy + Level.DY[fd])) {
                            String k = lv.faceKind(cx, cy, fd);
                            Atlas.Sprite s = face(k, false, x4, zq);
                            if (s != null) g.blit(s, s.ox, s.oy);
                        }
                    } else {
                        drawContents(lv, cx, cy, px, py, fx, fy, rx, ry, sx, sz, time);
                        if (lv.at(cx, cy) == Level.OPEN && lv.faceOnAxis(cx, cy, (dir + 2) & 3)) {
                            Atlas.Sprite s = face("arch", false, x4, zq);
                            if (s != null) g.blit(s, s.ox, s.oy);
                        }
                    }
                }
            }
        }
    }

    private void drawContents(Level lv, int cx, int cy, int px, int py, int fx, int fy, int rx, int ry, int sx, int sz, float time) {
        for (Item it : lv.items) {
            if (it.x != cx || it.y != cy) continue;
            float relx = cx - px, rely = cy - py;
            String pre = it.prop ? "o:" + it.type + ":" : "i:" + it.type + ":";
            billboard(pre, it.prop ? "" : suffix, relx * fx + rely * fy - sz / 4f, relx * rx + rely * ry - sx / 4f, 1, 0);
        }
        for (Monster m : lv.monsters) {
            if (!m.alive()) continue;
            float wx = m.wx(), wy = m.wy();
            if (Math.round(wx) != cx || Math.round(wy) != cy) continue;
            float relx = wx - px, rely = wy - py;
            float dzf = relx * fx + rely * fy - sz / 4f;
            float dxf = relx * rx + rely * ry - sx / 4f;
            billboard("m:" + m.type + ":" + m.frame() + ":", suffix, dzf, dxf, 2, m.hitFlash > 0 ? 1 : 0);
        }
    }

    private void billboard(String prefix, String suf, float dz, float dx, int minZq, int mode) {
        int zq = Math.round(dz * 4);
        if (zq < minZq) return;
        Atlas.Sprite s = atlas.get(prefix + zq + suf);
        if (s == null) s = atlas.get(prefix + zq);
        if (s == null) return;
        float d = (zq + 1.2f) / 4f;
        int ax = Math.round(64 + dx * 64f / d);
        out.blit(s, ax + s.ox, 64 + s.oy, mode, 0, 0, V, V);
    }
}
