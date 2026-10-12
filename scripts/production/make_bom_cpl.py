"""JLCPCB BOM + CPL for fra_clock from the board file (footprint origins, absolute coords, Y negated = Gerber frame)."""
import json, csv, re, collections, sys
F = json.load(open(sys.argv[1]))
# (value, footprint lib id) -> (LCSC, MPN, package label)
PARTS = {
 ("100nF", "Capacitor_SMD:C_0402_1005Metric"): ("C1525", "CL05B104KO5NNNC", "0402"),
 ("100nF", "Capacitor_SMD:C_0603_1608Metric"): ("C14663", "CC0603KRX7R9BB104", "0603"),
 ("1uF", "Capacitor_SMD:C_0603_1608Metric"): ("C15849", "CL10A105KB8NNNC", "0603"),
 ("10uF", "Capacitor_SMD:C_0805_2012Metric"): ("C15850", "CL21A106KAYNNNE", "0805"),
 ("22uF", "Capacitor_SMD:C_0805_2012Metric"): ("C45783", "CL21A226MAQNNNE", "0805"),
 ("470uF", "Capacitor_SMD:CP_Elec_8x10"): ("C82006", "RVT1C471M0810 (16V)", "SMD D8xL10.2"),
 ("10k", "Resistor_SMD:R_0603_1608Metric"): ("C25804", "0603WAF1002T5E", "0603"),
 ("5.1k", "Resistor_SMD:R_0603_1608Metric"): ("C23186", "0603WAF5101T5E", "0603"),
 ("1M", "Resistor_SMD:R_0603_1608Metric"): ("C22935", "0603WAF1004T5E", "0603"),
 ("470", "Resistor_SMD:R_0603_1608Metric"): ("C23179", "0603WAF4700T5E", "0603"),
 ("33", "Resistor_SMD:R_0603_1608Metric"): ("C23140", "0603WAF330JT5E", "0603"),
 ("100k", "Resistor_SMD:R_0603_1608Metric"): ("C25803", "0603WAF1003T5E", "0603"),
 ("2A", "Fuse:Fuse_1812_4532Metric"): ("C20812", "SMD1812P200TF16 (PTC 2A hold)", "1812"),
 ("MMBT3904", "Package_TO_SOT_SMD:SOT-23"): ("C20526", "MMBT3904", "SOT-23"),
 ("2N7002", "Package_TO_SOT_SMD:SOT-23"): ("C8545", "2N7002", "SOT-23"),
 ("AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5"): ("C51118", "AP2112K-3.3TRG1", "SOT-23-5"),
 ("USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6"): ("C7519", "USBLC6-2SC6", "SOT-23-6"),
 ("CH340C", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"): ("C84681", "CH340C", "SOIC-16"),
 ("74AHCT125", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"): ("C554502", "74AHCT125D,118", "SOIC-14"),
 ("ESP32-WROOM-32E", "RF_Module:ESP32-WROOM-32E"): ("C701341", "ESP32-WROOM-32E-N4", "Module"),
 ("MAX98357A", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm"): ("C910544", "MAX98357AETE+T", "TQFN-16 3x3"),
 ("WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm"): ("C965555", "WS2812B-2020", "2020"),
 ("USB_C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"): ("C165948", "TYPE-C-31-M-12", "USB-C SMD"),
 ("SPK_TOP", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal"): ("C295747", "S2B-PH-SM4-TB(LF)(SN)", "JST PH 2P SMD"),
 ("SPK_BOT", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal"): ("C295747", "S2B-PH-SM4-TB(LF)(SN)", "JST PH 2P SMD"),
}
def nat(s): return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]
skip, used = [], []
for f in F:
    if "board_only" in f["attr"] or "exclude_from_bom" in f["attr"] or f["lib"].startswith("TestPoint:"):
        skip.append(f["ref"]); continue
    key = (f["val"], f["lib"])
    if key not in PARTS: sys.exit("missing part for %s %s" % (f["ref"], key))
    used.append(f)
groups = collections.OrderedDict()
for f in sorted(used, key=lambda f: nat(f["ref"])):
    lc, mpn, pkg = PARTS[(f["val"], f["lib"])]
    groups.setdefault((lc, f["val"] if not f["val"].startswith("SPK") else "S2B-PH-SM4-TB", pkg, mpn), []).append(f["ref"])
with open("fra_clock_BOM_JLCPCB.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part", "Quantity"])
    for (lc, val, pkg, mpn), refs in sorted(groups.items(), key=lambda kv: nat(kv[1][0])):
        w.writerow([val, ",".join(refs), pkg, lc, mpn, len(refs)])
with open("fra_clock_CPL_JLCPCB.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for f in sorted(used, key=lambda f: nat(f["ref"])):
        w.writerow([f["ref"], "%.4fmm" % f["x"], "%.4fmm" % (-f["y"]), "Top" if f["layer"] == "F.Cu" else "Bottom", "%g" % (f["rot"] % 360)])
print("placed", len(used), "lines", len(groups), "skipped", sorted(skip, key=nat))
