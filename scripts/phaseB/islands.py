import json
from shapely.geometry import Polygon, Point
F = json.load(open("fill_B.json")); D = json.load(open("geomB.json"))
polys = []
for f in F:
    p = Polygon(f["outline"], [h for h in f["holes"] if len(h) >= 3]); polys.append(p)
main = max(range(len(polys)), key=lambda i: polys[i].area)
items = [("via", v["x"] - 50, v["y"] - 50, v["grp"]) for v in D["vias"] if v["net"] == "GND"]
items += [("pad %s.%s" % (p["ref"], p["num"]), p["x"] - 50, p["y"] - 50, "") for p in D["pads"] if p["net"] == "GND"]
for i, p in enumerate(polys):
    if i == main: continue
    inside = [it for it in items if p.buffer(0.35).contains(Point(it[1] + 50, it[2] + 50))]
    print("island", i, "area %.1f" % p.area, [(n, round(x, 2), round(y, 2), g) for n, x, y, g in inside])
