"""
Generates the oil-pastel rose shown under the final declaration (SVG markup).

How it works
------------
* The drawing lives in a 100 x 240 box.  Each petal and leaf is described by
  two edges (cubic Béziers); the area between them is filled the way a
  pastel stick fills it — with overlapping strokes that run along the form, in two or three shades.  A few accent lines go on top.
* Every stroke gets a seeded random wobble in position, width and opacity,
  so no two strokes are identical (but the drawing is the same every build).
* Each stroke carries its own start time (--d) and duration (--t); the CSS
  draws them with stroke-dashoffset in order: stem, leaves, petals.
* The paper-tooth texture (gaps where the pastel skips over the grain) and
  the ragged edges are added in the browser by the SVG filter #rose-pastel.

Usage:
    python3 tools/make_rose.py > rose.html      # then paste into index.html
"""
import math
import random

rnd = random.Random(20261026)

# Palette: dusty, desaturated. Rose = antique pink; foliage = grey sage.
ROSE_DEEP = "#7a4752"
ROSE_MID = "#9e6871"
ROSE_SOFT = "#b98790"
ROSE_LIGHT = "#d6b0b5"
ROSE_HIGHLIGHT = "#ecd3d7"  # the catch-light on the topmost curled edges
SAGE_DEEP = "#59655c"
SAGE = "#77857b"
SAGE_LIGHT = "#9eaa9f"


def bez(p, t):
    """Point on a cubic Bézier given as 4 (x, y) tuples."""
    u = 1 - t
    return (
        u**3 * p[0][0] + 3 * u * u * t * p[1][0] + 3 * u * t * t * p[2][0] + t**3 * p[3][0],
        u**3 * p[0][1] + 3 * u * u * t * p[1][1] + 3 * u * t * t * p[2][1] + t**3 * p[3][1],
    )


def fmt(*pts):
    return " ".join(f"{x:.1f} {y:.1f}" for x, y in pts)


strokes = []  # (layer, d, colour, width, opacity, delay, duration)


def line(layer, d, colour, width, delay, dur, opacity=0.92):
    strokes.append((layer, d, colour, width, opacity, delay, dur))


def hatch(layer, inner, outer, n, colours, width, start, span, bend=0.0,
          t0=0.0, t1=1.0, reach=(0.05, 0.95), each=0.18):
    """Fill the region between two edges with n contour strokes.

    Each stroke runs *along* the form (like the rim of a petal or the length
    of a leaf), at a fraction s between the inner and the outer edge, and
    covers a slightly random part of it — the way a pastel stick is laid
    down in overlapping, curved passes.

    inner, outer : the two edges (cubic Béziers), drawn in the same direction
    reach        : range of s (0 = inner edge, 1 = outer edge) to fill
    t0, t1       : the part of the edges' length the strokes may cover
    start, span  : when the first stroke starts and how long the whole field
                   takes to draw (seconds, relative to the rose start)
    bend         : unused, kept for call compatibility
    """
    for i in range(n):
        s = reach[0] + (reach[1] - reach[0]) * (i + rnd.uniform(0.2, 0.8)) / n
        ta = t0 + rnd.uniform(0.0, 0.16) * (t1 - t0)
        tb = t1 - rnd.uniform(0.0, 0.16) * (t1 - t0)
        pts = []
        for j in range(9):
            t = ta + (tb - ta) * j / 8
            a, b = bez(inner, t), bez(outer, t)
            pts.append((a[0] + (b[0] - a[0]) * s + rnd.uniform(-0.25, 0.25),
                        a[1] + (b[1] - a[1]) * s + rnd.uniform(-0.25, 0.25)))
        d = "M" + fmt(pts[0]) + " L" + " ".join(fmt(p) for p in pts[1:])
        colour = rnd.choice(colours)
        w = width * rnd.uniform(0.8, 1.15)
        op = rnd.uniform(0.72, 0.95)
        delay = start + span * i / max(1, n)
        line(layer, d, colour, w, delay, each, op)


