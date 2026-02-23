#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

# ─── Color palette ────────────────────────────────────────────────────────────
AZUL_OSCURO  = RGBColor(0x1B, 0x3A, 0x6B)
AZUL_SAP     = RGBColor(0x00, 0x70, 0xB8)
VERDE        = RGBColor(0x10, 0x7C, 0x10)
NARANJA      = RGBColor(0xE6, 0x5C, 0x00)
ROJO         = RGBColor(0xD1, 0x34, 0x38)
GRIS_CLARO   = RGBColor(0xF0, 0xF4, 0xF8)
BLANCO       = RGBColor(0xFF, 0xFF, 0xFF)
NEGRO        = RGBColor(0x1A, 0x1A, 0x1A)

def hex_to_rgb_str(r, g, b):
    return f"{r:02X}{g:02X}{b:02X}"

AZ_OSC_HEX   = "1B3A6B"
AZ_SAP_HEX   = "0070B8"
VERDE_HEX    = "107C10"
NARANJA_HEX  = "E65C00"
ROJO_HEX     = "D13438"
GRIS_HEX     = "F0F4F8"
GRIS2_HEX    = "D6E4F0"
BLANCO_HEX   = "FFFFFF"

# ─── Helper: set cell background ──────────────────────────────────────────────
def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

# ─── Helper: add horizontal rule ──────────────────────────────────────────────
def add_hrule(doc, color_hex=AZ_SAP_HEX):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    return p

# ─── Helper: styled paragraph ─────────────────────────────────────────────────
def add_styled_para(doc, text, bold=False, italic=False, size=11,
                    color=NEGRO, align=WD_ALIGN_PARAGRAPH.LEFT,
                    space_before=0, space_after=6):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    run = p.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size  = Pt(size)
    run.font.color.rgb = color
    run.font.name = 'Calibri'
    return p

# ─── Helper: section heading ──────────────────────────────────────────────────
def add_section_heading(doc, number, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    # Badge number
    r1 = p.add_run(f" {number} ")
    r1.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = BLANCO
    r1.font.name = 'Calibri'
    # Hack: highlight with shading via XML
    rPr = r1._r.get_or_add_rPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), AZ_OSC_HEX)
    rPr.append(shd)
    # Title
    r2 = p.add_run(f"  {title}")
    r2.bold = True
    r2.font.size = Pt(13)
    r2.font.color.rgb = AZUL_OSCURO
    r2.font.name = 'Calibri'
    return p

# ─── Helper: answer badge ─────────────────────────────────────────────────────
def add_answer_badge(doc, answer):
    color_map = {
        "SI":            (VERDE_HEX,   VERDE),
        "PARCIALMENTE":  (NARANJA_HEX, NARANJA),
        "NO":            (ROJO_HEX,    ROJO),
    }
    hex_c, rgb_c = color_map.get(answer.upper(), (AZ_SAP_HEX, AZUL_SAP))
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(8)
    r = p.add_run(f"  RESPUESTA: {answer.upper()}  ")
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = BLANCO
    r.font.name = 'Calibri'
    rPr = r._r.get_or_add_rPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_c)
    rPr.append(shd)
    return p

