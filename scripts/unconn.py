import json, sys, collections, re
d = json.load(open(sys.argv[1]))
by = collections.defaultdict(list)
for u in d["unconnected_items"]:
    its = u["items"]
    net = re.search(r'\[([^\]]+)\]', its[0]["description"])
    net = net.group(1) if net else "?"
    by[net].append(" -- ".join("%s(%.2f,%.2f)" % (re.sub(r'\s*\[.*?\]','',i["description"])[:40], i["pos"]["x"]-50, i["pos"]["y"]-50) for i in its))
for n in sorted(by, key=lambda k: -len(by[k])):
    print("## %s (%d)" % (n, len(by[n])))
    for l in by[n][: (100 if len(sys.argv)>2 else 6)]: print("   ", l)
