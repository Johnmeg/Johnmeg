#!/usr/bin/env python3
"""Generador de flujogramas profesionales para el Documento de Diseño SAP BUILD.
Paleta alineada a la marca del documento (Proyecto Build / Fanalca / Accenture)."""
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

# ---- Paleta de marca ----
NAVY   = "#1F3864"   # azul corporativo (cabeceras tabla)
BLUE   = "#2E74B5"   # azul medio
BLUE_D = "#002060"   # azul títulos
LBLUE  = "#DCE6F2"   # azul claro relleno
RED    = "#C00000"   # rojo acento
LRED   = "#F6DBDB"   # rojo claro
GREEN  = "#548235"   # verde salidas
LGREEN = "#E2EFDA"   # verde claro
AMBER  = "#BF8F00"   # ámbar integración
LAMBER = "#FCEFCE"   # ámbar claro
GREY   = "#595959"
LGREY  = "#EDEDED"
WHITE  = "#FFFFFF"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9.2,
})


def _wrap(text, width):
    return "\n".join(textwrap.wrap(text, width)) if width else text


def box(ax, cx, cy, w, h, text, fc=LBLUE, ec=NAVY, tc="#1A1A1A",
        fs=9.2, bold=False, wrap=None, lw=1.4, rounding=0.02, align="center"):
    """Dibuja una caja redondeada centrada en (cx, cy)."""
    x, y = cx - w / 2, cy - h / 2
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.005,rounding_size={rounding}",
                       linewidth=lw, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(p)
    ax.text(cx, cy, _wrap(text, wrap), ha=align, va="center",
            fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
            zorder=4, linespacing=1.25)
    return (cx, cy, w, h)


def header_box(ax, cx, cy, w, h, title, body, fc=WHITE, ec=NAVY,
               hc=NAVY, htc=WHITE, fs=8.6, wrap=26):
    """Caja con cabecera de color (título) y cuerpo en blanco."""
    x, y = cx - w / 2, cy - h / 2
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.004,rounding_size=0.02",
                 linewidth=1.4, edgecolor=ec, facecolor=fc, zorder=3))
    hh = min(0.16, h * 0.34)
    ax.add_patch(plt.Rectangle((x, y + h - hh), w, hh, facecolor=hc,
                 edgecolor=ec, linewidth=1.4, zorder=4))
    ax.text(cx, y + h - hh / 2, title, ha="center", va="center",
            fontsize=fs + 0.6, color=htc, fontweight="bold", zorder=5)
    ax.text(cx, y + (h - hh) / 2, _wrap(body, wrap), ha="center", va="center",
            fontsize=fs, color="#1A1A1A", zorder=5, linespacing=1.3)


def arrow(ax, p1, p2, color=NAVY, lw=2.0, style="-|>", ls="-", rad=0.0,
          shrink=2):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=15,
                        lw=lw, color=color, zorder=2, linestyle=ls,
                        connectionstyle=f"arc3,rad={rad}",
                        shrinkA=shrink, shrinkB=shrink)
    ax.add_patch(a)


def stage_label(ax, cx, cy, text, color=NAVY):
    ax.text(cx, cy, text.upper(), ha="center", va="center", fontsize=9.4,
            color=color, fontweight="bold")


def new_canvas(w=13.2, h=7.0, title=None, subtitle=None):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h / w)
    ax.axis("off")
    top = 100 * h / w
    if title:
        ax.text(2, top - 2.4, title, ha="left", va="center", fontsize=15.5,
                color=BLUE_D, fontweight="bold")
    if subtitle:
        ax.text(2, top - 5.4, subtitle, ha="left", va="center", fontsize=10,
                color=GREY)
    ax.add_line(Line2D([2, 98], [top - 6.8, top - 6.8], color=NAVY, lw=1.6))
    return fig, ax, top


def finish(fig, path):
    fig.savefig(path, bbox_inches="tight", pad_inches=0.18, facecolor="white")
    plt.close(fig)
    print("saved", path)


