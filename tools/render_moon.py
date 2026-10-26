"""
Render a photoreal moon disc from NASA LRO data (CGI Moon Kit derived maps).

Inputs : albedo (LROC WAC mosaic) + tangent normal map (from LOLA elevation),
         equirectangular, near side centred, north up, east to the right.
Output : RGBA PNG of the disc on transparency (supersampled, antialiased).

Shading: Lunar-Lambert (mix of Lommel-Seeliger and Lambert), which is what
makes a real moon look "flat-bright" towards the limb instead of a plastic ball.
"""
# Usage:
#   python3 render_moon.py moon_albedo.jpg moon_normal.png moon.png [size=1200] [phase_deg=24]
# Source maps (2048x1024, public domain, derived from NASA SVS CGI Moon Kit #4720):
#   https://github.com/hadealahmad/kde-moonphase-wallpaper  -> contents/images/
import math, sys
import numpy as np
from PIL import Image, ImageFilter

ALB, NRM, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 1200
PHASE_DEG = float(sys.argv[5]) if len(sys.argv) > 5 else 24.0
SS = 2  # supersampling

alb = np.asarray(Image.open(ALB).convert("L"), np.float32) / 255.0
nrm = np.asarray(Image.open(NRM).convert("RGB"), np.float32) / 255.0 * 2 - 1
H, W = alb.shape

N = SIZE * SS
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
sx = (xx + 0.5) / N * 2 - 1
sy = 1 - (yy + 0.5) / N * 2
r2 = sx * sx + sy * sy
inside = r2 <= 1.0
sz = np.sqrt(np.clip(1 - r2, 0, 1))

# small libration-like tilt so the view isn't perfectly "map centred"
lon_off, lat_off = math.radians(-4.0), math.radians(3.0)
ca, sa = math.cos(lon_off), math.sin(lon_off)
cb, sb = math.cos(lat_off), math.sin(lat_off)

def to_model(x, y, z):
    mx = ca * x - sa * z
    mz = sa * x + ca * z
    my = y
    my2 = cb * my - sb * mz
    mz2 = sb * my + cb * mz
    return mx, my2, mz2

mx, my, mz = to_model(sx, sy, sz)
lon = np.arctan2(mx, mz)
lat = np.arcsin(np.clip(my, -1, 1))
u = 0.5 + lon / (2 * math.pi)
v = 0.5 - lat / math.pi

x = (u * W - 0.5) % W
y = np.clip(v * H - 0.5, 0, H - 1)

def bicubic_weights(t):
    # Catmull-Rom
    t2, t3 = t * t, t * t * t
    return [(-0.5*t3 + t2 - 0.5*t), (1.5*t3 - 2.5*t2 + 1), (-1.5*t3 + 2*t2 + 0.5*t), (0.5*t3 - 0.5*t2)]

def sample(tex):
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    fx, fy = x - x0, y - y0
    wx, wy = bicubic_weights(fx), bicubic_weights(fy)
    acc = 0
    for j in range(4):
        yi = np.clip(y0 + j - 1, 0, H - 1)
        row = 0
        for i in range(4):
            xi = (x0 + i - 1) % W
            t = tex[yi, xi]
            w = wx[i] if tex.ndim == 2 else wx[i][..., None]
            row = row + t * w
        acc = acc + row * (wy[j] if tex.ndim == 2 else wy[j][..., None])
    return acc

A = np.clip(sample(alb), 0, 1)
# expand albedo contrast: the graded mosaic flattens maria vs highlands
A = (A / 0.6) ** 1.4 * 0.6
Nm = sample(nrm)

# tangent frame (model space): east, north, outward
clat, slat = np.cos(lat), np.sin(lat)
clon, slon = np.cos(lon), np.sin(lon)
T = (clon, np.zeros_like(lon), -slon)
B = (-slat * slon, clat, -slat * clon)
G = (clat * slon, slat, clat * clon)
RELIEF = 1.0
px = T[0]*Nm[...,0]*RELIEF + B[0]*Nm[...,1]*RELIEF + G[0]*Nm[...,2]
py = T[1]*Nm[...,0]*RELIEF + B[1]*Nm[...,1]*RELIEF + G[1]*Nm[...,2]
pz = T[2]*Nm[...,0]*RELIEF + B[2]*Nm[...,1]*RELIEF + G[2]*Nm[...,2]
ln = np.sqrt(px*px + py*py + pz*pz) + 1e-6
px, py, pz = px/ln, py/ln, pz/ln

# Sun: from the viewer's left and slightly above (waning gibbous look).
ph = math.radians(PHASE_DEG)
Ls = np.array([-math.sin(ph), 0.10, math.cos(ph)], np.float32)
Ls /= np.linalg.norm(Ls)
Lm = np.array(to_model(*Ls), np.float32)
Vm = np.array(to_model(0.0, 0.0, 1.0), np.float32)

cos_i_geo = G[0]*Lm[0] + G[1]*Lm[1] + G[2]*Lm[2]
cos_i = px*Lm[0] + py*Lm[1] + pz*Lm[2]
cos_e = np.clip(G[0]*Vm[0] + G[1]*Vm[1] + G[2]*Vm[2], 1e-3, 1)

ci = np.clip(cos_i, 0, None)
# smooth terminator (the real one is soft because of relief + finite sun)
term = np.clip((cos_i_geo + 0.035) / 0.07, 0, 1)
term = term * term * (3 - 2 * term)
Lw = 0.62  # Lunar-Lambert weight
ls = 2 * ci / (ci + cos_e + 1e-4)
shade = ((1 - Lw) * ci + Lw * ls) * term
# relief emphasis: modulate by perturbed/geometric ratio (shadows in craters)
rel = np.clip(cos_i, 0, None) / np.clip(cos_i_geo, 0.06, None)
shade = shade * np.clip(0.55 + 0.45 * rel, 0, 1.6)

img = A * shade
# faint earthshine on the night side keeps the outline legible
earth = 0.022 * A * (1 - term) * (0.6 + 0.4 * cos_e)
img = img + earth

# tone map: gentle filmic curve, keep highlights silver not clipped
img = img / np.percentile(img[inside], 99.6)
img = np.clip(img, 0, None)
img = 1 - np.exp(-img * 1.6)
img = img / (1 - math.exp(-1.6)) * 0.97
img = np.clip(img, 0, 1) ** 1.05

# antialiased alpha mask (supersampled)
r = np.sqrt(r2)
alpha = np.clip((1.0 - r) * N / 2 + 0.5, 0, 1)

gray = (img * 255).astype(np.float32)
# cool silver tint: very slightly lift blue in highlights
Rch = gray * 0.985
Gch = gray * 0.995
Bch = np.clip(gray * 1.01 + 1.5, 0, 255)
rgba = np.dstack([Rch, Gch, Bch, alpha * 255]).astype(np.float32)
rgba[~(alpha > 0)] = 0
im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
im = im.resize((SIZE, SIZE), Image.LANCZOS)
# light unsharp to recover crater edges after resampling
rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=1))
out = Image.merge("RGBA", (*rgb.split(), im.split()[3]))
out.save(OUT)
print("saved", OUT, out.size)
