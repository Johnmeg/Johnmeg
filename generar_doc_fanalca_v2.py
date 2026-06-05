import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

SAP_BLUE   = RGBColor(0x00, 0x61, 0x9A)
SAP_DARK   = RGBColor(0x00, 0x33, 0x69)
SAP_GOLD   = RGBColor(0xF0, 0xAB, 0x00)
SAP_LIGHT  = RGBColor(0xE8, 0xF4, 0xFD)
SAP_GREEN  = RGBColor(0x10, 0x7E, 0x3E)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
GRAY_MED   = RGBColor(0x75, 0x75, 0x75)
GRAY_LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
ORANGE     = RGBColor(0xE8, 0x6A, 0x19)
PURPLE     = RGBColor(0x7B, 0x3F, 0xA0)
RED_DARK   = RGBColor(0xC6, 0x28, 0x28)

def set_cell_bg(cell, rgb):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '%02X%02X%02X' % (rgb[0], rgb[1], rgb[2]))
    tcPr.append(shd)

def set_cell_borders(cell, sides=('top','bottom','left','right'), color='B0C4D8', sz=4):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for s in sides:
        b = OxmlElement(f'w:{s}')
        b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), str(sz)); b.set(qn('w:color'), color)
        tcBorders.append(b)
    tcPr.append(tcBorders)

def add_heading(doc, text, level=1, space_before=14, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    run = p.add_run(text)
    if level == 1:
        run.font.size = Pt(16); run.font.bold = True; run.font.color.rgb = SAP_DARK
        pPr = p._p.get_or_add_pPr(); pBdr = OxmlElement('w:pBdr')
        bot = OxmlElement('w:bottom')
        bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), '6'); bot.set(qn('w:color'), '003369')
        pBdr.append(bot); pPr.append(pBdr)
    elif level == 2:
        run.font.size = Pt(13); run.font.bold = True; run.font.color.rgb = SAP_BLUE
    elif level == 3:
        run.font.size = Pt(11); run.font.bold = True; run.font.color.rgb = SAP_BLUE

