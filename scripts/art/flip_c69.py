"""Move C69 (470uF bulk) from B.Cu to F.Cu at the same XY, keeping the +5V pad on the C4 side.
usage: flip_c69.py <board.kicad_pcb>"""
import sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
fp = b.FindFootprintByReference("C69")
mm = pcbnew.ToMM
def pads(): return {p.GetNumber(): (round(mm(p.GetPosition().x) - 50, 3), round(mm(p.GetPosition().y) - 50, 3), b.GetLayerName(p.GetLayer()) if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD else "TH") for p in fp.Pads()}
print("before", b.GetLayerName(fp.GetLayer()), fp.GetOrientationDegrees(), pads())
if fp.GetLayer() == pcbnew.B_Cu:
    pos = fp.GetPosition()
    try:
        fp.Flip(pos, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except Exception:
        fp.Flip(pos, True)
    p = pads()
    if p["1"][0] < p["2"][0]:            # +5V pad must stay east (x 93.25, next to C4)
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 180)
print("after ", b.GetLayerName(fp.GetLayer()), fp.GetOrientationDegrees(), pads())
b.Save(sys.argv[1]); print("saved")
