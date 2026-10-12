import json
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from model import Board, LAYERS
def connectivity(b, nets, extra_items):
    """For each net: list of pad groups (ref.num) that are not connected (by tracks/vias/pads; zones ignored)."""
    res = {}
    for net in nets:
        objs = []  # (layerset, geom, label)
        for (ref, num), plist in b.pads.items():
            for p in plist:
                if p["net"] != net: continue
                for lay, polys in p["polys"].items():
                    g = unary_union([Polygon([(q[0]-50, q[1]-50) for q in o]) for o in polys])
                    objs.append(({lay}, g, "%s.%s" % (ref, num)))
        for t in b.D["tracks"]:
            if t["net"] == net:
                objs.append(({t["layer"]}, LineString([(t["x1"]-50, t["y1"]-50), (t["x2"]-50, t["y2"]-50)]).buffer(t["w"]/2), None))
        for v in b.D["vias"]:
            if v["net"] == net:
                objs.append((set(LAYERS), Point(v["x"]-50, v["y"]-50).buffer(v["d"]/2), None))
        for it in extra_items:
            if it["net"] != net: continue
            if it["type"] == "via": objs.append((set(LAYERS), Point(it["x"], it["y"]).buffer(it["d"]/2), None))
            else: objs.append(({it["layer"]}, LineString([(it["x1"], it["y1"]), (it["x2"], it["y2"])]).buffer(it["w"]/2), None))
        n = len(objs); par = list(range(n))
        def f(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        for i in range(n):
            for j in range(i+1, n):
                if objs[i][0] & objs[j][0] and objs[i][1].distance(objs[j][1]) < 1e-3:
                    par[f(i)] = f(j)
        groups = {}
        for i, o in enumerate(objs):
            if o[2]: groups.setdefault(f(i), set()).add(o[2])
        if len(groups) > 1: res[net] = list(groups.values())
    return res