def add_body(doc, text, space_before=2, space_after=4, italic=False, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    run = p.add_run(text); run.font.size = Pt(10); run.font.italic = italic
    if color: run.font.color.rgb = color

def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent  = Cm(0.5 + level * 0.5)
    run = p.add_run(text); run.font.size = Pt(10)

def header_row(table, cols, bg=None):
    bg = bg or SAP_DARK; row = table.rows[0]
    for i, txt in enumerate(cols):
        cell = row.cells[i]; set_cell_bg(cell, bg)
        set_cell_borders(cell, color='003369', sz=6)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(txt); run.font.size = Pt(9); run.font.bold = True; run.font.color.rgb = WHITE

def data_row(table, row_idx, values, alt=False, center_cols=None, bold_col=None):
    center_cols = center_cols or []; row = table.rows[row_idx]; bg = SAP_LIGHT if alt else WHITE
    for i, val in enumerate(values):
        cell = row.cells[i]; set_cell_bg(cell, bg)
        set_cell_borders(cell, color='C5D8EA', sz=2)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in center_cols else WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(str(val)); run.font.size = Pt(9)
        if bold_col is not None and i == bold_col:
            run.font.bold = True; run.font.color.rgb = SAP_DARK

def add_info_box(doc, title, lines, bg_title=None, bg_body=None):
    bg_title = bg_title or SAP_BLUE; bg_body = bg_body or SAP_LIGHT
    tbl = doc.add_table(rows=1 + len(lines), cols=1)
    tbl.style = 'Table Grid'; tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tc = tbl.rows[0].cells[0]; set_cell_bg(tc, bg_title)
    set_cell_borders(tc, color='003369', sz=6)
    p = tc.paragraphs[0]; run = p.add_run(title)
    run.font.size = Pt(10); run.font.bold = True; run.font.color.rgb = WHITE
    for i, line in enumerate(lines, 1):
        tc = tbl.rows[i].cells[0]; set_cell_bg(tc, bg_body)
        set_cell_borders(tc, color='B0C4D8', sz=2)
        p = tc.paragraphs[0]; run = p.add_run(line); run.font.size = Pt(9)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def add_footer(doc):
    section = doc.sections[0]; footer = section.footer
    p = footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('SAP BUILD | Fanalca S.A. — SAP Analytics Cloud | Documento Confidencial | 2026')
    run.font.size = Pt(8); run.font.color.rgb = GRAY_MED; run.font.italic = True

# ── FLOWCHART ─────────────────────────────────────────────────────────────────
def generar_flowchart(path):
    fig, ax = plt.subplots(figsize=(22, 15))
    ax.set_xlim(0, 22); ax.set_ylim(0, 15); ax.axis('off')
    fig.patch.set_facecolor('#F5F8FC')

    def band(y, h, color, label):
        ax.add_patch(plt.Rectangle((0.3, y), 21.4, h, color=color, zorder=0, alpha=0.22))
        ax.text(0.52, y + h/2, label, va='center', ha='left', fontsize=8,
                color='#2C3E50', fontweight='bold', rotation=90, zorder=2)

    def box(x, y, w, h, label, sub='', fc='#00619A', tc='white', fs=9, subfs=7.5, radius=0.2):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                     boxstyle=f'round,pad=0.04,rounding_size={radius}',
                     fc=fc, ec='white', lw=1.8, zorder=3))
        cy = y + h/2 + (0.13 if sub else 0)
        ax.text(x + w/2, cy, label, ha='center', va='center',
                fontsize=fs, color=tc, fontweight='bold', zorder=4, multialignment='center')
        if sub:
            ax.text(x + w/2, y + h/2 - 0.22, sub, ha='center', va='center',
                    fontsize=subfs, color=tc, style='italic', zorder=4)

    def arrow(x1, y1, x2, y2, color='#003369', lw=1.4):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=lw))

    band(0.4, 1.8, '#D6E8F7', 'FUENTES DE DATOS SAP')
    band(2.4, 1.4, '#FFF5D6', 'CAPA DE INTEGRACIÓN')
    band(4.0, 4.2, '#E8F5E9', 'MODELOS SAP ANALYTICS CLOUD')
    band(8.4, 3.8, '#F3E5F5', 'UNIDADES DE NEGOCIO / PROCESOS')
    band(12.4, 2.2, '#FFEBEE', 'SALIDAS — DASHBOARDS & REPORTES')

    box(0.8,  0.6, 2.8, 1.1, 'SAP FI',      'Contabilidad Financiera\nCuentas · Sociedades',    fc='#1565C0', fs=9)
    box(4.0,  0.6, 2.8, 1.1, 'SAP CO',      'Controlling\nCEBES · CECOS · CUENTAS',             fc='#1565C0', fs=9)
    box(7.2,  0.6, 2.8, 1.1, 'SAP SD',      'Ventas y Distribución\nClientes · Referencias',    fc='#1565C0', fs=9)
    box(10.4, 0.6, 2.8, 1.1, 'SAP MM',      'Gestión de Materiales\nReferencias / SKU',         fc='#1565C0', fs=9)
    box(13.6, 0.6, 2.8, 1.1, 'BW/4HANA',   'Data Warehouse\nConsolidación DWH',                fc='#0D47A1', fs=9)
    box(16.8, 0.6, 2.8, 1.1, 'DataSphere\n/ SLT', 'Replicación y\nTransformación',             fc='#0D47A1', fs=9)
    box(19.8, 0.6, 1.8, 1.1, 'TCURC\nMONEDA',                                                   fc='#1976D2', fs=8)

    box(3.5, 2.6, 14.5, 0.9,
        'SAP Analytics Cloud — Import Connection  |  Live Connection  |  OData / CSV / BW Connector',
        fc='#F57F17', tc='#1A1A1A', fs=9.5)
    for x in [2.2, 5.4, 8.6, 11.8, 15.0, 18.2]:
        arrow(x, 1.7, x, 2.6)
    arrow(20.7, 1.7, 18.0, 2.6)

    box(0.8, 4.3, 6.0, 3.6,
        'Modelo Ingresos\nFanalca',
        'Medida: Importe (Decimal)\n9 Dimensiones:\nVersion · RATIO · Date\nAUDITORIA · CEBES · CLIENTES\nMONEDA · REFERENCIA · SOCIEDAD',
        fc='#2E7D32', fs=10.5, subfs=8)
    box(7.8, 4.3, 6.0, 3.6,
        'Modelo EEFF\nFanalca',
        'Medida: Importe (Decimal)\n7 Dimensiones:\nVersion · CUENTA · Date\nAUDITORIA · CEBES\nMONEDA · SOCIEDAD',
        fc='#6A1B9A', fs=10.5, subfs=8)
    box(14.8, 4.3, 6.2, 3.6,
        'Modelo Costos\ny Gastos Fanalca',
        'Medida: Importe (Decimal)\n8 Dimensiones:\nVersion · CUENTAS · Date\nAUDITORIA · CEBES · CECOS\nMONEDA · SOCIEDAD',
        fc='#E65100', fs=10.5, subfs=8)

    for x in [3.8, 10.8, 17.9]:
        arrow(x, 3.5, x, 4.3)

    ax.text(11, 3.75,
            '★ Dimensiones compartidas: SOCIEDAD · CEBES · MONEDA · AUDITORIA · Version · Date',
            ha='center', va='center', fontsize=7.5, color='#003369', style='italic', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', fc='#E3F2FD', ec='#1565C0', lw=0.8))

    box(0.8, 8.7, 5.8, 3.0,
        'Fanalca Metalmecánica',
        'PMF · EMM · Autopartes\nTubería · Metal Sur · Ambiental\n→ CEBES: PMF/EMM/AUC/TUP\n→ Scripts: T02, autopartes, TUP',
        fc='#BF360C', fs=10, subfs=8.5)
    box(7.8, 8.7, 6.0, 3.0,
        'Honda Supermotos / Motos',
        'CKD · CBU · Repuestos · Motopartes\nNITs: FANALCA · SIM\n→ CEBES: HMC/HOC/HOD/HON/MPC/HRC\n→ Scripts: T01, SINB_HAC1, cartera',
        fc='#558B2F', fs=10, subfs=8.5)
    box(14.8, 8.7, 6.2, 3.0,
        'Honda Autos',
        'HAC · 16 Agencias · HPC · Talleres\nNIT: FANALCA (34 CEBEs)\n→ CEBES: HAC/HPC/HS1-HC3\n→ Scripts: T01, inventario, cartera',
        fc='#4527A0', fs=10, subfs=8.5)

    arrow(3.8, 7.9, 3.8, 8.7)
    arrow(10.8, 7.9, 10.8, 8.7)
    arrow(17.9, 7.9, 17.9, 8.7)

    dash = [
        (1.0,  'Dashboard\nEjecutivo\nEBITDA/KPIs'),
        (4.5,  'Análisis de\nIngresos P×Q\nRef · Cliente'),
        (7.8,  'EEFF Multi-\nsociedad\nReal vs Plan'),
        (11.2, 'Control\nCostos/Gastos\nCECOS/CEBES'),
        (14.6, 'Flujo de\nCaja\nDirecto'),
        (18.0, 'Variación\nForecast\nvs Budget'),
    ]
    for x, lbl in dash:
        box(x, 12.6, 3.0, 1.6, lbl, fc='#B71C1C', fs=8.5)
    arrow(11, 11.7, 11, 12.6)

    box(19.0, 4.3, 2.5, 1.2, 'Archivos\nValidación', 'SAC vs SAP FI', fc='#37474F', fs=8.5, subfs=7.5)
    arrow(19.0, 3.5, 19.0 + 1.25, 4.3)

    ax.text(11, 14.6, 'Arquitectura de Modelos SAC — Fanalca S.A. | Grupo Fanalca',
            ha='center', va='center', fontsize=14, fontweight='bold', color='#003369')
    ax.text(11, 14.15,
            'Proyecto SAP BUILD  ·  SAP Analytics Cloud Planning  ·  Metalmecánica | Honda Supermotos | Honda Autos  ·  2026',
            ha='center', va='center', fontsize=9, color='#555', style='italic')

    items = [
        (mpatches.Patch(color='#1565C0'), 'Módulos SAP ERP'),
        (mpatches.Patch(color='#F57F17'), 'Integración SAC'),
        (mpatches.Patch(color='#2E7D32'), 'Modelo Ingresos'),
        (mpatches.Patch(color='#6A1B9A'), 'Modelo EEFF'),
        (mpatches.Patch(color='#E65100'), 'Modelo Costos y Gastos'),
        (mpatches.Patch(color='#BF360C'), 'Metalmecánica'),
        (mpatches.Patch(color='#558B2F'), 'Honda Supermotos'),
        (mpatches.Patch(color='#4527A0'), 'Honda Autos'),
        (mpatches.Patch(color='#B71C1C'), 'Dashboards / Salidas'),
    ]
    fig.legend([h for h, _ in items], [l for _, l in items],
               loc='lower center', ncol=5, fontsize=8.5,
               framealpha=0.9, edgecolor='#BBBBBB', bbox_to_anchor=(0.5, -0.01))
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#F5F8FC')
    plt.close()
    print(f'Flowchart: {path}')


# ── DOCUMENTO WORD ────────────────────────────────────────────────────────────
def generar_doc(flowchart_path, doc_path):
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Cm(2.0); sec.bottom_margin = Cm(2.0)
        sec.left_margin = Cm(2.5); sec.right_margin = Cm(2.5)
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(10)
    add_footer(doc)

    # ── PORTADA ──────────────────────────────────────────────────────────────
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    set_cell_bg(cell, SAP_DARK)

    def cline(text, sz, bold=True, color=WHITE, sb=4, sa=4, italic=False):
        p = cell.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(sb); p.paragraph_format.space_after = Pt(sa)
        r = p.add_run(text)
        r.font.size = Pt(sz); r.font.bold = bold
        r.font.color.rgb = color; r.font.italic = italic

    cline('', 6, sb=20, sa=0)
    cline('SAP BUILD', 13, color=SAP_GOLD, italic=True, sa=2)
    cline('GRUPO FANALCA', 11, color=RGBColor(0xCC, 0xDD, 0xEE), bold=False)
    cline('', 6, sb=8, sa=8)
    cline('Documento de Diseño de Solución', 14, color=WHITE)
    cline('SAP Analytics Cloud', 24, color=WHITE, sa=2)
    cline('Modelos de Planeación Financiera', 16, color=SAP_GOLD, sb=2)
    cline('', 6, sb=12, sa=12)

    meta_tbl = doc.add_table(rows=6, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate([
        ('Cliente',   'Fanalca S.A.'),
        ('Proyecto',  'SAP BUILD — Implementación SAP S/4HANA + SAC'),
        ('Unidades',  'Metalmecánica | Honda Supermotos | Honda Autos'),
        ('Versión',   'v2.0'),
        ('Fecha',     '05 de junio de 2026'),
        ('Estado',    'Borrador para revisión y aprobación'),
    ]):
        r = meta_tbl.rows[i]
        set_cell_bg(r.cells[0], SAP_BLUE); set_cell_bg(r.cells[1], SAP_LIGHT)
        set_cell_borders(r.cells[0], color='003369', sz=4)
        set_cell_borders(r.cells[1], color='B0C4D8', sz=2)
        pk = r.cells[0].paragraphs[0]; pk.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rk = pk.add_run(k); rk.font.size = Pt(9); rk.font.bold = True; rk.font.color.rgb = WHITE
        pv = r.cells[1].paragraphs[0]
        rv = pv.add_run(v); rv.font.size = Pt(9); rv.font.color.rgb = SAP_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    doc.add_page_break()

    # ── TABLA DE CONTENIDO ────────────────────────────────────────────────────
    add_heading(doc, 'Tabla de Contenido', level=1, space_before=4)
    toc = [
        ('1.',   'Propósito del documento', '4'),
        ('2.',   'Cómo usar el documento', '4'),
        ('3.',   'Escenario / Proceso de negocio', '5'),
        ('3.1.', 'Objetivos empresariales y beneficios esperados', '5'),
        ('3.2.', 'Descripción a alto nivel de Requisitos empresariales', '6'),
        ('4.',   'Estructura organizativa relevante', '7'),
        ('5.',   'Diseño y configuración de soluciones', '9'),
        ('5.1.', 'Alcance del proceso de solución', '9'),
        ('5.2.', 'Valor de Actividad de Configuración — Scripts y Proceso', '12'),
        ('5.3.', 'Roles', '14'),
        ('5.4.', 'Inventario de datos maestros susceptibles de migración', '15'),
        ('5.5.', 'Componente de Solución Técnica Relacionada', '17'),
    ]
    tt = doc.add_table(rows=len(toc), cols=3)
    for i, (n, t, p) in enumerate(toc):
        r = tt.rows[i]; bg = SAP_LIGHT if i % 2 == 0 else WHITE
        for c in r.cells: set_cell_bg(c, bg)
        r.cells[0].paragraphs[0].add_run(n).font.size = Pt(9)
        p1 = r.cells[1].paragraphs[0]
        p1.paragraph_format.left_indent = Cm(0 if '.' not in n[1:] else 0.5)
        run = p1.add_run(t); run.font.size = Pt(9); run.font.bold = ('.' not in n[1:])
        r.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r.cells[2].paragraphs[0].add_run(p).font.size = Pt(9)
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════════
    # 1. PROPÓSITO
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, '1. Propósito del documento', level=1)
    add_body(doc,
        'El presente documento describe el diseño y la configuración de la solución SAP Analytics '
        'Cloud (SAC) implementada para Fanalca S.A., empresa colombiana líder en el sector '
        'automotriz, metalmecánico y de distribución de vehículos Honda, con más de 70 años de '
        'trayectoria en el mercado. Este artefacto constituye el Blueprint de Diseño de Solución '
        'del proyecto SAP BUILD, detallando los tres modelos analíticos de planeación financiera, '
        'sus dimensiones, los scripts de cálculo, las fuentes de datos, los componentes técnicos '
        'y los datos maestros involucrados. El documento se basa en las sesiones de levantamiento '
        'de información realizadas con los equipos de Metalmecánica, Honda Supermotos y Honda Autos.')

    add_info_box(doc, 'Modelos SAC en Alcance — Fanalca S.A.',
        ['Modelo de Ingresos Fanalca — 9 dimensiones | Planning Model (Read/Write)',
         'Modelo de Estados Financieros (EEFF) Fanalca — 7 dimensiones | Planning Model (Read/Write)',
         'Modelo de Costos y Gastos Fanalca — 8 dimensiones | Planning Model (Read/Write)',
         'Dimensiones compartidas: SOCIEDAD · CEBES · MONEDA · AUDITORIA · Version · Date',
         'NITs en alcance: FANALCA · Supermotos · SIM · Metal Sur | Periodo: 2024–2026'],
        bg_title=SAP_DARK)

    add_body(doc, 'Alcance del documento:')
    for b in [
        'Unidades de negocio: Metalmecánica (8 líneas), Honda Supermotos/Motos (5 líneas), Honda Autos (34 CEBEs)',
        'Plataforma: SAP Analytics Cloud (SAC) — Tenencia en la nube SAP BTP',
        'Período de referencia: Ejercicios fiscales 2024–2026 (horizonte 5 años para bancos)',
        'Versiones: Presupuesto (3 escenarios), Forecast mensual, Plan Bancos 1 y 2',
        'Migración desde: SAP BPC (sistema actual) → SAC como plataforma de destino',
        'Fuera de alcance inmediato: Flujo de Caja (en planificación), módulo de Renting',
    ]:
        add_bullet(doc, b)

    # ══════════════════════════════════════════════════════════════════════════
    # 2. CÓMO USAR EL DOCUMENTO
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, '2. Cómo usar el documento', level=1)
    add_body(doc,
        'Este documento está dirigido a múltiples perfiles del proyecto SAP BUILD. Utilice la '
        'Tabla de Contenido para navegar directamente a la sección de interés. Las tablas de '
        'la Sección 5 contienen los valores de configuración que deben implementarse en SAC '
        'en la secuencia descrita. Los scripts identificados en la Sección 5.2 corresponden '
        'a los paquetes de cálculo BPC que deben replicarse como Data Actions en SAC.')

    uso_t = doc.add_table(rows=6, cols=3)
    header_row(uso_t, ['Perfil', 'Uso del Documento', 'Secciones Clave'])
    for i, (p, u, s) in enumerate([
        ('Arquitectos SAP/SAC',   'Revisión del diseño técnico, dimensiones y scripts de cálculo',   '4, 5.1, 5.5'),
        ('Analistas Funcionales', 'Validación del mapeo de requisitos de negocio y proceso P×Q',      '3, 5.2'),
        ('Equipo TI / BASIS',     'Configuración de integración SAP ERP ↔ SAC y DataSphere',          '5.1, 5.5'),
        ('Usuarios Clave',        'Validación de la lógica de negocio, datos maestros y UAT',         '3, 5.3, 5.4'),
        ('Gestión del Proyecto',  'Seguimiento del alcance, actividades, roles y entregables',        '5.2, 5.3'),
    ], 1):
        data_row(uso_t, i, [p, u, s], alt=(i % 2 == 0), bold_col=0)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ══════════════════════════════════════════════════════════════════════════
    # 3. ESCENARIO / PROCESO DE NEGOCIO
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, '3. Escenario / Proceso de negocio', level=1)
    add_body(doc,
        'Fanalca S.A. es un conglomerado industrial colombiano con más de 70 años de trayectoria, '
        'conformado por tres grandes vicepresidencias estratégicas. La compañía requiere una '
        'plataforma de analítica centralizada que integre los datos financieros y operativos de '
        'sus divisiones para soportar la toma de decisiones gerenciales y ejecutivas en tiempo '
        'real. El proceso de presupuestación inicia en agosto-septiembre del año en curso para el '
        'año siguiente (N+1), se aprueba ante la Junta Directiva en diciembre/enero, y se '
        'complementa con una proyección de 5 años que se presenta en asamblea en marzo. '
        'Adicionalmente se maneja un forecast mensual actualizado (Forecast 1 a N) y escenarios '
        'para bancos (Plan Bancos 1 en marzo, Plan Bancos 2 en junio).')

    un_t = doc.add_table(rows=4, cols=4)
    header_row(un_t, ['Unidad de Negocio', 'Líneas de Negocio', 'Proceso Clave SAC', 'Sistema Fuente'])
    for i, (u, l, p, s) in enumerate([
        ('Fanalca Metalmecánica\n(Transformación de Acero)',
         'PMF · Ensamble Medellín · Autopartes · Defensas\nAmbiental · Tubería · Metal Sur · Mecanizado',
         'Costos de producción por CECOS/CEBES\nP&G por línea · Capital de trabajo',
         'BPC / UNOE → SAC\nS/4HANA (futuro)'),
        ('Honda Supermotos / Motos',
         'Motos CKD (HMC) · CBU (HOC/HOD/HON)\nRepuestos (HRC) · Motopartes (MPC/MPCE)',
         'Ingresos P×Q por referencia, cliente y CEBE\nJuego de cartera e inventario de motos',
         'NIGURI / BPC → SAC\nS/4HANA + DataSphere (futuro)'),
        ('Honda Autos\n(34 CEBEs)',
         'HAC (importador) · 16 Agencias · HPC (repuestos)\n16 Talleres · Renting (NIT aparte)',
         'P×Q por referencia y agencia · EEFF\nCapital de trabajo HAC · Agencias · HPC',
         'Excel / BPC → SAC\nS/4HANA + DataSphere (futuro)'),
    ], 1):
        data_row(un_t, i, [u, l, p, s], alt=(i % 2 == 0), bold_col=0)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_heading(doc, 'Arquitectura de Modelos SAC — Fanalca S.A.', level=2, space_before=8)
    doc.add_picture(flowchart_path, width=Inches(6.3))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = doc.add_paragraph(
        'Figura 1. Arquitectura de modelos SAP Analytics Cloud — Fanalca S.A. | Proyecto SAP BUILD 2026')
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.runs[0].font.size = Pt(8); cap.runs[0].font.italic = True; cap.runs[0].font.color.rgb = GRAY_MED
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Ciclo presupuestal
    add_heading(doc, 'Ciclo de Planeación y Versiones', level=2, space_before=8)
    ver_t = doc.add_table(rows=8, cols=4)
    header_row(ver_t, ['Versión', 'Descripción', 'Período de Elaboración', 'Escenarios'])
    for i, (v, d, p, e) in enumerate([
        ('Presupuesto (Plan)', 'Presupuesto anual aprobado por Junta Directiva', 'Agosto–Enero', 'Pesimista · Optimista · Medio'),
        ('Forecast 1-N',      'Proyección mensual actualizada (rolling)',         'Mensual',     '1 versión activa por mes'),
        ('Plan Bancos 1',     'Proyección 5 años para presentación a bancos',    'Marzo',       '5 años calendario Honda'),
        ('Plan Bancos 2',     'Actualización del Plan Bancos mid-year',           'Junio',       '5 años (revisado)'),
        ('Real / Actual',     'Ejecución contable real desde SAP FI/BW',         'Mensual (cierre)', 'Un único real por período'),
        ('Proyección de cierre', 'Estimado de cierre del año en curso',          'Q3–Q4',       'Coincide con Forecast N'),
        ('Plan 3 años',       'Presupuesto estratégico para planeación LP',      'Q4',          'Consolidado de 3 años'),
    ], 1):
        data_row(ver_t, i, [v, d, p, e], alt=(i % 2 == 0), bold_col=0)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 3.1
    add_heading(doc, '3.1. Objetivos empresariales y beneficios esperados', level=2)
    obj_t = doc.add_table(rows=7, cols=3)
    header_row(obj_t, ['#', 'Objetivo Empresarial', 'Beneficio Esperado'])
    for i, (n, o, b) in enumerate([
        ('1', 'Visibilidad financiera consolidada multi-sociedad',
              'Vista unificada de resultados de NITs FANALCA, Supermotos, SIM y Metal Sur en tiempo real'),
        ('2', 'Análisis de ingresos granular por referencia y cliente',
              'P×Q desagregado por modelo de moto/auto, cliente (distribuidor/agencia), CEBE y mes'),
        ('3', 'Migración BPC → SAC preservando lógica de scripts',
              'Replicar los scripts T01, T02, cartera, inventario como Data Actions en SAC sin pérdida de lógica'),
        ('4', 'Control de costos por línea de Metalmecánica',
              'Seguimiento CECOS/CEBES para PMF, Tubería, Autopartes, Ambiental con tarifas reales vs. estándar'),
        ('5', 'Cierre financiero ágil con EEFF consolidado',
              'Reducción del tiempo de cierre mensual mediante envío automático vía scripts desde modelos de origen'),
        ('6', 'Planeación xP&A integrada 5 años',
              'Horizontes 1, 3, 5 y 10 años en SAC para presentaciones ejecutivas y bancarias de Fanalca S.A.'),
    ], 1):
        data_row(obj_t, i, [n, o, b], alt=(i % 2 == 0), center_cols=[0], bold_col=1)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 3.2
    add_heading(doc, '3.2. Descripción a alto nivel de Requisitos empresariales', level=2)
    req_t = doc.add_table(rows=10, cols=4)
    header_row(req_t, ['ID', 'Requisito', 'Descripción', 'Modelo SAC'])
    for i, (rid, req, desc, mod) in enumerate([
        ('REQ-001', 'P×Q Ingresos por referencia',
         'Calcular ingresos = Unidades × Precio de venta, por referencia (moto/auto), CEBE y mes. '
         'Incluir IVA (19%), impuesto al consumo (8%) y recuperación de fletes (cta. 42)',
         'Ingresos'),
        ('REQ-002', 'Juego de cartera por entidad',
         'Saldo inicial + Facturación con IVA - Recaudos = Saldo final. Tasas: 50/50 HAC, 80/20 agencias, '
         '75/25 talleres. Cartera renting separada ($12.000M no se recauda en proyección)',
         'Ingresos'),
        ('REQ-003', 'Juego de inventarios motos/autos',
         'Inventario inicial + Compras/producción - Despachos = Inventario final, en unidades y pesos. '
         'Valoración a costo promedio (HMC) y costo estándar. Inventario HAC en zona franca',
         'Ingresos'),
        ('REQ-004', 'EEFF consolidado por sociedad',
         'Estado de Resultados (P&G) y Balance por cuenta contable, CEBE y sociedad. '
         'P&G "sábana" (detalle administrativo con CSC discriminados) + P&G NIT (sin ventas internas)',
         'EEFF'),
        ('REQ-005', 'Costos de conversión por CEBE PMF',
         'Tarifas de mano de obra directa y CIF por centro de trabajo, distribuidas a las líneas '
         'clientes (Autopartes, Motopartes, Ambiental, etc.) mediante alícuotas y centros transversales',
         'Costos y Gastos'),
        ('REQ-006', 'Flujo de caja directo',
         'Recaudos, pagos de MP exterior, nómina, impuestos bimestrales (IVA, IC, autorretención, ICA), '
         'giros financiados en USD (tasas BL contratadas, plazo 6 meses), caja mínima operativa',
         'EEFF'),
        ('REQ-007', 'Variables macroeconómicas',
         'TRM (USD/COP), IBR + spread (deuda nacional), SOFR + spread (deuda extranjera), '
         'IPC, tasas de coberturas. Parametrizadas como datos de entrada por escenario en SAC',
         'Todos'),
        ('REQ-008', 'Versionamiento y escenarios',
         'Real, Plan (3 sub-escenarios: pesimista/optimista/medio), Forecast 1-N, Plan Bancos 1-2. '
         'El presupuesto aprobado es inmutable; los escenarios son versiones adicionales en SAC',
         'Todos'),
        ('REQ-009', 'Separación de scripts por línea de negocio',
         'El script T01 actual (motos+autos comparten un paquete) debe separarse para evitar '
         'sobreescritura entre líneas cuando los datos aún están incompletos en alguna unidad',
         'Ingresos'),
    ], 1):
        data_row(req_t, i, [rid, req, desc, mod], alt=(i % 2 == 0),
                 center_cols=[0, 3], bold_col=1)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ══════════════════════════════════════════════════════════════════════════
    # 4. ESTRUCTURA ORGANIZATIVA
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, '4. Estructura organizativa relevante', level=1)
    add_body(doc,
        'La estructura organizativa de Fanalca S.A. está conformada por múltiples entidades '
        'jurídicas (NITs) y centros de beneficio (CEBEs) que se mapean directamente a las '
        'dimensiones SOCIEDAD y CEBES de los modelos SAC. A continuación se detallan los '
        'elementos organizativos identificados en las sesiones de levantamiento de información.')

    # NITs
    add_heading(doc, 'Entidades Jurídicas (Dimensión SOCIEDAD)', level=2, space_before=8)
    nit_t = doc.add_table(rows=8, cols=4)
    header_row(nit_t, ['NIT / Sociedad', 'Descripción', 'Unidades SAC', 'Estado en SAP'])
    for i, (n, d, u, s) in enumerate([
        ('FANALCA S.A.', 'NIT principal. Consolida motos (HMC/HOC/HOD/HON/MPC/HRC), '
         'autos (HAC/agencias/HPC/talleres) y toda transformación de acero',
         'Ingresos · EEFF · Costos y Gastos', 'NIT activo — S/4HANA en impl.'),
        ('Supermotos',   'NIT aparte. Canal tradicional de motos Honda B2C. Tiene SAP ERP propio.',
         'EEFF · Ingresos (carga desde BW)', 'SAP ERP activo con ODS/BW'),
        ('SIM — Servicios Industriales Metal Mecánicos',
         'NIT aparte. Fabrica piezas plásticas para ensamble de motos en Fanalca.',
         'EEFF · Costos y Gastos', 'Dentro del alcance del proyecto'),
        ('Metal Sur',    'NIT aparte. Tubería de diferente diámetro, dos plantas físicas.',
         'Ingresos · EEFF · Costos y Gastos', 'NIT independiente — en alcance'),
        ('FN Servicios', 'NIT aparte. Tiene SAP ERP. Carga de real automática vía BW.',
         'EEFF', 'SAP ERP activo con ODS/BW'),
        ('Renting',      'NIT aparte. Empresa de leasing operativo de vehículos. Compra a agencias.',
         'Cartera separada en modelo Ingresos', 'Fuera de alcance directo SAC'),
        ('Compañía 6',   'Sociedad virtual de ajustes y eliminaciones de consolidación.',
         'EEFF (eliminaciones)', 'Pendiente definición — no es SAC'),
    ], 1):
        data_row(nit_t, i, [n, d, u, s], alt=(i % 2 == 0), bold_col=0)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # CEBEs - Motos
    add_heading(doc, 'Centros de Beneficio (CEBES) — Honda Supermotos / Motos', level=2, space_before=8)
    cebe_m = doc.add_table(rows=10, cols=4)
    header_row(cebe_m, ['Código CEBE', 'Nombre', 'Descripción del Proceso', 'Modelos SAC'])
    for i, (c, n, d, m) in enumerate([
        ('HMC',  'Honda Motos CKD',        'Importación CKD, ensamble en planta Yumbo. Venta B2B a canal tradicional, Dim y HON',     'Ingresos · EEFF'),
        ('HOC',  'Honda CBU Consolidado',   'Importación motos armadas (CBU). CEBE padre de HOD y HON',                                'Ingresos · EEFF'),
        ('HOD',  'Honda CBU Canal Tradicional', 'Ventas CBU al canal tradicional (distribuidores terceros y red propia)',              'Ingresos · EEFF'),
        ('HON',  'Honda CBU Negocios Especiales', 'Ventas CBU a negocios especiales e institucionales',                               'Ingresos · EEFF'),
        ('MPC',  'Motopartes',              'Fabricación y compra de piezas para integración nacional. Venta interna a HMC',           'Ingresos · Costos'),
        ('MPCE', 'Motopartes Externo',      'Ventas externas de motopartes a Yamaha, Hero y otras ensambladoras',                     'Ingresos · EEFF'),
        ('HRC',  'Repuestos Motos Honda',   'Importación y comercialización de repuestos, llantas, cascos, aceites Honda',             'Ingresos · EEFF'),
        ('APG',  'Sede APG Motos',          'Sede regional de motos — ventas B2C canal tradicional',                                  'Ingresos'),
        ('SBH',  'Sede SBH Motos',          'Sede regional de motos — ventas B2C canal tradicional',                                  'Ingresos'),
    ], 1):
        data_row(cebe_m, i, [c, n, d, m], alt=(i % 2 == 0), bold_col=0, center_cols=[0])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # CEBEs - Metalmecánica
    add_heading(doc, 'Centros de Beneficio (CEBES) — Metalmecánica / Transformación de Acero', level=2, space_before=4)
    cebe_mm = doc.add_table(rows=12, cols=4)
    header_row(cebe_mm, ['Código CEBE', 'Nombre', 'Descripción del Proceso', 'Tipo de Ingreso SAC'])
    for i, (c, n, d, t) in enumerate([
        ('PMF',  'Planta Metalmecánica Fanalca', 'Gran planta de manufactura. Presta servicios a todas las líneas comerciales. Su "ingreso" = costo absorbido vía órdenes de producción', 'Costo absorbido → EEFF'),
        ('EMM',  'Ensamble Medellín',        'Servicio de ensamble autopartes para Renault Sofasa (Duster, Kwid, VW). 12 referencias de facturación. In-house y planta exterior', 'P×Q → Ingresos · EEFF'),
        ('AUC',  'Autopartes',               '73 referencias nacionales + 85 exportación (158 total). Clientes: Renault, Hino, Superpolo, Fenacional, Exportación', 'P×Q × referencia → Ingresos'),
        ('DEF',  'Defensas Viales',          'Fabricación de defensas viales en acero para carreteras. Nacional por ahora. Referencias agrupadas (no SKU)', 'P×Q directo → EEFF'),
        ('AMB',  'Ambiental / Carrocerías',  'Fabricación de cajas compactadoras de residuos. Venta nacional + CKD exportación. Incluye kits hidráulicos importados', 'P×Q → Ingresos · EEFF'),
        ('TUP',  'Tubería Fanalca',          'Lámina importada → cold roll, galvanizado, estructural, steel deck. Venta nacional + exportación. Script corre 2 veces', 'P×Q (2 corridas) → Ingresos · EEFF'),
        ('MSR',  'Metal Sur',                'NIT aparte. Tubería diámetros distintos, 2 plantas. Proceso idéntico a TUP. Caja mínima: $1.500M/mes', 'P×Q (2 corridas) → Ingresos · EEFF'),
        ('COR',  'Centro de Corte Externo',  '~6-7 clientes. Unidad: toneladas. Precio promedio. Actualmente graba directo a EEFF sin P×Q', 'Directo → EEFF'),
        ('MEC',  'Mecanizado Externo',       'Servicio de mecanizado (agujeros, doblez). Proceso idéntico a Centro de Corte', 'Directo → EEFF'),
        ('PDB',  'Ingeniería (transversal)', 'Área de ingeniería. Se distribuye 97% a AUC, 3% a DEF como alícuota de costo', 'Costos y Gastos'),
        ('PPC',  'Mantenimiento y Calidad',  'Área transversal de mantenimiento (~10-12 CECOS) y calidad. Se distribuye por % a cada línea productiva', 'Costos y Gastos'),
    ], 1):
        data_row(cebe_mm, i, [c, n, d, t], alt=(i % 2 == 0), bold_col=0, center_cols=[0])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # CEBEs - Autos
    add_heading(doc, 'Centros de Beneficio (CEBES) — Honda Autos (34 CEBEs total)', level=2, space_before=4)
    cebe_a = doc.add_table(rows=8, cols=4)
    header_row(cebe_a, ['Código / Grupo', 'Nombre', 'Descripción', 'Impuestos / Proceso'])
    for i, (c, n, d, t) in enumerate([
        ('HAC',  'Honda Autos Cali (importador)', 'Importa vehículos de Brasil, EE.UU., Canadá, Japón, Tailandia. Venta interna sin IVA a agencias. Inventario en zona franca', 'Sin IVA en factura interna. FOB + factor internamiento'),
        ('HPC',  'Honda Parts (repuestos)',        '90% venta interna a talleres propios · 10% distribuidores externos. Margen repuestos: 48%. Ref: RHPC (una referencia)', 'IVA 19% en ventas a distribuidores'),
        ('HS1-HS3-HSB', 'Agencias Honda Sur (3)', 'Agencias propias ciudad sur. Facturan al cliente final con IVA 19% + IC 8% = 27%. Tienen taller y gestión de usados', 'IVA 27% (o 28% Pilot, <19% híbridos)'),
        ('HC1-HC3-HCB', 'Agencias Honda Centro (3)', 'Agencias propias ciudad centro. Misma estructura que agencias sur', 'IVA 27% estándar'),
        ('HXX (10 más)', 'Otras 10 agencias activas', 'Total 16 agencias, algunas aún no funcionales. Mismo proceso para todas', 'Mismo esquema impositivo'),
        ('TAL-xx (16)', 'Talleres (16)',           '16 talleres ligados a las 16 agencias. Referencias: MO mecánica, lámina, pintura, eléctrica, enlucimiento + repuestos', 'Recaudo 75%/25%/10% en 3 meses'),
        ('RENTING',     'Renting (NIT aparte)',    'Empresa del grupo. Compra autos a agencias. Cartera separada $12.000M. No se recauda en proyección. Plan colocación por agencia', 'Cartera renting aislada'),
    ], 1):
        data_row(cebe_a, i, [c, n, d, t], alt=(i % 2 == 0), bold_col=0)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_info_box(doc, 'Estructura de Centros de Costo (CECOS) — Dimensión Costos y Gastos',
        ['CECOS 11 — Mano de obra directa (PMF): tarifas estándar por centro de trabajo y referencia',
         'CECOS 12 — Servicios a la producción / administrativos operativos de planta',
         'CECOS 2  — Centros de costo administrativos (gerencias, finanzas, recursos humanos)',
         'CECOS PPC — Mantenimiento (~10-12 centros) y Calidad · Kaizen: distribuidos por alícuota a líneas productivas',
         'CECOS PDB — Ingeniería: 97% distribuido a Autopartes, 3% a Defensas Viales',
         'CECOS Metal Sur — identificados por planta 1 / planta 2 para distribución de MO y CIF',
         'Pendiente: reunión con FI/CO/SD para definición de jerarquías de CECOS en S/4HANA'],
        bg_title=SAP_BLUE)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. DISEÑO Y CONFIGURACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    add_heading(doc, '5. Diseño y configuración de soluciones', level=1)

    # 5.1
    add_heading(doc, '5.1. Alcance del proceso de solución', level=2)
    add_body(doc,
        'SAC para Fanalca S.A. contempla 3 modelos Planning interconectados migrados desde SAP BPC. '
        'Los modelos de Ingresos y Costos/Gastos alimentan el modelo EEFF mediante scripts '
        '(Data Actions en SAC), replicando la lógica de "destination app" existente en BPC.')

    # Model 1
    add_heading(doc, 'Modelo 1: Ingresos Fanalca — 9 Dimensiones', level=3, space_before=8)
    add_body(doc, 'Planning Model (Read/Write) | Medida: Importe (Decimal) | P×Q + Capital de trabajo',
             italic=True, color=SAP_BLUE)
    m1 = doc.add_table(rows=10, cols=4)
    header_row(m1, ['Dimensión', 'Tipo', 'Descripción / Uso en Fanalca', 'Valores / Fuente'])
    for j, (d, tp, de, vals) in enumerate([
        ('Version★', 'Estándar SAC', 'Plan / Forecast 1-N / Real / Plan Bancos 1-2',
         'Estándar SAC — configuración de versiones'),
        ('RATIO',    'Genérica',     'Ratios P×Q: ventas brutas, precio unitario, IVA, unidades, costo unitario, cartera CI/ECI, facturación IVA, recaudos, inventario, proveedores',
         'Definición manual — listado de ~30 ratios por unidad'),
        ('Date★',    'Estándar SAC', 'Dimensión temporal mensual (Año/Mes)',
         'Estándar SAC — granularidad mensual'),
        ('AUDITORIA★','Genérica',   'Origen de carga: "script" (datos calculados) vs. "ajuste" (entrada manual correctiva)',
         'Script · Ajuste · definición manual'),
        ('CEBES★',   'Genérica',    'CEBEs de motos (HMC,HOC,HOD,HON,MPC,MPCE,HRC) y autos (HAC, 16 agencias, HPC, 16 talleres)',
         'CO-PCA: tabla CEPC — SAP FI/CO'),
        ('CLIENTES', 'Genérica',    'Distribuidores motos (Supermotos, terceros) · Agencias autos · Clientes Autopartes (Renault/Sofasa, Hino)',
         'SD: tabla KNA1 — SAP SD'),
        ('MONEDA★',  'Genérica',    'Moneda de operación. Motos y autos: COP. Exportación autopartes: USD',
         'FI: tabla TCURC — COP / USD'),
        ('REFERENCIA','Genérica',   'Motos CKD: nivel familia (ej. CB125, NAVI, C192). Autos: por modelo (ZR-V, CR-V, HR-V, City). Autopartes: 158 referencias (73 nac + 85 exp). Repuestos: 13 agrupadores',
         'MM: MARA/MVKE — homologación BPC→SAP pendiente'),
        ('SOCIEDAD★','Genérica',    'FANALCA, SUPERMOTOS, SIM, METAL SUR',
         'FI: tabla T001'),
    ], 1):
        data_row(m1, j, [d, tp, de, vals], alt=(j % 2 == 0), bold_col=0, center_cols=[1])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Model 2
    add_heading(doc, 'Modelo 2: EEFF Fanalca — 7 Dimensiones', level=3, space_before=8)
    add_body(doc, 'Planning Model (Read/Write) | Medida: Importe (Decimal) | Estado de Resultados + Balance + Flujo de Caja',
             italic=True, color=PURPLE)
    m2 = doc.add_table(rows=8, cols=4)
    header_row(m2, ['Dimensión', 'Tipo', 'Descripción / Uso en Fanalca', 'Valores / Fuente'], bg=PURPLE)
    for j, (d, tp, de, vals) in enumerate([
        ('Version★',  'Estándar SAC', 'Plan / Forecast / Real / Plan Bancos — misma config que Modelo Ingresos',
         'Estándar SAC'),
        ('CUENTA',    'Genérica',     'Cuentas contables del P&G y Balance. Incluye cuentas 4 (ingresos), 5 (gastos), 7 (costos), cuentas de balance. P&G "sábana" (con CSC discriminados) + P&G NIT (sin ventas internas)',
         'FI: tablas SKA1/SKB1'),
        ('Date★',     'Estándar SAC', 'Dimensión temporal mensual',
         'Estándar SAC'),
        ('AUDITORIA★','Genérica',     'Script (envío desde modelos de origen) · Ajuste (correcciones manuales)',
         'Script · Ajuste'),
        ('CEBES★',    'Genérica',     'Todos los CEBEs de los 3 modelos. EEFF recibe de Ingresos y Costos/Gastos',
         'CO-PCA: tabla CEPC'),
        ('MONEDA★',   'Genérica',     'COP principal. Giros financiados en USD (saldo ~$82M USD ejemplo)',
         'FI: tabla TCURC'),
        ('SOCIEDAD★', 'Genérica',     'FANALCA · SUPERMOTOS · SIM · METAL SUR · Compañía 6 (eliminaciones)',
         'FI: tabla T001'),
    ], 1):
        data_row(m2, j, [d, tp, de, vals], alt=(j % 2 == 0), bold_col=0, center_cols=[1])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Model 3
    add_heading(doc, 'Modelo 3: Costos y Gastos Fanalca — 8 Dimensiones', level=3, space_before=8)
    add_body(doc, 'Planning Model (Read/Write) | Medida: Importe (Decimal) | Nómina · CIF · OPEX desde UNOE',
             italic=True, color=ORANGE)
    m3 = doc.add_table(rows=9, cols=4)
    header_row(m3, ['Dimensión', 'Tipo', 'Descripción / Uso en Fanalca', 'Valores / Fuente'], bg=ORANGE)
    for j, (d, tp, de, vals) in enumerate([
        ('Version★',  'Estándar SAC', 'Plan / Forecast / Real — misma config',
         'Estándar SAC'),
        ('CUENTAS',   'Genérica',     'Cuentas de costos/gastos CO. Incluye: MO directa (11), CIF (12), gastos administrativos (2), gastos financieros. Se mapea a ecocuenta en scripts',
         'CO: tablas CSKA/CSKB — desde UNOE'),
        ('Date★',     'Estándar SAC', 'Dimensión temporal mensual',
         'Estándar SAC'),
        ('AUDITORIA★','Genérica',     'Script (calculado) · Ajuste (manual UNOE/correcciones)',
         'Script · Ajuste'),
        ('CEBES★',    'Genérica',     'PMF, EMM, AUC, DEF, AMB, TUP, MSR, PDB, PPC y transversales de motos y autos',
         'CO-PCA: tabla CEPC'),
        ('CECOS',     'Genérica',     'Centros de costo de producción (11), servicios (12), administrativos (2), mantenimiento (PPC ~10-12), calidad, Kaizen, ingeniería (PDB)',
         'CO-CCA: tabla CSKS — definición pendiente con CO'),
        ('MONEDA★',   'Genérica',     'COP (principal). USD para exportación en autopartes y ambiental',
         'FI: tabla TCURC'),
        ('SOCIEDAD★', 'Genérica',     'FANALCA · SIM · METAL SUR',
         'FI: tabla T001'),
    ], 1):
        data_row(m3, j, [d, tp, de, vals], alt=(j % 2 == 0), bold_col=0, center_cols=[1])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_info_box(doc, 'Flujo de datos entre los 3 modelos SAC',
        ['1. MODELO INGRESOS → MODELO EEFF: vía script T01/T02/autopartes (P×Q → cuentas 4/costo de ventas)',
         '2. MODELO COSTOS Y GASTOS → MODELO EEFF: vía paquetes de envío de gastos (UNOE → cuentas 5/7)',
         '3. MODELO EEFF consolida: P&G + Balance + Flujo de Caja + Capital de trabajo integrado',
         'En BPC actual se usa "destination app" en cada script. En SAC: Data Actions con escritura cruzada',
         'El script T01 (motos+autos) debe separarse en SAC en 2 Data Actions independientes'],
        bg_title=SAP_GREEN)

    # 5.2
    add_heading(doc, '5.2. Valor de Actividad de Configuración — Scripts y Proceso', level=2)
    add_body(doc,
        'Los siguientes scripts fueron identificados en las sesiones de levantamiento. En SAC '
        'deben replicarse como Data Actions (equivalente a paquetes BPC). Se listan por unidad '
        'de negocio con su descripción funcional y el modelo de destino.')

    # Scripts Motos
    add_heading(doc, 'Scripts — Honda Supermotos / Motos', level=3, space_before=6)
    sc_m = doc.add_table(rows=10, cols=4)
    header_row(sc_m, ['Script / Data Action', 'Descripción Funcional', 'Modelos Afectados', 'Prioridad'])
    for i, (s, d, m, p) in enumerate([
        ('SINB_HAC1', 'Juego de inventarios tránsito y producción de motos en unidades (HMC CKD)', 'Ingresos', 'Alta'),
        ('T01 Motos (separar)', 'Cálculo P×Q ventas y costos motos. Genera facturación con IVA y envía a EEFF. DEBE separarse del T01 de autos para evitar sobreescritura', 'Ingresos → EEFF', 'Crítica'),
        ('ls_saldos_car_motos', 'Juego de cartera motos: Saldo inicial + Facturación IVA - Recaudo = Saldo final → siguiente período', 'Ingresos', 'Alta'),
        ('ls_saldos_inv_motos', 'Juego de inventarios motos: unidades y pesos. Alimenta balance en EEFF', 'Ingresos → EEFF', 'Alta'),
        ('Ingresos HRC', 'Cálculo ingresos y costos de Repuestos Motos (HRC): 13 agrupadores de referencias', 'Ingresos → EEFF', 'Alta'),
        ('P01 Motopartes', 'Cálculo compras nacionales motopartes (MPC). Costo materia prima + MO + CIF separados', 'Ingresos → EEFF', 'Alta'),
        ('IVA descontable motos', 'Cálculo IVA descontable bimestral. Base: unidades a nacionalizar × FOB. Mejora: usar unidades de venta vs. pago', 'Ingresos → EEFF (flujo caja)', 'Media'),
        ('Plan Bancos scripts', 'Corrida de presupuesto 5 años (Plan Bancos 1 en marzo, Plan Bancos 2 en junio)', 'Todos', 'Alta'),
        ('Paquete envío EEFF', 'Envío consolidado de P&G y balance desde Ingresos hacia modelo EEFF por período', 'Ingresos → EEFF', 'Alta'),
    ], 1):
        data_row(sc_m, i, [s, d, m, p], alt=(i % 2 == 0), bold_col=0, center_cols=[2, 3])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Scripts Metalmecánica
    add_heading(doc, 'Scripts — Metalmecánica / Transformación de Acero', level=3, space_before=6)
    sc_mm = doc.add_table(rows=10, cols=4)
    header_row(sc_mm, ['Script / Data Action', 'Descripción Funcional', 'Modelos Afectados', 'Prioridad'])
    for i, (s, d, m, p) in enumerate([
        ('T02 EMM', 'P×Q Ensamble Medellín (12 referencias, cliente Renault/Sofasa). Genera ingresos y envía costos al EEFF', 'Ingresos → EEFF', 'Alta'),
        ('Script autopartes', 'P×Q para 158 referencias (73 nac + 85 exp) por cliente. Costo: MP (lámina) + conversión (PMF) + alícuotas PDB + PPC', 'Ingresos → EEFF', 'Alta'),
        ('Script TUP (x2)', 'Tubería: corre 2 veces. 1ª corrida: costo unitario lámina (CFR × factor internamiento). 2ª corrida: precio de venta con margen', 'Ingresos → EEFF', 'Alta'),
        ('Script Metal Sur (x2)', 'Proceso idéntico a TUP. Dos plantas físicas → distribución de MO/CIF por planta', 'Ingresos → EEFF', 'Alta'),
        ('Script Ambiental', 'P×Q cajas compactadoras nacionales + CKD. Lámina importada + kit hidráulico + compras nacionales + MO/CIF PMF', 'Ingresos → EEFF', 'Alta'),
        ('Paquete Defensas', 'Carga directa en EEFF (sin P×Q modelo ingresos actualmente). Cartera manual en Ingresos', 'EEFF · Ingresos', 'Media'),
        ('Paquete UNOE → Gastos', 'Importación de gastos desde UNOE a modelo Costos y Gastos. Fiel copia de UNOE en SAC', 'Costos y Gastos → EEFF', 'Alta'),
        ('Distribución CECOS transversales', 'Alícuota de PPC (mantenimiento/calidad) y PDB (ingeniería) hacia líneas productivas. Driver: % definido por VP Transformación', 'Costos y Gastos', 'Alta'),
        ('Cálculo costo no absorbido', 'Diferencia entre tarifa estándar PMF y absorción real de costos de producción', 'Costos y Gastos → EEFF', 'Media'),
    ], 1):
        data_row(sc_mm, i, [s, d, m, p], alt=(i % 2 == 0), bold_col=0, center_cols=[2, 3])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Scripts Autos
    add_heading(doc, 'Scripts — Honda Autos', level=3, space_before=6)
    sc_a = doc.add_table(rows=9, cols=4)
    header_row(sc_a, ['Script / Data Action', 'Descripción Funcional', 'Modelos Afectados', 'Prioridad'])
    for i, (s, d, m, p) in enumerate([
        ('T01 Autos (separar)', 'P×Q vehículos HAC: FOB × factor internamiento × TRM = costo. Precio × unidades = ingresos. SEPARAR del T01 de motos', 'Ingresos → EEFF', 'Crítica'),
        ('Inventario HAC (HACCP)', 'Juego de inventario importador: saldo inicial + compras (unidades+pesos) - despachos a agencias = saldo final. Inventario en zona franca', 'Ingresos → EEFF', 'Alta'),
        ('Cartera HAC', 'Cartera comercial (distribuidores externos, 50%/50% recaudo) + cartera renting ($12.000M, no se recauda). Separación obligatoria', 'Ingresos', 'Alta'),
        ('Cartera Agencias (FNAG)', 'Juego de cartera por agencia: 80%/20% comercial · renting por plan inversiones. Corre individualmente. Mejora: correr por jerarquía en SAC', 'Ingresos', 'Alta'),
        ('Ingresos HPC + Talleres', 'P×Q HPC (RHPC, una referencia, margen 48%) + ingresos talleres por tipo servicio (MO mecánica, lámina, pintura, eléctrica, enlucimiento)', 'Ingresos → EEFF', 'Alta'),
        ('Cartera HPC', 'Juego cartera HPC: 60%/40% recaudo. 10% trabajos internos personal Fanalca: no se recauda (0.75-3.88% por taller)', 'Ingresos', 'Alta'),
        ('Inventario Agencias', 'Usados: retomas = ventas (inventario estable). Costo promedio global. IVA 5% impuesto al consumo', 'Ingresos → EEFF', 'Media'),
        ('Costo de oportunidad autos', 'KPI financiero: (Cartera HAC - Cartera Renting) × IBR+spread + (Inventario - Proveedores) × SOFR+spread', 'Ingresos → EEFF', 'Media'),
    ], 1):
        data_row(sc_a, i, [s, d, m, p], alt=(i % 2 == 0), bold_col=0, center_cols=[2, 3])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Actividades de configuración
    add_heading(doc, 'Actividades de Configuración SAC', level=3, space_before=6)
    cfg_t = doc.add_table(rows=12, cols=5)
    header_row(cfg_t, ['Actividad', 'Área', 'Estado', 'Prioridad', 'Notas'])
    for i, (a, ar, st, pr, n) in enumerate([
        ('Creación de los 3 modelos SAC Planning', 'Modelado SAC', 'COMPLETO', 'Alta',
         '3 modelos en ambiente Desarrollo con dimensiones configuradas'),
        ('Separación script T01 motos / autos', 'Data Actions', 'PENDIENTE', 'Crítica',
         'Riesgo: sobreescritura entre unidades si se corre el paquete unificado'),
        ('Apertura HOC → HOD / HON', 'Modelado SAC', 'PENDIENTE', 'Alta',
         'P&G debe reflejar las 3 sedes CBU. HOC solo compra; HOD/HON venden'),
        ('Migración BPC → SAC (17+ scripts)', 'Data Actions', 'EN PROGRESO', 'Alta',
         'Mapeo 1:1 de paquetes BPC a Data Actions SAC por unidad'),
        ('Plantillas SAC instanciables (BPF)', 'Planning', 'EN PROGRESO', 'Alta',
         'Autos actualmente usa consultas Excel fijas; migrar a plantillas SAC con selector de CEBE'),
        ('Integración SAP S/4HANA → DataSphere → SAC', 'Integración', 'EN PROGRESO', 'Alta',
         'Capa DataSphere para transformaciones; evita replicar datos cuando sea posible'),
        ('Carga automática real BW → SAC', 'Integración', 'COMPLETO', 'Alta',
         'NITs con ERP activo (Supermotos, FN Servicios): ODS/BW ya configurados'),
        ('Definición jerarquías SD/FI/CO en S/4HANA', 'Maestros', 'PENDIENTE', 'Alta',
         'Reunión requerida: IDs referencias BPC no coinciden con ERP. Maestros pendientes'),
        ('Excel Add-in SAC para usuarios', 'Adopción', 'PENDIENTE', 'Media',
         'Requiere Office 365 de 64 bits. Usuarios BPC ya tienen 365-64. Instalar desde tienda Excel'),
        ('Perfilamiento de acceso y roles SAC', 'Seguridad', 'PENDIENTE', 'Alta',
         'Data Access Control por SOCIEDAD. Roles: Admin, Modeler, Key User, Viewer'),
        ('Pruebas UAT por unidad de negocio', 'Calidad', 'PENDIENTE', 'Alta',
         'Key users: Sofía (motos), Gustavo (autos), Freddy/Ana (metalmecánica)'),
    ], 1):
        data_row(cfg_t, i, [a, ar, st, pr, n], alt=(i % 2 == 0), bold_col=0, center_cols=[2, 3])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 5.3
    add_heading(doc, '5.3. Roles', level=2)
    add_body(doc,
        'Los siguientes roles fueron identificados durante las sesiones de levantamiento. '
        'Los responsables funcionales son Key Users del proyecto SAP BUILD y liderarán '
        'las pruebas UAT y la validación de los modelos SAC en sus respectivas unidades.')

    rol_t = doc.add_table(rows=13, cols=4)
    header_row(rol_t, ['Nombre / Perfil', 'Responsabilidad en SAC', 'Unidad', 'Tipo de Acceso SAC'])
    for i, (r, resp, un, acc) in enumerate([
        ('Sofía',          'Key User motos. Mantiene datos de HMC (CKD), HOC/HOD/HON (CBU), HRC (repuestos), MPC/MPCE (motopartes). Valida plantillas y scripts de motos', 'Honda Supermotos / Motos', 'Planning — Read/Write'),
        ('Gustavo',        'Key User autos. Mantiene datos HAC, agencias (HS/HC), HPC, talleres, renting. También corre scripts de motos como respaldo', 'Honda Autos', 'Planning — Read/Write'),
        ('Juan Camilo',    'Líder funcional del proyecto. Coordina sesiones técnicas, valida arquitectura y define mejoras de configuración en SAC', 'Proyecto SAP BUILD', 'Modeler / Admin'),
        ('Freddy',         'Key User Transformación de Acero. Responsable de tubería (TUP), Metal Sur, PMF, ensamble Medellín (EMM) y autopartes', 'Metalmecánica', 'Planning — Read/Write'),
        ('Ana / Nancy Puentes', 'Key User Aplicaciones Industriales. Responsable de defensas viales, ambiental, tubería y Metal Sur', 'Metalmecánica', 'Planning — Read/Write'),
        ('Edison',         'Técnico TI. Mantenimiento actual de ODS en SAP ERP. Administrará conectores SAC ↔ BW/DataSphere', 'Transformación Digital', 'Admin / Integración'),
        ('Gabriela',       'Técnico TI. Equipo transversal Transformación Digital. Configuración técnica SAC', 'Transformación Digital', 'Admin / Modeler'),
        ('Jonathan',       'Técnico TI. Equipo transversal Transformación Digital. Desarrollo de Data Actions', 'Transformación Digital', 'Modeler'),
        ('Área de Costos', 'Entrega porcentajes de IVA exportación, costo promedio de lámina, amortizaciones herramentales y tarifas PMF', 'Costos / Finanzas', 'Viewer / Aprobador'),
        ('Contabilidad',   'Entrega reales mes a mes acumulados (balance + P&G) para carga en SAC como versión Real', 'Contabilidad / FI', 'Viewer'),
        ('Gerentes Comerciales', 'Entregan unidades, precios de venta y validación de rangos por línea de negocio', 'Cada línea de negocio', 'Viewer / Input via plantillas'),
        ('Consultor SAP/SAC', 'Diseño y construcción de modelos, Data Actions y Stories en SAC. Soporte técnico durante implementación', 'Proyecto SAP BUILD', 'Admin / Modeler / Developer'),
    ], 1):
        data_row(rol_t, i, [r, resp, un, acc], alt=(i % 2 == 0), bold_col=0)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 5.4
    add_heading(doc, '5.4. Inventario de datos maestros susceptibles de migración', level=2)
    add_body(doc,
        'Los datos maestros identificados deben cargarse en SAC desde los sistemas SAP ERP '
        '(S/4HANA, FI, CO, SD, MM) y desde fuentes propias de Fanalca. La carga se realiza '
        'mediante archivos CSV o conectores OData. Nota crítica: los identificadores de referencias '
        'en BPC (ej. "FN_HUR_HR01") no coinciden con los códigos en el ERP legacy; se requiere '
        'tabla de mapeo antes de la carga en SAC.')

    dm_t = doc.add_table(rows=13, cols=5)
    header_row(dm_t, ['Dato Maestro / Dimensión', 'Fuente SAP', 'Método de Carga', 'Volumen Estimado', 'Complejidad'])
    for i, (d, f, m, v, c) in enumerate([
        ('SOCIEDAD',   'FI – T001',        'Import CSV manual',   '~7 sociedades',    'BAJA'),
        ('CEBES',      'CO-PCA – CEPC',    'Import CSV / OData',  '~50+ CEBEs',       'ALTA'),
        ('CECOS',      'CO-CCA – CSKS',    'Import CSV / OData',  '~40+ CECOS',       'ALTA'),
        ('CUENTA (EEFF)', 'FI – SKA1/SKB1', 'Import CSV / BW',   'Plan de cuentas FI', 'ALTA'),
        ('CUENTAS (C&G)', 'CO – CSKA/CSKB','Import CSV / BW',    'Plan de cuentas CO', 'ALTA'),
        ('CLIENTES',   'SD – KNA1',        'OData / Import CSV',  'Red distribuidores + agencias', 'ALTA'),
        ('REFERENCIA', 'MM – MARA/MVKE',   'Import CSV / BW',     '158+ SKUs (mapeo BPC→SAP pendiente)', 'MUY ALTA'),
        ('RATIO',      'Definición manual', 'Carga manual SAC',   '~30 ratios por unidad', 'MEDIA'),
        ('MONEDA',     'FI – TCURC',       'Import CSV manual',   'COP · USD · EUR',  'BAJA'),
        ('AUDITORIA',  'Definición manual', 'Carga manual SAC',   'Script · Ajuste',  'BAJA'),
        ('Version',    'Estándar SAC',      'Configuración SAC',  'Plan/Forecast/Real + escenarios', 'BAJA'),
        ('TRM / Macroeconómicas', 'Tesorería / DIAN', 'Import CSV por escenario', 'TRM · IBR · SOFR · IPC por mes', 'MEDIA'),
    ], 1):
        data_row(dm_t, i, [d, f, m, v, c], alt=(i % 2 == 0), bold_col=0, center_cols=[4])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_info_box(doc, 'Prioridad de carga de datos maestros — Fanalca S.A.',
        ['FASE 1 — Crítico pre Go-Live: SOCIEDAD, CEBES, MONEDA, Version, AUDITORIA (sin estos no corren los scripts)',
         'FASE 2 — Alto para configuración de modelos: CECOS, CUENTA, CUENTAS, CLIENTES',
         'FASE 3 — Medio (historiales y datos transaccionales 2024–2025): REFERENCIA, RATIO, datos reales',
         'PENDIENTE CRITICO: Reunión con módulos FI/CO/SD para alinear jerarquías de materiales y CECOS en S/4HANA',
         'PENDIENTE: Tabla de mapeo entre identificadores BPC (ej. FN_HUR_HR01) y códigos SAP ERP'],
        bg_title=SAP_GREEN)

    # Ratios identificados
    add_heading(doc, 'Ratios identificados en las sesiones (Dimensión RATIO)', level=3, space_before=8)
    rat_t = doc.add_table(rows=17, cols=3)
    header_row(rat_t, ['Ratio', 'Descripción', 'Aplica a'])
    for i, (r, d, a) in enumerate([
        ('VTA_BRU',   'Ventas brutas (unidades × precio de venta)',             'Motos · Autos · Autopartes · Tubería'),
        ('PVU',       'Precio de venta unitario (COP o USD para exportación)',   'Todos los modelos de ingresos'),
        ('UND_VTA',   'Unidades de venta por referencia y mes',                 'Motos · Autos · Autopartes'),
        ('UND_COM',   'Unidades de compra/pago (difiere de venta para IVA desc.)', 'Motos CKD · Autos HAC'),
        ('FOB',       'Precio FOB de compra al proveedor exterior',             'Motos · Autos · Tubería · Ambiental'),
        ('FACTOR_INT','Factor de internamiento (aranceles + seguros + fletes)',  'Motos · Autos · Tubería'),
        ('TRM',       'Tasa de cambio USD/COP por mes (inicial = final = promedio)', 'Todo lo importado'),
        ('TASA_BL',   'Tasa ponderada de la fecha de compra de lámina (≠TRM presupuesto)', 'Tubería · Metal Sur · Ambiental'),
        ('IVA',       'IVA facturado: 19% estándar · 5% imp.consumo usados · 8% imp.consumo vehículos nuevos', 'Todos'),
        ('CAR_CI',    'Saldo inicial cartera (crédito)',                        'Motos · Autos · Autopartes'),
        ('CAR_FAC_IVA','Facturación con IVA del período',                      'Todos'),
        ('RECAUDO',   'Recaudos por ventas nuevas y saldo inicial cartera',     'Todos'),
        ('INV_CI',    'Saldo inicial inventario (unidades y pesos)',             'Motos · Autos · Ambiental · Tubería'),
        ('COSTO_OPT', 'Costo de oportunidad: (Cartera-Renting)×IBR + (Inv-Prov)×SOFR', 'Autos · Tubería · Defensas'),
        ('CTO_NO_ABS','Costo no absorbido PMF (diferencia cuenta 7 vs. absorción real)', 'Metalmecánica PMF'),
        ('ROYALTY',   'Royalty Honda: 2% del PVP. Fee por moto. Se carga en ratios de flujo de caja', 'Motos CKD (HMC)'),
    ], 1):
        data_row(rat_t, i, [r, d, a], alt=(i % 2 == 0), bold_col=0, center_cols=[0])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 5.5
    add_heading(doc, '5.5. Componente de Solución Técnica Relacionada', level=2)
    add_body(doc,
        'La arquitectura técnica de la solución SAC para Fanalca S.A. se basa en SAP BTP '
        'como plataforma central, con SAP DataSphere como capa de integración y transformación '
        'entre SAP S/4HANA (en implementación) y SAC. La migración desde SAP BPC implica '
        'replicar la lógica de scripts y plantillas en los equivalentes SAC.')

    tech_t = doc.add_table(rows=11, cols=4)
    header_row(tech_t, ['Componente', 'Descripción', 'Entorno', 'Versión / Estado'])
    for i, (c, d, e, v) in enumerate([
        ('SAP Analytics Cloud (SAC)',
         'Plataforma SaaS en SAP BTP. 3 tenants: DEV / QA / PRD. Módulos: Planning, Stories, Data Actions, BPF',
         'SAP BTP – SaaS', 'PRD · QA · DEV — Activo 2024.Q4+'),
        ('SAP S/4HANA',
         'Sistema ERP en implementación como fuente futura del real. Módulos FI, CO, SD, MM. Fuente de maestros y transacciones',
         'On-Premise Colombia', 'En implementación — S/4HANA 2023+'),
        ('SAP BPC (actual)',
         'Sistema de planeación actual con 17+ scripts/paquetes. Referencia para migración a SAC. Fuente de lógica de negocio',
         'On-Premise', 'BPC 11.1 — A migrar'),
        ('SAP BW/4HANA',
         'Data Warehouse para carga del real desde ERP (Supermotos, FN Servicios ya conectados). ODS y jobs de madrugada',
         'On-Premise / Cloud', 'BW/4HANA 2.0+ — Activo para Supermotos/FN'),
        ('SAP DataSphere',
         'Capa de integración/transformación entre S/4HANA y SAC. Permite conectarse sin replicar datos. AWS y Azure disponibles como data lakes adicionales',
         'SAP BTP', 'En configuración — clave para FANALCA NIT'),
        ('UNOE',
         'Sistema de presupuesto de gastos (origen del Modelo de Costos y Gastos). Carga fiel copia de UNOE a BPC/SAC vía script de gastos',
         'On-Premise Fanalca', 'Activo — integración pendiente a SAC'),
        ('SAC – Import Connection',
         'Conector batch: archivos CSV, OData y conectores SAP BW. Carga programada de datos maestros y transaccionales',
         'SAC (cloud)', 'Estándar SAC — configurar por dimensión'),
        ('SAC – Live Connection',
         'Conexión en tiempo real hacia SAP BW/4HANA o SAP HANA para reportes live (sin copia de datos)',
         'SAC ↔ BW / DataSphere', 'Requiere SAP Connector — planificado'),
        ('SAC Excel Add-in',
         'Complemento Excel para carga de datos desde plantillas. Requiere Office 365 de 64 bits. Instalar desde tienda Excel (pestaña Inicio → Complementos)',
         'Estación de usuario', 'Office 365 64-bit — validado con key users'),
        ('SAP IAS / SSO',
         'Single Sign-On (SSO) para acceso de usuarios Fanalca a SAC mediante SAP Identity Authentication Service',
         'SAP BTP', 'SAP IAS Cloud — Activo'),
    ], 1):
        data_row(tech_t, i, [c, d, e, v], alt=(i % 2 == 0), bold_col=0, center_cols=[2])
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Mejoras pendientes de la sesión
    add_heading(doc, 'Mejoras y Decisiones de Arquitectura Pendientes', level=3, space_before=8)
    mej_t = doc.add_table(rows=10, cols=3)
    header_row(mej_t, ['Mejora / Decisión', 'Descripción', 'Responsable'])
    for i, (m, d, r) in enumerate([
        ('Separar T01 en 2 Data Actions',
         'Script T01 actual cubre motos y autos. Al correr parcialmente puede sobreescribir datos. SAC debe tener 2 Data Actions independientes',
         'Juan Camilo / TI'),
        ('Apertura HOC en HOD y HON',
         'El P&G de CBU debe reflejar los 3 CEBEs (HOC compra, HOD/HON venden). Requiere reconfigurar modelo de ingresos y scripts',
         'Sofía / Consultor SAC'),
        ('IVA descontable bimestral',
         'Reemplazar base de pagos por base de unidades a nacionalizar (más preciso). Mejora para flujo de caja bimestral',
         'Sofía / Área de Costos'),
        ('Correr scripts por jerarquía',
         'Actualmente algunos paquetes (cartera taller, cartera HPC) corren individualmente por CEBE. SAC permite correr sobre jerarquía completa, reduciendo tiempo',
         'TI / Consultor SAC'),
        ('Plantillas instanciables autos',
         'Autos usa consultas Excel fijas con escenario "quemado". Migrar a plantillas SAC instanciables con BPF y selector de CEBE/escenario como motos',
         'Gustavo / Consultor SAC'),
        ('Referencia dummy para IVA motos/defensas',
         'Actualmente IVA se carga referencia a referencia. Mejora: usar referencia NA0 y que el script aplique IVA a todas. Reduce entradas manuales',
         'Sofía / Freddy'),
        ('Costo metodología HMC',
         'Actualmente costo promedio. Con S/4HANA puede migrar a costo real. Definir con área de Costos y CO',
         'Área de Costos / CO'),
        ('Jerarquías de materiales en S/4HANA',
         'Reunión requerida con FI, SD, CO para definir jerarquías de referencias. IDs actuales BPC no coinciden con ERP',
         'Juan Camilo / SD/CO'),
        ('Sesiones técnicas adicionales',
         'El equipo técnico (Edison, Gabriela, Jonathan) solicita sesiones adicionales de arquitectura con Sergio y equipo SAC para adopción de la metodología',
         'Sergio / Transformación Digital'),
    ], 1):
        data_row(mej_t, i, [m, d, r], alt=(i % 2 == 0), bold_col=0)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Próximos pasos
    add_info_box(doc, 'Próximos Pasos — Proyecto SAP BUILD Fanalca',
        ['1.  Aprobación de este documento de diseño (v2.0) por comité del proyecto',
         '2.  Reunión urgente con FI/CO/SD: definir jerarquías de materiales y CECOS en S/4HANA',
         '3.  Tabla de mapeo: identificadores BPC → códigos SAP ERP (todas las líneas)',
         '4.  Carga Fase 1: SOCIEDAD, CEBES, MONEDA, Version, AUDITORIA en SAC DEV',
         '5.  Separación del script T01 en 2 Data Actions independientes (motos / autos)',
         '6.  Sesión de arquitectura técnica: Sergio + Edison + Gabriela + Jonathan + Consultor',
         '7.  Migración de los 17+ scripts BPC a Data Actions SAC por unidad de negocio',
         '8.  Desarrollo de plantillas SAC instanciables para autos (equivalente a BPF motos)',
         '9.  UAT con key users: Sofía (motos), Gustavo (autos), Freddy/Ana (metalmecánica)',
         '10. Formación Excel Add-in y SAC a todos los usuarios clave. Go-Live planificado'],
        bg_title=SAP_DARK)

    doc.save(doc_path)
    print(f'Documento: {doc_path}')


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    BASE = '/home/user/Johnmeg'
    fp = os.path.join(BASE, 'arquitectura_fanalca.png')
    dp = os.path.join(BASE, 'Diseno_Modelos_SAC_Fanalca_v2.docx')
    print('Generando flowchart...')
    generar_flowchart(fp)
    print('Generando documento Word...')
    generar_doc(fp, dp)
    print('Listo!')
