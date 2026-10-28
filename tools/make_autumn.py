"""
Builds the image assets of the autumn experiment (autumn.html):

  assets/autumn/leaves.webp    sprite atlas of falling leaves
                               12 leaves x 4 rows (front sharp, back sharp,
                               front blurred, back blurred), 128 px tiles
  assets/autumn/floor-1.webp   the ground: dark soil + the first, deepest leaves
  assets/autumn/floor-2.webp   more leaves on top
  assets/autumn/floor-3.webp   the last, freshest leaves (brightest, on top)

The three floor layers are stacked in the page and fade in one after the
other as she scrolls, so the ground seems to build up.

Everything is rendered from tools/autumn_leaf.py (no photographs).

Usage:  python3 tools/make_autumn.py            (takes ~2 minutes)
"""
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
from autumn_leaf import render_leaf  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "autumn")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(1028)

LEAVES = [  # (species, palette)
    ("maple", "copper"), ("maple", "wine"), ("maple", "rust"), ("maple", "gold"),
    ("oak", "caramel"), ("oak", "umber"), ("oak", "copper"),
    ("beech", "gold"), ("beech", "copper"), ("beech", "wine"),
    ("birch", "caramel"), ("birch", "rust"),
]


def bleed(rgba):
    """Give transparent pixels the colour of the nearest leaf pixel, so that
    scaling/rotating never produces dark fringes."""
    a = rgba[..., 3]
    _, (iy, ix) = ndimage.distance_transform_edt(a < 0.02, return_indices=True)
    out = rgba.copy()
    out[..., :3] = rgba[iy, ix, :3]
    return out


def blur_rgba(rgba, sigma):
    a = rgba[..., 3:4]
    pm = rgba[..., :3] * a
    pm = np.stack([ndimage.gaussian_filter(pm[..., c], sigma) for c in range(3)], -1)
    a2 = ndimage.gaussian_filter(a[..., 0], sigma)[..., None]
    rgb = np.where(a2 > 1e-4, pm / np.maximum(a2, 1e-4), 0)
    return np.dstack([rgb, a2])


def to_img(rgba):
    return Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


# --------------------------------------------------------------- atlas ----
def build_atlas(T=128):
    print("atlas…")
    atlas = np.zeros((4 * T, len(LEAVES) * T, 4), np.float32)
    for i, (kind, pal) in enumerate(LEAVES):
        front = render_leaf(kind, 500 + i, T, pal, back=False)
        backs = render_leaf(kind, 500 + i, T, pal, back=True)
        for row, tile in enumerate((front, backs, blur_rgba(front, 2.6), blur_rgba(backs, 2.6))):
            atlas[row * T:(row + 1) * T, i * T:(i + 1) * T] = bleed(tile) if row < 2 else tile
    to_img(atlas).save(os.path.join(OUT, "leaves.webp"), "WEBP", quality=84, alpha_quality=90, method=6)


