import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','generador_diseno'))
import flowcharts as F
from flowcharts import header_box, arrow, stage_label, new_canvas, finish
from flowcharts import NAVY, BLUE, BLUE_D, LBLUE, RED, LRED, GREEN, LGREEN, GREY, LGREY, WHITE, AMBER, LAMBER

fig, ax, top = new_canvas(w=13.2, h=5.6,
    title="Conexión de importación a Microsoft SharePoint en SAP Analytics Cloud",
    subtitle="Flujo de la solución vía SAP Integration Suite — Open Connectors (Nota SAP 3446524)")

cxs=[14,38,62,86]; cy=19; w=21; h=17
labels=["FUENTE","INTEGRACIÓN (SAP BTP)","SAC — CONEXIÓN","CONSUMO"]
for cx,lb in zip(cxs,labels):
    stage_label(ax, cx, top-9.0, lb, color=NAVY)

header_box(ax, cxs[0], cy, w, h, "Microsoft\nSharePoint", "Sitios y bibliotecas de\ndocumentos (Online)", hc=GREEN, fs=8.8)
header_box(ax, cxs[1], cy, w, h, "SAP BTP · Open\nConnectors", "Instancia del conector\nSharePoint (OAuth)", hc=AMBER, fs=8.8)
header_box(ax, cxs[2], cy, w, h, "SAP Analytics\nCloud", "Conexión de importación\n(query-based)", hc=BLUE, fs=8.8)
header_box(ax, cxs[3], cy, w, h, "Consumo en SAC", "Modelos e historias con\ndatos de SharePoint", hc=NAVY, fs=8.8)

for i in range(3):
    x1=cxs[i]+w/2; x2=cxs[i+1]-w/2
    arrow(ax, (x1,cy),(x2,cy), color=NAVY, lw=2.2)
ax.text((cxs[0]+cxs[1])/2, cy+11.5, "OAuth\nClient ID / Secret", ha="center", va="center", fontsize=7.4, color=GREY, style="italic")
ax.text((cxs[1]+cxs[2])/2, cy+11.5, "API Key / Secret\nMS OAuth Scope", ha="center", va="center", fontsize=7.4, color=GREY, style="italic")

ax.text(2, 3.2, "Acceso de importación de datos (no en vivo). Requiere que Open Connectors esté configurado en SAC (KBA 3435156).",
        ha="left", va="center", fontsize=8.2, color=GREY, style="italic")
finish(fig, "img/sharepoint_sac_flujo.png")
print("saved img/sharepoint_sac_flujo.png")
