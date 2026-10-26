"""
Generates assets/moon-wash.webp: translucent silver watercolour washes that
bloom around the moon when it is touched.

What makes it read as watercolour rather than smoke or a glow:
  * irregular, crisp-ish edges (pigment stops where the water stopped),
  * pigment pooled at the edges of each wash ("edge darkening" — here,
    because the pigment is pale on a dark page, the edges are brighter),
  * a tide line inside some washes (a second, drier front),
  * uneven density and fine granulation inside.

The image is square; the moon sits in the middle with a radius of
SIZE / (2 * SPREAD).  It is placed *behind* the moon photo, so the washes are
only visible around the disc and never cover the craters.

Usage:  python3 tools/make_wash.py assets/moon-wash.webp
"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = sys.argv[1] if len(sys.argv) > 1 else "moon-wash.webp"
SIZE = 900
SPREAD = 1.7          # wash element = 1.7 x the moon's diameter (matches CSS)
R = SIZE / (2 * SPREAD)
rng = np.random.default_rng(1026)

yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
cx = cy = SIZE / 2


def fbm(octaves, base, persistence=0.5):
    """Smooth fractal noise in [-1, 1] (sum of upscaled random grids)."""
    out = np.zeros((SIZE, SIZE), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = int(base * 2 ** o) + 2
        grid = rng.standard_normal((n, n)).astype(np.float32)
        up = ndimage.zoom(grid, SIZE / n, order=3)[:SIZE, :SIZE]
        out += amp * up
        total += amp
        amp *= persistence
    out /= total
    return out / (np.abs(out).max() + 1e-6)


warp_x = fbm(4, 3)
warp_y = fbm(4, 3)
# fine warp: the small irregularities of an edge where water met dry paper
fine_x = fbm(3, 14)
fine_y = fbm(3, 14)
density = fbm(4, 4)
grain = fbm(2, 160, 0.6)


def wash(cxp, cyp, radius, wobble, warp, edge_px, tide=None):
    """Alpha field (0..1) of a single wash."""
    wx = xx + warp_x * warp + fine_x * R * 0.035
    wy = yy + warp_y * warp + fine_y * R * 0.035
    dx, dy = wx - cxp, wy - cyp
    ang = np.arctan2(dy, dx)
    k = rng.uniform(0, 2 * np.pi, 3)
    shape = (1
             + wobble * 0.55 * np.sin(2 * ang + k[0])
             + wobble * 0.30 * np.sin(3 * ang + k[1])
             + wobble * 0.15 * np.sin(5 * ang + k[2]))
    f = np.sqrt(dx * dx + dy * dy) / (radius * shape)
    inside = f < 1.0
    # distance from the edge, inwards (px)
    dist = ndimage.distance_transform_edt(inside).astype(np.float32)
    # soft but defined edge (2 px antialias)
    cover = np.clip(dist / 2.0, 0, 1)
    pooled = 0.42 + 0.95 * np.exp(-dist / edge_px)
    a = cover * pooled
    if tide is not None:
        # a second, drier front inside the wash
        inner = f < tide
        d2 = ndimage.distance_transform_edt(~inner).astype(np.float32)
        a = a * (0.78 + 0.22 * inner) + 0.35 * np.exp(-d2 / 2.2) * cover * (~inner)
    return a


layers = []
# one broad, faint wash under everything (the paper got wet first)
layers.append((wash(cx + R * 0.04, cy - R * 0.03, R * 1.30, 0.10, R * 0.30, 14), 0.08))
# smaller washes leaning out around the disc, uneven on purpose
for ang_deg, dist_r, rad_r, amt in [
    (212, 1.02, 0.58, 0.24),
    (328, 1.00, 0.48, 0.21),
    (118, 1.10, 0.40, 0.19),
    (42, 1.12, 0.30, 0.18),
]:
    a = np.deg2rad(ang_deg)
    layers.append((
        wash(cx + np.cos(a) * R * dist_r, cy + np.sin(a) * R * dist_r,
             R * rad_r * 1.3, rng.uniform(0.10, 0.18), R * 0.22, rng.uniform(5, 9),
             tide=rng.uniform(0.72, 0.86) if rng.random() < 0.7 else None),
        amt,
    ))

alpha = np.zeros((SIZE, SIZE), np.float32)
for a, amt in layers:
    a = a * amt * (0.55 + 0.6 * density) * (0.78 + 0.22 * grain)
    alpha = 1 - (1 - alpha) * (1 - np.clip(a, 0, 1))

# fade out towards the square's edges so the element never shows a border
r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (SIZE / 2)
alpha *= np.clip((1.0 - r) / 0.12, 0, 1)

# cool silver pigment, a little greyer where it is thin
tone = 0.86 + 0.14 * np.clip(alpha / max(alpha.max(), 1e-6), 0, 1)
rgb = np.stack([226 * tone, 231 * tone, 239 * tone], -1)
img = np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8)
Image.fromarray(img, "RGBA").save(OUT, "WEBP", quality=82, alpha_quality=80, method=6)
print("saved", OUT, "max alpha", float(alpha.max()))
