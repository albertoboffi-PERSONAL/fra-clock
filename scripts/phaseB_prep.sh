#!/bin/zsh
# Reset FREEROUTE_AUTO, (re)apply CRITICAL_AUTO, export DSN, prepare it and start Freerouting in background.
# usage: scripts/phaseB_prep.sh <tag> [max_passes] [--skip NET ...]
set -e
cd "$(dirname "$0")/.."
TAG=$1; MP=${2:-20}; shift 2 || true
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
scripts/apply_and_drc.sh scripts/empty.json FREEROUTE_AUTO tools/drc_tmp.json > /dev/null 2>&1 || true
scripts/apply_and_drc.sh scripts/critical.json CRITICAL_AUTO drc_A.json | tail -6
$KPY -u scripts/export_dsn.py fra_clock.kicad_pcb tools/fr/fra_B.dsn 2>&1 | grep -v -E "swig|assert"
python3 scripts/dsn_prepare.py tools/fr/fra_B.dsn drc_A.json tools/fr/fra_$TAG.dsn "$@" | tail -1
rm -f tools/fr/fra_$TAG.ses
scripts/run_freerouting.sh tools/fr/fra_$TAG.dsn tools/fr/fra_$TAG.ses tools/fr/fr_$TAG.log $MP
