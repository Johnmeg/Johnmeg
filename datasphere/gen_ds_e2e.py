import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','generador_diseno'))
import flowcharts as F
from flowcharts import header_box, box, arrow, stage_label, new_canvas, finish
from flowcharts import NAVY, BLUE, BLUE_D, LBLUE, RED, LRED, GREEN, LGREEN, GREY, LGREY, WHITE, AMBER, LAMBER
OUT="img_ds"

# ================= FIG 1: Arquitectura end-to-end =================
fig, ax, top = new_canvas(w=13.4, h=6.8,
  title="Arquitectura end-to-end — Real vs. Presupuesto en SAP Datasphere",
  subtitle="El presupuesto se carga desde el archivo; el real se integra desde S/4HANA; ambos se combinan y se consumen en Power BI o SAC")
up=top-14; lo=top-30; mid=(up+lo)/2
# fuentes
box(ax,11,up,18,9,"Presupuesto\ncomercial (Excel)",fc=LGREEN,ec=GREEN,tc="#1A1A1A",bold=True,fs=8.4,wrap=17)
box(ax,11,lo,18,9,"Datos reales\nSAP S/4HANA\n(ACDOCA · CDS)",fc=LRED,ec=RED,tc="#1A1A1A",bold=True,fs=8.2,wrap=17)
stage_label(ax,11,top-8.5,"FUENTES",color=NAVY)
# integración
box(ax,34,up,19,9,"Carga del archivo\n(opción recomendada)",fc=LAMBER,ec=AMBER,tc="#1A1A1A",fs=8.0,wrap=22)
box(ax,34,lo,19,9,"Replication Flow\n(CDS / ODP)",fc=LAMBER,ec=AMBER,tc="#1A1A1A",fs=8.0,wrap=22)
stage_label(ax,34,top-8.5,"INTEGRACIÓN",color=AMBER)
# datasphere
header_box(ax,58,mid,17,20,"SAP Datasphere\n(Space)","Tabla Presupuesto\n+\nTabla Real",hc=BLUE,fs=8.2,wrap=18)
stage_label(ax,58,top-8.5,"SAP DATASPHERE",color=BLUE)
# modelo
box(ax,78,mid,14,13,"Vista analítica\nReal vs. Presupuesto\n(versión + dimensiones\ncomunes)",fc=LBLUE,ec=NAVY,tc="#1A1A1A",bold=True,fs=7.9,wrap=18)
stage_label(ax,78,top-8.5,"MODELO",color=NAVY)
# consumo
box(ax,93,mid,12,13,"Power BI\n/\nSAP Analytics\nCloud",fc=WHITE,ec=NAVY,tc=NAVY,bold=True,fs=8.0,wrap=15)
stage_label(ax,93,top-8.5,"CONSUMO",color=NAVY)
# flechas
arrow(ax,(20,up),(24.5,up),color=NAVY,lw=2.0); arrow(ax,(20,lo),(24.5,lo),color=NAVY,lw=2.0)
arrow(ax,(43.5,up),(49.5,mid+4),color=NAVY,lw=2.0,rad=-0.08); arrow(ax,(43.5,lo),(49.5,mid-4),color=NAVY,lw=2.0,rad=0.08)
arrow(ax,(66.5,mid),(71,mid),color=NAVY,lw=2.2)
arrow(ax,(85,mid),(87,mid),color=NAVY,lw=2.2)
ax.text(3,3.0,"El reporte Real vs. Presupuesto se genera sobre la vista que combina ambas tablas por sociedad, periodo y dimensiones comunes.",
        ha="left",va="center",fontsize=8.2,color=GREY,style="italic")
finish(fig,f"{OUT}/arch_e2e.png"); print("saved arch_e2e")

# ================= FIG 7: Propuesta recomendada (mejor opción) =================
def pipeline(path,title,subtitle,stages,hcolors,footer,stagelabels,h=5.2):
    fig,ax,top=new_canvas(w=13.4,h=h,title=title,subtitle=subtitle)
    N=len(stages); gap=3.5; x0=3.0; x1=97.0
    bw=(x1-x0-(N-1)*gap)/N; cy=(top-8)/2+1; bh=min(18,top-16)
    cxs=[x0+bw/2+i*(bw+gap) for i in range(N)]
    for cx,lb in zip(cxs,stagelabels): stage_label(ax,cx,top-8.5,lb,color=NAVY)
    for cx,(t,b),hc in zip(cxs,stages,hcolors): header_box(ax,cx,cy,bw,bh,t,b,hc=hc,fs=7.8,wrap=int(bw*1.05))
    for i in range(N-1): arrow(ax,(cxs[i]+bw/2,cy),(cxs[i+1]-bw/2,cy),color=NAVY,lw=2.2)
    ax.text(3,3.0,footer,ha="left",va="center",fontsize=8.3,color=GREY,style="italic")
    finish(fig,path); print("saved",path)

pipeline(f"{OUT}/recomendada.png",
  "Propuesta recomendada — Almacenamiento en la nube + Data Flow programado",
  "Mejor opción para la carga recurrente del archivo, que convive con el real de S/4HANA",
  [("Presupuesto\ncomercial","Exportar a CSV (UTF-8) con convención sociedad/año/mes"),
   ("Cloud Storage","SFTP u Object Store (S3 · Azure Blob · GCS)"),
   ("Conexión","SAP Datasphere · Conexión al Cloud Storage"),
   ("Data Flow","Validación + carga programada -> Tabla Presupuesto"),
   ("Real vs Ppto","Vista que combina con la Tabla Real (S/4HANA)"),
   ("Consumo","Power BI o SAC")],
  [GREEN,AMBER,BLUE,BLUE,NAVY,NAVY],
  "Mejor opción: file-based, automatizada y programada, con validación; se integra con el real de S/4HANA para Real vs. Presupuesto.",
  ["FUENTE","ALMACENAMIENTO","CONEXIÓN","INGESTA","MODELO","CONSUMO"])
print("done")
