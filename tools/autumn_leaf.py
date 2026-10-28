"""
Procedural dried autumn leaves (no photographs are used).

render_leaf(kind, seed, size) returns an RGBA float image (0..1) of one dried
leaf, lit as if by moonlight, with:
  * a botanical silhouette per species (maple, oak, beech, birch),
  * the vein network of that species (palmate or pinnate), slightly raised,
  * curled, crinkled surface (height map -> normals -> light),
  * dried colouring: mottled base, browner edges, dark spots, small holes,
  * a short petiole.

`back=True` renders the underside: paler, duller, veins more prominent.

Used by tools/make_autumn.py. Only numpy + scipy + Pillow.
"""
import math

import numpy as np
from scipy import ndimage

# dried-leaf palettes (linear-ish RGB 0..1): (base, secondary, edge)
PALETTES = {
    "copper":   ((0.55, 0.27, 0.12), (0.68, 0.40, 0.17), (0.28, 0.13, 0.07)),
    "caramel":  ((0.66, 0.42, 0.18), (0.75, 0.55, 0.26), (0.36, 0.20, 0.09)),
    "wine":     ((0.38, 0.12, 0.11), (0.52, 0.20, 0.14), (0.20, 0.07, 0.06)),
    "gold":     ((0.66, 0.52, 0.20), (0.74, 0.62, 0.30), (0.40, 0.27, 0.10)),
    "umber":    ((0.42, 0.26, 0.14), (0.52, 0.34, 0.18), (0.22, 0.13, 0.07)),
    "rust":     ((0.60, 0.25, 0.10), (0.70, 0.36, 0.14), (0.30, 0.11, 0.05)),
}


def _noise(shape, scale, rng, octaves=4, persistence=0.55):
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = max(2, int(scale * 2 ** o))
        g = rng.standard_normal((n + 2, n + 2)).astype(np.float32)
        up = ndimage.zoom(g, (h / n, w / n), order=3)[:h, :w]
        out += amp * up
        tot += amp
        amp *= persistence
    out /= tot
    return out / (np.abs(out).max() + 1e-6)


def _seg_dist(px, py, ax, ay, bx, by):
    """distance from points to segment ab, and position t along it"""
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy + 1e-9
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / L2, 0, 1)
    dx, dy = px - (ax + t * vx), py - (ay + t * vy)
    return np.sqrt(dx * dx + dy * dy), t


def _polyline(points):
    return list(zip(points[:-1], points[1:]))


def _curve(a, b, bend, n=6):
    """a slightly bent polyline from a to b (a vein is never straight)"""
    (ax, ay), (bx, by) = a, b
    nx, ny = -(by - ay), (bx - ax)
    pts = []
    for i in range(n + 1):
        t = i / n
        k = bend * math.sin(math.pi * t)
        pts.append((ax + (bx - ax) * t + nx * k, ay + (by - ay) * t + ny * k))
    return pts


# --------------------------------------------------------------- shapes ----
def _shape_maple(U, V, rng):
    # polar around the point where the petiole meets the blade
    bx, by = 0.0, -0.30
    dx, dy = U - bx, V - by
    rho = np.sqrt(dx * dx + dy * dy)
    th = np.arctan2(dx, dy)                      # 0 = up
    # five broad, pointed lobes with shallow sinuses and toothed sides
    lobes = [(0.0, 1.02, 0.50), (0.95, 0.92, 0.48), (-0.95, 0.92, 0.48),
             (1.95, 0.55, 0.45), (-1.95, 0.55, 0.45)]
    R = np.zeros_like(rho)
    tips = []
    for ang, L, wdt in lobes:
        ang += rng.uniform(-0.05, 0.05)
        L *= rng.uniform(0.94, 1.05)
        d = np.abs(np.angle(np.exp(1j * (th - ang))))
        t = d / wdt
        lobe = 0.30 + (L - 0.30) * np.clip(1 - t, 0, None) ** 1.6
        teeth = 0.05 * L * np.clip(np.cos(t * 9.0), 0, None) ** 4 * (t < 1)
        R = np.maximum(R, lobe + teeth)
        tips.append((bx + math.sin(ang) * L * 0.95, by + math.cos(ang) * L * 0.95))
    R = np.maximum(R, 0.30)
    # the notch where the petiole joins
    R = R * (1 - 0.35 * np.exp(-((np.abs(th) - math.pi) / 0.35) ** 2))
    inside = rho < R
    veins = []
    for tip in tips:
        pts = _curve((bx, by), tip, rng.uniform(-0.05, 0.05))
        veins.append((pts, 0.022))
        # secondaries
        for f in (0.35, 0.55, 0.72):
            ax = bx + (tip[0] - bx) * f
            ay = by + (tip[1] - by) * f
            ang = math.atan2(tip[0] - bx, tip[1] - by)
            for side in (-1, 1):
                a2 = ang + side * rng.uniform(0.55, 0.85)
                L2 = 0.28 * (1.15 - f)
                veins.append((_curve((ax, ay), (ax + math.sin(a2) * L2, ay + math.cos(a2) * L2),
                                     rng.uniform(-0.1, 0.1), 4), 0.010))
    return inside, veins, (bx, by)