# =====================================================================
#  DIAGRAMA DE ARQUITECTURA  (genérico, parametrizado por cliente)
# =====================================================================
def architecture(path, client, sources, integration, dims, models_note,
                 outputs, ingresos_label, costos_label):
    fig, ax, top = new_canvas(
        title=f"Arquitectura de la solución SAP Analytics Cloud — {client}",
        subtitle="Fuentes de datos · Integración · Dimensiones compartidas · "
                 "Modelos de planeación · Consumo")
    midy = (top - 7) / 2 + 1

    # --- Stage labels ---
    xs = [11, 30, 49.5, 71, 91]
    ytop = top - 9
    for x, lab in zip(xs, ["Fuentes", "Integración", "Dimensiones",
                           "Modelos SAC", "Consumo"]):
        stage_label(ax, x, ytop, lab)

    # --- Stage 1: Fuentes ---
    n = len(sources)
    gap = 2.0
    sh = max(6.5, min(14.0, 34.0 / n - gap))
    total = n * sh + (n - 1) * gap
    y0 = midy + total / 2 - sh / 2
    src_centers = []
    for i, s in enumerate(sources):
        cy = y0 - i * (sh + gap)
        box(ax, xs[0], cy, 17, sh, s, fc=LGREY, ec=GREY, fs=8.4, wrap=20)
        src_centers.append((xs[0], cy))

    # --- Stage 2: Integración ---
    box(ax, xs[1], midy, 15, 30, integration, fc=LAMBER, ec=AMBER, bold=True,
        fs=9.2, wrap=16)
    for c in src_centers:
        arrow(ax, (c[0] + 8.5, c[1]), (xs[1] - 7.5, midy), color=GREY, lw=1.6)

    # --- Stage 3: Dimensiones compartidas ---
    header_box(ax, xs[2], midy, 16, 34, "Dimensiones\ncompartidas", dims,
               hc=NAVY, fs=8.4, wrap=20)
    arrow(ax, (xs[1] + 7.5, midy), (xs[2] - 8, midy), color=AMBER, lw=2.2)

    # --- Stage 4: Modelos SAC ---
    mx = xs[3]
    iy = midy + 11.5     # Ingresos (arriba)
    cyy = midy - 11.5    # Costos (abajo)
    ey = midy            # EEFF (centro-derecha, ligeramente a la derecha)
    box(ax, mx, iy, 17, 8.4, ingresos_label, fc=LBLUE, ec=BLUE, bold=True,
        fs=8.8, wrap=20)
    box(ax, mx, cyy, 17, 8.4, costos_label, fc=LRED, ec=RED, bold=True,
        fs=8.8, wrap=20)
    box(ax, mx + 0.0, ey, 17, 8.0, "Modelo EEFF\n(P&G · Balance · Flujo de Caja)",
        fc=LGREEN, ec=GREEN, bold=True, fs=8.8, wrap=22)
    # dims -> modelos
    for ty in (iy, cyy):
        arrow(ax, (xs[2] + 8, midy + (6 if ty > midy else -6)),
              (mx - 8.5, ty), color=NAVY, lw=1.6, rad=0.05 if ty > midy else -0.05)
    arrow(ax, (xs[2] + 8, midy), (mx - 8.5, ey), color=NAVY, lw=1.6)
    # ingresos & costos -> EEFF (data actions)
    arrow(ax, (mx, iy - 4.2), (mx, ey + 4.0), color=BLUE, lw=2.0)
    arrow(ax, (mx, cyy + 4.2), (mx, ey - 4.0), color=RED, lw=2.0)
    ax.text(mx + 9.0, (iy + ey) / 2, "Data\nActions", ha="left", va="center",
            fontsize=7.4, color=BLUE, style="italic")

    # --- Stage 5: Consumo ---
    n = len(outputs)
    oh = 6.6
    gap = 2.2
    total = n * oh + (n - 1) * gap
    y0 = midy + total / 2 - oh / 2
    for i, o in enumerate(outputs):
        cy = y0 - i * (oh + gap)
        box(ax, xs[4], cy, 15, oh, o, fc="#EFE7F3", ec="#7030A0", fs=8.2, wrap=18)
    arrow(ax, (mx + 8.5, ey), (xs[4] - 7.5, midy), color=GREEN, lw=2.2)

    # nota inferior
    ax.text(2, 1.6, models_note, ha="left", va="center", fontsize=8.0,
            color=GREY, style="italic")
    finish(fig, path)


