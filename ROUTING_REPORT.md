# fra_clock — Report di routing (KiCad 10)

Data: 2026-10-11 · Progetto: `~/Documents/30-PERSONAL/fra_pcb_gift/kicad/fra_clock/` · Board: `fra_clock.kicad_pcb`
Coordinate nel report: **relative all'angolo (50, 50)** come nel brief (assoluta = relativa + 50).

Fonti dei numeri riportati: `drc_00_baseline.json`, `drc_A.json`, `drc_B.json`, `drc_D.json`, `tools/drc_B_parity.json`, `tools/verify_B.json`, `tools/verify_D.json` (script `scripts/verify.py`), `tools/keepcheck_D.json`, `git log`.

## 1. Strumenti e versioni

| Strumento | Versione / percorso |
|---|---|
| KiCad / kicad-cli | 10.0.5 — `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` |
| Python KiCad + `pcbnew` | Python 3.9 bundled — `.../Frameworks/Python.framework/Versions/Current/bin/python3`, `pcbnew.Version()` = 10.0.5 (import da Python esterno OK, `ExportSpecctraDSN`/`ImportSpecctraSES` presenti) |
| Java | OpenJDK 27 (Homebrew, `/opt/homebrew/opt/openjdk/bin/java`, nessun link in `/usr/bin`) |
| Freerouting | 2.5.0 (release del 2026-10-05), jar in `tools/freerouting/` (escluso da git). SHA-256 `f6f51bb0…5de3c7` |
| Router/verifiche ausiliarie | script Python propri (A* su griglia 0.1 mm + DRC locale con shapely) in `scripts/phaseA/` e `scripts/phaseB/` |

Telemetria di Freerouting: disattivata dal 2° lancio in poi (`--profile.allow_telemetry=false --usage_and_diagnostic_data.disable_analytics=true`). **Il primo lancio di prova è partito con le impostazioni di default (telemetria attiva).**

## 2. Cosa è stato fatto

### Fase 0 — Preparazione
- KiCad aveva il progetto aperto: chiuso da te su richiesta prima di qualsiasi modifica.
- `git init` (repo locale, identità locale *Alberto Boffi*), `.gitignore` per `.history/`, lock, `tools/`, `*.ses`.
- DRC di partenza → `drc_00_baseline.json`.

### Fase A — Routing critico (gruppo `CRITICAL_AUTO`, script, nessun autorouter)
Geometria generata da script (`scripts/phaseA/*.py` → `scripts/critical.json`), applicata con `scripts/apply_group.py` (rilanciabile: cancella e ricrea il gruppo), zone riempite con `kicad-cli pcb drc --refill-zones --save-board`.
Elementi a fine Fase A: 208 piste, 63 via; dopo lo spostamento di C69 (§8): **210 piste, 67 via**.

