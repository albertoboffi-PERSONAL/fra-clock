import json
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
D = json.load(open("geomB.json"))
Z = {z["name"]: unary_union([Polygon(o) for o in z["outline"]]) for z in D["zones"] if z["rule"]}
ant = [z for z in Z if z.startswith("fp:")][0]
spk = [box(105, 64, 205, 109), box(105, 275, 205, 320)]
res = {"FOTO_FCu_tracks": 0, "FOTO_vias": 0, "NFC_any": 0, "ANT_any": 0, "SPK_FCu_new": 0, "SPK_vias_new": 0}
for t in D["tracks"]:
    g = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2)
    if t["layer"] == "F.Cu" and g.intersects(Z["FOTO"]): res["FOTO_FCu_tracks"] += 1
    if g.intersects(Z["NFC"]): res["NFC_any"] += 1
    if g.intersects(Z[ant]): res["ANT_any"] += 1
    if t["layer"] == "F.Cu" and t["grp"] != "RING_AUTO" and any(g.intersects(s) for s in spk): res["SPK_FCu_new"] += 1
for v in D["vias"]:
    g = Point(v["x"], v["y"]).buffer(v["d"] / 2)
    if g.intersects(Z["FOTO"]): res["FOTO_vias"] += 1
    if g.intersects(Z["NFC"]): res["NFC_any"] += 1
    if g.intersects(Z[ant]): res["ANT_any"] += 1
    if v["grp"] != "RING_AUTO" and any(g.intersects(s) for s in spk): res["SPK_vias_new"] += 1
# minimum distance of F.Cu new copper from FOTO edge (info)
dmin = min(LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2).distance(Z["FOTO"]) for t in D["tracks"] if t["layer"] == "F.Cu" and t["grp"] != "RING_AUTO")
res["min_gap_FCu_to_FOTO_mm"] = round(dmin, 3)
import collections
c = collections.Counter((t["grp"], t["layer"]) for t in D["tracks"]); res["tracks_by_group_layer"] = {"%s|%s" % k: v for k, v in c.items()}
c = collections.Counter(v["grp"] for v in D["vias"]); res["vias_by_group"] = dict(c)
print(json.dumps(res, indent=1))
json.dump(res, open("keepcheck_B.json", "w"), indent=1)
