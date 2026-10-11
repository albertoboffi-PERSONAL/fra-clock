"""Place the photo art and the two speaker 3D placeholders (group ART_3D), relax the FOTO rule area
so that it still forbids tracks/vias/pads/zone copper but accepts the art footprint. Re-runnable.
usage: place_art.py <board.kicad_pcb>"""
import sys, os
import pcbnew
path = sys.argv[1]
prj = os.path.dirname(os.path.abspath(path))
lib = os.path.join(prj, "fra_clock.pretty")
b = pcbnew.LoadBoard(path)
P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x + 50), pcbnew.FromMM(y + 50))   # relative -> absolute
# remove previous ART_3D group
for g in [g for g in b.Groups() if g.GetName() == "ART_3D"]:
    for it in list(g.GetItems()):
        g.RemoveItem(it); b.Remove(it)
    b.Remove(g)
grp = pcbnew.PCB_GROUP(b); grp.SetName("ART_3D"); b.Add(grp)
def place(name, ref, x, y, back):
    fp = pcbnew.FootprintLoad(lib, name)
    fp.SetFPID(pcbnew.LIB_ID("fra_clock", name))
    fp.SetReference(ref)
    b.Add(fp)
    fp.SetPosition(P(x, y))
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM if hasattr(pcbnew, "FLIP_DIRECTION_TOP_BOTTOM") else False)
    fp.SetLocked(True)
    grp.AddItem(fp)
    return fp
place("ART_FOTO", "ART1", 105.0, 142.0, False)                    # centre of FOTO zone (20,63)-(190,221)
place("Speaker_Makerverse_CE08483_100x45", "LS1", 105.0, 36.5, False)    # top outline (55,14)-(155,59)
place("Speaker_Makerverse_CE08483_100x45", "LS2", 105.0, 247.5, False)   # bottom outline (55,225)-(155,270)
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetZoneName() == "FOTO":
        z.SetDoNotAllowFootprints(False)
        print("FOTO rule area: tracks", z.GetDoNotAllowTracks(), "vias", z.GetDoNotAllowVias(), "pads", z.GetDoNotAllowPads(),
              "zone copper", z.GetDoNotAllowZoneFills(), "footprints", z.GetDoNotAllowFootprints())
b.Save(path)
print("saved")