# --------------------------------------------------------------- floor ----
def build_floor(W=1800, H=560, TILE=260):
    print("floor tiles…")
    tiles = []
    for i in range(30):
        kind, pal = LEAVES[i % len(LEAVES)]
        t = render_leaf(kind, 900 + i, TILE, pal, back=(i % 7 == 3))
        tiles.append(bleed(t))

    xs = np.arange(W, dtype=np.float32)
    # where the ground starts (the "top" of the pile): higher in the middle,
    # where the rose stands, falling away to the sides, never a straight line
    xn = (xs - W / 2) / (W / 2)
    top = H * (0.22 + 0.12 * xn ** 2) + H * 0.03 * ndimage.gaussian_filter1d(rng.standard_normal(W), 40) * 6

    def light(x, y):
        """moonlight pooled around the centre, darker at the sides and back"""
        pool = math.exp(-((x - W / 2) / (0.34 * W)) ** 2 - ((y - 0.50 * H) / (0.60 * H)) ** 2)
        return 0.26 + 0.70 * pool

    # leaves, back to front
    items = []
    for _ in range(1500):
        x = rng.uniform(-0.05 * W, 1.05 * W)
        xi = int(np.clip(x, 0, W - 1))
        y0 = top[xi]
        # more leaves towards the front; a few right at the edge of the pile
        y = y0 - 0.02 * H + (H * 1.10 - y0) * rng.random() ** 0.9
        items.append((y, x))
    items.sort()

    layers = [np.zeros((H, W, 4), np.float32) for _ in range(3)]

    def over(dst, src, ox, oy):
        """premultiplied 'over' of src (straight RGBA) into dst at ox, oy"""
        h, w = src.shape[:2]
        x0, y0 = max(0, ox), max(0, oy)
        x1, y1 = min(W, ox + w), min(H, oy + h)
        if x1 <= x0 or y1 <= y0:
            return
        s = src[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        a = s[..., 3:4]
        d = dst[y0:y1, x0:x1]
        d[..., :3] = s[..., :3] * a + d[..., :3] * (1 - a)
        d[..., 3:4] = a + d[..., 3:4] * (1 - a)

    print("floor composite…")
    n = len(items)
    for k, (y, x) in enumerate(items):
        xi = int(np.clip(x, 0, W - 1))
        depth = np.clip((y - top[xi]) / (H - top[xi]), 0, 1.1)   # 0 back, 1 front
        scale = (0.20 + 0.62 * depth) * rng.uniform(0.8, 1.2)
        squash = 0.38 + 0.36 * depth                                # lying flat, seen at an angle
        tile = tiles[rng.integers(len(tiles))]
        img = to_img(tile)
        sz = max(8, int(TILE * scale))
        img = img.resize((sz, max(5, int(sz * rng.uniform(0.85, 1.0)))), Image.LANCZOS)
        img = img.rotate(rng.uniform(0, 360), Image.BICUBIC, expand=True)
        img = img.resize((img.width, max(4, int(img.height * squash))), Image.LANCZOS)
        leaf = np.asarray(img, np.float32) / 255.0
        # depth of field: the farthest and the nearest leaves are softer
        dof = 1.6 * max(0.0, 0.25 - depth) * 4 + 1.4 * max(0.0, depth - 0.92) * 10
        if dof > 0.3:
            leaf = blur_rgba(leaf, dof)
        b = light(x, y) * (0.62 + 0.38 * depth) * rng.uniform(0.75, 1.1)
        leaf[..., :3] *= b
        h, w = leaf.shape[:2]
        ox, oy = int(x - w / 2), int(y - h / 2)
        # which layer: the first 55% of leaves are the ground already there,
        # then 30% more, then the last 15% on top — but sorted by depth so
        # every layer keeps the perspective
        r = rng.random()
        layer = 0 if r < 0.50 else (1 if r < 0.80 else 2)
        dst = layers[layer]
        # contact shadow on everything below it (drawn into this layer)
        sh = ndimage.gaussian_filter(leaf[..., 3], 2.5 + 5 * depth)
        shadow = np.zeros_like(leaf)
        shadow[..., 3] = sh * 0.55
        over(dst, shadow, ox + int(3 + 4 * depth), oy + int(4 + 6 * depth))
        over(dst, leaf, ox, oy)
        if k % 300 == 0:
            print(f"  {k}/{n}")

    # dark, irregular soil under everything (bottom layer only)
    yy = np.arange(H, dtype=np.float32)[:, None]
    soil_a = np.clip((yy - (top[None, :] - 0.02 * H)) / (0.10 * H), 0, 1)
    soil = np.zeros((H, W, 4), np.float32)
    soil[..., 0], soil[..., 1], soil[..., 2] = 0.030, 0.022, 0.018
    soil[..., 3] = soil_a
    base = layers[0]
    a = base[..., 3:4]
    merged = np.empty_like(base)
    merged[..., :3] = base[..., :3] + soil[..., :3] * soil[..., 3:4] * (1 - a)
    merged[..., 3:4] = a + soil[..., 3:4] * (1 - a)
    layers[0] = merged

    # soft transition into the black above the pile
    fade = np.clip((yy - (top[None, :] - 0.10 * H)) / (0.16 * H), 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    for i, L in enumerate(layers):
        L[..., :3] *= fade[..., None]
        L[..., 3:4] *= fade[..., None]
        a = L[..., 3:4]
        rgb = np.where(a > 1e-4, L[..., :3] / np.maximum(a, 1e-4), 0)
        to_img(np.dstack([rgb, a])).save(
            os.path.join(OUT, f"floor-{i + 1}.webp"), "WEBP", quality=80, alpha_quality=80, method=6)
    print("done")


if __name__ == "__main__":
    if "--floor-only" not in sys.argv:
        build_atlas()
    build_floor()