def _shape_pinnate(U, V, rng, kind):
    s = (V + 0.92) / 1.84                         # 0 at base, 1 at tip
    s_c = np.clip(s, 1e-6, 1)
    if kind == "oak":
        prof = np.sin(np.pi * s_c ** 0.85) ** 0.8 * 0.62
        n_lobes = rng.integers(4, 6)
        phase_l, phase_r = rng.uniform(0, 1), rng.uniform(0, 1)
        lob_l = 0.42 + 0.58 * np.abs(np.sin(np.pi * (n_lobes * s_c + phase_l))) ** 0.55
        lob_r = 0.42 + 0.58 * np.abs(np.sin(np.pi * (n_lobes * s_c + phase_r))) ** 0.55
        teeth = 0.0
    elif kind == "beech":
        prof = np.sin(np.pi * s_c ** 0.75) ** 1.0 * 0.50
        lob_l = lob_r = 1.0
        teeth = 0.018 * np.abs(np.sin(np.pi * 9 * s_c))
    else:  # birch: broad base, pointed tip, double-serrate
        prof = (np.sin(np.pi * s_c ** 0.62) ** 1.1) * 0.56
        lob_l = lob_r = 1.0
        teeth = 0.03 * np.abs(np.sin(np.pi * 14 * s_c)) ** 2 + 0.012 * np.abs(np.sin(np.pi * 28 * s_c))
    bend = 0.05 * np.sin(np.pi * s_c) * rng.uniform(-1, 1)    # slightly curved midrib
    X = U - bend
    w_l = prof * lob_l + teeth
    w_r = prof * lob_r * rng.uniform(0.92, 1.0) + teeth
    inside = (s > 0) & (s < 1) & (((X < 0) & (-X < w_l)) | ((X >= 0) & (X < w_r)))
    veins = [(_curve((0, -0.92), (0.0, 0.92), rng.uniform(-0.03, 0.03), 8), 0.024)]
    n_lat = {"oak": 5, "beech": 8, "birch": 7}[kind]
    for i in range(n_lat):
        f = 0.12 + 0.78 * (i + 0.5) / n_lat
        y0 = -0.92 + 1.84 * f
        for side in (-1, 1):
            reach = float(np.interp(f, np.linspace(0, 1, 50),
                                    np.sin(np.pi * np.linspace(0, 1, 50) ** 0.8) ** 0.8)) * 0.6
            ang = math.radians(rng.uniform(48, 62))
            x1 = side * reach * 0.95
            y1 = y0 + reach * math.cos(ang) * 0.9
            veins.append((_curve((0, y0), (x1, y1), side * rng.uniform(0.04, 0.12), 5), 0.011))
    return inside, veins, (0.0, -0.92)