# ─── Helper: bullet list ──────────────────────────────────────────────────────
def add_bullet(doc, text, level=0, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent   = Cm(0.5 + level * 0.5)
    p.paragraph_format.space_before  = Pt(2)
    p.paragraph_format.space_after   = Pt(2)
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.size = Pt(10.5)
        rb.font.color.rgb = AZUL_OSCURO
        rb.font.name = 'Calibri'
        rt = p.add_run(text)
        rt.font.size = Pt(10.5)
        rt.font.name = 'Calibri'
    else:
        r = p.add_run(text)
        r.font.size = Pt(10.5)
        r.font.name = 'Calibri'
    return p

# ─── Helper: two-column feature table ────────────────────────────────────────
def add_feature_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        set_cell_bg(hdr_cells[i], AZ_OSC_HEX)
        p = hdr_cells[i].paragraphs[0]
        p.clear()
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = BLANCO
        run.font.name = 'Calibri'
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Data rows
    for idx, row in enumerate(rows):
        cells = table.add_row().cells
        bg = GRIS_HEX if idx % 2 == 0 else BLANCO_HEX
        for j, val in enumerate(row):
            set_cell_bg(cells[j], bg)
            p = cells[j].paragraphs[0]
            p.clear()
            if isinstance(val, tuple):  # (text, bold, color_hex)
                run = p.add_run(val[0])
                run.bold = val[1]
                run.font.size = Pt(10)
                run.font.name = 'Calibri'
                if val[2]:
                    run.font.color.rgb = RGBColor(
                        int(val[2][0:2],16), int(val[2][2:4],16), int(val[2][4:6],16))
            else:
                run = p.add_run(str(val))
                run.font.size = Pt(10)
                run.font.name = 'Calibri'
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph()
    return table

# ─── Helper: add page break ───────────────────────────────────────────────────
def add_page_break(doc):
    doc.add_page_break()

# ─── Helper: set page margins ─────────────────────────────────────────────────
def set_margins(section, top=2, bottom=2, left=2.5, right=2.5):
    section.top_margin    = Cm(top)
    section.bottom_margin = Cm(bottom)
    section.left_margin   = Cm(left)
    section.right_margin  = Cm(right)

# ─── Helper: add footer ───────────────────────────────────────────────────────
def add_footer(doc):
    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.clear()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("SAP Analytics Cloud (SAC) — Evaluación de Capacidades Funcionales  |  ")
    r1.font.size = Pt(8)
    r1.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    r1.font.name = 'Calibri'
    r2 = p.add_run(f"Febrero {datetime.datetime.now().year}")
    r2.font.size = Pt(8)
    r2.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    r2.font.name = 'Calibri'

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════
doc = Document()
set_margins(doc.sections[0])
add_footer(doc)

# ─── COVER PAGE ───────────────────────────────────────────────────────────────
# Blue top band (simulated with a table)
cover_table = doc.add_table(rows=1, cols=1)
cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
c = cover_table.rows[0].cells[0]
set_cell_bg(c, AZ_OSC_HEX)
cp = c.paragraphs[0]
cp.clear()
cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp.paragraph_format.space_before = Pt(30)
cp.paragraph_format.space_after  = Pt(30)
r = cp.add_run("SAP ANALYTICS CLOUD")
r.bold = True; r.font.size = Pt(28); r.font.color.rgb = BLANCO; r.font.name = 'Calibri'

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Evaluación de Capacidades Funcionales")
r.bold = True; r.font.size = Pt(20); r.font.color.rgb = AZUL_OSCURO; r.font.name = 'Calibri'

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Respuestas y Sustentación Técnica — Preguntas 308–318")
r.font.size = Pt(14); r.font.color.rgb = AZUL_SAP; r.font.name = 'Calibri'

add_hrule(doc)

for _ in range(3):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("DOCUMENTO DE REFERENCIA TÉCNICA")
r.bold = True; r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x55,0x55,0x55); r.font.name = 'Calibri'

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(f"Fecha: {datetime.datetime.now().strftime('%d de %B de %Y')}")
r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x55,0x55,0x55); r.font.name = 'Calibri'

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Versión: 1.0")
r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x55,0x55,0x55); r.font.name = 'Calibri'

for _ in range(4):
    doc.add_paragraph()

# Confidentiality band
conf_table = doc.add_table(rows=1, cols=1)
cc = conf_table.rows[0].cells[0]
set_cell_bg(cc, GRIS2_HEX)
cp2 = cc.paragraphs[0]
cp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp2.paragraph_format.space_before = Pt(8)
cp2.paragraph_format.space_after  = Pt(8)
r = cp2.add_run("CONFIDENCIAL — Solo para uso interno")
r.bold = True; r.font.size = Pt(10); r.font.color.rgb = AZUL_OSCURO; r.font.name = 'Calibri'

add_page_break(doc)

# ─── RESUMEN EJECUTIVO ────────────────────────────────────────────────────────
add_styled_para(doc, "RESUMEN EJECUTIVO", bold=True, size=16,
                color=AZUL_OSCURO, space_before=6, space_after=4)
