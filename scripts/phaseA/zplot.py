import json, sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
def plot(D, out, win, rel=True, extra=None):
    off = 50 if rel else 0
    x0, y0, x1, y1 = [v + off for v in win]
    w = x1 - x0; h = y1 - y0
    fig, ax = plt.subplots(figsize=(16, 16 * h / w))
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal")
    sc = 16 * 72 / w  # points per mm
    for z in D["zones"]:
        col = {"FOTO": "yellow", "NFC": "cyan", "GND_BACK": None}.get(z["name"], "magenta")
        if col:
            for o in z["outline"]: ax.add_patch(Polygon(o, closed=True, fc=col, alpha=0.15, ec=col))
    for d in D["drawings"]:
        if d["layer"] == "User.Drawings":
            ax.add_patch(Rectangle(d["start"], d["end"][0]-d["start"][0], d["end"][1]-d["start"][1], fill=False, ec="green", ls="--"))
    for t in sorted(D["tracks"], key=lambda t: t["layer"] != "B.Cu"):
        c = {"F.Cu": "red", "B.Cu": "blue"}[t["layer"]]
        if t["grp"] == "CRITICAL_AUTO": c = {"F.Cu": "darkorange", "B.Cu": "purple"}[t["layer"]]
        elif t["grp"] != "RING_AUTO": c = {"F.Cu": "gold", "B.Cu": "deepskyblue"}[t["layer"]]
        ax.plot([t["x1"], t["x2"]], [t["y1"], t["y2"]], color=c, lw=t["w"] * sc, alpha=0.55, solid_capstyle="round")
    for p in D["pads"]:
        for lay, polys in p["polys"].items():
            for o in polys:
                ax.add_patch(Polygon(o, closed=True, fc=("salmon" if lay == "F.Cu" else "lightblue"), ec="k", lw=0.3, alpha=0.7))
        if x0 < p["x"] < x1 and y0 < p["y"] < y1 and w < 80:
            ax.text(p["x"], p["y"], "%s.%s\n%s" % (p["ref"], p["num"], p["net"].replace("/", "").replace("Net-", "")[:12]), fontsize=max(3, 300 / w), ha="center", va="center")
    for v in D["vias"]:
        ax.add_patch(Circle((v["x"], v["y"]), v["d"] / 2, fc="gray" if v["grp"] == "RING_AUTO" else "black", ec="k", lw=0.3, alpha=0.8))
        if w < 80 and x0 < v["x"] < x1 and y0 < v["y"] < y1: ax.text(v["x"], v["y"]+v["d"]/2+0.2, v["net"].replace("/", "")[:8], fontsize=max(3, 250 / w), color="purple", ha="center")
    if extra: extra(ax)
    import numpy as np
    step = 1 if w < 40 else (5 if w < 120 else 10)
    ax.set_xticks(np.arange(int(x0), x1, step)); ax.set_yticks(np.arange(int(y0), y1, step))
    ax.set_xticklabels([("%g" % (v - off)) for v in np.arange(int(x0), x1, step)], fontsize=6, rotation=90)
    ax.set_yticklabels([("%g" % (v - off)) for v in np.arange(int(y0), y1, step)], fontsize=6)
    ax.grid(True, lw=0.2)
    plt.savefig(out, dpi=100, bbox_inches="tight"); plt.close()
if __name__ == "__main__":
    D = json.load(open(sys.argv[1]))
    plot(D, sys.argv[2], [float(v) for v in sys.argv[3].split(",")])
