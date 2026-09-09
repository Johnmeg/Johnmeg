# -*- coding: utf-8 -*-
"""Genera maquetas esquemáticas (wireframe) de las pantallas del instructivo.
NO son capturas reales: son ilustraciones para guiar cada paso."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon
import os

NAVY="#1F3864"; NAVY2="#2E5496"; BLUE="#2E75B6"; GREY="#6B7280"; BORDER="#B7C0CC"
INPUT="#FFFFFF"; AMBER="#C55A11"; GREENC="#2E7D32"; RED="#C00000"; FIELDLBL="#374151"
PANEL="#F4F6F9"

def canvas(w=11.0, h=7.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    ytop = 100*h/w
    ax.set_xlim(0,100); ax.set_ylim(0,ytop); ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax, ytop

def window(ax, x, y, w, h, title, addr=None):
    ax.add_patch(FancyBboxPatch((x+0.6,y-0.6), w, h, boxstyle="round,pad=0,rounding_size=0.6",
                 fc="#0000000D", ec="none", zorder=1))
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0,rounding_size=0.6",
                 fc="white", ec=BORDER, lw=1.2, zorder=2))
    tb=4.2
    ax.add_patch(FancyBboxPatch((x,y+h-tb), w, tb, boxstyle="round,pad=0,rounding_size=0.6",
                 fc=NAVY, ec=NAVY, zorder=3))
    ax.add_patch(Rectangle((x,y+h-tb), w, tb-0.6, fc=NAVY, ec="none", zorder=3))
    for i,c in enumerate(["#FF5F57","#FEBC2E","#28C840"]):
        ax.add_patch(Circle((x+1.7+i*1.5, y+h-tb/2), 0.5, fc=c, ec="none", zorder=4))
    ax.text(x+7.6, y+h-tb/2, title, ha="left", va="center", color="white",
            fontsize=9.5, fontweight="bold", zorder=4)
    ct=y+h-tb
    if addr:
        ab=3.0
        ax.add_patch(Rectangle((x, ct-ab), w, ab, fc="#EEF1F5", ec=BORDER, lw=0.6, zorder=3))
        ax.add_patch(FancyBboxPatch((x+1.4, ct-ab+0.7), w-2.8, ab-1.4,
                     boxstyle="round,pad=0,rounding_size=0.5", fc="white", ec=BORDER, lw=0.8, zorder=4))
        ax.text(x+2.4, ct-ab/2, addr, ha="left", va="center", color=GREY, fontsize=7.4, zorder=5)
        ct-=ab
    return ct

def field(ax, x, y, w, label, value="", kind="text", fh=3.1):
    ax.text(x, y+0.25, label, ha="left", va="bottom", color=FIELDLBL, fontsize=7.7, fontweight="bold")
    by=y-fh-0.3
    if kind=="checkbox":
        ax.add_patch(FancyBboxPatch((x, by+0.5), 2.0, 2.0, boxstyle="round,pad=0,rounding_size=0.3",
                     fc=NAVY, ec=NAVY, lw=1, zorder=4))
        ax.text(x+1.0, by+1.45, "✓", ha="center", va="center", color="white", fontsize=8, zorder=5)
        ax.text(x+3.0, by+1.45, value, ha="left", va="center", color="#1A1A1A", fontsize=8, zorder=5)
        return by
    ax.add_patch(FancyBboxPatch((x, by), w, fh, boxstyle="round,pad=0,rounding_size=0.35",
                 fc=INPUT, ec=BORDER, lw=1.0, zorder=4))
    ax.text(x+1.1, by+fh/2, value, ha="left", va="center",
            color="#1A1A1A" if value else GREY, fontsize=7.9, zorder=5,
            fontstyle="normal" if value else "italic")
    if kind=="dropdown":
        ax.text(x+w-1.5, by+fh/2, "▼", ha="center", va="center", color=GREY, fontsize=7.5, zorder=5)
    return by

def button(ax, x, y, w, h, text, primary=True):
    fc, tc = (NAVY,"white") if primary else ("white",NAVY)
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0,rounding_size=0.4",
                 fc=fc, ec=NAVY, lw=1.2, zorder=5))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", color=tc, fontsize=7.8,
            fontweight="bold", zorder=6)

def badge(ax, x, y, n, color=AMBER):
    ax.add_patch(Circle((x,y), 1.35, fc=color, ec="white", lw=1.3, zorder=8))
    ax.text(x, y, str(n), ha="center", va="center", color="white", fontsize=8.4, fontweight="bold", zorder=9)

def note(ax, x, y, w, text, color=RED, fc="#FDECEA"):
    h=3.0
    ax.add_patch(FancyBboxPatch((x,y-h), w, h, boxstyle="round,pad=0,rounding_size=0.3",
                 fc=fc, ec=color, lw=1.0, zorder=6))
    tri=[(x+1.6,y-0.7),(x+0.8,y-2.3),(x+2.4,y-2.3)]
    ax.add_patch(Polygon(tri, closed=True, fc=color, ec=color, zorder=7))
    ax.text(x+1.6, y-1.95, "!", ha="center", va="center", color="white", fontsize=7, fontweight="bold", zorder=8)
    ax.text(x+3.4, y-h/2, text, ha="left", va="center", color=color, fontsize=7.3, zorder=7)
    return y-h

def draw_screen(path, title, elements, addr=None, subtitle=None, w=11.0, h=7.6):
    fig, ax, ytop = canvas(w,h)
    x0, wwin = 5, 90
    ywin_top = ytop-1.3; hwin = ytop-3.2; ywin = ywin_top-hwin
    ct = window(ax, x0, ywin, wwin, hwin, title, addr)
    cx = x0+9; fw = 52
    cy = ct-3.0
    if subtitle:
        ax.text(x0+4, cy, subtitle, ha="left", va="center", color=NAVY2, fontsize=8.3, fontweight="bold")
        cy -= 3.8
    for el in elements:
        t=el["t"]
        if t=="section":
            ax.text(x0+4, cy, el["text"], ha="left", va="center", color=NAVY, fontsize=8.6, fontweight="bold")
            ax.plot([x0+4, x0+wwin-4],[cy-1.2,cy-1.2], color="#E1E6EC", lw=1.0)
            cy-=3.4
        elif t=="field":
            by=field(ax, cx, cy, el.get("w",fw), el["label"], el.get("value",""), el.get("kind","text"))
            if "badge" in el: badge(ax, cx-4.0, (cy+by)/2+0.3, el["badge"])
            if "hint" in el:
                ax.text(cx+el.get("w",fw)+2.0, by+1.55, el["hint"], ha="left", va="center",
                        color=GREY, fontsize=6.7, fontstyle="italic")
            cy = by-2.7
        elif t=="button":
            bw=el.get("w",22)
            button(ax, cx, cy-3.0, bw, 3.0, el["text"], el.get("primary",True))
            if "badge" in el: badge(ax, cx-4.0, cy-1.5, el["badge"])
            if "hint" in el:
                ax.text(cx+bw+2.0, cy-1.5, el["hint"], ha="left", va="center", color=GREY, fontsize=6.7, fontstyle="italic")
            cy-=5.4
        elif t=="row":
            bx=cx
            for bt in el["items"]:
                bw=bt.get("w",18); button(ax, bx, cy-3.0, bw, 3.0, bt["text"], bt.get("primary",True)); bx+=bw+2.5
            cy-=5.4
        elif t=="note":
            cy=note(ax, cx, cy, fw+18, el["text"], el.get("color",RED), el.get("fc","#FDECEA"))-1.6
        elif t=="chips":
            bx=cx
            for c in el["items"]:
                sel=c.get("sel",False); tw=len(c["t"])*1.15+4
                ax.add_patch(FancyBboxPatch((bx,cy-2.6), tw, 2.6, boxstyle="round,pad=0,rounding_size=0.6",
                             fc=NAVY if sel else "white", ec=NAVY, lw=1.0, zorder=4))
                ax.text(bx+tw/2, cy-1.3, c["t"], ha="center", va="center",
                        color="white" if sel else NAVY, fontsize=7.2, fontweight="bold", zorder=5)
                bx+=tw+2
            if "badge" in el: badge(ax, cx-4.0, cy-1.3, el["badge"])
            cy-=4.6
        elif t=="gap":
            cy-=el.get("dy",2.5)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)
    print("saved", path)

OUT="img"; os.makedirs(OUT, exist_ok=True)

# ---- Paso 1: SAC — Configuración de origen de datos (integrar Open Connectors)
draw_screen(f"{OUT}/paso1_sac_openconnectors.png", "SAP Analytics Cloud",
    subtitle="Administración del sistema  ›  Configuración de origen de datos",
    elements=[
        {"t":"section","text":"Open Connectors"},
        {"t":"button","text":"Let's integrate your Open Connectors Account","w":48,"badge":1,"primary":False},
        {"t":"gap","dy":1.5},
        {"t":"field","label":"Región de la subcuenta de SAP BTP","value":"Europe (Frankfurt)  —  eu10","kind":"dropdown","badge":2},
        {"t":"field","label":"Open Connectors User Secret","value":"••••••••••••••••","badge":3},
        {"t":"field","label":"Open Connectors Organization Secret","value":"••••••••••••••••","badge":4},
        {"t":"gap","dy":0.6},
        {"t":"button","text":"Guardar","w":20,"badge":5},
    ])

# ---- Paso 2a: Azure — Registrar aplicación
draw_screen(f"{OUT}/paso2a_azure_appreg.png", "Microsoft Entra ID (Azure)",
    addr="https://portal.azure.com  ›  App registrations  ›  New registration",
    elements=[
        {"t":"section","text":"Registrar una aplicación"},
        {"t":"field","label":"Name (nombre de la aplicación)","value":"SAC-SharePoint-Connector","badge":1},
        {"t":"field","label":"Supported account types","value":"Single tenant","kind":"dropdown"},
        {"t":"field","label":"Redirect URI","value":"Web  —  https://…/oauth/callback  (Callback URL de Open Connectors)","badge":2,"w":66},
        {"t":"gap","dy":0.6},
        {"t":"button","text":"Register","w":18,"badge":3},
        {"t":"note","text":"Anote Application (Client) ID y Directory (Tenant) ID de la aplicación registrada.","color":NAVY2,"fc":"#EAF1FB"},
    ])

# ---- Paso 2b: Azure — Certificados y secretos
draw_screen(f"{OUT}/paso2b_azure_secret.png", "Microsoft Entra ID (Azure)",
    addr="Certificates & secrets  ›  New client secret",
    elements=[
        {"t":"section","text":"Nuevo secreto de cliente (Client Secret)"},
        {"t":"field","label":"Description","value":"SAC-OpenConnectors","badge":1},
        {"t":"field","label":"Expires","value":"180 días (recomendado: certificado)","kind":"dropdown"},
        {"t":"button","text":"Add","w":16,"badge":2,"primary":False},
        {"t":"gap","dy":1.0},
        {"t":"field","label":"Value (secreto generado)","value":"Qy8~9dHc…•••••••••••••   [ Copiar ]","badge":3,"w":60},
        {"t":"note","text":"Copie el valor del secreto ahora: no se puede recuperar después.","color":RED,"fc":"#FDECEA"},
    ])

# ---- Paso 3: Open Connectors — Instancia del conector SharePoint
draw_screen(f"{OUT}/paso3_openconnectors_instance.png", "SAP Integration Suite — Open Connectors",
    subtitle="Connectors  ›  SharePoint  ›  Authenticate / Create Instance",
    elements=[
        {"t":"field","label":"Buscar conector","value":"SharePoint","kind":"dropdown","w":40,"badge":1},
        {"t":"gap","dy":0.6},
        {"t":"section","text":"Create Instance"},
        {"t":"field","label":"Name (nombre de la instancia)","value":"SharePoint-Finanzas","badge":2},
        {"t":"field","label":"SharePoint Site Address","value":"contoso.sharepoint.com","badge":3},
        {"t":"field","label":"API Key","value":"(Client ID de la app)","badge":4,"hint":"= Client ID"},
        {"t":"field","label":"API Secret","value":"(Client Secret de la app)","badge":5,"hint":"= Client Secret"},
        {"t":"button","text":"Create Instance","w":24,"badge":6},
    ])

# ---- Paso 4: SAC — Nueva conexión (Open Connectors)
draw_screen(f"{OUT}/paso4_sac_conexion.png", "SAP Analytics Cloud",
    subtitle="Conexiones  ›  Añadir conexión  ›  Adquirir datos (Acquire Data)",
    elements=[
        {"t":"chips","items":[{"t":"Todos"},{"t":"Open Connectors","sel":True},{"t":"OData"},{"t":"SAP BW"}],"badge":1},
        {"t":"section","text":"Query-based data connection"},
        {"t":"field","label":"Connection Name","value":"SP_Finanzas","badge":2},
        {"t":"field","label":"SharePoint Site Address","value":"contoso.sharepoint.com/sites/finanzas","badge":3,"hint":"SIN https://","w":56},
        {"t":"field","label":"OAuth API Key","value":"(Client ID)","badge":4},
        {"t":"field","label":"OAuth API Secret","value":"••••••••••••","badge":5},
        {"t":"field","label":"MS OAuth Scope","value":"AllSites.Manage","badge":6},
        {"t":"field","label":"Use Scope","value":"true","kind":"checkbox","badge":7},
        {"t":"button","text":"Crear / OK","w":22,"badge":8},
        {"t":"note","text":"En «SharePoint Site Address» no incluya el prefijo https://.","color":RED,"fc":"#FDECEA"},
    ], h=8.6)

# ---- Paso 5: SAC — Adquirir datos / importar
draw_screen(f"{OUT}/paso5_sac_importar.png", "SAP Analytics Cloud",
    subtitle="Nuevo modelo  ›  Adquirir datos",
    elements=[
        {"t":"field","label":"Seleccionar conexión","value":"SP_Finanzas  (SharePoint · Open Connectors)","kind":"dropdown","badge":1,"w":56},
        {"t":"field","label":"Recurso / consulta","value":"/Documentos compartidos/Ventas_2026.xlsx","kind":"dropdown","badge":2,"w":56},
        {"t":"gap","dy":0.6},
        {"t":"row","items":[{"text":"Previsualizar","w":22,"primary":False},{"text":"Importar","w":20,"primary":True}]},
        {"t":"note","text":"Revise los datos y aplique transformaciones antes de importar al modelo.","color":NAVY2,"fc":"#EAF1FB"},
    ])
print("OK")
