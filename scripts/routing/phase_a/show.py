import json, sys, copy
from zplot import plot
def show(D0, items, out, win):
    D = copy.deepcopy(D0)
    for it in items:
        if it["type"] == "via":
            D["vias"].append(dict(x=it["x"]+50, y=it["y"]+50, d=it["d"], drill=it["drill"], net=it["net"], grp="CRITICAL_AUTO"))
        else:
            D["tracks"].append(dict(x1=it["x1"]+50, y1=it["y1"]+50, x2=it["x2"]+50, y2=it["y2"]+50, w=it["w"], layer=it["layer"], net=it["net"], grp="CRITICAL_AUTO"))
    plot(D, out, win)
