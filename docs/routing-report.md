# fra_clock — Report di routing (KiCad 10)

Data: 2026-10-11 (aggiornato 2026-10-12) · Board: `hardware/fra_clock.kicad_pcb`

> Percorsi e hash dei commit sono aggiornati alla struttura della repo GitHub `fra-clock` (riorganizzata il 2026-10-12; la storia è stata riscritta solo nell'email dell'autore, quindi gli hash differiscono da quelli della repo locale originale).
Coordinate nel report: **relative all'angolo (50, 50)** come nel brief (assoluta = relativa + 50).

Fonti dei numeri riportati: `docs/checks/drc_00_baseline.json`, `docs/checks/drc_A.json`, `docs/checks/drc_B.json`, `docs/checks/drc_D.json`, `docs/checks/drc_E.json`, `docs/checks/drc_B_parity.json`, `docs/checks/verify_B.json`, `docs/checks/verify_D.json`, `docs/checks/verify_E.json` (script `scripts/kicad/verify.py`), `docs/checks/keepcheck_D.json`, `git log`.

## 1. Strumenti e versioni

| Strumento | Versione / percorso |
|---|---|
| KiCad / kicad-cli | 10.0.5 — `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` |
| Python KiCad + `pcbnew` | Python 3.9 bundled — `.../Frameworks/Python.framework/Versions/Current/bin/python3`, `pcbnew.Version()` = 10.0.5 (import da Python esterno OK, `ExportSpecctraDSN`/`ImportSpecctraSES` presenti) |
| Java | OpenJDK 27 (Homebrew, `/opt/homebrew/opt/openjdk/bin/java`, nessun link in `/usr/bin`) |
| Freerouting | 2.5.0 (release del 2026-10-05), jar in `tools/freerouting/` (escluso da git). SHA-256 `f6f51bb0…5de3c7` |
| Router/verifiche ausiliarie | script Python propri (A* su griglia 0.1 mm + DRC locale con shapely) in `scripts/routing/phase_a/` e `scripts/routing/phase_b/` |

Telemetria di Freerouting: disattivata dal 2° lancio in poi (`--profile.allow_telemetry=false --usage_and_diagnostic_data.disable_analytics=true`). **Il primo lancio di prova è partito con le impostazioni di default (telemetria attiva).**

## 2. Cosa è stato fatto

### Fase 0 — Preparazione
- KiCad aveva il progetto aperto: chiuso da te su richiesta prima di qualsiasi modifica.
- `git init` (repo locale, identità locale *Alberto Boffi*), `.gitignore` per `.history/`, lock, `tools/`, `*.ses`.
- DRC di partenza → `docs/checks/drc_00_baseline.json`.