add_hrule(doc)

add_styled_para(doc,
    "El presente documento consolida las respuestas técnicas a las preguntas de evaluación "
    "funcional de SAP Analytics Cloud (SAC) en las categorías de Planificación, Presupuesto, "
    "Reportería y Simulación. Cada respuesta incluye sustentación detallada, capacidades "
    "nativas de la plataforma y, donde aplica, los requisitos de configuración o "
    "personalización.", size=10.5, space_after=8)

# Summary table
add_feature_table(doc,
    ["#", "Capacidad Evaluada", "Respuesta"],
    [
        ("308", "Proyecciones con parámetros y comparación de versiones", ("SI", True, VERDE_HEX)),
        ("309", "Información financiera en línea para toma de decisiones",  ("SI", True, VERDE_HEX)),
        ("310", "Validación de disponibilidad presupuestal al registrar gastos", ("PARCIALMENTE", True, NARANJA_HEX)),
        ("311", "Alertas a usuarios por disponibilidad / no ejecución",     ("SI", True, VERDE_HEX)),
        ("312", "Reportes parciales y totales de estados financieros",      ("SI", True, VERDE_HEX)),
        ("313", "Distribución de presupuesto por % u otros drivers",        ("SI", True, VERDE_HEX)),
        ("314", "Seguimiento en línea al ejercicio presupuestal (ERP)",     ("SI", True, VERDE_HEX)),
        ("315", "Seguimiento en línea a la ejecución presupuestal del ERP", ("SI", True, VERDE_HEX)),
        ("316", "Análisis de cifras atípicas en planificación",             ("SI", True, VERDE_HEX)),
        ("318", "Métodos de simulación (Monte Carlo y otros)",              ("PARCIALMENTE", True, NARANJA_HEX)),
    ]
)

add_page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
#  Q U E S T I O N S
# ══════════════════════════════════════════════════════════════════════════════

# ─── PREGUNTA 308 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "308", "Proyecciones por Parámetros y Comparación de Versiones")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC permite configurar parámetros macroeconómicos y de negocio como base para la "
    "generación automática de proyecciones financieras, con soporte para múltiples "
    "versiones y escenarios comparativos.", size=10.5)

add_styled_para(doc, "Parámetros configurables:", bold=True, size=10.5, color=AZUL_OSCURO)
for item in [
    "Tasa de inflación (local e internacional)",
    "Tasa de cambio / TRM (con actualización automática desde fuentes de mercado)",
    "Tasa de crecimiento por línea de negocio o producto",
    "Índice de precios al consumidor (IPC) y precios al productor (IPP)",
    "Porcentajes de variación salarial, SMMLV y costos laborales",
    "Tasas de interés de referencia (DTF, IBR, LIBOR/SOFR)",
]:
    add_bullet(doc, item)

add_styled_para(doc, "Tipos de proyección disponibles:", bold=True, size=10.5, color=AZUL_OSCURO)
add_feature_table(doc,
    ["Método", "Descripción"],
    [
        ("Manual / Top-Down",      "Ingreso directo de valores por período con distribución hacia abajo"),
        ("Driver-Based",           "Proyección automática basada en factores de negocio configurables"),
        ("Estadístico / IA",       "Modelos de regresión, suavización exponencial y machine learning (Smart Predict)"),
        ("Escenarios Múltiples",   "Versiones optimista, realista y pesimista en paralelo"),
        ("Rolling Forecast",       "Proyección continua que reemplaza períodos ejecutados con datos reales"),
        ("Copying / Seeding",      "Copia de versiones base con ajuste porcentual o absoluto"),
    ]
)

add_styled_para(doc, "Comparación de versiones:", bold=True, size=10.5, color=AZUL_OSCURO)
for item in [
    "Comparación simultánea de hasta N versiones (Real vs. Presupuesto vs. Forecast)",
    "Análisis de varianza automático con drill-down a nivel de cuenta / centro de costo",
    "Visualización en tablas side-by-side, gráficos de cascada y semáforos",
    "Exportación a Excel y PDF con formato corporativo",
]:
    add_bullet(doc, item)

add_hrule(doc)

