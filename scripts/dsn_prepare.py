"""Prepare the KiCad-exported DSN for Freerouting (fra_clock, Phase B).
 - F.Cu keepouts: speaker outlines (User.Drawings), ESP32 module body, ring DIN pad+stub+via (entry on B.Cu)
 - copper-to-edge 0.5 mm strips (Freerouting does not know the rule)
 - B.Cu keepouts that protect the GND plane continuity: perimeter band inside the LED ring (with windows
   at the DIN entry vias), the ESP32 area, the USB-C pocket and the corridor between +5V trunk and bridge
 - only the nets still unconnected after Phase A (read from a DRC json) are routed (class 'route');
   all other nets go to class 'fixed' and keep a single pin. --skip NET removes a net from routing.
usage: dsn_prepare.py in.dsn drc.json out.dsn [--skip NET ...]"""
import sys, json, re

args = sys.argv[1:]
skip = set()
while "--skip" in args:
    i = args.index("--skip"); skip.add(args[i + 1]); del args[i:i + 2]
src, drcf, out = args[:3]
s = open(src).read()
d = json.load(open(drcf))
route = set()
for u in d["unconnected_items"]:
    for it in u["items"]:
        m = re.search(r"\[([^\]]+)\]", it["description"])
        if m:
            route.add(m.group(1))
route.discard("GND")
route -= skip
print("nets to route:", len(route), sorted(route))

def rect(name, lay, x0, y0, x1, y1, rel=True):
    o = 50 if rel else 0
    X0, Y0, X1, Y1 = [round((v + o) * 1000) for v in (x0, y0, x1, y1)]
    return '    (keepout "%s" (polygon %s 0  %d %d  %d %d  %d %d  %d %d  %d %d))\n' % (name, lay, X0, -Y0, X1, -Y0, X1, -Y1, X0, -Y1, X0, -Y0)

ko = ""
# F.Cu
ko += rect("SPK_TOP", "F.Cu", 55, 14, 155, 59) + rect("SPK_BOT", "F.Cu", 55, 225, 155, 270)
ko += rect("U3BODY", "F.Cu", 31.0, 255.3, 46.5, 273.2)
ko += rect("U6BODY", "F.Cu", 78.6, 278.5, 81.45, 287.6) + rect("U5BODY", "F.Cu", 178.6, 262.4, 181.4, 272.2)
for nm, r in (("DINA", (111.4, 289.75, 112.6, 291.95)), ("DINB", (202.75, 143.6, 204.95, 144.7)),
              ("DINC", (102.75, 5.05, 103.85, 7.25)), ("DIND", (5.05, 147.0, 7.25, 148.1))):
    ko += rect(nm, "F.Cu", *r)
# edge clearance strips, both layers
for lay in ("F.Cu", "B.Cu"):
    for nm, r in (("EDGT", (0, 0, 210, 0.6)), ("EDGB", (0, 296.4, 210, 297)), ("EDGL", (0, 0, 0.6, 297)),
                  ("EDGR", (209.4, 0, 210, 297)), ("CTL", (0, 0, 3.6, 3.6)), ("CTR", (206.4, 0, 210, 3.6)),
                  ("CBL", (0, 293.4, 3.6, 297)), ("CBR", (206.4, 293.4, 210, 297))):
        ko += rect(nm, lay, *r)
# B.Cu plane-protection keepouts
for nm, r in (("BAND_L1", (0, 13, 13, 142.0)), ("BAND_L2", (0, 148.3, 13, 288.6)),
              ("BAND_R1", (201.5, 13, 210, 143.0)), ("BAND_R2", (201.5, 145.2, 210, 288.6)),
              ("BAND_T1", (0, 0, 101.8, 13)), ("BAND_T2", (104.8, 0, 210, 13)),
              ("BAND_B1", (0, 288.6, 111.2, 297)), ("BAND_B2", (113.0, 288.6, 210, 297)),
              ("U3CORE", (29.0, 252.0, 49.0, 273.3)), ("U3NORTH", (37.0, 221.0, 41.0, 252.0)),
              ("U6NORTH", (78.5, 270.0, 81.0, 279.0)),
              ("J1POCKET", (99.8, 282.0, 110.2, 294.0)), ("J1CORR", (95.5, 277.9, 113.6, 281.0))):
    ko += rect(nm, "B.Cu", *r)

anchor = '    (via "Via[0-1]_600:300_um"'
assert anchor in s
s = s.replace(anchor, ko + anchor, 1)

m = re.search(r"\(class kicad_default (.*?)\n(\s+)\(circuit", s, re.S)
toks = re.findall(r'"[^"]*"|\S+', m.group(1))
names = [t.strip('"') for t in toks]
q = lambda n: '"%s"' % n if re.search(r'[\s()"{}~]', n) or n.startswith(("Net-", "unconnected")) else n
keep = [n for n in names if n in route]
fixed = [n for n in names if n not in route]
assert not (route - set(names)), route - set(names)
blk_start = m.start(); depth = 0; i = blk_start
while True:
    c = s[i]
    if c == "(": depth += 1
    elif c == ")":
        depth -= 1
        if depth == 0: break
    i += 1
blk_end = i + 1
tail = s[m.end() - len("(circuit"):blk_end]
new = "(class route " + " ".join(q(n) for n in keep) + "\n      " + tail + \
      "\n    (class fixed " + " ".join(q(n) for n in fixed) + "\n      " + tail
s = s[:blk_start] + new + s[blk_end:]

def single_pin(mm):
    name, pins = mm.group(1), mm.group(2).split()
    if name.strip('"') in route: return mm.group(0)
    return "(net %s\n      (pins %s)" % (name, pins[0])
s, n = re.subn(r'\(net ("[^"]*"|\S+)\n\s+\(pins ([^)]*)\)', single_pin, s)
open(out, "w").write(s)
print("route:", len(keep), "fixed:", len(fixed), "net blocks seen:", n)