# --------------------------------------------------------------- render ----
def render_leaf(kind, seed, size=160, palette=None, back=False, ss=3):
    rng = np.random.default_rng(seed)
    N = size * ss
    ys, xs = np.mgrid[0:N, 0:N].astype(np.float32)
    U = (xs + 0.5) / N * 2.3 - 1.15
    V = 1.12 - (ys + 0.5) / N * 2.3              # y up, slight margin

    if kind == "maple":
        inside, veins, base = _shape_maple(U, V, rng)
    else:
        inside, veins, base = _shape_pinnate(U, V, rng, kind)

    # ragged margin: erode with noise (dried leaves are torn and nibbled)
    rag = _noise((N, N), 18, rng, 3)
    dist_in = ndimage.distance_transform_edt(inside) / N * 2.3
    inside = inside & (dist_in > 0.012 * (rag + 1.0))
    # a few holes and torn bites
    for _ in range(rng.integers(0, 4)):
        hx, hy = rng.uniform(-0.45, 0.45), rng.uniform(-0.4, 0.7)
        hr = rng.uniform(0.02, 0.06)
        inside &= ((U - hx) ** 2 + (V - hy) ** 2) > hr ** 2 * (1 + 0.5 * rag) ** 2
    dist_in = ndimage.distance_transform_edt(inside) / N * 2.3

    # vein field
    vein = np.zeros((N, N), np.float32)
    for pts, width in veins:
        for (ax, ay), (bx, by) in _polyline(pts):
            d, t = _seg_dist(U, V, ax, ay, bx, by)
            w = width * (1.0 - 0.45 * t)
            vein = np.maximum(vein, np.clip(1 - d / w, 0, 1))
    # tertiary network (fine reticulation)
    net = np.abs(_noise((N, N), 26, rng, 2))
    reticul = np.clip(1 - net / 0.08, 0, 1) * 0.35

    # petiole
    px0, py0 = base
    d_pet, t_pet = _seg_dist(U, V, px0, py0, px0 + rng.uniform(-0.08, 0.08), -1.10)
    petiole = d_pet < 0.022 * (1 - 0.4 * t_pet)

    # ---- surface height: curl + crinkle + raised veins
    curl_k = rng.uniform(0.25, 0.55)
    tip_curl = rng.uniform(-0.3, 0.3)
    H = (-curl_k * np.abs(U) ** 1.4 + tip_curl * np.clip(V, 0, None) ** 2
         + 0.06 * _noise((N, N), 5, rng, 4)
         + 0.010 * vein + 0.004 * reticul
         - 0.05 * np.exp(-dist_in / 0.05))                  # edges curl down
    gy, gx = np.gradient(H, 2.3 / N)
    nz = 1.0 / np.sqrt(1 + gx * gx + gy * gy)
    nx, ny = -gx * nz, gy * nz
    L = np.array([-0.45, 0.55, 0.70]); L /= np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    shade = 0.38 + 0.75 * lam

    # ---- colour
    pal = PALETTES[palette or rng.choice(list(PALETTES))]
    c_base, c_sec, c_edge = (np.array(c) for c in pal)
    mott = 0.5 + 0.5 * _noise((N, N), 4, rng, 4)
    col = c_base[None, None] * (1 - mott[..., None]) + c_sec[None, None] * mott[..., None]
    # brown, dry edges
    edge = np.exp(-dist_in / rng.uniform(0.05, 0.12))
    col = col * (1 - edge[..., None] * 0.85) + c_edge[None, None] * edge[..., None] * 0.85
    # dark spots
    spots = np.clip((_noise((N, N), 9, rng, 2) - 0.55) / 0.25, 0, 1)
    col *= (1 - 0.55 * spots[..., None])
    # veins: paler on top
    vcol = np.minimum(1, c_sec * 1.25 + 0.05)
    col = col * (1 - vein[..., None] * 0.55) + vcol[None, None] * vein[..., None] * 0.55
    col *= (1 - 0.18 * reticul[..., None])
    # grain
    col *= (0.92 + 0.08 * _noise((N, N), 60, rng, 1))[..., None]

    if back:
        grey = col.mean(-1, keepdims=True)
        col = 0.55 * col + 0.45 * grey
        col = col * 0.85 + 0.06
        col = col * (1 - vein[..., None] * 0.2) + 0.42 * vein[..., None] * 0.2
        shade = 0.45 + 0.6 * lam

    rgb = col * shade[..., None]
    pet_col = c_edge * 1.1
    rgb = np.where(petiole[..., None], pet_col[None, None] * (0.6 + 0.6 * lam[..., None]), rgb)
    alpha = (inside | petiole).astype(np.float32)

    # downsample with antialias
    rgba = np.dstack([rgb * alpha[..., None], alpha])
    small = rgba.reshape(size, ss, size, ss, 4).mean(axis=(1, 3))
    a = small[..., 3:4]
    small[..., :3] = np.where(a > 1e-4, small[..., :3] / np.maximum(a, 1e-4), 0)
    if back:
        small = small[:, ::-1]
    return np.clip(small, 0, 1)