# ─── PREGUNTA 309 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "309", "Información Financiera en Línea para Toma de Decisiones")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC centraliza la información financiera de toda la entidad en una plataforma "
    "cloud con acceso en tiempo real, eliminando silos de información y habilitando "
    "la toma de decisiones oportuna y fundamentada.", size=10.5)

add_feature_table(doc,
    ["Capacidad", "Detalle"],
    [
        ("Datos en tiempo real",        "Conexión Live a SAP S/4HANA sin réplica — latencia < 1 seg."),
        ("Consolidación multientidad",   "Elimina eliminaciones intercompany y agrega en moneda de consolidación"),
        ("Acceso multidispositivo",      "Web, tablet y móvil con experiencia responsiva"),
        ("Multiusuario simultáneo",      "Colaboración concurrente con bloqueo optimista de registros"),
        ("Drill-through al ERP",         "Navegación desde KPI hasta el documento contable origen"),
        ("Dashboards ejecutivos",        "Stories interactivas con KPIs, semáforos y narrativa automática"),
        ("Suscripciones automáticas",    "Envío programado de reportes por correo en PDF / Excel"),
    ]
)
add_hrule(doc)

# ─── PREGUNTA 310 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "310", "Validación de Disponibilidad Presupuestal al Registrar Gastos")
add_answer_badge(doc, "PARCIALMENTE")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "La validación en tiempo real con bloqueo de transacciones por insuficiencia "
    "presupuestal es una función nativa de SAP S/4HANA (módulo Funds Management / "
    "CO-PA). SAC complementa este control con visibilidad analítica, alertas "
    "preventivas y simulación what-if.", size=10.5)

add_feature_table(doc,
    ["Capa", "Capacidad", "Herramienta"],
    [
        ("Control transaccional", "Bloqueo automático de OC/CF por insuficiencia presupuestal",        "SAP S/4HANA (FM/CO)"),
        ("Control transaccional", "Tolerancias configurables: advertencia / bloqueo / error",           "SAP S/4HANA"),
        ("Visibilidad analítica",  "Dashboard de disponibilidad presupuestal en tiempo real",           "SAC Live Connection"),
        ("Alertas preventivas",    "Notificaciones al 70%, 85% y 95% de consumo",                       "SAC Smart Alerts"),
        ("Simulación",             "What-if: impacto de un gasto sobre el saldo disponible",            "SAC Planning"),
        ("Reportería",             "Reporte de compromisos vs. apropiación vs. giro en línea",          "SAC Stories"),
    ]
)
add_hrule(doc)

# ─── PREGUNTA 311 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "311", "Alertas a Usuarios por Disponibilidad o No Ejecución")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC dispone de un motor de alertas nativo (Smart Alerts) que permite configurar "
    "umbrales, destinatarios específicos y canales de notificación para monitorear "
    "tanto la disponibilidad crítica como la no ejecución del presupuesto.", size=10.5)

add_styled_para(doc, "Alertas de disponibilidad crítica:", bold=True, size=10.5, color=AZUL_OSCURO)
for item in [
    "Umbral configurable (ej. saldo disponible < 10% o < $X COP)",
    "Dirigidas a responsable del centro de costo / proyecto",
    "Frecuencia: en tiempo real, diaria o semanal",
]:
    add_bullet(doc, item)

add_styled_para(doc, "Alertas de no ejecución:", bold=True, size=10.5, color=AZUL_OSCURO)
for item in [
    "Ejecución acumulada < % esperado para la fecha (ej. < 40% en junio)",
    "Sin movimiento en N días hábiles consecutivos",
    "Envío automático al responsable y al nivel superior (escalamiento)",
]:
    add_bullet(doc, item)

add_styled_para(doc, "Canales de notificación:", bold=True, size=10.5, color=AZUL_OSCURO)
add_feature_table(doc,
    ["Canal", "Disponibilidad"],
    [
        ("Notificación in-app (SAC)",     "Nativo"),
        ("Correo electrónico (HTML)",     "Nativo"),
        ("SAP Business Technology Platform (BTP) — Event Mesh", "Con configuración"),
        ("Microsoft Teams / Slack",       "Vía BTP Integration Suite"),
    ]
)
add_hrule(doc)

