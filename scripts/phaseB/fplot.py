import json, sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from shapely.geometry import Polygon as SP
fill = json.load(open(sys.argv[1])); D = json.load(open(sys.argv[2]))
win = [float(v) + 50 for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else [50, 50, 260, 347]
x0, y0, x1, y1 = win; w = x1 - x0; h = y1 - y0
fig, ax = plt.subplots(figsize=(14, 14 * h / w)); ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal")
areas = []
for k, f in enumerate(fill):
    a = SP(f["outline"]).area; areas.append(a)
    col = "lightgreen" if a > 10000 else "red"
    ax.add_patch(Polygon(f["outline"], closed=True, fc=col, ec="k", lw=0.2, alpha=0.5))
    for hh in f["holes"]: ax.add_patch(Polygon(hh, closed=True, fc="white", ec="k", lw=0.1))
    if a < 10000:
        c = SP(f["outline"]).centroid; ax.text(c.x, c.y, "%d" % k, fontsize=8, color="red")
for t in D["tracks"]:
    if t["layer"] == "B.Cu": ax.plot([t["x1"], t["x2"]], [t["y1"], t["y2"]], color="blue", lw=t["w"] * 72 * 14 / w * 0.7)
for v in D["vias"]:
    ax.add_patch(Circle((v["x"], v["y"]), v["d"] / 2, fc="black" if v["net"] == "GND" else "purple"))
plt.savefig(sys.argv[3], dpi=100, bbox_inches="tight")
print(sorted(round(a, 2) for a in areas))