# ---------------------------------------------------------------- stem ----
line("stem", "M47 229 C52 186, 47 140, 50.5 76", SAGE, 2.1, 0.00, 1.10)
line("stem", "M48.3 225 C52.6 184, 48.5 140, 51.5 80", SAGE_LIGHT, 1.1, 0.35, 1.00, 0.7)
line("stem", "M49.6 196 C46.6 194.6, 44.6 192.6, 43.5 189.6", SAGE_DEEP, 1.4, 0.75, 0.25)
line("stem", "M50.6 150 C53.5 148.3, 55.3 146.3, 56.3 143.3", SAGE_DEEP, 1.4, 0.85, 0.25)
# sepals, the green star under the bloom
line("stem", "M50.5 75 C45 75.5, 40.5 78.5, 36.8 83.5", SAGE, 2.0, 0.95, 0.35)
line("stem", "M50.5 75 C56 75.5, 60.5 78, 64.2 83", SAGE, 2.0, 1.00, 0.35)
line("stem", "M50.5 75.5 C49.6 79.5, 47.4 82.5, 44.2 84.8", SAGE_DEEP, 1.6, 1.05, 0.30)

# -------------------------------------------------------------- leaves ----
# left leaf: the two halves filled with hatching, then edge and midrib
LL_MID = [(49.8, 128), (41, 124), (30, 120.5), (19, 119.5)]
LL_TOP = [(49.8, 128), (41, 117.5), (30, 114.5), (19, 119.5)]
LL_BOT = [(49.8, 128), (41, 133), (29, 130.5), (19, 119.5)]
hatch("leaf", LL_MID, LL_TOP, 9, [SAGE_LIGHT, SAGE], 2.1, 1.15, 0.40, bend=0.8, t0=0.06, t1=0.94)
hatch("leaf", LL_MID, LL_BOT, 9, [SAGE, SAGE_DEEP], 2.1, 1.35, 0.40, bend=-0.8, t0=0.06, t1=0.94)
line("leaf", "M49.8 128 C41 117.5, 30 114.5, 19 119.5", SAGE_DEEP, 0.9, 1.55, 0.35, 0.8)
line("leaf", "M48.8 127.4 C41 124, 30 120.5, 21 119.8", SAGE_DEEP, 0.8, 1.60, 0.30, 0.8)

RL_MID = [(50.4, 168), (59, 162.5), (70, 157.5), (81, 155)]
RL_TOP = [(50.4, 168), (58.5, 156.5), (69.5, 151.5), (81, 155)]
RL_BOT = [(50.4, 168), (60, 171.5), (72, 167), (81, 155)]
hatch("leaf", RL_MID, RL_TOP, 9, [SAGE_LIGHT, SAGE], 2.1, 1.45, 0.40, bend=-0.8, t0=0.06, t1=0.94)
hatch("leaf", RL_MID, RL_BOT, 9, [SAGE, SAGE_DEEP], 2.1, 1.65, 0.40, bend=0.8, t0=0.06, t1=0.94)
line("leaf", "M50.4 168 C60 171.5, 72 167, 81 155", SAGE_DEEP, 0.9, 1.85, 0.35, 0.8)
line("leaf", "M51.4 167 C59 162.5, 70 157.5, 79 155.4", SAGE_DEEP, 0.8, 1.90, 0.30, 0.8)

# -------------------------------------------------------------- petals ----
# Light falls from the upper left: left petals lighter, right petals deeper.
T = 2.05  # petals begin

# back petal (top), seen over the heart
hatch("bloom", [(37, 45), (41.5, 37), (58.5, 37), (63, 45)],
               [(28, 41), (33, 22.5), (67, 22.5), (72, 41)],
      16, [ROSE_MID, ROSE_SOFT], 2.9, T, 0.45, reach=(0.0, 1.0))
# left outer petal
hatch("bloom", [(37, 46), (34, 52), (37, 60), (44, 66)],
               [(28, 41), (17.5, 48), (21.5, 65), (38, 73)],
      13, [ROSE_SOFT, ROSE_LIGHT, ROSE_MID], 2.9, T + 0.40, 0.40, bend=-1.4)