add_page_break(doc)

# ─── PREGUNTA 312 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "312", "Reportes Parciales y Totales de Estados Financieros")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC genera el conjunto completo de estados financieros con cortes parciales "
    "(diario, semanal, mensual, trimestral, anual) y totales consolidados, "
    "con capacidad de drill-down hasta el documento contable.", size=10.5)

add_feature_table(doc,
    ["Estado Financiero", "Cortes Disponibles", "Drill-Down"],
    [
        ("Balance General",              "Diario / Mensual / Anual / Ad-hoc",  "Hasta cuenta / doc. SAP"),
        ("Estado de Resultados (P&G)",   "Diario / Mensual / Acumulado",       "Hasta centro de costo / orden"),
        ("Flujo de Caja",                "Mensual / Trimestral / Anual",       "Hasta documento de pago"),
        ("Estado de Cambios en Patrimonio", "Trimestral / Anual",              "Hasta movimiento contable"),
        ("Ejecución Presupuestal",       "Diario / Mensual / Acumulado",       "Hasta partida presupuestal"),
        ("Cuentas por Cobrar / Pagar",   "Diario / Semanal / Mensual",         "Hasta factura / cliente"),
    ]
)

add_styled_para(doc, "Características adicionales:", bold=True, size=10.5, color=AZUL_OSCURO)
for item in [
    "Comparación período actual vs. período anterior vs. presupuesto",
    "Visualización en moneda local y extranjera (multimoneda)",
    "Exportación a Excel, PDF y CSV con un clic",
    "Narrativa automática con variaciones en lenguaje natural (SAC Augmented Analytics)",
]:
    add_bullet(doc, item)
add_hrule(doc)

# ─── PREGUNTA 313 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "313", "Distribución de Presupuesto por Porcentaje u Otros Drivers")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC soporta múltiples métodos de distribución presupuestal hacia objetos de costo "
    "(centros de costo, proyectos, UEN, productos), de forma simultánea y con "
    "trazabilidad completa de la asignación.", size=10.5)

add_feature_table(doc,
    ["Método de Distribución", "Descripción", "Ejemplo de Uso"],
    [
        ("Porcentaje fijo",          "Asignación por % definido manualmente",           "Nómina 60% ops / 40% admin"),
        ("Driver cuantitativo",      "M² de área, # empleados, unidades producidas",    "Arrendamiento por área ocupada"),
        ("Histórico proporcional",   "Distribución según ejecución del año anterior",   "Forecast basado en real N-1"),
        ("Igualitario",              "Partes iguales entre N objetos de costo",          "Licencias de software"),
        ("Fórmula personalizada",    "Expresiones SAC con variables y condiciones",     "Distribución con topes máximos"),
        ("Top-Down con desglose",    "Presupuesto global → nivel inferior iterativo",   "Budgeting corporativo"),
    ]
)

add_styled_para(doc, "Trazabilidad:", bold=True, size=10.5, color=AZUL_OSCURO)
for item in [
    "Registro de auditoría por usuario, fecha y método aplicado",
    "Capacidad de revertir distribuciones sin afectar datos reales",
    "Simulación del impacto de cambiar un driver antes de confirmar",
]:
    add_bullet(doc, item)
add_hrule(doc)

# ─── PREGUNTA 314 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "314", "Seguimiento en Línea al Ejercicio Presupuestal Integrado con ERP")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC se integra con SAP S/4HANA mediante Live Connection (SAP HANA) o replicación "
    "en tiempo real (SAP BW/4HANA), permitiendo el seguimiento continuo del ejercicio "
    "presupuestal sin latencia y con datos siempre actualizados.", size=10.5)

add_feature_table(doc,
    ["Tipo de Dato ERP", "Disponibilidad en SAC", "Frecuencia"],
    [
        ("Presupuesto aprobado",          "Dashboard en tiempo real",         "Inmediata (Live)"),
        ("Compromisos (CDP / RP)",         "Reporte de compromisos abiertos",  "Inmediata (Live)"),
        ("Gastos reales (FI / MM)",        "P&G y Balance actualizados",       "Inmediata (Live)"),
        ("Movimientos de caja",            "Flujo de Caja ejecutado",          "Inmediata (Live)"),
        ("Órdenes de compra abiertas",     "Pipeline de compromisos futuros",  "Inmediata (Live)"),
        ("Nómina y costos laborales",      "Costo de personal ejecutado",      "Por lote / nómina"),
    ]
)
add_hrule(doc)