| Collegamento | Realizzazione | Larghezze |
|---|---|---|
| J1 VBUS → F1.2 | A4/B9 su F.Cu (0.5 in uscita, poi 1.0); A9/B4 unito via B.Cu con 2+2 via 0.8/0.4; U2.5 con 0.4 + via | 0.5 / 1.0 / 0.4 |
| F1.1 → C4.1 | F.Cu | 1.5 |
| C4 → C69 | (§8) C69 ora sul fronte a destra di J1: C4.1 → 2 via 0.8/0.4 → B.Cu y = 277.35 (dorsale) → 2 via 0.8/0.4 → C69.1 su F.Cu | 1.5 |
| C4 → C8 → U6.14 | F.Cu (ripercorso a y = 277.05 dopo §8) | 0.6 |
| C4 → C3 → U1 VIN | dorsale su B.Cu, 2 via 0.8/0.4 vicino a C3; EN (U1.3) legato a +5V | 1.0 (0.6 nell'ultimo tratto sul pad SOT-23) |
| +5V → C72 → C102 → U102 VDD, R102 | F.Cu, alimentazione da est | 1.0 / 0.5 / 0.25 sui pin TQFN |
| +5V → C71 → C101 → U101 VDD, R101 | ramo su B.Cu a x = 191.6 lungo il lato destro, coppie di via 0.8/0.4 a (191.6, 252/250.8) e (191.6, 28.9/30.1), fuori FOTO | 1.0 / 0.25 |
| U1 → C2 → C1 → C6 → C5 → U3.2 (+3V3) | F.Cu, corsia a y≈273.4 sopra la zona antenna (fuori dalla zona: distanza ≥ 0.7 mm) | 0.6 |
| +3V3 verso U5 | C2 → via → B.Cu → C70 → U5.16 → (sotto il corpo) U5.4 | 0.6 |
| USB D+/D− | J1 → U2 (flow-through pin 6→1 / 4→3) → U5, F.Cu affiancate. Lunghezze D− 88.3 mm / D+ 84.0 mm | 0.3 (0.25 nei raccordi fra i pad del connettore) |
| U102 → J102, U101 → J101 | F.Cu affiancate; uscita a 0.25 dai pin TQFN, poi 0.5 | 0.25 / 0.5 |
| Via GND | una via 0.6/0.3 per ogni pad GND non della corona; due per C4, C3, C2, C6, C71, C72; EP di U101/U102 con 2 via nel pad + pin GND legati all'EP | 0.25–0.4 |

### Fase B — Resto del routing (gruppo `FREEROUTE_AUTO`)
Flusso: export DSN da una **copia in memoria** della board con tutto bloccato (`scripts/export_dsn.py`) → `scripts/dsn_prepare.py` → Freerouting headless (`scripts/run_freerouting.sh`, 20 passate, fanout disattivato) → conversione SES→JSON (`ses2json.py`) → correzioni con il router A* (`scripts/phaseB/fix_B2.py`) → allargamento dei neck-down dove possibile (`widen.py`) → applicazione con lo stesso `apply_group.py`.
**Non ho usato `ImportSpecctraSES`**: in KiCad cancella tutte le piste esistenti e le reimporta fuori dai gruppi, il che avrebbe alterato `RING_AUTO`.

Vincoli aggiunti al DSN (Freerouting non li conosce dal file KiCad):
- strisce di keepout a 0.6 mm dal bordo (copper-to-edge 0.5);
- keepout F.Cu: sagome speaker, corpo di U3, U5 e U6, pad+stub+via d'ingresso delle catene (ingresso obbligato su B.Cu);
- keepout B.Cu per la continuità del piano: fascia perimetrale interna alla corona (con finestre agli ingressi A/B/C/D), nucleo di U3 + corridoio verso nord, tasca USB‑C e corridoio dorsale/ponte +5V, corridoio a nord di U6;
- solo le 29 net ancora scollegate dopo la Fase A sono instradabili; le altre restano ostacoli fissi.

Correzioni via script dopo Freerouting: LED_B_DIN, LED_C_DIN, LED_D_DIN (non completate da Freerouting); AUD_BCLK, AUD_DIN, AMP_SHDN verso U101 spostate dal F.Cu a filo del bordo della FOTO (sopra la dorsale +5V) a tre piste su B.Cu affiancate a x = 188.6/189.4/190.0; legame GND F.Cu C4.2 → R7.1.
Elementi finali: **435 piste, 54 via**.

## 3. Conteggi DRC per fase

| | Errori | Unconnected | Warning |
|---|---|---|---|
| Baseline (`drc_00_baseline.json`) | 0 | 133 | 18 = 14 `lib_footprint_mismatch` + 4 `via_dangling` (via d'ingresso catene) |
| Dopo Fase A (`drc_A.json`) | 0 | 49 (solo net della Fase B) | 18 = 14 `lib_footprint_mismatch` + 4 `via_dangling` |
| Dopo Fase B (`drc_B.json`) | **0** | **0** | **14 `lib_footprint_mismatch`** |

Parità con lo schematico (`kicad-cli pcb drc --schematic-parity`, `tools/drc_B_parity.json`): 0 problemi.

## 4. Criteri di accettazione

| Criterio | Esito | Verifica |
|---|---|---|
| DRC 0 errori | ✅ | `drc_B.json` |
| Warning ammessi solo U3 | ⚠️ 13 in più, vedi sotto | `drc_B.json` |
| 0 unconnected | ✅ | `drc_B.json` |
| Niente rame F.Cu né via in FOTO | ✅ (0 piste F.Cu, 0 via; distanza minima del rame F.Cu dal bordo FOTO 0.43 mm) | `scripts/phaseB/keepcheck.py` + DRC rule area |
| Niente rame in NFC e zona antenna | ✅ (0 elementi) | come sopra |
| Sagome speaker: nessun rame F.Cu nuovo | ✅ (0 piste, 0 via) | come sopra |
| `RING_AUTO` invariato | ✅ 2517 piste + 367 via, geometria identica elemento per elemento rispetto al commit `pre-routing` | `tools/verify_B.json` |
| Nessun componente spostato | ✅ (0 footprint con posizione/rotazione/lato diversi) | `tools/verify_B.json` |
| Larghezze alimentazioni | ✅ come da tabella §2 | `tools/verify_B.json` (`widths`) |

**Warning `lib_footprint_mismatch` oltre U3 (13):** D317, D318, D319, D426, D427, D428, D526 (WS2812B-2020) e C216, C318, C319, C426, C427, C428 (0402). Sono **già presenti nella baseline**, riguardano footprint della corona che non dovevo toccare; non li ho modificati.

## 5. Compromessi e scostamenti dal brief

1. **USB, 2 via su D−.** Con l'orientamento di U2 e U5 l'ordine dei pin si inverte: senza spostare/ruotare componenti un incrocio è inevitabile. D− fa un salto su B.Cu di ~2.8 mm vicino a (157–159, 279–281). Differenza di lunghezza 4.3 mm (~25 ps): trascurabile per USB Full Speed.
2. **Ponte VBUS A9/B4 su B.Cu** (2+2 via 0.8/0.4) e **VBUS di U2.5 con via**: i pad CC sono interni ai VBUS e U2.5 è racchiuso da D+/D−. CC1/CC2 passano su B.Cu con via.
3. **Uscite audio.** Il brief dice "U102 → J101; U101 → J102": ho seguito la netlist (U102 → J102, U101 → J101). OUTN gira a ovest del connettore per rispettare l'ordine dei pin: le due piste sono affiancate ma OUTN è più lunga (~23 vs ~12 mm).
4. **EP di U101/U102 senza via nel footprint** (contrariamente al brief): ho aggiunto 2 via 0.6/0.3 nel pad esposto e legato i pin GND 3/11/15 all'EP. Via nel pad non tappate: per l'assemblaggio JLCPCB valuta l'opzione via-in-pad/plugging.
5. **C69 GND**: (dopo §8) C69.2 sul fronte ha 2 via GND 0.6/0.3 proprie verso il piano B.Cu.
6. **Continuità del piano GND**: con piste lunghe sul retro alcune zone del piano restano collegate solo tramite ponti F.Cu: spina GND sotto U6 → U6.7 → via GND della corona (D541), J1 schermo → R1.2/R2.2, C4.2 → R7.1. Il riempimento B.Cu contiene ancora un'isola di ~1035 mm² attorno a U6/C4 (già presente a fine Fase B, ~1025 mm²), collegata elettricamente a GND (DRC 0 unconnected) ma tramite questi ponti e non con continuità diretta del piano.
7. **Rame sul fronte fuori dalla foto**: alcune net (LED_C_3V3 in basso a sinistra a y≈288.7, linee locali attorno a U3, U6, U5) sono su F.Cu nelle aree libere tra corona e foto; nessuna dentro FOTO o sagome speaker.
8. **Neck-down residui**: 3 segmenti sotto 0.25 mm (0.15–0.187 mm, ≥ track min 0.15) in prossimità dei pin, dove 0.25 non rispetta la clearance.
9. **R101.2** collegata a +5V con 0.25 mm (larghezza non specificata nel brief; uguale a R102).
10. La net class `Power` (1.5 mm) non risulta assegnata a +5V/GND/VBUS nel DSN esportato (tutte le net sono in `Default`). Non ha influito sul routing (le larghezze sono imposte da script), ma è da verificare in Board Setup.

## 6. Elenco commit

| Hash | Messaggio |
|---|---|
| `a861094` | pre-routing |
| `0e0e22c` | Phase A: critical routing (CRITICAL_AUTO) - power, USB, audio outputs, GND vias |
| `7363f8d` | Phase B: Freerouting 2.5.0 + scripted fixes (FREEROUTE_AUTO), GND plane continuity |
| `76d5e0a` | docs: ROUTING_REPORT.md |
| (§8) | Art + 3D: foto sul fronte, speaker Makerverse sul fronte, C69 sul fronte a destra di J1 |

## 7. Stato

Fermo al punto di stop "fine Fase B": **nessun lavoro su Gerber o file di produzione**.
Consigliato prima della produzione: controllo visivo in KiCad (pcbnew + 3D), in particolare tasca USB-C, zona U6/C4 (punto 6) e via negli EP (punto 4).

## 8. Foto, speaker 3D e C69 sul fronte (richiesta successiva, con approvazione)

Richiesta: foto come footprint su F.Cu + F.Mask visibile in 3D, volti al centro, nessun volto tagliato in alto, foto non rimpicciolita; speaker Makerverse 8 Ω 5 W (Core Electronics CE08483) in 3D; **tutto sul fronte**; C69 spostato sul fronte **a destra di J1** (scelta tua).

| Elemento | Realizzazione | File |
|---|---|---|
| Foto | `art/foto.jpeg` → crop (0,190)–(665,808) px, autocontrast + unsharp + gamma 1.1, dithering Floyd–Steinberg a 0.35 mm/pixel → 33 985 rettangoli su F.Cu e F.Mask (rame dorato esposto = chiaro). Footprint `ART1` (board-only, nessuna net) centrato sulla FOTO (105, 142), stessa area della zona FOTO | `scripts/art/make_art.py`, `scripts/art/gen_fp.py`, `fra_clock.pretty/ART_FOTO.kicad_mod` |
| Speaker | Footprint `LS1` (105, 36.5) e `LS2` (105, 247.5) sul **fronte**, solo F.Fab + modello 3D; fori di fissaggio 91.2 × 36.2 mm coincidenti con H3–H6 / H9–H12. Dimensioni dal datasheet CE08483: 100 × 45 × 21 mm, 2 coni Ø35 | `fra_clock.pretty/Speaker_Makerverse_CE08483_100x45.kicad_mod`, `3d/Speaker_Makerverse_CE08483.wrl` |
| Gruppo | `ART_3D` (ART1, LS1, LS2), elementi bloccati | `scripts/art/place_art.py` |
| Rule area FOTO | consentiti i footprint (necessario per ART1); restano vietati piste, via, pad e riempimenti | — |
| Libreria | `fp-lib-table` di progetto: `fra_clock` → `${KIPRJMOD}/fra_clock.pretty` | — |
| C69 | Sul fronte a (138, 284.8), +5V (pad 1) a est; collegamenti rigenerati in `CRITICAL_AUTO` (`scripts/phaseA/pa_pwr.py`, `pa_gnd.py`) | `scripts/art/move_c69.py` |

Verifiche dopo §8 (`drc_D.json`, `tools/verify_D.json`, `tools/keepcheck_D.json`):

| Criterio | Esito |
|---|---|
| DRC errori / unconnected | **0 / 0** (courtyard inclusi) |
| Warning | 14 `lib_footprint_mismatch`, identici alla baseline |
| `RING_AUTO` | identico (2517 piste + 367 via) |
| Componenti spostati rispetto a `pre-routing` | solo **C69** (approvato) |
| Rame F.Cu / via in FOTO, rame in NFC/antenna, rame nuovo F.Cu sotto gli speaker | 0 / 0 / 0 / 0 |

Note: la sezione "Rame in antenna" di `verify.py` segnala 5 elementi solo per sovrapposizione di bounding-box (stessa lista già in `verify_B.json`); il controllo geometrico preciso (`keepcheck`) dà 0. I render 3D sono in `tools/render_D_top.png`, `tools/render_D_iso.png`, `tools/render_D_bottom.png` (esclusi da git).
