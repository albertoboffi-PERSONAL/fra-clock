"""Place C69 on F.Cu at relative (138.0, 284.8), +5V pad (1) to the east. usage: move_c69.py board"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); fp = b.FindFootprintByReference("C69")
if fp.GetLayer() == pcbnew.B_Cu:
    try: fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except Exception: fp.Flip(fp.GetPosition(), True)
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(138.0 + 50), pcbnew.FromMM(284.8 + 50)))
p = {q.GetNumber(): pcbnew.ToMM(q.GetPosition().x) - 50 for q in fp.Pads()}
if p["1"] < p["2"]: fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 180)
print({q.GetNumber(): (round(pcbnew.ToMM(q.GetPosition().x) - 50, 3), round(pcbnew.ToMM(q.GetPosition().y) - 50, 3)) for q in fp.Pads()}, b.GetLayerName(fp.GetLayer()))
b.Save(sys.argv[1]); print("saved")
