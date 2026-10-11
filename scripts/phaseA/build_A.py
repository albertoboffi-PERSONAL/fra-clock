import json
from model import Board
import pa_j1, pa_pwr, pa_amp, pa_gnd
it = pa_j1.items() + pa_j1.items_pair() + pa_pwr.items() + pa_amp.items() + pa_gnd.items()
b = Board("geom0.json"); b.add(it)
v = b.check(it, verbose=True)
print("items", len(it), "violations", len(v))
json.dump(it, open("critical.json", "w"), indent=0)
