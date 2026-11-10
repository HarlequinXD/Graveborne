package com.harlequin.graveborne;

/** Software framebuffer (ARGB ints) with sprite blits and a 5x7 pixel font. */
public final class Gfx {
    public final int w, h;
    public final int[] px;

    public Gfx(int w, int h) {
        this.w = w; this.h = h; this.px = new int[w * h];
    }

    public void clear(int c) { java.util.Arrays.fill(px, c); }

    public void fill(int x, int y, int ww, int hh, int c) {
        int x0 = Math.max(0, x), y0 = Math.max(0, y), x1 = Math.min(w, x + ww), y1 = Math.min(h, y + hh);
        for (int yy = y0; yy < y1; yy++) {
            int o = yy * w;
            for (int xx = x0; xx < x1; xx++) px[o + xx] = c;
        }
    }

    /** Darken a rectangle (for overlays). k = 0..256 keep factor. */
    public void shade(int x, int y, int ww, int hh, int k) {
        int x0 = Math.max(0, x), y0 = Math.max(0, y), x1 = Math.min(w, x + ww), y1 = Math.min(h, y + hh);
        for (int yy = y0; yy < y1; yy++) {
            int o = yy * w;
            for (int xx = x0; xx < x1; xx++) {
                int c = px[o + xx];
                int r = ((c >> 16) & 255) * k >> 8, g = ((c >> 8) & 255) * k >> 8, b = (c & 255) * k >> 8;
                px[o + xx] = 0xff000000 | (r << 16) | (g << 8) | b;
            }
        }
    }

    /** Bevelled panel in the stone/iron UI style. */
    public void panel(int x, int y, int ww, int hh, int face, int hi, int lo) {
        fill(x, y, ww, hh, Pal.INK);
        fill(x + 1, y + 1, ww - 2, hh - 2, face);
        fill(x + 1, y + 1, ww - 2, 1, hi);
        fill(x + 1, y + 1, 1, hh - 2, hi);
        fill(x + 1, y + hh - 2, ww - 2, 1, lo);
        fill(x + ww - 2, y + 1, 1, hh - 2, lo);
    }

    public void frame(int x, int y, int ww, int hh, int c) {
        fill(x, y, ww, 1, c); fill(x, y + hh - 1, ww, 1, c);
        fill(x, y, 1, hh, c); fill(x + ww - 1, y, 1, hh, c);
    }

    /** Copy a sprite; mode 0 normal, 1 white flash, 2 greyscale-dim. Clipped to (cx,cy,cw,ch). */
    public void blit(Atlas.Sprite s, int dx, int dy, int mode, int cx, int cy, int cw, int ch) {
        if (s == null) return;
        int[] src = s.sheet.px; int sw = s.sheet.w;
        int x0 = Math.max(dx, cx), y0 = Math.max(dy, cy);
        int x1 = Math.min(dx + s.w, Math.min(cx + cw, w)), y1 = Math.min(dy + s.h, Math.min(cy + ch, h));
        for (int y = y0; y < y1; y++) {
            int so = (s.y + y - dy) * sw + s.x - dx;
            int o = y * w;
            for (int x = x0; x < x1; x++) {
                int c = src[so + x];
                if ((c >>> 24) < 128) continue;
                if (mode == 1) {
                    c = 0xff000000 | ((((c >> 16) & 255) + 255 * 2) / 3 << 16) | ((((c >> 8) & 255) + 255 * 2) / 3 << 8) | (((c & 255) + 230 * 2) / 3);
                } else if (mode == 2) {
                    int l = (((c >> 16) & 255) * 3 + ((c >> 8) & 255) * 5 + (c & 255) * 2) / 20;
                    c = 0xff000000 | (l << 16) | (l << 8) | (l + 8 > 255 ? 255 : l + 8);
                }
                px[o + x] = c;
            }
        }
    }

    public void blit(Atlas.Sprite s, int dx, int dy) { blit(s, dx, dy, 0, 0, 0, w, h); }

    /** Copy a region of another buffer (used for the 128x128 view and turn pans). */
    public void copy(int[] src, int sw, int sx, int sy, int dx, int dy, int ww, int hh) {
        for (int y = 0; y < hh; y++) {
            int ty = dy + y; if (ty < 0 || ty >= h) continue;
            for (int x = 0; x < ww; x++) {
                int tx = dx + x; if (tx < 0 || tx >= w) continue;
                px[ty * w + tx] = src[(sy + y) * sw + sx + x];
            }
        }
    }

    // ------------------------------------------------------------------ font
    public static final int CW = 6, CH = 8;

    public int text(String s, int x, int y, int col) { return text(s, x, y, col, 1); }

    public int text(String s, int x, int y, int col, int scale) {
        int cx = x;
        for (int i = 0; i < s.length(); i++) {
            char c = Character.toUpperCase(s.charAt(i));
            int[] g = Font.glyph(c);
            if (g != null) {
                for (int r = 0; r < 7; r++) {
                    int bits = g[r];
                    for (int b = 0; b < 5; b++) {
                        if ((bits & (16 >> b)) != 0) {
                            if (scale == 1) {
                                int px_ = cx + b, py_ = y + r;
                                if (px_ >= 0 && px_ < w && py_ >= 0 && py_ < h) px[py_ * w + px_] = col;
                            } else fill(cx + b * scale, y + r * scale, scale, scale, col);
                        }
                    }
                }
            }
            cx += (c == ' ' ? 4 : CW) * scale;
            if (c == 'I' || c == '.' || c == ',' || c == '!' || c == ':' || c == '\'') cx -= 2 * scale;
        }
        return cx;
    }

    /** Text with a 1px dark drop shadow. */
    public int textS(String s, int x, int y, int col) {
        text(s, x + 1, y + 1, Pal.INK);
        return text(s, x, y, col);
    }

    public static int width(String s) {
        int n = 0;
        for (int i = 0; i < s.length(); i++) {
            char c = Character.toUpperCase(s.charAt(i));
            n += (c == ' ' ? 4 : CW);
            if (c == 'I' || c == '.' || c == ',' || c == '!' || c == ':' || c == '\'') n -= 2;
        }
        return n;
    }

    public void textC(String s, int cx, int y, int col) { textS(s, cx - width(s) / 2, y, col); }

    public void textC(String s, int cx, int y, int col, int scale) {
        int x = cx - width(s) * scale / 2;
        text(s, x + scale, y + scale, Pal.INK, scale);
        text(s, x, y, col, scale);
    }
}
