#!/bin/zsh
# usage: scripts/kicad/apply_and_drc.sh <items.json> <GROUP> <drc_out.json>
# Applies the items to hardware/fra_clock.kicad_pcb (group recreated), refills zones via kicad-cli, saves, runs DRC.
set -e
cd "$(dirname "$0")/../.."   # repo root
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
KC=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
# pcbnew may segfault on interpreter exit after the save (KiCad 10 swig): tolerate it, verify below
$KPY -u scripts/kicad/apply_group.py hardware/fra_clock.kicad_pcb "$1" "$2" --nofill 2>&1 | grep -v -E "swig/python|assert" || true
$KC pcb drc --refill-zones --save-board --format json --severity-all --units mm -o "$3" hardware/fra_clock.kicad_pcb | tail -3
python3 scripts/kicad/drc_summary.py "$3" | grep -v "^keys"
