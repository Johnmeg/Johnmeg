# -*- coding: utf-8 -*-
"""
Generador de presentación profesional:
SAP Analytics Cloud enfocado en Planning.
Versión orientada a COMITÉ DE DIRECCIÓN (público no técnico).
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.oxml.ns import qn
import copy

# ----------------------------------------------------------------------------
# PALETA Y TIPOGRAFÍA
# ----------------------------------------------------------------------------
NAVY      = RGBColor(0x0A, 0x2A, 0x43)   # Azul profundo (fondo oscuro)
BLUE      = RGBColor(0x00, 0x6E, 0xC7)   # Azul SAP
TEAL      = RGBColor(0x0F, 0xA9, 0xB0)   # Verde-azulado acento
GOLD      = RGBColor(0xF5, 0xB2, 0x41)   # Ámbar acento
GREEN     = RGBColor(0x2E, 0x9E, 0x6B)   # Verde positivo
TERRA     = RGBColor(0xC2, 0x6B, 0x5A)   # Terracota (dolor / "antes")
LIGHT     = RGBColor(0xF4, 0xF7, 0xFA)   # Fondo claro
GREY      = RGBColor(0x5B, 0x6B, 0x7B)   # Texto secundario
DARKTXT   = RGBColor(0x13, 0x2A, 0x3E)   # Texto principal
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
CARD      = RGBColor(0xFF, 0xFF, 0xFF)
SOFT      = RGBColor(0xE6, 0xED, 0xF3)   # Bordes suaves

FONT_H = "Segoe UI Semibold"
FONT_T = "Segoe UI"
FONT_L = "Segoe UI Light"

# 16:9
prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def slide():
    return prs.slides.add_slide(BLANK)

def bg(s, color):
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = color

def rect(s, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE, line=None, line_w=None):
    sp = s.shapes.add_shape(shape, x, y, w, h)
    sp.fill.solid()
    sp.fill.fore_color.rgb = color
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = line_w or Pt(1)
    sp.shadow.inherit = False
    return sp

def no_fill_rect(s, x, y, w, h, line, line_w=Pt(1.25), shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = s.shapes.add_shape(shape, x, y, w, h)
    sp.fill.background()
    sp.line.color.rgb = line
    sp.line.width = line_w
    sp.shadow.inherit = False
    return sp

def soft_shadow(sp):
    """Sombra sutil para tarjetas."""
    spPr = sp._element.spPr
    el = spPr.makeelement(qn('a:effectLst'), {})
    sh = el.makeelement(qn('a:outerShdw'),
        {'blurRad':'90000','dist':'40000','dir':'5400000','rotWithShape':'0'})
    clr = sh.makeelement(qn('a:srgbClr'), {'val':'0A2A43'})
    alpha = clr.makeelement(qn('a:alpha'), {'val':'22000'})
    clr.append(alpha); sh.append(clr); el.append(sh); spPr.append(el)

def txt(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
        space_after=6, line_spacing=1.0, wrap=True):
    """runs: lista de párrafos; cada párrafo lista de (texto, size, color, font, bold)"""
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.space_before = Pt(0)
        p.line_spacing = line_spacing
        for (t, sz, col, fn, bold) in para:
            r = p.add_run(); r.text = t
            r.font.size = Pt(sz); r.font.color.rgb = col
            r.font.name = fn; r.font.bold = bold
    return tb

def one(t, sz, col, fn=FONT_T, bold=False):
    return [(t, sz, col, fn, bold)]

def icon_circle(s, x, y, d, color, glyph, gsize=18, gcolor=WHITE):
    c = rect(s, x, y, d, d, color, shape=MSO_SHAPE.OVAL)
    txt(s, x, y, d, d, [one(glyph, gsize, gcolor, FONT_H, True)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return c

def page_header(s, kicker, title, dark=False):
    tc = WHITE if dark else DARKTXT
    kc = TEAL if dark else BLUE
    rect(s, Inches(0.55), Inches(0.62), Inches(0.14), Inches(0.62), GOLD)
    txt(s, Inches(0.85), Inches(0.5), Inches(11.6), Inches(0.4),
        [one(kicker.upper(), 12.5, kc, FONT_H, True)], space_after=0)
    txt(s, Inches(0.83), Inches(0.82), Inches(11.8), Inches(0.7),
        [one(title, 30, tc, FONT_H, True)], space_after=0)

def footer(s, n, dark=False):
    col = RGBColor(0x8A,0x9C,0xAD) if not dark else RGBColor(0x5E,0x7A,0x92)
    txt(s, Inches(0.85), Inches(7.02), Inches(8), Inches(0.3),
        [one("SAP Analytics Cloud  ·  Planning", 9, col, FONT_T, False)], space_after=0)
    txt(s, Inches(11.4), Inches(7.02), Inches(1.1), Inches(0.3),
        [one(f"{n:02d}", 9, col, FONT_H, True)], align=PP_ALIGN.RIGHT, space_after=0)

_page = {"n": 0}
def pnum():
    _page["n"] += 1
    return _page["n"]


# ============================================================================
# SLIDE 1 — PORTADA
# ============================================================================
s = slide(); bg(s, NAVY)
band = rect(s, Inches(-1), Inches(4.7), Inches(16), Inches(4), BLUE, shape=MSO_SHAPE.PARALLELOGRAM)
band.fill.fore_color.rgb = RGBColor(0x0C,0x3A,0x5C)
rect(s, Inches(10.4), Inches(-1.3), Inches(3.6), Inches(3.6), RGBColor(0x0F,0x3E,0x60), shape=MSO_SHAPE.OVAL)
rect(s, Inches(11.6), Inches(4.9), Inches(2.4), Inches(2.4), RGBColor(0x11,0x4A,0x70), shape=MSO_SHAPE.OVAL)
rect(s, Inches(0.9), Inches(1.05), Inches(0.16), Inches(0.9), GOLD)

txt(s, Inches(1.25), Inches(1.0), Inches(10), Inches(0.5),
    [one("PLANIFICACIÓN PARA LA TOMA DE DECISIONES", 13, TEAL, FONT_H, True)], space_after=0)
txt(s, Inches(1.2), Inches(1.7), Inches(10.7), Inches(2.2),
    [ one("SAP Analytics Cloud", 54, WHITE, FONT_H, True),
      one("El futuro del negocio, planificado", 38, GOLD, FONT_L, False) ],
    space_after=6, line_spacing=1.02)
txt(s, Inches(1.24), Inches(4.05), Inches(9.8), Inches(1.0),
    [one("Una plataforma para planificar, anticipar y decidir con datos fiables. "
         "Menos hojas de cálculo, más visión de negocio.",
         16, RGBColor(0xC7,0xD6,0xE3), FONT_T, False)],
    line_spacing=1.25, space_after=0)

chips = ["Visión", "Control", "Agilidad"]
cx = Inches(1.24)
for c in chips:
    w = Inches(2.0)
    no_fill_rect(s, cx, Inches(5.7), w, Inches(0.52), TEAL, line_w=Pt(1.25))
    txt(s, cx, Inches(5.7), w, Inches(0.52), [one(c, 13, WHITE, FONT_H, True)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cx += Inches(2.2)

txt(s, Inches(1.24), Inches(6.65), Inches(9), Inches(0.4),
    [one("Sesión para el equipo directivo  ·  2026", 11, RGBColor(0x8A,0x9C,0xAD), FONT_T, False)],
    space_after=0)


# ============================================================================
# SLIDE 2 — AGENDA
# ============================================================================
s = slide(); bg(s, LIGHT)
rect(s, 0, 0, Inches(4.5), SH, NAVY)
rect(s, Inches(4.5), 0, Inches(0.06), SH, GOLD)
rect(s, Inches(0.6), Inches(0.95), Inches(0.14), Inches(0.7), GOLD)
txt(s, Inches(0.85), Inches(0.85), Inches(3.4), Inches(0.5),
    [one("CONTENIDO", 13, TEAL, FONT_H, True)], space_after=0)
txt(s, Inches(0.83), Inches(1.25), Inches(3.5), Inches(1.4),
    [one("Recorrido de hoy", 30, WHITE, FONT_H, True)], line_spacing=1.02, space_after=0)
txt(s, Inches(0.85), Inches(5.85), Inches(3.4), Inches(1.2),
    [one("Del problema que vivimos hoy al valor que aporta al negocio. "
         "Sin tecnicismos.", 12, RGBColor(0xB9,0xCB,0xDA), FONT_T, False)],
    line_spacing=1.25, space_after=0)

agenda = [
    ("01", "El reto que tenemos hoy", "Por qué planificar nos cuesta tanto"),
    ("02", "¿Qué es SAP Analytics Cloud?", "Una única plataforma, explicada simple"),
    ("03", "Qué aporta a la dirección", "Planificar mirando al futuro"),
    ("04", "Qué podremos hacer", "En lenguaje de negocio"),
    ("05", "Antes y después", "El cambio, de un vistazo"),
    ("06", "Impacto y beneficios", "Valor para cada área"),
]
ay = Inches(0.95)
for num, t, sub in agenda:
    card = rect(s, Inches(4.95), ay, Inches(7.9), Inches(0.88), CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    soft_shadow(card)
    rect(s, Inches(5.12), ay+Inches(0.14), Inches(0.6), Inches(0.6), BLUE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(5.12), ay+Inches(0.14), Inches(0.6), Inches(0.6),
        [one(num, 16, WHITE, FONT_H, True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, Inches(5.95), ay+Inches(0.13), Inches(6.7), Inches(0.4),
        [one(t, 16, DARKTXT, FONT_H, True)], space_after=0)
    txt(s, Inches(5.95), ay+Inches(0.5), Inches(6.7), Inches(0.3),
        [one(sub, 11.5, GREY, FONT_T, False)], space_after=0)
    ay += Inches(1.0)
footer(s, pnum())


# ============================================================================
# SLIDE 3 — EL RETO ACTUAL
# ============================================================================
s = slide(); bg(s, LIGHT)
page_header(s, "El punto de partida", "El reto que tenemos hoy")
txt(s, Inches(0.85), Inches(1.6), Inches(11.6), Inches(0.5),
    [one("Planificar el negocio sigue siendo lento, disperso y poco fiable. Estos son los síntomas habituales:",
         14, GREY, FONT_T, False)], space_after=0)

pains = [
    ("✕", "Demasiado Excel", "Decenas de hojas sueltas, versiones que no cuadran y errores manuales."),
    ("↺", "Miramos al retrovisor", "Analizamos el pasado, pero cuesta anticipar lo que viene."),
    ("⧉", "Cada área, su versión", "Finanzas, ventas y RR. HH. trabajan con números distintos."),
    ("⏱", "Ciclos lentos", "Cerrar un presupuesto lleva semanas de idas y venidas."),
]
gx0 = Inches(0.85); cw = Inches(2.87); gap = Inches(0.24)
for i,(ic, h, d) in enumerate(pains):
    x = gx0 + i*(cw+gap)
    card = rect(s, x, Inches(2.35), cw, Inches(3.15), CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    soft_shadow(card)
    rect(s, x, Inches(2.35), cw, Inches(0.12), TERRA, shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
    icon_circle(s, x+Inches(0.35), Inches(2.7), Inches(0.7), TERRA, ic, 22)
    txt(s, x+Inches(0.35), Inches(3.6), cw-Inches(0.7), Inches(0.5),
        [one(h, 16, DARKTXT, FONT_H, True)], space_after=0)
    txt(s, x+Inches(0.35), Inches(4.15), cw-Inches(0.7), Inches(1.2),
        [one(d, 12, GREY, FONT_T, False)], line_spacing=1.2, space_after=0)

band = rect(s, Inches(0.85), Inches(5.85), Inches(11.63), Inches(0.75), NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
txt(s, Inches(1.1), Inches(5.96), Inches(11.2), Inches(0.55),
    [[("La consecuencia:  ", 14, GOLD, FONT_H, True),
      ("decidimos tarde y con información en la que no siempre confiamos.",
       14, RGBColor(0xDD,0xE7,0xF0), FONT_T, False)]],
    anchor=MSO_ANCHOR.MIDDLE, space_after=0)
footer(s, pnum())


# ============================================================================
# SLIDE 4 — ¿QUÉ ES SAP ANALYTICS CLOUD?
# ============================================================================
s = slide(); bg(s, LIGHT)
page_header(s, "La solución", "¿Qué es SAP Analytics Cloud?")

txt(s, Inches(0.85), Inches(1.85), Inches(6.2), Inches(2.6),
    [ one("Es una plataforma en la nube de SAP que reúne, en un mismo sitio, "
          "todo lo que la dirección necesita para entender y planificar el negocio.",
          15.5, DARKTXT, FONT_T, False),
      [("", 6, DARKTXT, FONT_T, False)],
      one("Piénselo como un “cuadro de mando único”: en lugar de pedir informes "
          "a distintas áreas y juntarlos en Excel, todos trabajan sobre los "
          "mismos números, siempre actualizados.",
          14, GREY, FONT_T, False) ],
    line_spacing=1.28, space_after=8)

card = rect(s, Inches(7.55), Inches(1.85), Inches(5.0), Inches(4.55), NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
soft_shadow(card)
rect(s, Inches(7.55), Inches(1.85), Inches(5.0), Inches(0.12), GOLD, shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
txt(s, Inches(7.95), Inches(2.15), Inches(4.3), Inches(0.5),
    [one("EN POCAS PALABRAS", 12, TEAL, FONT_H, True)], space_after=0)
facts = [
    ("Todo en un solo lugar", "Informes, presupuestos y previsiones juntos."),
    ("Siempre en la nube", "Accesible y actualizado, sin instalar nada."),
    ("Para toda la empresa", "Las áreas comparten los mismos datos."),
    ("Fácil de usar", "Pensada para el negocio, no solo para técnicos."),
]
fy = Inches(2.65)
for h, d in facts:
    icon_circle(s, Inches(7.95), fy, Inches(0.4), TEAL, "✔", 14)
    txt(s, Inches(8.5), fy-Inches(0.02), Inches(3.8), Inches(0.35),
        [one(h, 14.5, WHITE, FONT_H, True)], space_after=0)
    txt(s, Inches(8.5), fy+Inches(0.32), Inches(3.8), Inches(0.5),
        [one(d, 11.5, RGBColor(0xB9,0xCB,0xDA), FONT_T, False)], line_spacing=1.15, space_after=0)
    fy += Inches(0.95)

b = rect(s, Inches(0.85), Inches(5.35), Inches(6.2), Inches(1.05), WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
soft_shadow(b)
rect(s, Inches(0.85), Inches(5.35), Inches(0.12), Inches(1.05), BLUE)
txt(s, Inches(1.15), Inches(5.5), Inches(5.7), Inches(0.8),
    [ one("Una única versión de la verdad", 14.5, BLUE, FONT_H, True),
      one("Se acabó el “¿con qué número nos quedamos?”.",
          12, GREY, FONT_T, False) ], line_spacing=1.15, space_after=3)
footer(s, pnum())


# ============================================================================
# SLIDE 5 — QUÉ APORTA A LA DIRECCIÓN (Planning)
# ============================================================================
s = slide(); bg(s, NAVY)
rect(s, Inches(8.9), 0, Inches(4.43), SH, RGBColor(0x0C,0x3A,0x5C))
rect(s, Inches(8.9), 0, Inches(0.06), SH, GOLD)
page_header(s, "El foco de hoy", "Planificar mirando al futuro", dark=True)

txt(s, Inches(0.85), Inches(1.9), Inches(7.6), Inches(2.0),
    [ one("Dentro de la plataforma, Planning es la parte que ayuda a la "
          "dirección a preparar el futuro: presupuestos, previsiones y planes "
          "de las distintas áreas, en un mismo lugar y siempre conectados con "
          "la realidad del negocio.", 15.5, RGBColor(0xDD,0xE7,0xF0), FONT_T, False) ],
    line_spacing=1.3, space_after=0)

txt(s, Inches(0.85), Inches(3.7), Inches(7.6), Inches(0.4),
    [one("QUÉ SIGNIFICA PARA LA DIRECCIÓN", 12.5, TEAL, FONT_H, True)], space_after=0)

diff = [
    ("Anticiparse, no reaccionar", "Ver a dónde va el negocio antes de que ocurra."),
    ("Adiós a los Excel dispersos", "Un plan compartido, ordenado y fiable."),
    ("Todos remando a la vez", "Áreas alineadas sobre los mismos objetivos."),
    ("Del dato a la decisión", "La información lleva directamente a la acción."),
]
dy = Inches(4.15)
for h, d in diff:
    icon_circle(s, Inches(0.9), dy, Inches(0.42), TEAL, "→", 16)
    txt(s, Inches(1.5), dy-Inches(0.02), Inches(6.9), Inches(0.35),
        [one(h, 14.5, WHITE, FONT_H, True)], space_after=0)
    txt(s, Inches(1.5), dy+Inches(0.31), Inches(6.9), Inches(0.35),
        [one(d, 12, RGBColor(0xB9,0xCB,0xDA), FONT_T, False)], space_after=0)
    dy += Inches(0.72)

txt(s, Inches(9.25), Inches(1.95), Inches(3.8), Inches(0.4),
    [one("LA IDEA, EN 4 PASOS", 12, GOLD, FONT_H, True)], space_after=0)
steps = [("Reunir", "los datos del negocio"),
         ("Planear", "objetivos y previsiones"),
         ("Colaborar", "entre todas las áreas"),
         ("Decidir", "con confianza")]
sy = Inches(2.5)
for i,(h,d) in enumerate(steps):
    icon_circle(s, Inches(9.25), sy, Inches(0.5), GOLD, str(i+1), 16, NAVY)
    txt(s, Inches(9.95), sy-Inches(0.03), Inches(3.1), Inches(0.35),
        [one(h, 15, WHITE, FONT_H, True)], space_after=0)
    txt(s, Inches(9.95), sy+Inches(0.32), Inches(3.1), Inches(0.4),
        [one(d, 11.5, RGBColor(0xB9,0xCB,0xDA), FONT_T, False)], line_spacing=1.1, space_after=0)
    if i < len(steps)-1:
        rect(s, Inches(9.48), sy+Inches(0.52), Inches(0.035), Inches(0.5), RGBColor(0x2A,0x5A,0x7E))
    sy += Inches(1.02)
footer(s, pnum(), dark=True)


# ============================================================================
# SLIDE 6 — QUÉ PODREMOS HACER (en lenguaje de negocio)
# ============================================================================
s = slide(); bg(s, LIGHT)
page_header(s, "En la práctica", "Qué podremos hacer")
txt(s, Inches(0.85), Inches(1.6), Inches(11.6), Inches(0.5),
    [one("Capacidades explicadas en lenguaje de negocio, sin entrar en la tecnología que hay detrás.",
         14, GREY, FONT_T, False)], space_after=0)

caps = [
    ("◈", "Planificar en un solo lugar",
     "Presupuestos y previsiones ordenados, sin hojas sueltas.", BLUE),
    ("?", "Escenarios «¿y si...?»",
     "Simular decisiones antes de tomarlas, en minutos.", TEAL),
    ("◑", "Plan frente a realidad",
     "Comparar lo previsto con lo real, al instante.", GOLD),
    ("✦", "Previsiones con IA",
     "Proyecciones automáticas, sin fórmulas complicadas.", BLUE),
    ("⧉", "Colaborar entre áreas",
     "Finanzas, ventas y RR. HH. sobre los mismos números.", TEAL),
    ("▤", "Información clara",
     "Cuadros de mando visuales y en tiempo real para decidir.", GOLD),
]
gx0, gy0 = Inches(0.85), Inches(2.35)
cw, chh = Inches(3.83), Inches(1.95)
gapx, gapy = Inches(0.25), Inches(0.22)
for i,(ic, h, d, col) in enumerate(caps):
    r, c = divmod(i, 3)
    x = gx0 + c*(cw+gapx)
    y = gy0 + r*(chh+gapy)
    card = rect(s, x, y, cw, chh, CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    soft_shadow(card)
    rect(s, x, y, Inches(0.12), chh, col)
    icon_circle(s, x+Inches(0.35), y+Inches(0.32), Inches(0.62), col, ic, 20)
    txt(s, x+Inches(1.15), y+Inches(0.34), cw-Inches(1.35), Inches(0.55),
        [one(h, 15, DARKTXT, FONT_H, True)], line_spacing=1.0, space_after=0)
    txt(s, x+Inches(0.35), y+Inches(1.15), cw-Inches(0.65), Inches(0.7),
        [one(d, 12, GREY, FONT_T, False)], line_spacing=1.18, space_after=0)
footer(s, pnum())


# ============================================================================
# SLIDE 7 — ANTES Y DESPUÉS
# ============================================================================
s = slide(); bg(s, LIGHT)
page_header(s, "El cambio", "Antes y después")
txt(s, Inches(0.85), Inches(1.6), Inches(11.6), Inches(0.5),
    [one("Cómo cambia el día a día de la planificación al pasar a una única plataforma.",
         14, GREY, FONT_T, False)], space_after=0)

# columna ANTES
ax, aw = Inches(0.85), Inches(5.6)
ca = rect(s, ax, Inches(2.3), aw, Inches(4.1), CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
soft_shadow(ca)
head = rect(s, ax, Inches(2.3), aw, Inches(0.95), TERRA, shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
txt(s, ax+Inches(0.4), Inches(2.3), aw-Inches(0.8), Inches(0.95),
    [[("✕  ", 18, WHITE, FONT_H, True),("Hoy, con hojas de cálculo", 17, WHITE, FONT_H, True)]],
    anchor=MSO_ANCHOR.MIDDLE, space_after=0)
antes = ["Datos dispersos y desactualizados",
         "Semanas para cerrar un presupuesto",
         "Difícil simular escenarios",
         "Cada área con su propia versión"]
iy = Inches(3.55)
for it in antes:
    txt(s, ax+Inches(0.4), iy, Inches(0.4), Inches(0.4), [one("—", 15, TERRA, FONT_H, True)], space_after=0)
    txt(s, ax+Inches(0.85), iy+Inches(0.02), aw-Inches(1.2), Inches(0.6),
        [one(it, 13.5, DARKTXT, FONT_T, False)], line_spacing=1.15, space_after=0)
    iy += Inches(0.65)

# flecha central
icon_circle(s, Inches(6.42), Inches(4.05), Inches(0.75), NAVY, "→", 26, GOLD)

# columna DESPUÉS
dx, dw = Inches(7.25), Inches(5.6)
cd = rect(s, dx, Inches(2.15), dw, Inches(4.4), NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
soft_shadow(cd)
head2 = rect(s, dx, Inches(2.15), dw, Inches(0.95), GREEN, shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
txt(s, dx+Inches(0.4), Inches(2.15), dw-Inches(0.8), Inches(0.95),
    [[("✔  ", 18, WHITE, FONT_H, True),("Con SAP Analytics Cloud", 17, WHITE, FONT_H, True)]],
    anchor=MSO_ANCHOR.MIDDLE, space_after=0)
despues = ["Una única fuente de datos fiable",
           "Ciclos de días, no de semanas",
           "Escenarios en minutos",
           "Toda la organización alineada"]
iy = Inches(3.45)
for it in despues:
    icon_circle(s, dx+Inches(0.4), iy, Inches(0.34), GREEN, "✔", 12)
    txt(s, dx+Inches(0.9), iy-Inches(0.02), dw-Inches(1.25), Inches(0.6),
        [one(it, 13.5, WHITE, FONT_H, True)], line_spacing=1.15, space_after=0)
    iy += Inches(0.72)
footer(s, pnum())


# ============================================================================
# SLIDE 8 — CASOS DE USO POR ÁREA
# ============================================================================
s = slide(); bg(s, LIGHT)
page_header(s, "Aplicación", "Valor para cada área")
txt(s, Inches(0.85), Inches(1.6), Inches(11.6), Inches(0.5),
    [one("La misma plataforma da respuesta a las necesidades de las principales áreas de la empresa.",
         14, GREY, FONT_T, False)], space_after=0)

cases = [
    ("Finanzas", BLUE, [
        "Presupuesto anual y revisiones periódicas",
        "Visión completa de resultados y tesorería",
        "Control claro de desviaciones"]),
    ("Ventas", TEAL, [
        "Objetivos comerciales por equipo y zona",
        "Previsión de ventas y demanda",
        "Impacto de precios en el margen"]),
    ("Recursos Humanos", GOLD, [
        "Planificación de plantilla y costes",
        "Escenarios de contratación",
        "Capacidad alineada con la demanda"]),
]
cx = Inches(0.85); cw = Inches(3.83)
for name, col, items in cases:
    card = rect(s, cx, Inches(2.35), cw, Inches(4.05), CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    soft_shadow(card)
    rect(s, cx, Inches(2.35), cw, Inches(0.95), col, shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
    txt(s, cx+Inches(0.35), Inches(2.35), cw-Inches(0.7), Inches(0.95),
        [one(name, 18, WHITE, FONT_H, True)], anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    iy = Inches(3.55)
    for it in items:
        rect(s, cx+Inches(0.38), iy+Inches(0.09), Inches(0.14), Inches(0.14), col, shape=MSO_SHAPE.OVAL)
        txt(s, cx+Inches(0.68), iy, cw-Inches(1.0), Inches(0.8),
            [one(it, 12.5, DARKTXT, FONT_T, False)], line_spacing=1.18, space_after=0)
        iy += Inches(0.92)
    cx += Inches(4.08)
footer(s, pnum())


# ============================================================================
# SLIDE 9 — IMPACTO Y BENEFICIOS
# ============================================================================
s = slide(); bg(s, LIGHT)
page_header(s, "Valor de negocio", "El impacto para la empresa")
txt(s, Inches(0.85), Inches(1.6), Inches(11.6), Inches(0.5),
    [one("Lo que la dirección gana al adoptar una planificación conectada e inteligente.",
         14, GREY, FONT_T, False)], space_after=0)

metrics = [("+", "rapidez", "Ciclos de días, no de semanas", BLUE),
           ("✔", "confianza", "Una sola versión de los números", TEAL),
           ("↗", "anticipación", "Ver el futuro antes de que llegue", GOLD),
           ("⧉", "alineación", "Toda la empresa, un mismo plan", NAVY)]
mx = Inches(0.85); mw = Inches(2.83)
for tag, big, d, col in metrics:
    card = rect(s, mx, Inches(2.35), mw, Inches(1.7), col, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    soft_shadow(card)
    txt(s, mx+Inches(0.3), Inches(2.5), mw-Inches(0.6), Inches(0.7),
        [[(tag+"  ", 30, WHITE, FONT_H, True),(big, 16, RGBColor(0xDD,0xE7,0xF0), FONT_L, False)]],
        space_after=0)
    txt(s, mx+Inches(0.3), Inches(3.35), mw-Inches(0.6), Inches(0.6),
        [one(d, 11.5, RGBColor(0xE6,0xED,0xF3), FONT_T, False)], line_spacing=1.15, space_after=0)
    mx += Inches(3.0)

benefits = [
    ("Decisiones más rápidas", "Menos tiempo recopilando datos, más tiempo decidiendo."),
    ("Menos riesgo de error", "Adiós a los fallos manuales de las hojas de cálculo."),
    ("Mejor visión del futuro", "Escenarios y previsiones siempre a mano."),
    ("Crece con la empresa", "En la nube, sin grandes inversiones iniciales."),
]
by = Inches(4.5)
for i,(h,d) in enumerate(benefits):
    r,c = divmod(i,2)
    x = Inches(0.85) + c*Inches(5.95)
    y = by + r*Inches(0.98)
    icon_circle(s, x, y, Inches(0.5), GREEN, "✔", 16)
    txt(s, x+Inches(0.7), y-Inches(0.03), Inches(5.0), Inches(0.35),
        [one(h, 14.5, DARKTXT, FONT_H, True)], space_after=0)
    txt(s, x+Inches(0.7), y+Inches(0.33), Inches(5.0), Inches(0.4),
        [one(d, 11.5, GREY, FONT_T, False)], line_spacing=1.12, space_after=0)
footer(s, pnum())


# ============================================================================
# SLIDE 10 — CIERRE
# ============================================================================
s = slide(); bg(s, NAVY)
rect(s, Inches(-1), Inches(4.9), Inches(16), Inches(4), RGBColor(0x0C,0x3A,0x5C), shape=MSO_SHAPE.PARALLELOGRAM)
rect(s, Inches(10.6), Inches(-1.2), Inches(3.4), Inches(3.4), RGBColor(0x0F,0x3E,0x60), shape=MSO_SHAPE.OVAL)
rect(s, Inches(0.9), Inches(2.2), Inches(0.16), Inches(1.0), GOLD)

txt(s, Inches(1.25), Inches(2.15), Inches(9), Inches(0.5),
    [one("EN RESUMEN", 13, TEAL, FONT_H, True)], space_after=0)
txt(s, Inches(1.22), Inches(2.75), Inches(11), Inches(1.6),
    [ one("Planificar el futuro,", 40, WHITE, FONT_H, True),
      one("con datos en los que confiar.", 40, GOLD, FONT_L, False) ],
    line_spacing=1.03, space_after=2)
txt(s, Inches(1.25), Inches(4.7), Inches(10.3), Inches(1.0),
    [one("SAP Analytics Cloud reúne análisis y planificación en una sola "
         "plataforma: más ágil, más fiable y alineada con toda la empresa.",
         16, RGBColor(0xC7,0xD6,0xE3), FONT_T, False)], line_spacing=1.3, space_after=0)

txt(s, Inches(1.25), Inches(6.4), Inches(9), Inches(0.4),
    [[("¿Hablamos?  ", 14, WHITE, FONT_H, True),
      ("Gracias por su atención.", 14, RGBColor(0x8A,0x9C,0xAD), FONT_T, False)]], space_after=0)


# ----------------------------------------------------------------------------
out = "/home/user/Johnmeg/SAP_Analytics_Cloud_Planning.pptx"
prs.save(out)
print("Guardado:", out, "| Slides:", len(prs.slides._sldIdLst))
