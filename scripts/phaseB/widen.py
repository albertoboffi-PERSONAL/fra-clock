import json, sys
from model import Board
A = json.load(open("critical.json")); F = json.load(open(sys.argv[1])); X = json.load(open(sys.argv[2]))
B = F + X
b = Board("geom0.json"); b.add(A + B)
nw = 0; kept = 0
for i, it in enumerate(B):
    if it["type"] == "track" and it["w"] < 0.25:
        old = it["w"]; it["w"] = 0.25
        b._rebuild() if False else None
        # check this single widened item against everything (rebuild trees with the change)
        b.new = A + B; b._rebuild()
        if b.check([it], verbose=False):
            it["w"] = old; kept += 1
        else:
            nw += 1
b.new = A + B; b._rebuild()
print("widened", nw, "kept narrow", kept, "final viol", len(b.check(B, verbose=True)))
json.dump(B, open(sys.argv[3], "w"), indent=0)
