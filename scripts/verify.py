"""Acceptance checks for fra_clock routing.
usage: verify.py <current.kicad_pcb> <pre_routing.kicad_pcb>"""
import sys, json, hashlib
import pcbnew
cur = pcbnew.LoadBoard(sys.argv[1]); pre = pcbnew.LoadBoard(sys.argv[2])
mm = pcbnew.ToMM
OFF = 50.0
def rect_hit(x0, y0, x1, y1, bb):  # bb in abs mm
    return not (bb[2] < x0 + OFF or bb[0] > x1 + OFF or bb[3] < y0 + OFF or bb[1] > y1 + OFF)
def grp_items(b, name):
    out = []
    for t in b.GetTracks():
        g = t.GetParentGroup()
        if g is not None and g.GetName() == name:
            if t.GetClass() == "PCB_VIA":
                out.append(("V", t.GetPosition().x, t.GetPosition().y, t.GetWidth(pcbnew.F_Cu), t.GetDrill(), t.GetNetname()))
            else:
                out.append(("T", t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth(), t.GetLayer(), t.GetNetname()))
    return sorted(out)
res = {}
r0, r1 = grp_items(pre, "RING_AUTO"), grp_items(cur, "RING_AUTO")
res["ring_auto"] = dict(pre=len(r0), now=len(r1), identical=(r0 == r1),
                        tracks_pre=sum(1 for i in r0 if i[0] == "T"), vias_pre=sum(1 for i in r0 if i[0] == "V"),
                        tracks_now=sum(1 for i in r1 if i[0] == "T"), vias_now=sum(1 for i in r1 if i[0] == "V"))
fp0 = {f.GetReference(): (f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(), f.GetLayer()) for f in pre.GetFootprints()}
fp1 = {f.GetReference(): (f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(), f.GetLayer()) for f in cur.GetFootprints()}
res["footprints_moved"] = sorted(r for r in fp0 if fp0[r] != fp1.get(r))
# keepout checks on our new copper (all tracks/vias not in RING_AUTO)
FOTO = (20, 63, 190, 221); NFC = (20, 20, 52, 58); ANT = (18.75, 273.33, 62.75, 288.27)
SPK = [(55, 14, 155, 59), (55, 225, 155, 270)]
viol = []; spk = []
for t in cur.GetTracks():
    g = t.GetParentGroup(); gname = g.GetName() if g is not None else ""
    bb = t.GetBoundingBox(); b = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
    isvia = t.GetClass() == "PCB_VIA"
    lay = "via" if isvia else cur.GetLayerName(t.GetLayer())
    if (isvia or lay == "F.Cu") and rect_hit(*FOTO, b): viol.append(("FOTO", gname, lay, t.GetNetname(), b))
    for nm, r in (("NFC", NFC), ("ANT", ANT)):
        if rect_hit(*r, b): viol.append((nm, gname, lay, t.GetNetname(), b))
    if (isvia or lay == "F.Cu") and any(rect_hit(*r, b) for r in SPK) and gname != "RING_AUTO":
        spk.append((gname, lay, t.GetNetname()))
res["keepout_violations"] = viol
res["speaker_outline_FCu_items"] = len(spk)
# F.Cu copper of zones inside FOTO (should be none: only B.Cu zone)
res["zones"] = [(z.GetZoneName(), [cur.GetLayerName(l) for l in z.GetLayerSet().Seq()]) for z in cur.Zones()]
# widths of power tracks in CRITICAL_AUTO
w = {}
for t in cur.GetTracks():
    g = t.GetParentGroup()
    if g is None or t.GetClass() == "PCB_VIA": continue
    key = (g.GetName(), t.GetNetname(), cur.GetLayerName(t.GetLayer()))
    w.setdefault(key, set()).add(round(mm(t.GetWidth()), 3))
res["widths"] = {"%s|%s|%s" % k: sorted(v) for k, v in sorted(w.items()) if k[0] != "RING_AUTO"}
res["counts"] = {}
for name in ("CRITICAL_AUTO", "FREEROUTE_AUTO"):
    it = grp_items(cur, name)
    res["counts"][name] = dict(tracks=sum(1 for i in it if i[0] == "T"), vias=sum(1 for i in it if i[0] == "V"))
print(json.dumps(res, indent=1, default=str))
