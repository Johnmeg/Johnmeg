import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','generador_diseno'))
import flowcharts as F
from flowcharts import header_box, box, arrow, stage_label, new_canvas, finish
from flowcharts import NAVY, BLUE, BLUE_D, LBLUE, RED, LRED, GREEN, LGREEN, GREY, LGREY, WHITE, AMBER, LAMBER
OUT="img_ds"; os.makedirs(OUT, exist_ok=True)

def pipeline(path, title, subtitle, stages, hcolors, footer=None, stagelabels=None, h=5.2):
    fig, ax, top = new_canvas(w=13.4, h=h, title=title, subtitle=subtitle)
    N=len(stages); gap=3.5; x0=3.0; x1=97.0
    bw=(x1-x0-(N-1)*gap)/N; cy=(top-8)/2+1; bh=min(18, top-16)
    cxs=[x0+bw/2+i*(bw+gap) for i in range(N)]
    if stagelabels:
        for cx,lb in zip(cxs, stagelabels): stage_label(ax, cx, top-8.5, lb, color=NAVY)
    for cx,(t,b),hc in zip(cxs, stages, hcolors):
        header_box(ax, cx, cy, bw, bh, t, b, hc=hc, fs=7.9, wrap=int(bw*1.05))
    for i in range(N-1):
        arrow(ax,(cxs[i]+bw/2,cy),(cxs[i+1]-bw/2,cy), color=NAVY, lw=2.2)
    if footer:
        ax.text(3, 3.0, footer, ha="left", va="center", fontsize=8.4, color=GREY, style="italic")
    finish(fig, path); print("saved", path)

# ---- 1: Carga manual CSV ----
pipeline(f"{OUT}/p1_manual.png",
  "Propuesta 1 — Carga manual (Import CSV a tabla local)",
  "Ideal para cargas puntuales o piloto, sin infraestructura adicional",
  [("Presupuesto\ncomercial","Archivo Excel del negocio"),
   ("Preparación","Exportar a CSV (UTF-8) y validar columnas"),
   ("SAP Datasphere","Data Builder · Import CSV → Tabla local"),
   ("Modelado","Vista analítica (medidas y atributos)"),
   ("Consumo","SAP Analytics Cloud")],
  [GREEN, AMBER, BLUE, NAVY, "6B21A8" if False else NAVY],
  footer="Ventaja: rápido, sin infraestructura.  ·  Límite: manual, no automatizable, requiere convertir Excel→CSV.",
  stagelabels=["FUENTE","PREPARACIÓN","CARGA","MODELADO","CONSUMO"])

# ---- 2: Cloud Storage + Replication Flow ----
pipeline(f"{OUT}/p2_cloudstorage.png",
  "Propuesta 2 — Almacenamiento en la nube + Replication Flow (recomendada)",
  "Carga recurrente y automatizada del presupuesto comercial",
  [("Presupuesto\ncomercial","Excel → CSV / Parquet"),
   ("Cloud Storage","Amazon S3 · Azure Blob · Google Cloud Storage · SFTP"),
   ("Conexión","SAP Datasphere · Conexión al Cloud Storage"),
   ("Ingesta","Replication Flow / Data Flow (programado)"),
   ("Tabla + Vista","Tabla local → Vista analítica"),
   ("Consumo","SAP Analytics Cloud")],
  [GREEN, AMBER, BLUE, BLUE, NAVY, NAVY],
  footer="Ventaja: automatizable, programado, mayor volumen, carga por periodo.  ·  Requiere: servicio de almacenamiento y convención de archivos.",
  stagelabels=["FUENTE","ALMACENAMIENTO","CONEXIÓN","INGESTA","MODELADO","CONSUMO"])

# ---- 3: Open SQL Schema + Python ----
pipeline(f"{OUT}/p3_opensql.png",
  "Propuesta 3 — Open SQL Schema + carga programática (Python)",
  "Automatización total con validación y transformación en el proceso",
  [("Presupuesto\ncomercial","Archivo Excel"),
   ("Proceso Python","pandas: lee, valida y normaliza (pivotea meses)"),
   ("Open SQL Schema","Usuario de BD · hdbcli / hana_ml (JDBC/ODBC)"),
   ("Tabla del Space","Tabla expuesta al Space de Datasphere"),
   ("Vista","Vista analítica"),
   ("Consumo","SAP Analytics Cloud")],
  [GREEN, AMBER, BLUE, BLUE, NAVY, NAVY],
  footer="Ventaja: control total, integrable en pipelines, validaciones.  ·  Requiere: desarrollo y gobierno de credenciales.",
  stagelabels=["FUENTE","PROCESO","CONEXIÓN","TABLA","MODELADO","CONSUMO"])

# ---- 4: Integration Suite / ETL ----
pipeline(f"{OUT}/p4_integrationsuite.png",
  "Propuesta 4 — SAP Integration Suite / ETL (empresarial)",
  "Orquestación corporativa con monitoreo y reintentos",
  [("Presupuesto\ncomercial","Excel u origen del negocio"),
   ("Orquestación","SAP Integration Suite (iFlow) o ETL (SAP DI / socio)"),
   ("Destino","SAP Datasphere · Open SQL / Object Store"),
   ("Tabla + Vista","Tabla local → Vista analítica"),
   ("Consumo","SAP Analytics Cloud")],
  [GREEN, AMBER, BLUE, NAVY, NAVY],
  footer="Ventaja: orquestación, monitoreo, integración corporativa.  ·  Requiere: plataforma/licencias y equipo especializado.",
  stagelabels=["FUENTE","ORQUESTACIÓN","DESTINO","MODELADO","CONSUMO"])
print("pipelines OK")
