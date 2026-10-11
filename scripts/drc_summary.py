import json, sys, collections
d = json.load(open(sys.argv[1]))
print("keys:", list(d.keys()))
for sec in ("violations", "unconnected_items", "schematic_parity"):
    items = d.get(sec, [])
    c = collections.Counter((i.get("severity"), i.get("type")) for i in items)
    print(f"== {sec}: {len(items)}")
    for (s, t), n in sorted(c.items(), key=lambda x: -x[1]):
        print(f"   {s:8s} {t:35s} {n}")
if len(sys.argv) > 2:
    for sec in ("violations",):
        for i in d.get(sec, []):
            print(i["severity"], i["type"], "|", i["description"], "|", " / ".join(it["description"] + " @(%.2f,%.2f)" % (it["pos"]["x"], it["pos"]["y"]) for it in i["items"]))
