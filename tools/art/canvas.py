"""Tiny shape painter for characters: shaded ellipses, capsules and polygons with
painted (not computed) light from the upper left, the way a pixel artist shades."""
import numpy as np
from common import hexrgb


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), np.float32)
        self.emi = np.zeros((h, w, 3), np.float32)
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # --- fills -------------------------------------------------------------
    def _put(self, m, col, emissive=None):
        self.rgb[m] = col[m] if np.ndim(col) == 3 else col
        self.a[m] = 1.0
        if emissive is not None:
            self.emi[m] = emissive[m] if np.ndim(emissive) == 3 else emissive
        else:
            self.emi[m] = 0

    def shade(self, base, nx, ny, amb=0.55, k=0.6, rim=0.0):
        """Painted lighting: light from upper-left-front."""
        L = np.array([-0.5, -0.6, 0.62])
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        dif = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        s = amb + k * dif + rim * (1 - nz) ** 3
        return hexrgb(base)[None, None, :] * s[..., None] if isinstance(base, str) else base * s[..., None]

    def ellipse(self, cx, cy, rx, ry, base, amb=0.55, k=0.6, emissive=None, flat=False, rot=0.0):
        dx, dy = self.xx - cx, self.yy - cy
        if rot:
            c, s = np.cos(rot), np.sin(rot)
            dx, dy = dx * c + dy * s, -dx * s + dy * c
        nx, ny = dx / rx, dy / ry
        m = nx * nx + ny * ny <= 1.0
        col = hexrgb(base) * np.ones((self.h, self.w, 1)) if flat else self.shade(base, nx * 0.95, ny * 0.95, amb, k)
        self._put(m, col, None if emissive is None else hexrgb(emissive))
        return m

    def capsule(self, x0, y0, x1, y1, r0, base, r1=None, amb=0.55, k=0.6, emissive=None):
        r1 = r0 if r1 is None else r1
        dx, dy = x1 - x0, y1 - y0
        L2 = max(dx * dx + dy * dy, 1e-6)
        t = np.clip(((self.xx - x0) * dx + (self.yy - y0) * dy) / L2, 0, 1)
        px, py = x0 + t * dx, y0 + t * dy
        r = r0 + (r1 - r0) * t
        ex, ey = (self.xx - px) / r, (self.yy - py) / r
        m = ex * ex + ey * ey <= 1.0
        col = self.shade(base, ex * 0.9, ey * 0.9, amb, k)
        self._put(m, col, None if emissive is None else hexrgb(emissive))
        return m

    def poly(self, pts, base, amb=0.8, k=0.0, emissive=None, grad=None):
        pts = np.array(pts, np.float32)
        n = len(pts)
        inside = np.zeros((self.h, self.w), bool)
        x, y = self.xx, self.yy
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]; xj, yj = pts[j]
            cond = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
            inside ^= cond
            j = i
        col = hexrgb(base)[None, None, :] * np.ones((self.h, self.w, 1)) * amb
        if grad is not None:
            # grad = (gx, gy, strength): linear painted light across the polygon
            gx, gy, st = grad
            cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
            span = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]), 1)
            g = ((x - cx) * gx + (y - cy) * gy) / span
            col = col * (1 - st * g)[..., None]
        self._put(inside, col, None if emissive is None else hexrgb(emissive))
        return inside

    def rect(self, x0, y0, x1, y1, base, amb=1.0, emissive=None):
        m = (self.xx >= x0) & (self.xx < x1) & (self.yy >= y0) & (self.yy < y1)
        self._put(m, hexrgb(base)[None, None, :] * np.ones((self.h, self.w, 1)) * amb, None if emissive is None else hexrgb(emissive))
        return m

    def line(self, x0, y0, x1, y1, w, base, emissive=None):
        return self.capsule(x0, y0, x1, y1, w / 2, base, amb=1.0, k=0.0, emissive=emissive)

    def glow(self, cx, cy, r, col, strength=1.0):
        g = np.exp(-((self.xx - cx) ** 2 + (self.yy - cy) ** 2) / (r * r))
        self.emi += hexrgb(col)[None, None, :] * (g * strength)[..., None]

    def darken(self, m, f):
        self.rgb[m] *= f

    def flip(self):
        c = Canvas(self.w, self.h)
        c.rgb = self.rgb[:, ::-1].copy(); c.a = self.a[:, ::-1].copy(); c.emi = self.emi[:, ::-1].copy()
        return c
