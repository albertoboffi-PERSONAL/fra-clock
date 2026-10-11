import pcbnew, re, sys, collections
b = pcbnew.LoadBoard("fra_clock.kicad_pcb")
mm = pcbnew.ToMM
ring = re.compile(r'^(D[2-5]\d\d|C[2-5]\d\d)$')
print("== groups")
for g in b.Groups():
    items = list(g.GetItems())
    c = collections.Counter(type(i).__name__ for i in items)
    print(" ", g.GetName(), dict(c))
print("== zones")
for z in b.Zones():
    bb = z.GetBoundingBox()
    print("  name=%r net=%r rule=%s layers=%s bbox=(%.2f,%.2f)-(%.2f,%.2f) prio=%d" % (z.GetZoneName(), z.GetNetname(), z.GetIsRuleArea(),
          [b.GetLayerName(l) for l in z.GetLayerSet().Seq()], mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()), z.GetAssignedPriority()))
    if z.GetIsRuleArea():
        print("     keepout tracks=%s vias=%s pads=%s copper=%s fp=%s" % (z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(), z.GetDoNotAllowPads(), z.GetDoNotAllowZoneFills(), z.GetDoNotAllowFootprints()))
print("== tracks/vias total", len(b.GetTracks()))
print("== net classes")
ds = b.GetDesignSettings()
ns = ds.m_NetSettings
try:
    for name, nc in ns.GetNetclasses().items():
        print("  ", name, mm(nc.GetTrackWidth()), mm(nc.GetClearance()), mm(nc.GetViaDiameter()), mm(nc.GetViaDrill()))
    dnc = ns.GetDefaultNetclass(); print("  Default", mm(dnc.GetTrackWidth()), mm(dnc.GetClearance()), mm(dnc.GetViaDiameter()), mm(dnc.GetViaDrill()))
except Exception as e: print("nc err", e)
print("  min track", mm(ds.m_TrackMinWidth), "min clear", mm(ds.m_MinClearance), "via min", mm(ds.m_ViasMinSize), "edge", mm(ds.m_CopperEdgeClearance), "h2h", mm(ds.m_HoleToHoleMin))
print("== footprints (non-ring)")
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    r = fp.GetReference()
    if ring.match(r): continue
    p = fp.GetPosition()
    print("%-6s %-38s (%.2f,%.2f) rot=%.0f %s locked=%s val=%s" % (r, fp.GetFPID().GetLibItemName().wx_str()[:38], mm(p.x)-50, mm(p.y)-50, fp.GetOrientationDegrees(), b.GetLayerName(fp.GetLayer()), fp.IsLocked(), fp.GetValue()))
    for pad in fp.Pads():
        pp = pad.GetPosition()
        print("       pad %-4s %-14s (%.2f,%.2f) size=(%.2f,%.2f) %s %s" % (pad.GetNumber(), pad.GetNetname(), mm(pp.x)-50, mm(pp.y)-50, mm(pad.GetSize(pcbnew.F_Cu).x), mm(pad.GetSize(pcbnew.F_Cu).y), "TH" if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else ("NPTH" if pad.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH else "SMD"), pad.GetPadName() if hasattr(pad,'GetPadName') else ""))
