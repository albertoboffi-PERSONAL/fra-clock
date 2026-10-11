import json, numpy as np
from shapely.geometry import Polygon, Point
from model import Board, V
B = json.load(open("phaseB.json"))
B = [i for i in B if not (i["type"] == "via" and i["net"] == "/AMP_SHDN" and abs(i["x"] - 184.75) < 0.05 and abs(i["y"] - 235.2) < 0.05)]
A = json.load(open("critical.json"))
b = Board("geom0.json"); b.add(A + B); b.build_raster()
F = json.load(open("fill_B.json"))
polys = [Polygon([(x - 50, y - 50) for x, y in f["outline"]], [[(x - 50, y - 50) for x, y in h] for h in f["holes"] if len(h) > 2]) for f in F]
main = max(polys, key=lambda p: p.area)
src = (174.25, 244.44)
cands = []
for x in np.arange(170, 186, 0.2):
    for y in np.arange(236, 256, 0.2):
        if main.buffer(-0.6).contains(Point(x, y)):
            cands.append((Point(x, y).distance(Point(*src)), round(x, 2), round(y, 2)))
cands.sort()
done = None
for d, x, y in cands[:60]:
    v = V("GND", x, y, tag="gnd_u102_main_v")
    if b.check([v], verbose=False): continue
    try:
        r = b.route("GND", (src[0], src[1], "F.Cu"), (x, y, "F.Cu"), w=0.25, layers=("F.Cu",), prefer="F.Cu", margin=0.1)
    except RuntimeError:
        continue
    for i in r: i["tag"] = "gnd_u102_main"
    if not b.check(r + [v], verbose=False):
        done = r + [v]; print("via", x, y, "len items", len(r)); break
assert done
G = json.load(open("gndfix_extra.json")) if False else []
B += done
b2 = Board("geom0.json"); b2.add(A + B); print("viol", len(b2.check(B, verbose=True)))
json.dump(B, open("phaseB.json", "w"), indent=0)
print(len(B))
