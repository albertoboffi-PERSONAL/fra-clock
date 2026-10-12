"""Dump footprints (ref, value, lib id, layer, position, rotation, attributes) from a .kicad_pcb to JSON.
usage: python3 dump_fps.py fra_clock.kicad_pcb fps.json"""
import sys, json
from sexp import parse, find, first
pcb = parse(open(sys.argv[1]).read()); out = []
for fp in find(pcb, 'footprint'):
    at = first(fp, 'at'); props = {p[1]: p[2] for p in find(fp, 'property')}
    attr = first(fp, 'attr')
    out.append(dict(ref=props.get('Reference'), val=props.get('Value'), lib=fp[1], layer=first(fp, 'layer')[1],
                    x=float(at[1]), y=float(at[2]), rot=float(at[3]) if len(at) > 3 else 0.0,
                    attr=attr[1:] if attr else []))
json.dump(out, open(sys.argv[2], 'w'), indent=0); print(len(out))