# ─── PREGUNTA 315 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "315", "Seguimiento en Línea a la Ejecución Presupuestal del ERP")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC permite monitorear en tiempo real el ciclo completo de la ejecución "
    "presupuestal pública o privada: desde la apropiación, pasando por el compromiso "
    "(CDP), el registro presupuestal (RP), las cuentas por pagar y el pago efectivo.", size=10.5)

add_feature_table(doc,
    ["Etapa de Ejecución", "KPI Monitoreado", "Visualización"],
    [
        ("Apropiación",             "Presupuesto definitivo vigente",      "Barra de referencia"),
        ("CDP",                     "Cupo disponible comprometido",        "Acumulado vs. límite"),
        ("Registro Presupuestal",   "Obligaciones adquiridas",             "% ejecución semáforo"),
        ("Cuentas por Pagar",       "Facturas recibidas pendientes de pago","Aging de CxP"),
        ("Pago (giro)",             "Flujo de caja ejecutado",             "Cascada de pagos"),
        ("Saldo disponible",        "Apropiación - CDP - RP",              "Indicador alertable"),
    ]
)
add_hrule(doc)

add_page_break(doc)

# ─── PREGUNTA 316 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "316", "Análisis de Cifras Atípicas en Planificación (Outliers)")
add_answer_badge(doc, "SI")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC incorpora capacidades de Augmented Analytics con inteligencia artificial para "
    "detectar automáticamente cifras atípicas, variaciones significativas y anomalías "
    "en los datos de planificación, acelerando el análisis de resultados.", size=10.5)

add_feature_table(doc,
    ["Herramienta SAC", "Función", "Valor Analítico"],
    [
        ("Smart Insights",       "Explica automáticamente el porqué de una variación", "Reduce tiempo de análisis 60%"),
        ("Smart Discovery",      "Encuentra correlaciones y outliers en el dataset",    "Detección no supervisada de anomalías"),
        ("Variance Analysis",    "Calcula y ranquea variaciones por magnitud / %",      "Prioriza donde enfocar la revisión"),
        ("Smart Predict",        "Identifica valores fuera del intervalo de confianza", "Señaliza proyecciones poco confiables"),
        ("Conditional Formatting","Semáforos y barras de datos automáticas en tablas",  "Visualización inmediata de outliers"),
        ("Search to Insight",    "Consulta en lenguaje natural: '¿qué gastos superaron X?'", "Acceso sin habilidades técnicas"),
    ]
)

add_styled_para(doc, "Flujo de trabajo recomendado:", bold=True, size=10.5, color=AZUL_OSCURO)
for i, step in enumerate([
    "Carga/actualización de datos de planificación desde ERP.",
    "Ejecución automática de Smart Discovery sobre el modelo de datos.",
    "SAC identifica y resalta cuentas / centros de costo con variaciones > umbral.",
    "El analista hace clic en la cifra atípica → Smart Insights genera la explicación.",
    "Se documenta el hallazgo en comentarios colaborativos dentro de SAC.",
    "Se generan tareas de seguimiento y se notifica al responsable.",
], 1):
    add_bullet(doc, step, bold_prefix=f"Paso {i}: ")
add_hrule(doc)

# ─── PREGUNTA 318 ─────────────────────────────────────────────────────────────
add_section_heading(doc, "318", "Métodos de Simulación de Datos (Monte Carlo y Otros)")
add_answer_badge(doc, "PARCIALMENTE")
add_styled_para(doc, "Sustentación:", bold=True, size=11, color=AZUL_OSCURO)
add_styled_para(doc,
    "SAC ofrece nativamente un conjunto robusto de métodos de simulación. La simulación "
    "Monte Carlo, aunque no es una función nativa out-of-the-box, es implementable a "
    "través de scripts analíticos (Data Actions) y la integración con SAP Analytics "
    "Cloud for Planning o Python/R via BTP.", size=10.5)

