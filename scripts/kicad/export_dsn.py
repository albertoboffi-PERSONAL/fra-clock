"""Export a Specctra DSN for Freerouting from a COPY of the board, with all existing
tracks/vias locked (-> exported as protected wiring). The real board is not modified.
usage: export_dsn.py <board.kicad_pcb> <out.dsn>"""
import sys
import pcbnew

src, dsn = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
n = 0
for t in b.GetTracks():
    if not t.IsLocked():
        t.SetLocked(True)
        n += 1
print("locked (in memory only):", n, "of", len(b.GetTracks()))
ok = pcbnew.ExportSpecctraDSN(b, dsn)
print("export ok:", ok, dsn)