# right outer petal
hatch("bloom", [(63, 46), (66, 52), (63, 60), (56, 66)],
               [(72, 41), (82.5, 48), (78.5, 65), (62, 73)],
      13, [ROSE_MID, ROSE_DEEP], 2.9, T + 0.72, 0.40, bend=1.4)
# inner-top petal: bridges the heart and the back petal, so the bloom reads
# as a full layered rose rather than a ring with a hollow centre
hatch("bloom", [(40, 46), (43.5, 40), (56.5, 40), (60, 46)],
               [(35, 43.5), (39, 31), (61, 31), (65, 43.5)],
      12, [ROSE_MID, ROSE_SOFT], 2.5, T + 0.18, 0.38, reach=(0.0, 1.0))
# the heart: deepest colour, a little lighter where the petals curl over
hatch("bloom", [(39, 45.5), (43, 39), (57, 39), (61, 45.5)],
               [(39, 50.5), (44, 57.5), (56, 57.5), (61, 50.5)],
      14, [ROSE_DEEP, ROSE_DEEP, ROSE_MID], 2.5, T + 1.05, 0.30, reach=(0.0, 1.0), each=0.14)
# front petal, cupping everything
hatch("bloom", [(34, 53), (42, 59.5), (58, 59.5), (66, 53)],
               [(38, 71), (44, 77.5), (56, 77.5), (62, 71)],
      15, [ROSE_SOFT, ROSE_MID, ROSE_SOFT], 3.0, T + 1.30, 0.45, bend=0.8)

# accents: the spiral of the heart, the lit lip, a few defining edges
A = T + 1.80
line("bloom", "M44.5 47 C46.5 42, 54.6 41.6, 55.6 46.4 C56 49.6, 50.6 51.2, 48.8 48.2", ROSE_SOFT, 1.2, A, 0.35, 0.85)
line("bloom", "M41.5 50.8 C44 55.2, 55.5 55.6, 58.6 49.6", ROSE_DEEP, 1.1, A + 0.15, 0.30, 0.85)
line("bloom", "M31.5 54.5 C38 60.8, 61 61.4, 69 53.6", ROSE_LIGHT, 1.7, A + 0.25, 0.40)
line("bloom", "M28.4 41.5 C33.5 23.5, 66.5 23.5, 71.6 41.5", ROSE_DEEP, 0.9, A + 0.35, 0.40, 0.7)
line("bloom", "M72 41.5 C83 48, 79.5 65.5, 62 73", ROSE_DEEP, 1.0, A + 0.45, 0.30, 0.75)
line("bloom", "M37.5 72.2 C44 78.2, 56 78.2, 62.5 72.2", ROSE_DEEP, 1.0, A + 0.50, 0.25, 0.8)
line("bloom", "M27 43 C24.5 41.5, 23.6 39, 24.4 36.4", ROSE_LIGHT, 1.3, A + 0.55, 0.20, 0.8)
# catch-light: a couple of pale, broken highlights where the curl faces the
# light, the detail that gives the bloom some shine instead of reading flat
line("bloom", "M35.5 25.5 C42 23, 51 22.3, 58.5 23.3", ROSE_HIGHLIGHT, 1.0, A + 0.65, 0.22, 0.6)
line("bloom", "M21.5 49 C20.3 54.5, 21.8 60, 26 65", ROSE_HIGHLIGHT, 0.9, A + 0.72, 0.20, 0.55)


def emit():
    groups = {"stem": [], "leaf": [], "bloom": []}
    for layer, d, colour, w, op, delay, dur in strokes:
        groups[layer].append(
            f'<path pathLength="1" d="{d}" stroke="{colour}" stroke-width="{w:.2f}" '
            f'stroke-opacity="{op:.2f}" style="--d:{delay:.2f};--t:{dur:.2f}"/>'
        )
    names = {"stem": "rose__stem", "leaf": "rose__leaves", "bloom": "rose__bloom"}
    return "\n".join(
        f'<g class="{names[k]}">\n' + "\n".join(groups[k]) + "\n</g>"
        for k in ("stem", "leaf", "bloom")
    )


if __name__ == "__main__":
    print(emit())
