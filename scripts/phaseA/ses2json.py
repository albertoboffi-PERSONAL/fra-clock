import re, sys, json
def sexp(s):
    toks = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)
    st = [[]]
    for t in toks:
        if t == "(": st.append([])
        elif t == ")": x = st.pop(); st[-1].append(x)
        else: st[-1].append(t.strip('"'))
    return st[0][0]
def find(node, key):
    if isinstance(node, list):
        if node and node[0] == key: yield node
        for c in node: yield from find(c, key)
def convert(ses_path, out_path, scale=10000.0, off=50.0):
    S = sexp(open(ses_path).read())
    pads = {}
    for ps in find(S, "padstack"):
        name = ps[1]
        circ = next(find(ps, "circle"))
        pads[name] = float(circ[2]) / scale
    items = []
    for net in find(S, "net"):
        if len(net) < 2 or not isinstance(net[1], str): continue
        name = net[1]
        for w in [c for c in net[2:] if isinstance(c, list) and c[0] == "wire"]:
            path = next(find(w, "path"))
            layer, width = path[1], float(path[2]) / scale
            pts = [(float(path[i]) / scale - off, -float(path[i + 1]) / scale - off) for i in range(3, len(path), 2)]
            for a, b in zip(pts, pts[1:]):
                items.append(dict(type="track", layer=layer, net=name, w=round(width, 4), x1=round(a[0], 4), y1=round(a[1], 4), x2=round(b[0], 4), y2=round(b[1], 4), tag="fr"))
        for v in [c for c in net[2:] if isinstance(c, list) and c[0] == "via"]:
            d = pads[v[1]]
            items.append(dict(type="via", net=name, x=round(float(v[2]) / scale - off, 4), y=round(-float(v[3]) / scale - off, 4), d=d, drill={0.6: 0.3, 0.8: 0.4}[round(d, 2)], tag="fr"))
    json.dump(items, open(out_path, "w"), indent=0)
    return items
if __name__ == "__main__":
    it = convert(sys.argv[1], sys.argv[2])
    print(len(it), "items", sum(1 for i in it if i["type"] == "via"), "vias")