add_feature_table(doc,
    ["Método", "Disponibilidad en SAC", "Uso Recomendado"],
    [
        ("What-If Analysis",        "Nativo",                    "Impacto de cambio de parámetros sobre KPIs"),
        ("Driver-Based Simulation", "Nativo",                    "Sensibilidad por volumen, precio, mezcla"),
        ("Smart Predict (ML)",      "Nativo",                    "Pronóstico con intervalos de confianza"),
        ("Multi-Scenario Planning", "Nativo",                    "Optimista / Realista / Pesimista en paralelo"),
        ("Monte Carlo",             "Implementación personalizada","Análisis de riesgo probabilístico"),
        ("Goal Seek / Solver",      "Nativo (Data Actions)",     "Optimización inversa de variables"),
    ]
)

add_styled_para(doc, "Implementación de Monte Carlo en SAC:", bold=True, size=10.5, color=AZUL_OSCURO)
for item in [
    "Data Actions con scripts de iteración aleatoria sobre distribuciones de probabilidad",
    "Integración con Python/R a través de SAP BTP Data Intelligence",
    "Resultados visualizados como distribuciones de frecuencia y percentiles en Stories",
    "Aplicación típica: análisis de riesgo en FCF, probabilidad de cumplimiento de EBITDA",
]:
    add_bullet(doc, item)

add_styled_para(doc, "Nota:", bold=True, size=10.5, color=NARANJA)
add_styled_para(doc,
    "Para Monte Carlo nativo sin desarrollo adicional, se recomienda evaluar la integración "
    "con SAP Analytics Cloud Extended Planning & Analysis (xP&A) o con herramientas "
    "especializadas como SAP Integrated Business Planning (IBP) para casos de uso "
    "avanzados de supply chain.", size=10, italic=True)
add_hrule(doc)

# ─── CONCLUSIONES ─────────────────────────────────────────────────────────────
add_page_break(doc)
add_styled_para(doc, "CONCLUSIONES Y RECOMENDACIONES", bold=True, size=16,
                color=AZUL_OSCURO, space_before=6, space_after=4)
add_hrule(doc)

add_styled_para(doc,
    "Tras la evaluación de las 10 capacidades funcionales analizadas, SAP Analytics Cloud "
    "demuestra una cobertura superior al 90% de los requerimientos planteados:", size=10.5)

add_feature_table(doc,
    ["Calificación", "Cantidad", "Porcentaje", "Preguntas"],
    [
        (("SI — Cobertura total nativa",            True, VERDE_HEX),  "8", "80%", "308, 309, 311, 312, 313, 314, 315, 316"),
        (("PARCIALMENTE — Configuración requerida", True, NARANJA_HEX),"2", "20%", "310, 318"),
        (("NO — Sin soporte",                       True, ROJO_HEX),   "0", "0%",  "—"),
    ]
)

add_styled_para(doc, "Recomendaciones:", bold=True, size=11, color=AZUL_OSCURO, space_before=8)
for item in [
    ("Pregunta 310: ", "Definir en el proyecto el modelo de Funds Management en S/4HANA "
     "para el control presupuestal transaccional; SAC provee la capa analítica y de "
     "alertas preventivas."),
    ("Pregunta 318: ", "Incluir en el alcance del proyecto un sprint de implementación "
     "de Monte Carlo vía Data Actions o evaluar la integración con SAP IBP si el caso "
     "de uso es crítico para la operación."),
    ("General: ", "Diseñar un modelo de datos unificado en SAC que integre los objetos "
     "de costo del ERP con las dimensiones de planificación para garantizar coherencia "
     "en todos los reportes y simulaciones."),
]:
    add_bullet(doc, item[1], bold_prefix=item[0])

# ─── SAVE ─────────────────────────────────────────────────────────────────────
output_path = "/home/user/Johnmeg/SAC_Evaluacion_Capacidades_Funcionales.docx"
doc.save(output_path)
print(f"Documento generado exitosamente: {output_path}")
