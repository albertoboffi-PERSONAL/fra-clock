"""SES -> items, find unrouted connections, route them with the local router, widen neck-downs."""
import json, sys, subprocess
from model import Board
from conn import connectivity
import ses2json
ses, tag = sys.argv[1], sys.argv[2]
F = ses2json.convert(ses, "fr_%s.json" % tag)
A = json.load(open("critical.json"))
b = Board("geom0.json"); b.add(A + F)
print("fr items", len(F), "viol", len(b.check(F, verbose=True)))
NETS = ['+3V3','/AMP_SD','/AMP_SHDN','/AUD_BCLK','/AUD_DIN','/AUD_WS','/ESP_EN','/ESP_IO0','/ESP_RX','/ESP_TX','/I2S_BCLK','/I2S_DOUT','/I2S_WS','/LED_A_3V3','/LED_A_DIN','/LED_B_3V3','/LED_B_DIN','/LED_C_3V3','/LED_C_DIN','/LED_D_3V3','/LED_D_DIN','Net-(Q1-B)','Net-(Q1-E)','Net-(Q2-B)','Net-(Q2-E)','Net-(R13-Pad1)','Net-(R14-Pad1)','Net-(R15-Pad1)','Net-(R8-Pad1)']
miss = connectivity(b, NETS, A + F)
print("unrouted:", miss)
json.dump(miss and {k: [sorted(g) for g in v] for k, v in miss.items()}, open("miss_%s.json" % tag, "w"))
