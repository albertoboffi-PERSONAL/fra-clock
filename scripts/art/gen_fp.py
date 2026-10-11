import json, math, uuid
U = lambda: str(uuid.uuid4())
# ---------- ART_FOTO footprint ----------
def art_fp(rjson, out):
    R = json.load(open(rjson)); px = R["px"]; nx, ny = R["nx"], R["ny"]
    # origin = centre of the FOTO zone (relative 105,142); art grid top-left at relative (20.6, 63.6)
    x0 = 20.6 - 105.0; y0 = 63.6 - 142.0
    L = []
    L.append('(footprint "ART_FOTO"\n\t(version 20250114)\n\t(generator "fra_clock_art")\n\t(layer "F.Cu")\n'
             '\t(descr "Photo art: ENIG copper dither (F.Cu + F.Mask opening), %dx%d px, %.2f mm/px, from foto.jpeg")\n' % (nx, ny, px))
    L.append('\t(property "Reference" "ART1" (at 0 %.2f 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))\n' % (y0 - 2, U()))
    L.append('\t(property "Value" "ART_FOTO" (at 0 %.2f 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))\n' % (-y0 + 2, U()))
    L.append('\t(attr board_only exclude_from_pos_files exclude_from_bom)\n')
    for lay in ("F.Cu", "F.Mask"):
        for (a, b, c, d) in R["rects"]:
            L.append('\t(fp_rect (start %.3f %.3f) (end %.3f %.3f) (stroke (width 0) (type solid)) (fill yes) (layer "%s") (uuid "%s"))\n'
                     % (x0 + a * px, y0 + b * px, x0 + c * px, y0 + d * px, lay, U()))
    L.append('\t(fp_rect (start %.3f %.3f) (end %.3f %.3f) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "%s"))\n' % (x0, y0, x0 + nx * px, y0 + ny * px, U()))
    L.append(')\n')
    open(out, "w").write("".join(L))
# ---------- speaker footprint + VRML ----------
def spk_fp(out):
    L = ['(footprint "Speaker_Makerverse_CE08483_100x45"\n\t(version 20250114)\n\t(generator "fra_clock_art")\n\t(layer "F.Cu")\n'
         '\t(descr "Makerverse enclosed speaker 8 ohm 5 W (Core Electronics CE08483): 100x45x21 mm, mounting 91.2x36.2 mm, 2x 35 mm cones at 27.5 mm from the ends")\n',
         '\t(property "Reference" "LS1" (at 0 -24.5 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))\n' % U(),
         '\t(property "Value" "CE08483" (at 0 24.5 0) (layer "F.Fab") (hide yes) (uuid "%s") (effects (font (size 1 1) (thickness 0.15))))\n' % U(),
         '\t(attr board_only exclude_from_pos_files exclude_from_bom)\n',
         '\t(fp_rect (start -50 -22.5) (end 50 22.5) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "%s"))\n' % U()]
    for cx in (-22.5, 22.5):
        L.append('\t(fp_circle (center %.1f 0) (end %.1f 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "%s"))\n' % (cx, cx + 17.5, U()))
    L.append('\t(model "${KIPRJMOD}/3d/Speaker_Makerverse_CE08483.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n)\n')
    open(out, "w").write("".join(L))

def vrml(out):
    S = 1 / 2.54  # mm -> VRML units (0.1 inch)
    shapes = []
    def mesh(pts, faces, col, spec=0.2, shin=0.3):
        c = " ".join("%.4f %.4f %.4f," % (x * S, y * S, z * S) for x, y, z in pts)
        f = " ".join(",".join(str(i) for i in fc) + ",-1," for fc in faces)
        shapes.append('Shape { appearance Appearance { material Material { diffuseColor %.3f %.3f %.3f specularColor %.2f %.2f %.2f shininess %.2f } }\n'
                      ' geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ %s ] } coordIndex [ %s ] } }\n'
                      % (col + (spec, spec, spec, shin) + (c, f)))
    def prism(poly, z0, z1, col, **k):
        n = len(poly); pts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
        faces = [list(range(n))[::-1], list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        mesh(pts, faces, col, **k)
    def rrect(w, h, r, seg=8):
        P = []
        for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
            for i in range(seg + 1):
                a = math.radians(a0 + 90 * i / seg); P.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return P
    def circ(cx, cy, r, n=48): return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    # body: z from 0 (board side) to 21 mm
    prism(rrect(100, 45, 4), 0.0, 21.0, (0.08, 0.08, 0.09))
    for cx in (-22.5, 22.5):
        prism(circ(cx, 0, 18.5), 21.0, 21.6, (0.15, 0.15, 0.16))          # trim ring
        prism(circ(cx, 0, 17.5), 21.6, 21.8, (0.30, 0.30, 0.32), spec=0.4)  # cone (grille)
        prism(circ(cx, 0, 6.0), 21.8, 22.6, (0.55, 0.55, 0.58), spec=0.6)  # dust cap
    for sx in (-45.6, 45.6):
        for sy in (-18.1, 18.1):
            prism(circ(sx, sy, 3.0, 24), 21.0, 21.05, (0.0, 0.0, 0.0))       # mounting holes (visual)
    open(out, "w").write("#VRML V2.0 utf8\n" + "".join(shapes))

if __name__ == "__main__":
    import sys
    art_fp(sys.argv[1], "ART_FOTO.kicad_mod"); spk_fp("Speaker_Makerverse_CE08483_100x45.kicad_mod"); vrml("Speaker_Makerverse_CE08483.wrl")
