import json, sys, time
import numpy as np
from model import Board, T, V, RES
from conn import connectivity
A = json.load(open("critical.json")); F = json.load(open(sys.argv[1]))
b = Board("geom0.json"); b.add(A + F); b.build_raster()
def box(*rs):
    m = np.zeros((b.ny, b.nx), bool)
    for x0, y0, x1, y1 in rs: m[int(y0 / RES):int(np.ceil(y1 / RES)) + 1, int(x0 / RES):int(np.ceil(x1 / RES)) + 1] = True
    return m
BLK = {"B.Cu": box((0, 13, 13, 142.0), (0, 148.3, 13, 288.6), (201.5, 13, 210, 143.0), (201.5, 145.2, 210, 288.6), (0, 0, 101.8, 13),
                   (104.8, 0, 210, 13), (0, 288.6, 111.2, 297), (113.0, 288.6, 210, 297), (29.0, 252.0, 49.0, 273.3), (37.0, 221.0, 41.0, 252.0), (78.5, 270.0, 81.0, 279.0), (99.8, 282.0, 110.2, 294.0), (95.5, 277.9, 113.6, 281.0)),
       "F.Cu": box((55, 14, 155, 59), (55, 225, 155, 270), (31.0, 255.3, 46.5, 273.2), (78.6, 278.5, 81.45, 287.6), (178.6, 262.4, 181.4, 272.2))}
jobs = json.load(open(sys.argv[2]))
new = []
for net, pts in jobs:
    t = time.time(); r = []
    for s, d in zip(pts, pts[1:]):
        pref = d[3] if len(d) > 3 else "B.Cu"
        rr = b.route(net, tuple(s[:3]), tuple(d[:3]), w=0.25, prefer=pref, other_pen=float(__import__("os").environ.get("OPEN","1.6")), via_cost=8.0, soft_pen=1.0, extra_block=BLK, margin=0.1)
        for x in rr: x["tag"] = "fix"
        b.add(rr); b.build_raster(); r += rr
    print(net, len(r), "items, vias", sum(1 for x in r if x["type"] == "via"), "%.1fs" % (time.time() - t))
    new += r
v = b.check(new, verbose=True); print("viol", len(v))
json.dump(new, open(sys.argv[3], "w"), indent=0)
