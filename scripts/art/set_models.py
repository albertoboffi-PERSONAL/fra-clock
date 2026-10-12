"""Assign downloaded LCSC/EasyEDA 3D models (3d/lcsc) to board footprints whose
KiCad-library model file does not exist. usage: set_models.py <board>"""
import sys, pcbnew
P = "${KIPRJMOD}/3d/lcsc/lcsc.3dshapes/"
# fpid -> (file, offset xyz (mm, KiCad 3D: +Y = up on screen), rotate xyz (deg))
MAP = {
 "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12": (P + "USB-C_SMD-TYPE-C-31-M-12_1.step", (0, 1.41, 0), (0, 0, 180)),
 "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal": (P + "CONN-SMD_P2.00_S2B-PH-SM4-TB-LF-SN.step", (0, 0, 0), (0, 0, 0)),
 "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm": (P + "LED-SMD_4P-L2.0-W2.0-H0.8-TL_WS2812B-2020.step", (0, 0, 0), (0, 0, 0)),
 "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm": (P + "TQFN-16_L3.0-W3.0-P0.50-BL-EP1.5.step", (0, 0, 0), (0, 0, 90)),
 "Fuse:Fuse_1812_4532Metric": ("${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_1812_4532Metric.step", (0, 0, 0), (0, 0, 0)),
}
b = pcbnew.LoadBoard(sys.argv[1]); n = {}
for fp in b.GetFootprints():
    k = str(fp.GetFPID().GetUniStringLibId())
    if k not in MAP: continue
    f, off, rot = MAP[k]
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = f
    m.m_Offset = pcbnew.VECTOR3D(*off); m.m_Rotation = pcbnew.VECTOR3D(*rot); m.m_Scale = pcbnew.VECTOR3D(1, 1, 1)
    m.m_Show = True
    fp.Models().clear(); fp.Add3DModel(m)
    n[k] = n.get(k, 0) + 1
for k, v in n.items(): print(v, k)
b.Save(sys.argv[1]); print("saved")
