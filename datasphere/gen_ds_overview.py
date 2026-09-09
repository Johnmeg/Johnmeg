import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','generador_diseno'))
import flowcharts as F
from flowcharts import header_box, box, arrow, stage_label, new_canvas, finish
from flowcharts import NAVY, BLUE, BLUE_D, LBLUE, RED, LRED, GREEN, LGREEN, GREY, LGREY, WHITE, AMBER, LAMBER
OUT="img_ds"

fig, ax, top = new_canvas(w=13.4, h=6.6,
    title="Carga del presupuesto comercial a SAP Datasphere — opciones de arquitectura",
    subtitle="Un mismo archivo de origen, cuatro rutas de ingesta hacia el modelo de consumo")
midy=(top-8)/2+1
# Fuente
box(ax, 11, midy, 17, 11, "Presupuesto\ncomercial\n(Excel)", fc=LGREEN, ec=GREEN, tc="#1A1A1A", bold=True, fs=8.6, wrap=16)
stage_label(ax, 11, top-8.5, "FUENTE", color=GREEN)
# Opciones (4 apiladas)
stage_label(ax, 43, top-8.5, "OPCIONES DE CARGA", color=AMBER)
opts=[("1 · Carga manual (Import CSV a tabla local)",),
      ("2 · Cloud Storage + Replication Flow",),
      ("3 · Open SQL Schema + Python",),
      ("4 · SAP Integration Suite / ETL",)]
oys=[top-13, top-20.5, top-28, top-35.5]
ocx=43; ow=34; oh=5.6
for (t,),oy in zip(opts,oys):
    box(ax, ocx, oy, ow, oh, t, fc=LAMBER, ec=AMBER, tc="#1A1A1A", fs=7.9, wrap=42)
    arrow(ax,(11+17/2, midy),(ocx-ow/2, oy), color=GREY, lw=1.4, rad=0.05)
    arrow(ax,(ocx+ow/2, oy),(70-17/2, midy), color=NAVY, lw=1.6, rad=-0.05)
# Datasphere
header_box(ax, 70, midy, 17, 13, "SAP\nDatasphere", "Tabla local +\nVista analítica\n(Space)", hc=BLUE, fs=8.2, wrap=16)
stage_label(ax, 70, top-8.5, "MODELADO", color=BLUE)
# SAC
box(ax, 90, midy, 15, 11, "SAP Analytics\nCloud\n(Ppto Comercial)", fc=LBLUE, ec=NAVY, tc="#1A1A1A", bold=True, fs=8.2, wrap=16)
stage_label(ax, 90, top-8.5, "CONSUMO", color=NAVY)
arrow(ax,(70+17/2, midy),(90-15/2, midy), color=NAVY, lw=2.2)
ax.text(3, 3.0, "El detalle de campos (dimensiones y medidas) y su aplicabilidad por sociedad se define en la sección de modelo de datos.",
        ha="left", va="center", fontsize=8.2, color=GREY, style="italic")
finish(fig, f"{OUT}/p0_overview.png"); print("saved overview")
