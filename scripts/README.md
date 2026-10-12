# scripts

Automation used while laying out `hardware/fra_clock.kicad_pcb`. Shell scripts run from anywhere and `cd` to the repository root; Python scripts that touch the board need KiCad's bundled Python (`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`) for `pcbnew`. Close KiCad before running anything that saves the board.

| Folder | Content |
|---|---|
| `kicad/` | board utilities: `apply_group.py` (recreate a named group of tracks/vias from JSON), `apply_and_drc.sh` (apply + refill zones + DRC), `verify.py` (acceptance checks), `dump_geom.py` / `dump_fill.py` (geometry dumps), `export_dsn.py`, `drc_summary.py`, `unconn.py`, `inspect.py` |
| `routing/phase_a/` | scripted critical routing (`CRITICAL_AUTO`): power, USB, audio, GND vias; grid A* router and local DRC in `model.py` |
| `routing/phase_b/` | post-processing of the Freerouting result (`FREEROUTE_AUTO`): fixes, widening, GND continuity, keep-out and island checks |
| `routing/` | `phaseB_prep.sh`, `dsn_prepare.py`, `run_freerouting.sh` (Freerouting 2.5.0 jar expected in the git-ignored `tools/freerouting/`) |
| `routing/data/` | generated track/via lists applied to the board (`critical.json`, `phaseB.json`) |
| `art/` | photo dithering (`make_art.py`), footprint/3D generation (`gen_fp.py`), placement and 3D model assignment |
| `production/` | `dump_fps.py` + `make_bom_cpl.py`: JLCPCB BOM/CPL from the board file (no KiCad needed) |

The Python files in `routing/phase_a` and `routing/phase_b` were run from a scratch directory holding geometry dumps (`geom0.json`, `fill_B.json`, … produced by `kicad/dump_geom.py` / `kicad/dump_fill.py`) and import `model.py` (`PYTHONPATH=scripts/routing/phase_a`). They are kept as a record of how the routing was produced; the results are already in the board.
