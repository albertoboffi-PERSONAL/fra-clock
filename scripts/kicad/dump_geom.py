import pcbnew, json, sys
b = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else "hardware/fra_clock.kicad_pcb")
mm = pcbnew.ToMM
L = b.GetLayerName
def polypts(sps):
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        out.append([[mm(o.CPoint(j).x), mm(o.CPoint(j).y)] for j in range(o.PointCount())])
    return out
D = {"tracks": [], "vias": [], "pads": [], "zones": [], "fps": [], "drawings": []}
for t in b.GetTracks():
    g = t.GetParentGroup(); g = g.GetName() if g else ""
    if t.GetClass() == "PCB_VIA":
        D["vias"].append(dict(x=mm(t.GetPosition().x), y=mm(t.GetPosition().y), d=mm(t.GetWidth(pcbnew.F_Cu)), drill=mm(t.GetDrill()), net=t.GetNetname(), grp=g, locked=t.IsLocked()))
    else:
        D["tracks"].append(dict(x1=mm(t.GetStart().x), y1=mm(t.GetStart().y), x2=mm(t.GetEnd().x), y2=mm(t.GetEnd().y), w=mm(t.GetWidth()), layer=L(t.GetLayer()), net=t.GetNetname(), grp=g, arc=t.GetClass()=="PCB_ARC", locked=t.IsLocked()))
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox(False)
    cy = fp.GetCourtyard(pcbnew.F_CrtYd if fp.GetLayer()==pcbnew.F_Cu else pcbnew.B_CrtYd)
    D["fps"].append(dict(ref=fp.GetReference(), x=mm(fp.GetPosition().x), y=mm(fp.GetPosition().y), rot=fp.GetOrientationDegrees(), layer=L(fp.GetLayer()),
                         bbox=[mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())], crtyd=polypts(cy)))
    for z in fp.Zones():
        D["zones"].append(dict(name="fp:%s:%s" % (fp.GetReference(), z.GetZoneName()), rule=z.GetIsRuleArea(), layers=[L(l) for l in z.GetLayerSet().Seq()], net=z.GetNetname(), outline=polypts(z.Outline()),
             notracks=z.GetDoNotAllowTracks() if z.GetIsRuleArea() else None, novias=z.GetDoNotAllowVias() if z.GetIsRuleArea() else None))
    for p in fp.Pads():
        lays = [L(l) for l in p.GetLayerSet().CuStack()]
        polys = {}
        for lname, lid in (("F.Cu", pcbnew.F_Cu), ("B.Cu", pcbnew.B_Cu)):
            if p.IsOnLayer(lid):
                polys[lname] = polypts(p.GetEffectivePolygon(lid, pcbnew.ERROR_INSIDE).CloneDropTriangulation() if hasattr(pcbnew.SHAPE_POLY_SET,'CloneDropTriangulation') else p.GetEffectivePolygon(lid, pcbnew.ERROR_INSIDE))
        D["pads"].append(dict(ref=fp.GetReference(), num=p.GetNumber(), x=mm(p.GetPosition().x), y=mm(p.GetPosition().y), net=p.GetNetname(), layers=lays,
                              attr=int(p.GetAttribute()), drill=mm(p.GetDrillSize().x), sx=mm(p.GetSize(pcbnew.F_Cu).x), sy=mm(p.GetSize(pcbnew.F_Cu).y), polys=polys))
for z in b.Zones():
    D["zones"].append(dict(name=z.GetZoneName(), rule=z.GetIsRuleArea(), layers=[L(l) for l in z.GetLayerSet().Seq()], net=z.GetNetname(), outline=polypts(z.Outline())))
for d in b.GetDrawings():
    try:
        D["drawings"].append(dict(layer=L(d.GetLayer()), cls=d.GetClass(), shape=d.ShowShape() if hasattr(d,'ShowShape') else "", start=[mm(d.GetStart().x), mm(d.GetStart().y)], end=[mm(d.GetEnd().x), mm(d.GetEnd().y)]))
    except Exception as e:
        D["drawings"].append(dict(layer=L(d.GetLayer()), cls=d.GetClass(), err=str(e)))
json.dump(D, open(sys.argv[2] if len(sys.argv) > 2 else "geom.json", "w"))
print({k: len(v) for k, v in D.items()})