### Fase A — Routing critico (gruppo `CRITICAL_AUTO`, script, nessun autorouter)
Geometria generata da script (`scripts/routing/phase_a/*.py` → `scripts/routing/data/critical.json`), applicata con `scripts/kicad/apply_group.py` (rilanciabile: cancella e ricrea il gruppo), zone riempite con `kicad-cli pcb drc --refill-zones --save-board`.
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
Flusso: export DSN da una **copia in memoria** della board con tutto bloccato (`scripts/kicad/export_dsn.py`) → `scripts/routing/dsn_prepare.py` → Freerouting headless (`scripts/routing/run_freerouting.sh`, 20 passate, fanout disattivato) → conversione SES→JSON (`ses2json.py`) → correzioni con il router A* (`scripts/routing/phase_b/fix_B2.py`) → allargamento dei neck-down dove possibile (`widen.py`) → applicazione con lo stesso `apply_group.py`.
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
| Baseline (`docs/checks/drc_00_baseline.json`) | 0 | 133 | 18 = 14 `lib_footprint_mismatch` + 4 `via_dangling` (via d'ingresso catene) |
| Dopo Fase A (`docs/checks/drc_A.json`) | 0 | 49 (solo net della Fase B) | 18 = 14 `lib_footprint_mismatch` + 4 `via_dangling` |
| Dopo Fase B (`docs/checks/drc_B.json`) | **0** | **0** | **14 `lib_footprint_mismatch`** |

Parità con lo schematico (`kicad-cli pcb drc --schematic-parity`, `docs/checks/drc_B_parity.json`): 0 problemi.

## 4. Criteri di accettazione

| Criterio | Esito | Verifica |
|---|---|---|
| DRC 0 errori | ✅ | `docs/checks/drc_B.json` |
| Warning ammessi solo U3 | ⚠️ 13 in più, vedi sotto | `docs/checks/drc_B.json` |
| 0 unconnected | ✅ | `docs/checks/drc_B.json` |
| Niente rame F.Cu né via in FOTO | ✅ (0 piste F.Cu, 0 via; distanza minima del rame F.Cu dal bordo FOTO 0.43 mm) | `scripts/routing/phase_b/keepcheck.py` + DRC rule area |
| Niente rame in NFC e zona antenna | ✅ (0 elementi) | come sopra |
| Sagome speaker: nessun rame F.Cu nuovo | ✅ (0 piste, 0 via) | come sopra |
| `RING_AUTO` invariato | ✅ 2517 piste + 367 via, geometria identica elemento per elemento rispetto al commit `pre-routing` | `docs/checks/verify_B.json` |
| Nessun componente spostato | ✅ (0 footprint con posizione/rotazione/lato diversi) | `docs/checks/verify_B.json` |
| Larghezze alimentazioni | ✅ come da tabella §2 | `docs/checks/verify_B.json` (`widths`) |

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
| `8a86c4b` | pre-routing |
| `a22fa12` | Phase A: critical routing (CRITICAL_AUTO) - power, USB, audio outputs, GND vias |
| `33cb8d0` | Phase B: Freerouting 2.5.0 + scripted fixes (FREEROUTE_AUTO), GND plane continuity |
| `2e2b028` | docs: ROUTING_REPORT.md |
| `465a5c6` | Art + 3D: foto sul fronte, speaker Makerverse sul fronte, C69 sul fronte a destra di J1 |
| `3c2f798` | 3D: modelli LCSC/EasyEDA (§9) |
| `f2e144c`, `8ff1b95` | Production: Gerber, forature, BOM/CPL JLCPCB (§10–11) |
| (ultimo) | Riorganizzazione della repo per GitHub |

## 7. Stato

Fermo al punto di stop "fine Fase B": **nessun lavoro su Gerber o file di produzione**.
Consigliato prima della produzione: controllo visivo in KiCad (pcbnew + 3D), in particolare tasca USB-C, zona U6/C4 (punto 6) e via negli EP (punto 4).

## 8. Foto, speaker 3D e C69 sul fronte (richiesta successiva, con approvazione)

Richiesta: foto come footprint su F.Cu + F.Mask visibile in 3D, volti al centro, nessun volto tagliato in alto, foto non rimpicciolita; speaker Makerverse 8 Ω 5 W (Core Electronics CE08483) in 3D; **tutto sul fronte**; C69 spostato sul fronte **a destra di J1** (scelta tua).

| Elemento | Realizzazione | File |
|---|---|---|
| Foto | `art/source/foto.jpeg` → crop (0,190)–(665,808) px, autocontrast + unsharp + gamma 1.1, dithering Floyd–Steinberg a 0.35 mm/pixel → 33 985 rettangoli su F.Cu e F.Mask (rame dorato esposto = chiaro). Footprint `ART1` (board-only, nessuna net) centrato sulla FOTO (105, 142), stessa area della zona FOTO | `scripts/art/make_art.py`, `scripts/art/gen_fp.py`, `hardware/fra_clock.pretty/ART_FOTO.kicad_mod` |
| Speaker | Footprint `LS1` (105, 36.5) e `LS2` (105, 247.5) sul **fronte**, solo F.Fab + modello 3D; fori di fissaggio 91.2 × 36.2 mm coincidenti con H3–H6 / H9–H12. Dimensioni dal datasheet CE08483: 100 × 45 × 21 mm, 2 coni Ø35 | `hardware/fra_clock.pretty/Speaker_Makerverse_CE08483_100x45.kicad_mod`, `hardware/3d/Speaker_Makerverse_CE08483.wrl` |
| Gruppo | `ART_3D` (ART1, LS1, LS2), elementi bloccati | `scripts/art/place_art.py` |
| Rule area FOTO | consentiti i footprint (necessario per ART1); restano vietati piste, via, pad e riempimenti | — |
| Libreria | `fp-lib-table` di progetto: `fra_clock` → `${KIPRJMOD}/fra_clock.pretty` | — |
| C69 | Sul fronte a (138, 284.8), +5V (pad 1) a est; collegamenti rigenerati in `CRITICAL_AUTO` (`scripts/routing/phase_a/pa_pwr.py`, `pa_gnd.py`) | `scripts/art/move_c69.py` |

Verifiche dopo §8 (`docs/checks/drc_D.json`, `docs/checks/verify_D.json`, `docs/checks/keepcheck_D.json`):

| Criterio | Esito |
|---|---|
| DRC errori / unconnected | **0 / 0** (courtyard inclusi) |
| Warning | 14 `lib_footprint_mismatch`, identici alla baseline |
| `RING_AUTO` | identico (2517 piste + 367 via) |
| Componenti spostati rispetto a `pre-routing` | solo **C69** (approvato) |
| Rame F.Cu / via in FOTO, rame in NFC/antenna, rame nuovo F.Cu sotto gli speaker | 0 / 0 / 0 / 0 |

Note: la sezione "Rame in antenna" di `verify.py` segnala 5 elementi solo per sovrapposizione di bounding-box (stessa lista già in `verify_B.json`); il controllo geometrico preciso (`keepcheck`) dà 0. I render 3D aggiornati (con i modelli del §9) sono in `docs/images/render_top.png` e `docs/images/render_iso.png`.

## 9. Modelli 3D mancanti (2026-10-12)

Diversi footprint della libreria KiCad puntavano a modelli 3D che non ci sono nella libreria 3D di KiCad 10.0.5 installata. Ho scaricato i modelli da LCSC/EasyEDA con `easyeda2kicad` 1.0.1 (installato da te): file STEP + WRL in `hardware/3d/lcsc/lcsc.3dshapes/`. Li ho assegnati ai footprint della scheda con `scripts/art/set_models.py`.

| Rif. | Componente | Codice LCSC | Modello | Offset / rotazione |
|---|---|---|---|---|
| J1 | HRO TYPE-C-31-M-12 | C165948 | `USB-C_SMD-TYPE-C-31-M-12_1.step` | Y +1.41 mm, Z 180° (allineato su fori SH/NPTH) |
| J101, J102 | JST S2B-PH-SM4-TB | C295747 | `CONN-SMD_P2.00_S2B-PH-SM4-TB-LF-SN.step` | 0 / 0° |
| 180 LED dell'anello (D2xx–D5xx) | WS2812B-2020 | C965555 | `LED-SMD_4P-L2.0-W2.0-H0.8-TL_WS2812B-2020.step` | 0 / 0° |
| U101, U102 | MAX98357A TQFN-16 3×3 | C910544 | `TQFN-16_L3.0-W3.0-P0.50-BL-EP1.5.step` | 0 / Z 90° (pin 1 verificato nel render) |
| F1 | fusibile 1812 | — | `${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_1812_4532Metric.step` (generico) | 0 / 0° |

Speaker LS1/LS2: resta il modello che ho costruito io dal disegno Core Electronics (non esiste un 3D ufficiale del CE08483). Senza modello, com'è normale: fori di montaggio, test point, ART1.

Verifiche (`docs/checks/drc_E.json`, `docs/checks/verify_E.json`): 0 errori, 0 unconnected, parità con lo schematico 0, gli stessi 14 `lib_footprint_mismatch` della baseline. `RING_AUTO` identico; nessun componente spostato oltre C69 (§8). Render: `docs/images/render_top.png`, `docs/images/render_iso.png`.

## 10. Gerber e forature (2026-10-12, su tua autorizzazione)

Generati con `kicad-cli` 10.0.5 dalla board al commit `3c2f798` (git pulito), in `production/gerber/`. Pacchetto da caricare: `production/fra_clock_gerber_jlcpcb.zip`.

| Impostazione | Valore |
|---|---|
| Layer | F.Cu, B.Cu, F/B.Paste, F/B.Silkscreen, F/B.Mask, Edge.Cuts |
| Formato | Gerber X2 con attributi netlist, precisione 6, estensioni Protel (`.gtl/.gbl/.gts/...`), silkscreen sottratto dalla maschera, controllo riempimento zone (`--check-zones`) |
| Forature | Excellon, mm, decimale, origine assoluta, asole in modo "alternate", PTH e NPTH separati, mappe Gerber X2 (non nello zip) |
| Scheda | 2 layer, 210 × 297 mm, angoli R3 |
| Fori PTH | 0.30 mm × 483, 0.40 × 17, 0.60 × 4, 3.20 × 6 (M3), 4.30 × 8 (M4) |
| Fori NPTH | 0.65 mm × 2 (perni USB-C) |

Controllo: render dei Gerber con gerbonara 1.6.3 (`production/preview/gerber_top.png`, `production/preview/gerber_bottom.png`). Rame, maschera, serigrafia, fori e contorno coincidono con la board (foto esposta sul fronte, piano GND sul retro, zone NFC/antenna libere).

Da scegliere al momento dell'ordine (non sono nei Gerber):
- **Finitura**: ENIG dà la foto dorata e piatta come nei render; con HASL il rame esposto della foto diventa stagno argentato e meno uniforme.
- **Colore maschera**: determina il contrasto della foto (i render usano il verde).
- **Spessore** (1.6 mm standard) e **via tented** (default).
- Via nel pad esposto di U101/U102 non tappate (§5.4): rilevante solo se la scheda viene assemblata/rifusa.
- BOM e file di piazzamento (CPL) per l'assemblaggio non sono stati generati.

## 11. BOM e CPL per l'assemblaggio JLCPCB (2026-10-12)

File: `production/assembly/fra_clock_BOM_JLCPCB.csv` (24 righe, 408 componenti) e `production/assembly/fra_clock_CPL_JLCPCB.csv` (408 posizioni, tutte sul lato Top). Generati dalla board con `scripts/production/dump_fps.py` + `scripts/production/make_bom_cpl.py` (rigenerabili).

Esclusi da BOM e CPL: ART1, LS1/LS2 (board-only), fori H1–H14, test point TP1–TP3 (solo pad). Il tag NFC (NFC1 nello schematico, "NTAG216 tag") non ha footprint: è un adesivo da applicare a parte.

| Componenti | LCSC | Codice costruttore | Note |
|---|---|---|---|
| 100nF 0402 ×182 | C1525 | CL05B104KO5NNNC | |
| 100nF 0603 ×4 | C14663 | CC0603KRX7R9BB104 | Basic |
| 1uF 0603 | C15849 | CL10A105KB8NNNC | |
| 10uF 0805 ×5 | C15850 | CL21A106KAYNNNE | |
| 22uF 0805 | C45783 | CL21A226MAQNNNE | Basic, 25 V |
| 470uF C69 | C82006 | RVT1C471M0810 | 16 V, D8×10.2, Extended |
| Resistenze 0603 | C25804 / C23186 / C22935 / C23179 / C23140 / C25803 | UNI-ROYAL 0603WAF… | 10k / 5.1k / 1M / 470 / 33 / 100k |
| F1 PTC 2A | C20812 | SMD1812P200TF16 | hold 2 A, trip 4 A, 16 V |
| Q1/Q2 | C20526 | MMBT3904 | |
| Q3 | C8545 | 2N7002 | Basic |
| U1 | C51118 | AP2112K-3.3TRG1 | Extended |
| U2 | C7519 | USBLC6-2SC6 | Extended |
| U3 | C701341 | ESP32-WROOM-32E-N4 | **da confermare la flash**: N8 = C701342, N16 = C701343 |
| U5 | C84681 | CH340C | Extended |
| U6 | C554502 | 74AHCT125D,118 | |
| U101/U102 | C910544 | MAX98357AETE+T | |
| D201…(180) | C965555 | WS2812B-2020 | |
| J1 | C165948 | TYPE-C-31-M-12 | |
| J101/J102 | C295747 | S2B-PH-SM4-TB(LF)(SN) | |

Fonti dei codici: pagine prodotto JLCPCB/LCSC consultate il 2026-10-12 (MPN, valore, package; classe Basic/Extended dove indicata sulla pagina). **Disponibilità a magazzino e prezzi non verificati**: li mostra JLCPCB al caricamento.

CPL: coordinate = origine del footprint KiCad, assolute, Y invertita (stesso sistema dei Gerber); rotazione = orientamento KiCad. Le rotazioni e i centri di alcuni package possono non coincidere con la libreria JLCPCB: nell'anteprima di piazzamento controllare in particolare SOT-23/-5/-6, SOIC-14/16, TQFN (pin 1), WS2812B-2020 (pin 1), ESP32 (antenna verso il bordo), USB-C, JST, polarità di C69.
