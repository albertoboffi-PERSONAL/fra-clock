import numpy as np, sys, json
from PIL import Image, ImageOps, ImageFilter
PX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
W_MM, H_MM = 170 - 1.2, 158 - 1.2          # FOTO zone 170x158 minus 0.6 mm inset per side
nx, ny = int(W_MM / PX), int(H_MM / PX)
SRC = sys.argv[2] if len(sys.argv) > 2 else "art/source/foto.jpeg"   # run from repo root
im = Image.open(SRC).convert("L")
w, h = im.size
ch = round(w * ny / nx)                     # crop height for full width
y0 = 190                                    # keeps the top head (hair starts ~y=218)
crop = im.crop((0, y0, w, y0 + ch))
g = crop.resize((nx, ny), Image.LANCZOS)
g = ImageOps.autocontrast(g, cutoff=1)
g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
a = np.asarray(g, dtype=np.float32) / 255.0
a = a ** 1.1
# Floyd-Steinberg (serpentine)
out = np.zeros_like(a, dtype=np.uint8)
e = a.copy()
for y in range(ny):
    rng = range(nx) if y % 2 == 0 else range(nx - 1, -1, -1)
    d = 1 if y % 2 == 0 else -1
    for x in rng:
        old = e[y, x]; new = 1.0 if old >= 0.5 else 0.0
        out[y, x] = int(new); err = old - new
        if 0 <= x + d < nx: e[y, x + d] += err * 7 / 16
        if y + 1 < ny:
            if 0 <= x - d < nx: e[y + 1, x - d] += err * 3 / 16
            e[y + 1, x] += err * 5 / 16
            if 0 <= x + d < nx: e[y + 1, x + d] += err * 1 / 16
Image.fromarray(out * 255).save("art_%s.png" % PX)
# rectangles: horizontal runs then merge identical runs vertically
runs = {}
rects = []
active = {}
for y in range(ny):
    row = out[y]; cur = {}
    x = 0
    while x < nx:
        if row[x]:
            s = x
            while x < nx and row[x]: x += 1
            cur[(s, x)] = True
        else:
            x += 1
    new_active = {}
    for k in cur:
        if k in active: new_active[k] = active[k]
        else: new_active[k] = y
    for k, ys in active.items():
        if k not in cur: rects.append((k[0], ys, k[1], y))
    active = new_active
for k, ys in active.items(): rects.append((k[0], ys, k[1], ny))
print("px", PX, "grid", nx, ny, "copper %.1f%%" % (100 * out.mean()), "rects", len(rects), "crop", (0, y0, w, y0 + ch))
json.dump(dict(px=PX, nx=nx, ny=ny, rects=rects), open("rects_%s.json" % PX, "w"))
