"""Apply a JSON list of tracks/vias (coordinates RELATIVE to (50,50), mm) to the board
inside a named group. Re-running deletes and recreates the group. Fills zones and saves.
usage: apply_group.py <board.kicad_pcb> <items.json> <GROUP_NAME> [--nofill]"""
import sys, json
import pcbnew

OFF = 50.0
path, jpath, gname = sys.argv[1], sys.argv[2], sys.argv[3]
nofill = "--nofill" in sys.argv
b = pcbnew.LoadBoard(path)
P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x + OFF), pcbnew.FromMM(y + OFF))

groups = {g.GetName(): g for g in b.Groups()}
ring = groups.get("RING_AUTO")
ring_before = len(ring.GetItems()) if ring else None
print("RING_AUTO items before:", ring_before)

# --- remove previous group + its items
removed = 0
if gname in groups:
    g = groups[gname]
    for it in list(g.GetItems()):
        g.RemoveItem(it)
        b.Remove(it)
        removed += 1
    b.Remove(g)
print("removed", removed)

grp = pcbnew.PCB_GROUP(b)
grp.SetName(gname)
b.Add(grp)
items = json.load(open(jpath))
nt = nv = 0
missing = set()
for it in items:
    net = b.FindNet(it["net"])
    if net is None:
        missing.add(it["net"])
        continue
    if it["type"] == "via":
        v = pcbnew.PCB_VIA(b)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetPosition(P(it["x"], it["y"]))
        try:
            v.SetWidth(pcbnew.FromMM(it["d"]))
        except TypeError:
            v.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(it["d"]))
        v.SetDrill(pcbnew.FromMM(it["drill"]))
        v.SetNet(net)
        if it.get("locked"):
            v.SetLocked(True)
        b.Add(v)
        grp.AddItem(v)
        nv += 1
    else:
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(P(it["x1"], it["y1"]))
        t.SetEnd(P(it["x2"], it["y2"]))
        t.SetWidth(pcbnew.FromMM(it["w"]))
        t.SetLayer(b.GetLayerID(it["layer"]))
        t.SetNet(net)
        if it.get("locked"):
            t.SetLocked(True)
        b.Add(t)
        grp.AddItem(t)
        nt += 1
print("added tracks", nt, "vias", nv, "missing nets", missing)

if not nofill:
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    print("zones filled")
b.Save(path)
print("saved", path)
try:
    print("RING_AUTO items after:", len(ring.GetItems()) if ring else None)
    print("%s items:" % gname, len(grp.GetItems()))
except Exception as e:
    print("count failed:", e)
