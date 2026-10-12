"""Dump the filled polygons of all copper zones (+ tracks/vias of the board) to JSON for inspection.
usage: dump_fill.py board.kicad_pcb out.json"""
import sys, json
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
mm = pcbnew.ToMM
out = []
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    for lay in z.GetLayerSet().Seq():
        if not z.HasFilledPolysForLayer(lay):
            continue
        sps = z.GetFilledPolysList(lay)
        for i in range(sps.OutlineCount()):
            o = sps.Outline(i)
            holes = []
            for h in range(sps.HoleCount(i)):
                hh = sps.Hole(i, h)
                holes.append([[mm(hh.CPoint(j).x), mm(hh.CPoint(j).y)] for j in range(hh.PointCount())])
            out.append(dict(zone=z.GetZoneName(), net=z.GetNetname(), layer=b.GetLayerName(lay),
                            outline=[[mm(o.CPoint(j).x), mm(o.CPoint(j).y)] for j in range(o.PointCount())], holes=holes))
json.dump(out, open(sys.argv[2], "w"))
print("islands:", len(out))