# =====================================================================
#  DIAGRAMA DE FLUJO DE DATOS / CÁLCULO  (Ingresos & Costos -> EEFF)
# =====================================================================
def dataflow(path, client, ingresos_items, costos_items, eeff_items,
             ingresos_engine, costos_engine, subtitle):
    fig, ax, top = new_canvas(
        h=6.6,
        title=f"Flujo de cálculo y consolidación de modelos — {client}",
        subtitle=subtitle)
    midy = (top - 7) / 2 + 1.0

    # Columna 1: entradas Ingresos / Costos
    iy = midy + 13
    cyy = midy - 13
    header_box(ax, 14, iy, 22, 15, "Modelo de Ingresos",
               ingresos_items, hc=BLUE, ec=BLUE, fs=8.2, wrap=34)
    header_box(ax, 14, cyy, 22, 15, "Modelo de Costos y Gastos",
               costos_items, hc=RED, ec=RED, fs=8.2, wrap=34)

    # Columna 2: motores de cálculo
    box(ax, 42, iy, 19, 11, ingresos_engine, fc=LBLUE, ec=BLUE, bold=True,
        fs=8.2, wrap=26)
    box(ax, 42, cyy, 19, 11, costos_engine, fc=LRED, ec=RED, bold=True,
        fs=8.2, wrap=26)
    arrow(ax, (25, iy), (32.5, iy), color=BLUE, lw=2.0)
    arrow(ax, (25, cyy), (32.5, cyy), color=RED, lw=2.0)

    # Columna 3: EEFF
    header_box(ax, 73, midy, 24, 30, "Modelo EEFF (consolidado)",
               eeff_items, hc=GREEN, ec=GREEN, fs=8.2, wrap=36)
    arrow(ax, (51.5, iy), (61, midy + 8), color=BLUE, lw=2.2, rad=-0.12)
    arrow(ax, (51.5, cyy), (61, midy - 8), color=RED, lw=2.2, rad=0.12)
    ax.text(56.5, midy + 12.5, "Data Action /\nenvío a EEFF", ha="center",
            va="center", fontsize=7.2, color=GREY, style="italic")

    ax.text(2, 1.4, "Cada modelo de origen escribe en el EEFF mediante Data "
            "Actions (equivalente a los paquetes/scripts de envío). La "
            "dimensión AUDITORIA preserva la trazabilidad del dato.",
            ha="left", va="center", fontsize=8.0, color=GREY, style="italic",
            wrap=True)
    finish(fig, path)


# =====================================================================
#  DIAGRAMA DE METODOLOGÍA P x Q  (cadena de pasos horizontal)
# =====================================================================
def pxq_flow(path, client, steps, result, subtitle):
    fig, ax, top = new_canvas(h=4.9, title=f"Metodología de cálculo P × Q — {client}",
                              subtitle=subtitle)
    midy = (top - 7) / 2 + 1.0
    n = len(steps)
    x0, x1 = 6, 78
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
    w = (x1 - x0) / n * 0.92
    pal = [LBLUE, LAMBER, LGREEN, LRED, "#E6E0EF", "#D9E7F5", LGREY]
    ecs = [BLUE, AMBER, GREEN, RED, "#7030A0", BLUE, GREY]
    for i, (x, s) in enumerate(zip(xs, steps)):
        box(ax, x, midy, w, 13, f"{i+1}. {s}", fc=pal[i % len(pal)],
            ec=ecs[i % len(ecs)], fs=8.0, wrap=15)
        if i < n - 1:
            arrow(ax, (x + w / 2, midy), (xs[i+1] - w / 2, midy), color=NAVY, lw=1.8)
    # resultado
    box(ax, 92, midy, 13, 15, result, fc=NAVY, ec=NAVY, tc=WHITE, bold=True,
        fs=8.4, wrap=16)
    arrow(ax, (xs[-1] + w / 2, midy), (92 - 6.5, midy), color=GREEN, lw=2.2)
    finish(fig, path)
