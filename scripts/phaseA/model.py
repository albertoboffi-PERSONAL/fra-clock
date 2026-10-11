"""Board model for fra_clock: obstacles, local DRC checker and a grid A* router.
All public coordinates are RELATIVE to (50,50) (rel = abs - 50), as in the routing brief."""
import json, math, heapq
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
from scipy import ndimage

OFF = 50.0
CLR = 0.2          # copper clearance
EDGE = 0.5         # copper to edge
HOLE_CLR = 0.25    # hole to other-net copper
H2H = 0.5          # hole to hole
LAYERS = ("F.Cu", "B.Cu")
RES = 0.1          # router grid (mm)

def rel(p): return (p[0] - OFF, p[1] - OFF)

class Board:
    def __init__(self, geom_path):
        D = json.load(open(geom_path))
        self.D = D
        self.items = {l: [] for l in LAYERS}   # (geom, net, desc)
        self.holes = []                        # (Point, radius, net, desc)
        self.pads = {}                         # (ref,num) -> list of pad dicts
        for p in D["pads"]:
            self.pads.setdefault((p["ref"], p["num"]), []).append(p)
            for lay, polys in p["polys"].items():
                g = unary_union([Polygon([rel(q) for q in o]) for o in polys if len(o) >= 3])
                self.items[lay].append((g, p["net"], "pad %s.%s" % (p["ref"], p["num"])))
            if p["drill"] > 0:
                self.holes.append((Point(rel((p["x"], p["y"]))), p["drill"] / 2, p["net"], "hole %s.%s" % (p["ref"], p["num"])))
        for t in D["tracks"]:
            g = LineString([rel((t["x1"], t["y1"])), rel((t["x2"], t["y2"]))]).buffer(t["w"] / 2, 16)
            self.items[t["layer"]].append((g, t["net"], "track %s %s" % (t["grp"], t["net"])))
        for v in D["vias"]:
            g = Point(rel((v["x"], v["y"]))).buffer(v["d"] / 2, 16)
            for l in LAYERS: self.items[l].append((g, v["net"], "via %s %s" % (v["grp"], v["net"])))
            self.holes.append((Point(rel((v["x"], v["y"]))), v["drill"] / 2, v["net"], "via-hole"))
        # outline: rounded rect (0,0)-(210,297), r=3
        self.outline = box(3, 3, 207, 294).buffer(3, 32)
        self.inner = self.outline.buffer(-EDGE)
        # keepouts
        self.keep_track = {l: [] for l in LAYERS}
        self.keep_via = []
        for z in D["zones"]:
            if not z["rule"]: continue
            poly = unary_union([Polygon([rel(q) for q in o]) for o in z["outline"]])
            for l in z["layers"]:
                if l in LAYERS: self.keep_track[l].append((poly, z["name"]))
            self.keep_via.append((poly, z["name"]))   # FOTO: vias forbidden as well (brief)
        # soft: speaker outlines on F.Cu, U3 module body on F.Cu
        self.soft_F = [box(55, 14, 155, 59), box(55, 225, 155, 270)]
        u3 = [f for f in D["fps"] if f["ref"] == "U3"][0]
        self.u3_body = unary_union([Polygon([rel(q) for q in o]) for o in u3["crtyd"]]) if u3["crtyd"] else None
        self.new = []   # list of dicts (tracks/vias) added by us
        self._rebuild()

    # ------------------------------------------------------------------ geometry of new items
    @staticmethod
    def item_geom(it):
        if it["type"] == "via":
            return Point(it["x"], it["y"]).buffer(it["d"] / 2, 16)
        return LineString([(it["x1"], it["y1"]), (it["x2"], it["y2"])]).buffer(it["w"] / 2, 16)

    def _rebuild(self):
        self.trees = {}
        for l in LAYERS:
            allit = list(self.items[l])
            for it in self.new:
                if it["type"] == "via" or it["layer"] == l:
                    allit.append((self.item_geom(it), it["net"], "NEW " + it.get("tag", "")))
            self.trees[l] = (STRtree([a[0] for a in allit]), allit)
        hol = list(self.holes) + [(Point(it["x"], it["y"]), it["drill"] / 2, it["net"], "NEW via-hole " + it.get("tag", "")) for it in self.new if it["type"] == "via"]
        self.htree = (STRtree([h[0] for h in hol]), hol)

    def add(self, items):
        self.new.extend(items); self._rebuild()

    # ------------------------------------------------------------------ local DRC
    def check(self, items=None, verbose=True):
        """Check items (default: all new) against everything else. Returns list of violation strings."""
        items = self.new if items is None else items
        viol = []
        for idx, it in enumerate(items):
            g = self.item_geom(it)
            lays = LAYERS if it["type"] == "via" else (it["layer"],)
            for l in lays:
                tree, allit = self.trees[l]
                for j in tree.query(g.buffer(CLR - 1e-4)):
                    og, onet, odesc = allit[j]
                    if onet == it["net"]: continue
                    dd = g.distance(og)
                    if dd < CLR - 1e-4:
                        viol.append("CLR %.3f %s %s [%s] vs %s [%s]" % (dd, l, it.get("tag", ""), it["net"], odesc, onet))
                for kp, kn in self.keep_track[l]:
                    if g.intersects(kp): viol.append("KEEPOUT %s %s in %s" % (l, it.get("tag", ""), kn))
            if it["type"] == "via":
                for kp, kn in self.keep_via:
                    if g.intersects(kp): viol.append("VIA-KEEPOUT %s in %s" % (it.get("tag", ""), kn))
                hp = Point(it["x"], it["y"]); r = it["drill"] / 2
                tree, hol = self.htree
                for j in tree.query(hp.buffer(r + H2H + 1.0)):
                    op, orad, onet, odesc = hol[j]
                    if op.distance(hp) < 1e-6: continue
                    if op.distance(hp) - r - orad < H2H - 1e-4:
                        viol.append("H2H %.3f %s vs %s" % (op.distance(hp) - r - orad, it.get("tag", ""), odesc))
                # hole clearance to other-net copper
                for l in LAYERS:
                    tree2, allit = self.trees[l]
                    for j in tree2.query(hp.buffer(r + HOLE_CLR)):
                        og, onet, odesc = allit[j]
                        if onet != it["net"] and hp.buffer(r, 16).distance(og) < HOLE_CLR - 1e-4:
                            viol.append("HOLECLR %s vs %s" % (it.get("tag", ""), odesc))
            if not g.within(self.inner):
                viol.append("EDGE %s" % it.get("tag", ""))
        # holes of existing pads/vias vs new track copper
        tree, hol = self.htree
        for it in items:
            if it["type"] == "via": continue
            g = self.item_geom(it)
            for j in tree.query(g.buffer(HOLE_CLR + 0.5)):
                op, orad, onet, odesc = hol[j]
                if onet != it["net"] and op.buffer(orad, 16).distance(g) < HOLE_CLR - 1e-4:
                    viol.append("HOLECLR track %s vs %s" % (it.get("tag", ""), odesc))
        viol = sorted(set(viol))
        if verbose:
            for v in viol: print("   ", v)
        return viol

    def pad(self, ref, num, i=0):
        p = self.pads[(ref, num)][i]
        return (p["x"] - OFF, p["y"] - OFF)

    # ------------------------------------------------------------------ raster router
    def build_raster(self):
        nx = int(round(210 / RES)) + 1; ny = int(round(297 / RES)) + 1
        self.nx, self.ny = nx, ny
        from PIL import Image, ImageDraw
        self.netid = {"": 0}
        def nid(n):
            if n not in self.netid: self.netid[n] = len(self.netid)
            return self.netid[n]
        def poly_to_img(draw, g, val):
            gs = g.geoms if hasattr(g, "geoms") else [g]
            for pg in gs:
                if pg.is_empty: continue
                draw.polygon([(x / RES, y / RES) for x, y in pg.exterior.coords], fill=val)
                for h in pg.interiors: draw.polygon([(x / RES, y / RES) for x, y in h.coords], fill=0)
        self.lab = {}
        for l in LAYERS:
            # per-net labels; overlapping different nets collapse (shouldn't happen)
            img = Image.new("I", (nx, ny), 0); dr = ImageDraw.Draw(img)
            tree, allit = self.trees[l]
            for g, net, desc in allit:
                poly_to_img(dr, g, nid(net) if net else 99999)
            self.lab[l] = np.array(img, dtype=np.int32)
        def mask_of(polys):
            img = Image.new("L", (nx, ny), 0); dr = ImageDraw.Draw(img)
            for pg in polys: poly_to_img(dr, pg, 1)
            return np.array(img, dtype=bool)
        self.kt = {l: mask_of([p for p, n in self.keep_track[l]]) for l in LAYERS}
        self.kv = mask_of([p for p, n in self.keep_via])
        self.inside = mask_of([self.inner])
        self.softF = mask_of(self.soft_F)
        self.u3m = mask_of([self.u3_body]) if self.u3_body is not None else np.zeros((ny, nx), bool)
        # holes raster (all holes)
        self.hole_img = mask_of([h[0].buffer(h[1], 12) for h in self.htree[1]])
        # same-net SMD pads (to forbid via-in-pad)
        self.smd = {l: mask_of([g for g, n, d in self.items[l] if d.startswith("pad")]) for l in LAYERS}
        self.d_keep = {l: ndimage.distance_transform_edt(~self.kt[l]) * RES for l in LAYERS}
        self.d_kv = ndimage.distance_transform_edt(~self.kv) * RES
        self.d_out = ndimage.distance_transform_edt(self.inside) * RES
        self.d_hole = ndimage.distance_transform_edt(~self.hole_img) * RES

    def route(self, net, src, dst, w=0.25, layers=("F.Cu", "B.Cu"), via=(0.6, 0.3), prefer="F.Cu", other_pen=2.0,
              via_cost=8.0, turn_pen=0.4, soft_pen=3.0, margin=0.06, window=None, start_layer=None, end_layer=None,
              extra_block=None, max_expand=4_000_000):
        """A* from point src to point dst (rel mm). Returns list of items (tracks/vias). src/dst may be (x,y,layer)."""
        nid = self.netid.get(net, -1)
        R = RES
        def tomask(l):
            other = (self.lab[l] != 0) & (self.lab[l] != nid)
            d = ndimage.distance_transform_edt(~other) * R
            return d
        dist = {l: tomask(l) for l in layers}
        free = {}
        for l in layers:
            f = (dist[l] >= CLR + w / 2 + margin) & (self.d_keep[l] >= w / 2 + margin) & (self.d_out >= w / 2 + margin)
            if extra_block is not None and l in extra_block: f &= ~extra_block[l]
            free[l] = f
        vr = via[0] / 2
        if len(layers) == 2:
            vfree = (self.d_kv >= vr + margin) & (self.d_out >= vr + margin) & (self.d_hole >= via[1] / 2 + H2H + margin) \
                    & ~self.smd["F.Cu"] & ~self.smd["B.Cu"]
            for l in layers:
                vfree &= (dist[l] >= CLR + vr + margin) & (self.d_keep[l] >= vr + margin)
            # hole clearance to other-net copper
            for l in layers: vfree &= dist[l] >= HOLE_CLR + via[1] / 2 + margin
        else:
            vfree = None
        nx, ny = self.nx, self.ny
        def cell(p): return (int(round(p[1] / R)), int(round(p[0] / R)))
        s = cell(src[:2]); t = cell(dst[:2])
        sl = [src[2]] if len(src) > 2 else ([start_layer] if start_layer else list(layers))
        tl = [dst[2]] if len(dst) > 2 else ([end_layer] if end_layer else list(layers))
        # allow start/end cells even if blocked (pad interiors): carve a small disc
        for l in layers:
            for (cy, cx) in (s, t):
                rr = int(0.35 / R)
                free[l][max(cy - rr, 0):cy + rr + 1, max(cx - rr, 0):cx + rr + 1] |= (self.lab[l][max(cy - rr, 0):cy + rr + 1, max(cx - rr, 0):cx + rr + 1] == nid)
        if window is not None:
            x0, y0, x1, y1 = window
            wm = np.zeros((ny, nx), bool); wm[int(y0 / R):int(y1 / R), int(x0 / R):int(x1 / R)] = True
            for l in layers: free[l] &= wm
        Ls = list(layers)
        pen = {l: (1.0 if l == prefer else other_pen) for l in Ls}
        DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        def h(c):
            dy = abs(c[0] - t[0]); dx = abs(c[1] - t[1])
            return (max(dx, dy) + 0.4142 * min(dx, dy)) * R
        openq = []
        g = {}
        came = {}
        for l in sl:
            st = (Ls.index(l), s[0], s[1])
            g[st] = 0.0; came[st] = (None, -1)
            heapq.heappush(openq, (h(s), 0.0, st))
        goal = None; n = 0
        tset = set(Ls.index(l) for l in tl)
        while openq:
            f, gc, st = heapq.heappop(openq)
            if gc > g.get(st, 1e18) + 1e-9: continue
            li, cy, cx = st
            if (cy, cx) == t and li in tset: goal = st; break
            n += 1
            if n > max_expand: break
            pdir = came[st][1]
            l = Ls[li]
            for di, (dy, dx) in enumerate(DIRS):
                ny2, nx2 = cy + dy, cx + dx
                if not (0 <= ny2 < ny and 0 <= nx2 < nx): continue
                if not free[l][ny2, nx2]: continue
                step = (1.4142 if di >= 4 else 1.0) * R * pen[l]
                if l == "F.Cu" and self.softF[ny2, nx2]: step *= soft_pen
                if l == "F.Cu" and self.u3m[ny2, nx2]: step *= 6
                if pdir >= 0 and pdir != di: step += turn_pen * (2 if (pdir < 4) != (di < 4) and False else 1) * R * 4
                ns = (li, ny2, nx2); ng = gc + step
                if ng < g.get(ns, 1e18) - 1e-12:
                    g[ns] = ng; came[ns] = (st, di)
                    heapq.heappush(openq, (ng + h((ny2, nx2)), ng, ns))
            if vfree is not None and vfree[cy, cx]:
                ns = (1 - li, cy, cx); ng = gc + via_cost
                if free[Ls[1 - li]][cy, cx] and ng < g.get(ns, 1e18) - 1e-12:
                    g[ns] = ng; came[ns] = (st, -2)
                    heapq.heappush(openq, (ng + h((cy, cx)), ng, ns))
        if goal is None:
            raise RuntimeError("no route %s %s->%s (expanded %d)" % (net, src, dst, n))
        path = []
        st = goal
        while st is not None:
            path.append(st); st = came[st][0]
        path.reverse()
        return self._path_to_items(path, Ls, net, w, via, src, dst)

    def _path_to_items(self, path, Ls, net, w, via, src, dst):
        R = RES
        items = []
        seg = []  # list of points on current layer
        cur_l = path[0][0]
        pts = []
        def flush(li, pts):
            # merge collinear
            if len(pts) < 2: return
            simp = [pts[0]]
            for i in range(1, len(pts) - 1):
                a, b, c = simp[-1], pts[i], pts[i + 1]
                if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) > 1e-9: simp.append(b)
            simp.append(pts[-1])
            for a, b in zip(simp, simp[1:]):
                if a != b:
                    items.append(dict(type="track", layer=Ls[li], net=net, w=w, x1=a[0], y1=a[1], x2=b[0], y2=b[1]))
        for k, (li, cy, cx) in enumerate(path):
            p = (round(cx * R, 4), round(cy * R, 4))
            if li != cur_l:
                flush(cur_l, pts)
                items.append(dict(type="via", net=net, x=pts[-1][0], y=pts[-1][1], d=via[0], drill=via[1]))
                pts = [pts[-1]]; cur_l = li
            pts.append(p)
        flush(cur_l, pts)
        # exact end points (pad centres)
        tr = [i for i in items if i["type"] == "track"]
        if tr:
            a = tr[0]; b = tr[-1]
            if (a["x1"], a["y1"]) != (round(src[0], 4), round(src[1], 4)):
                items.insert(0, dict(type="track", layer=a["layer"], net=net, w=w, x1=src[0], y1=src[1], x2=a["x1"], y2=a["y1"]))
            if (b["x2"], b["y2"]) != (round(dst[0], 4), round(dst[1], 4)):
                items.append(dict(type="track", layer=b["layer"], net=net, w=w, x1=b["x2"], y1=b["y2"], x2=dst[0], y2=dst[1]))
        return items


def T(layer, net, w, pts, tag=""):
    """Polyline helper -> list of track items."""
    return [dict(type="track", layer=layer, net=net, w=w, x1=a[0], y1=a[1], x2=b[0], y2=b[1], tag=tag) for a, b in zip(pts, pts[1:])]

def V(net, x, y, d=0.6, drill=0.3, tag=""):
    return dict(type="via", net=net, x=x, y=y, d=d, drill=drill, tag=tag)
