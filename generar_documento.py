#!/usr/bin/env python3
"""
Generador del documento de diseño SAP Analytics Cloud - Fanalca
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import io
import os

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy


# ─── PALETA DE COLORES SAP ───────────────────────────────────────────────────
SAP_BLUE       = RGBColor(0x00, 0x41, 0x7A)   # Azul primario SAP
SAP_LIGHT_BLUE = RGBColor(0x00, 0x70, 0xBF)   # Azul claro SAP
SAP_GOLD       = RGBColor(0xF0, 0xAB, 0x00)   # Dorado SAP
SAP_GREY       = RGBColor(0x35, 0x35, 0x3A)   # Gris oscuro SAP
SAP_LIGHT_GREY = RGBColor(0xF5, 0xF5, 0xF5)   # Gris claro (fondo tabla)
SAP_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
SAP_GREEN      = RGBColor(0x10, 0x74, 0x54)   # Verde SAP
SAP_TEAL       = RGBColor(0x00, 0x8A, 0x97)   # Teal SAP


def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return '#{:02X}{:02X}{:02X}'.format(int(r*255), int(g*255), int(b*255))


# ─── FLUJOGRAMA DE MODELOS ────────────────────────────────────────────────────
def crear_flujograma():
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')

    # Fondo
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#F8F9FA')

    # Título
    ax.text(8, 11.5, 'Arquitectura de Modelos SAP Analytics Cloud – Fanalca S.A.',
            ha='center', va='center', fontsize=14, fontweight='bold',
            color='#00417A', fontfamily='DejaVu Sans')
    ax.plot([1, 15], [11.1, 11.1], color='#F0AB00', linewidth=2.5)

    # ── Capa de Origen de Datos ─────────────────────────────────────────────
    origen_box = FancyBboxPatch((0.3, 8.8), 15.4, 1.8,
                                 boxstyle="round,pad=0.1",
                                 facecolor='#E8F4FD', edgecolor='#0070BF',
                                 linewidth=1.5, zorder=1)
    ax.add_patch(origen_box)
    ax.text(8, 10.3, 'FUENTES DE DATOS – SAP ERP / S/4HANA',
            ha='center', va='center', fontsize=10, fontweight='bold',
            color='#00417A')

    # Fuentes de datos
    fuentes = [
        ('FI\nContabilidad\nFinanciera', 2.5, 9.4, '#00417A'),
        ('CO\nControlling /\nCentros de Costo', 5.5, 9.4, '#00417A'),
        ('SD\nVentas y\nDistribución', 8.5, 9.4, '#00417A'),
        ('MM\nGestión de\nMateriales', 11.5, 9.4, '#00417A'),
        ('BW/4HANA\nData Warehouse\n', 14.0, 9.4, '#0070BF'),
    ]
    for lbl, x, y, col in fuentes:
        bx = FancyBboxPatch((x-1.1, y-0.5), 2.2, 0.95,
                             boxstyle="round,pad=0.08",
                             facecolor=col, edgecolor='white',
                             linewidth=1, zorder=2)
        ax.add_patch(bx)
        ax.text(x, y-0.02, lbl, ha='center', va='center',
                fontsize=7.5, color='white', fontweight='bold',
                multialignment='center')

    # ── Flechas hacia modelos ───────────────────────────────────────────────
    for xp in [2.5, 5.5, 8.5]:
        ax.annotate('', xy=(xp, 7.65), xytext=(xp, 8.8),
                    arrowprops=dict(arrowstyle='->', color='#0070BF',
                                   lw=1.8))
    # EEFF recibe de FI y CO
    ax.annotate('', xy=(8.0, 7.65), xytext=(5.5, 8.8),
                arrowprops=dict(arrowstyle='->', color='#0070BF',
                                lw=1.8, connectionstyle='arc3,rad=0.1'))
    ax.annotate('', xy=(8.0, 7.65), xytext=(11.5, 8.8),
                arrowprops=dict(arrowstyle='->', color='#0070BF',
                                lw=1.8, connectionstyle='arc3,rad=-0.1'))

    # ── Capa de Modelos SAC ─────────────────────────────────────────────────
    modelos_info = [
        {
            'titulo': 'Modelo Ingresos',
            'subtitulo': 'Fanalca',
            'medida': 'Medida: Importe (Decimal)',
            'dims': ['Version', 'RATIO', 'Date', 'AUDITORIA',
                     'CEBES', 'CLIENTES', 'MONEDA', 'REFERENCIA', 'SOCIEDAD'],
            'x': 2.5,
            'color_header': '#00417A',
            'color_body': '#E8F4FD',
            'color_dim': '#D0E8F8',
        },
        {
            'titulo': 'Modelo EEFF',
            'subtitulo': 'Fanalca',
            'medida': 'Medida: Importe (Decimal)',
            'dims': ['Version', 'CUENTA', 'Date', 'AUDITORIA',
                     'CEBES', 'MONEDA', 'SOCIEDAD'],
            'x': 8.0,
            'color_header': '#107454',
            'color_body': '#E8F5F0',
            'color_dim': '#C8EBE0',
        },
        {
            'titulo': 'Modelo Costos',
            'subtitulo': 'y Gastos Fanalca',
            'medida': 'Medida: Importe (Decimal)',
            'dims': ['Version', 'CUENTAS', 'Date', 'AUDITORIA',
                     'CEBES', 'CECOS', 'MONEDA', 'SOCIEDAD'],
            'x': 13.5,
            'color_header': '#5C3A8C',
            'color_body': '#F0EAF8',
            'color_dim': '#E0D0F4',
        },
    ]

    for m in modelos_info:
        x = m['x']
        # Caja del modelo
        mbx = FancyBboxPatch((x-2.3, 2.4), 4.6, 5.2,
                              boxstyle="round,pad=0.12",
                              facecolor=m['color_body'],
                              edgecolor=m['color_header'],
                              linewidth=2, zorder=2)
        ax.add_patch(mbx)

        # Header
        hbx = FancyBboxPatch((x-2.3, 7.0), 4.6, 0.6,
                              boxstyle="round,pad=0.05",
                              facecolor=m['color_header'],
                              edgecolor=m['color_header'],
                              linewidth=0, zorder=3)
        ax.add_patch(hbx)
        ax.text(x, 7.32, m['titulo'], ha='center', va='center',
                fontsize=9.5, fontweight='bold', color='white', zorder=4)
        ax.text(x, 7.1, m['subtitulo'], ha='center', va='center',
                fontsize=7.5, color='#F0AB00', zorder=4)

        # Medida
        mbx2 = FancyBboxPatch((x-2.0, 6.5), 4.0, 0.4,
                               boxstyle="round,pad=0.05",
                               facecolor=m['color_header'],
                               edgecolor='white',
                               linewidth=0.8, alpha=0.85, zorder=3)
        ax.add_patch(mbx2)
        ax.text(x, 6.72, m['medida'], ha='center', va='center',
                fontsize=7.5, color='white', zorder=4)
        ax.text(x, 6.42, '▼ Dimensiones', ha='center', va='center',
                fontsize=7.5, color=m['color_header'], fontweight='bold',
                zorder=4)

        # Dimensiones
        n = len(m['dims'])
        step = 3.7 / (n + 0.5)
        for i, dim in enumerate(m['dims']):
            dy = 6.2 - i * step
            is_common = dim in ['Version', 'Date', 'AUDITORIA', 'CEBES',
                                 'MONEDA', 'SOCIEDAD']
            fcolor = '#F0AB00' if is_common else m['color_dim']
            tcolor = '#00417A' if is_common else m['color_header']
            dbx = FancyBboxPatch((x-1.85, dy-0.18), 3.7, 0.32,
                                  boxstyle="round,pad=0.04",
                                  facecolor=fcolor,
                                  edgecolor=m['color_header'],
                                  linewidth=0.5, zorder=3)
            ax.add_patch(dbx)
            ax.text(x, dy-0.01, dim, ha='center', va='center',
                    fontsize=7, color=tcolor, fontweight='bold', zorder=4)

    # ── Capa SAC Reporting ──────────────────────────────────────────────────
    rep_box = FancyBboxPatch((0.3, 0.3), 15.4, 1.8,
                              boxstyle="round,pad=0.1",
                              facecolor='#FFF8E6', edgecolor='#F0AB00',
                              linewidth=2, zorder=1)
    ax.add_patch(rep_box)
    ax.text(8, 1.88, 'SAP ANALYTICS CLOUD – CAPA DE PRESENTACIÓN',
            ha='center', va='center', fontsize=10, fontweight='bold',
            color='#F0AB00')

    reportes = [
        ('Stories /\nDashboards\nFinancieros', 2.5, 1.1, '#F0AB00'),
        ('Análisis\nde Ingresos\nComercial', 5.5, 1.1, '#F0AB00'),
        ('Reportes\nde Gastos\nOpex/Capex', 8.5, 1.1, '#F0AB00'),
        ('Planeación\nFinanciera\nxP&A', 11.5, 1.1, '#F0AB00'),
        ('Alertas y\nKPIs\nEjecutivos', 14.0, 1.1, '#F0AB00'),
    ]
    for lbl, x, y, col in reportes:
        bx2 = FancyBboxPatch((x-1.0, y-0.48), 2.0, 0.9,
                              boxstyle="round,pad=0.06",
                              facecolor='white', edgecolor=col,
                              linewidth=1.5, zorder=2)
        ax.add_patch(bx2)
        ax.text(x, y+0.0, lbl, ha='center', va='center',
                fontsize=7, color='#35353A', fontweight='bold',
                multialignment='center')

    # Flechas de modelos a reporting
    for x in [2.5, 8.0, 13.5]:
        ax.annotate('', xy=(x, 2.15), xytext=(x, 2.4),
                    arrowprops=dict(arrowstyle='->', color='#35353A',
                                   lw=1.8))

    # Leyenda
    legend_elements = [
        mpatches.Patch(facecolor='#F0AB00', edgecolor='#00417A',
                       label='Dimensión común (compartida entre modelos)'),
        mpatches.Patch(facecolor='#D0E8F8', edgecolor='#00417A',
                       label='Dimensión específica – Ingresos'),
        mpatches.Patch(facecolor='#C8EBE0', edgecolor='#107454',
                       label='Dimensión específica – EEFF'),
        mpatches.Patch(facecolor='#E0D0F4', edgecolor='#5C3A8C',
                       label='Dimensión específica – Costos y Gastos'),
    ]
    ax.legend(handles=legend_elements, loc='lower center',
              bbox_to_anchor=(0.5, -0.04), ncol=2,
              fontsize=8, framealpha=0.9, edgecolor='#CCCCCC')

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=180, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    buf.seek(0)
    return buf


# ─── HELPERS DE FORMATO WORD ──────────────────────────────────────────────────
def set_cell_bg(cell, hex_color):
    """Relleno de fondo en celda de tabla."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color.lstrip('#'))
    tcPr.append(shd)


def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        tag = OxmlElement(f'w:{edge}')
        tag.set(qn('w:val'), kwargs.get('val', 'single'))
        tag.set(qn('w:sz'), kwargs.get('sz', '6'))
        tag.set(qn('w:color'), kwargs.get('color', '00417A'))
        tcBorders.append(tag)
    tcPr.append(tcBorders)


def add_horizontal_rule(doc, color_hex='00417A'):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:color'), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)


def set_doc_margins(section):
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3.0)
    section.right_margin  = Cm(2.5)


def apply_paragraph_format(para, space_before=6, space_after=6,
                            line_spacing=None):
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.space_after  = Pt(space_after)
    if line_spacing:
        para.paragraph_format.line_spacing = line_spacing


# ─── CONSTRUCCIÓN DEL DOCUMENTO ──────────────────────────────────────────────
def build_document():
    doc = Document()

    # ── Estilos de fuente base ────────────────────────────────────────────
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10)
    style.font.color.rgb = SAP_GREY

    # Márgenes
    set_doc_margins(doc.sections[0])

    # ══════════════════════════════════════════════════════════════════════
    # PORTADA
    # ══════════════════════════════════════════════════════════════════════

    # Banda de color superior (simulada con tabla de 1x1)
    cover_table = doc.add_table(rows=1, cols=1)
    cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = cover_table.cell(0, 0)
    set_cell_bg(cell, '#00417A')
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(14)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('SAP ANALYTICS CLOUD')
    run.font.name = 'Calibri'
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = SAP_WHITE
    run2 = p.add_run('\nDocumento de Diseño de Solución')
    run2.font.name = 'Calibri'
    run2.font.size = Pt(13)
    run2.font.bold = False
    run2.font.color.rgb = SAP_GOLD

    doc.add_paragraph()

    # Empresa y proyecto
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_title.add_run('FANALCA S.A.')
    r.font.name = 'Calibri'
    r.font.size = Pt(26)
    r.font.bold = True
    r.font.color.rgb = SAP_BLUE

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p_sub.add_run('Implementación SAP Analytics Cloud\nModelos Financieros y Comerciales')
    r2.font.name = 'Calibri'
    r2.font.size = Pt(13)
    r2.font.color.rgb = SAP_GREY

    doc.add_paragraph()

    # Tabla de metadatos del documento
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.style = 'Table Grid'

    meta_data = [
        ('Versión del Documento',  'v1.0'),
        ('Fecha de Creación',      '05 de Junio de 2026'),
        ('Estado',                 'Borrador para Revisión'),
        ('Clasificación',          'Confidencial – Uso Interno'),
        ('Responsable',            'Equipo de Implementación SAC'),
    ]
    for i, (k, v) in enumerate(meta_data):
        row = meta_table.rows[i]
        set_cell_bg(row.cells[0], '#00417A')
        set_cell_bg(row.cells[1], '#F5F5F5' if i % 2 == 0 else '#FFFFFF')
        pk = row.cells[0].paragraphs[0]
        pk.alignment = WD_ALIGN_PARAGRAPH.LEFT
        rk = pk.add_run(k)
        rk.font.bold = True
        rk.font.color.rgb = SAP_WHITE
        rk.font.size = Pt(9)
        rk.font.name = 'Calibri'
        pv = row.cells[1].paragraphs[0]
        rv = pv.add_run(v)
        rv.font.color.rgb = SAP_GREY
        rv.font.size = Pt(9)
        rv.font.name = 'Calibri'

    doc.add_paragraph()
    add_horizontal_rule(doc, 'F0AB00')

    # ══════════════════════════════════════════════════════════════════════
    # TABLA DE CONTENIDOS (manual)
    # ══════════════════════════════════════════════════════════════════════
    doc.add_page_break()

    toc_title = doc.add_paragraph()
    toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = toc_title.add_run('TABLA DE CONTENIDO')
    rt.font.name = 'Calibri'
    rt.font.size = Pt(14)
    rt.font.bold = True
    rt.font.color.rgb = SAP_BLUE
    add_horizontal_rule(doc)

    toc_entries = [
        ('1.', 'Propósito del documento',                                    '4'),
        ('2.', 'Cómo usar el documento',                                     '4'),
        ('3.', 'Escenario / Proceso de negocio',                             '4'),
        ('3.1.', 'Objetivos empresariales y beneficios esperados',           '4'),
        ('3.2.', 'Descripción a alto nivel de Requisitos empresariales',     '4'),
        ('4.', 'Estructura organizativa relevante',                          '5'),
        ('5.', 'Diseño y configuración de soluciones',                       '5'),
        ('5.1.', 'Alcance del proceso de solución',                          '5'),
        ('5.2.', 'Valor de Actividad de Configuración',                      '6'),
        ('5.3.', 'Roles',                                                    '6'),
        ('5.4.', 'Inventario de datos maestros susceptibles de migración',   '6'),
        ('5.5.', 'Componente de Solución Técnica Relacionada',               '6'),
    ]
    for num, name, page in toc_entries:
        p_toc = doc.add_paragraph()
        indent = Cm(0.5) if len(num) > 2 else Cm(0)
        p_toc.paragraph_format.left_indent = indent
        p_toc.paragraph_format.space_before = Pt(2)
        p_toc.paragraph_format.space_after  = Pt(2)
        r_num = p_toc.add_run(f'{num}  ')
        r_num.font.bold = True
        r_num.font.color.rgb = SAP_BLUE
        r_num.font.size = Pt(10)
        r_name = p_toc.add_run(name)
        r_name.font.color.rgb = SAP_GREY
        r_name.font.size = Pt(10)
        dots = '.' * (70 - len(name) - len(num))
        r_dots = p_toc.add_run(f' {dots} {page}')
        r_dots.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
        r_dots.font.size = Pt(9)

    # ══════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: PROPÓSITO DEL DOCUMENTO
    # ══════════════════════════════════════════════════════════════════════
    doc.add_page_break()

    def heading1(doc, num, text):
        p = doc.add_paragraph()
        apply_paragraph_format(p, space_before=12, space_after=4)
        # Banda lateral
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        left = OxmlElement('w:left')
        left.set(qn('w:val'), 'single')
        left.set(qn('w:sz'), '24')
        left.set(qn('w:color'), '00417A')
        pBdr.append(left)
        pPr.append(pBdr)
        p.paragraph_format.left_indent = Cm(0.5)
        r_num = p.add_run(f'{num}  ')
        r_num.font.name = 'Calibri'
        r_num.font.size = Pt(14)
        r_num.font.bold = True
        r_num.font.color.rgb = SAP_GOLD
        r_txt = p.add_run(text)
        r_txt.font.name = 'Calibri'
        r_txt.font.size = Pt(14)
        r_txt.font.bold = True
        r_txt.font.color.rgb = SAP_BLUE

    def heading2(doc, num, text):
        p = doc.add_paragraph()
        apply_paragraph_format(p, space_before=8, space_after=3)
        p.paragraph_format.left_indent = Cm(0.5)
        r_num = p.add_run(f'{num}  ')
        r_num.font.name = 'Calibri'
        r_num.font.size = Pt(11)
        r_num.font.bold = True
        r_num.font.color.rgb = SAP_LIGHT_BLUE
        r_txt = p.add_run(text)
        r_txt.font.name = 'Calibri'
        r_txt.font.size = Pt(11)
        r_txt.font.bold = True
        r_txt.font.color.rgb = SAP_GREY

    def body_text(doc, text, indent=0):
        p = doc.add_paragraph()
        apply_paragraph_format(p, space_before=3, space_after=3)
        if indent:
            p.paragraph_format.left_indent = Cm(indent)
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(10)
        r.font.color.rgb = SAP_GREY
        return p

    def bullet_item(doc, text, level=0, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.left_indent  = Cm(0.8 + level * 0.5)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after  = Pt(2)
        if bold_prefix:
            rb = p.add_run(bold_prefix + ': ')
            rb.font.bold = True
            rb.font.color.rgb = SAP_BLUE
            rb.font.size = Pt(10)
            rb.font.name = 'Calibri'
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(10)
        r.font.color.rgb = SAP_GREY
        return p

    def info_box(doc, title, content_lines, color_hex='#E8F4FD',
                 border_hex='#0070BF'):
        t = doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.cell(0, 0)
        set_cell_bg(c, color_hex.lstrip('#'))
        set_cell_border(c, color=border_hex.lstrip('#'), sz='12')
        p0 = c.paragraphs[0]
        if title:
            r0 = p0.add_run(title + '\n')
            r0.font.bold = True
            r0.font.color.rgb = RGBColor(
                *[int(x, 16) for x in
                  [border_hex.lstrip('#')[i:i+2] for i in (0, 2, 4)]])
            r0.font.size = Pt(10)
            r0.font.name = 'Calibri'
        for line in content_lines:
            r1 = p0.add_run(line + '\n')
            r1.font.size  = Pt(9.5)
            r1.font.name  = 'Calibri'
            r1.font.color.rgb = SAP_GREY
        doc.add_paragraph()

    # ─── 1. Propósito ────────────────────────────────────────────────────
    heading1(doc, '1.', 'Propósito del documento')
    add_horizontal_rule(doc)
    body_text(doc,
        'El presente documento describe el diseño y la configuración de la solución '
        'SAP Analytics Cloud (SAC) implementada para Fanalca S.A., empresa colombiana '
        'líder en el sector automotriz, metalmecánico y de distribución de vehículos '
        'Honda. Este artefacto constituye el Blueprint de Diseño de Solución del '
        'proyecto de implementación, detallando los modelos analíticos, las dimensiones '
        'de análisis, las fuentes de datos y los componentes técnicos involucrados.')
    body_text(doc,
        'El documento cubre los tres modelos centrales del proyecto: Modelo de Ingresos, '
        'Modelo de Estados Financieros (EEFF) y Modelo de Costos y Gastos, los cuales '
        'soportan la analítica financiera y comercial de las unidades de negocio '
        'Metalmecánica, Honda Supermotos y Honda Autos de Fanalca S.A.')

    info_box(doc,
        '📌  Alcance del documento:',
        [
            '• Unidades de negocio: Metalmecánica, Honda Supermotos, Honda Autos',
            '• Plataforma: SAP Analytics Cloud (SAC) – Tenencia en la nube SAP BTP',
            '• Período de referencia: Ejercicios fiscales 2024–2026',
            '• Versión de SAC: 2024.Q4 en adelante',
        ])

    # ─── 2. Cómo usar el documento ────────────────────────────────────────
    heading1(doc, '2.', 'Cómo usar el documento')
    add_horizontal_rule(doc)
    body_text(doc,
        'Este documento está dirigido a los siguientes perfiles dentro del equipo '
        'de proyecto y la organización de Fanalca S.A.:')
    for role, desc in [
        ('Arquitectos SAP / SAC', 'Revisión del diseño técnico de modelos y dimensiones.'),
        ('Analistas Funcionales', 'Validación del mapeo de requisitos de negocio.'),
        ('Equipo de TI / BASIS', 'Referencia de configuración e integración con SAP ERP.'),
        ('Usuarios Clave (Key Users)', 'Validación de la lógica de negocio y pruebas UAT.'),
        ('Gestión del Proyecto', 'Seguimiento del alcance, hitos y entregables.'),
    ]:
        bullet_item(doc, desc, bold_prefix=role)

    body_text(doc,
        'Para navegar el documento, utilice la Tabla de Contenido referenciada al '
        'inicio. Cada sección está numerada de forma jerárquica. Las tablas de '
        'configuración en la Sección 5 contienen valores de configuración en SAC '
        'que deben ser implementados en el sistema de acuerdo con la secuencia de '
        'actividades descrita.')

    # ─── 3. Escenario / Proceso de negocio ───────────────────────────────
    heading1(doc, '3.', 'Escenario / Proceso de negocio')
    add_horizontal_rule(doc)
    body_text(doc,
        'Fanalca S.A. es un conglomerado industrial colombiano con más de 70 años de '
        'trayectoria, conformado por tres grandes unidades de negocio estratégicas. La '
        'compañía requiere una plataforma de analítica centralizada que integre los '
        'datos financieros y operativos de sus divisiones para soportar la toma de '
        'decisiones gerenciales y ejecutivas en tiempo real.')

    # Tabla de divisiones
    div_table = doc.add_table(rows=4, cols=3)
    div_table.style = 'Table Grid'
    div_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['Unidad de Negocio', 'Descripción', 'Proceso Clave SAC']
    for j, h in enumerate(headers):
        c = div_table.cell(0, j)
        set_cell_bg(c, '#00417A')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9.5)
        r.font.name = 'Calibri'

    div_data = [
        ('Fanalca Metalmecánica',
         'Manufactura de autopartes, componentes metálicos y ensambles para la '
         'industria automotriz. Planta de producción en Colombia.',
         'Control de Costos de Producción y análisis de Gastos Operativos (OPEX/CAPEX)'),
        ('Honda Supermotos',
         'Importación, distribución y comercialización de motocicletas Honda en '
         'el territorio nacional. Red de concesionarios a nivel Colombia.',
         'Análisis de Ingresos por línea de producto, cliente y región'),
        ('Honda Autos (Autos Honda)',
         'Distribución de vehículos livianos Honda. Gestión de inventario de '
         'vehículos y análisis de rentabilidad por modelo y punto de venta.',
         'Estados Financieros (EEFF) y análisis de márgenes por sociedad'),
    ]
    for i, (u, d, p_) in enumerate(div_data):
        row = div_table.rows[i + 1]
        bg = '#F5F5F5' if i % 2 == 0 else '#FFFFFF'
        for j2 in range(3):
            set_cell_bg(row.cells[j2], bg)
        texts_ = [u, d, p_]
        bolds_ = [True, False, False]
        for j2, (tx, bl) in enumerate(zip(texts_, bolds_)):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name = 'Calibri'
            r2.font.size = Pt(9)
            r2.font.bold = bl
            r2.font.color.rgb = SAP_BLUE if bl else SAP_GREY
    doc.add_paragraph()

    # 3.1 Objetivos empresariales
    heading2(doc, '3.1.', 'Objetivos empresariales y beneficios esperados')
    body_text(doc,
        'La implementación de SAP Analytics Cloud en Fanalca S.A. responde a los '
        'siguientes objetivos estratégicos corporativos:')

    objectives = [
        ('Visibilidad financiera consolidada',
         'Obtener una vista unificada de los resultados financieros de las tres '
         'unidades de negocio en tiempo real, eliminando la dependencia de '
         'reportes manuales en hojas de cálculo.'),
        ('Análisis de ingresos granular',
         'Desagregación de los ingresos por cliente, referencia de producto, '
         'canal de distribución, moneda y centro de beneficio (CEBES), '
         'habilitando decisiones comerciales más ágiles.'),
        ('Control de costos y gastos',
         'Seguimiento detallado de costos de producción y gastos operativos '
         'por centro de costo (CECOS), facilitando la gestión del OPEX y CAPEX.'),
        ('Cierre financiero ágil',
         'Reducción del tiempo de cierre mensual mediante la automatización '
         'de los estados financieros desde el modelo EEFF integrado con SAP FI.'),
        ('Planeación integrada (xP&A)',
         'Sentar las bases para una planificación financiera extendida que '
         'integre los planes de ventas, costos y gastos de todas las unidades.'),
    ]
    for obj, desc in objectives:
        bullet_item(doc, desc, bold_prefix=obj)

    doc.add_paragraph()
    # Tabla de beneficios
    ben_table = doc.add_table(rows=5, cols=3)
    ben_table.style = 'Table Grid'
    ben_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(['Área', 'Beneficio Esperado', 'KPI de Medición']):
        c = ben_table.cell(0, j)
        set_cell_bg(c, '#107454')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9.5)
        r.font.name = 'Calibri'
    ben_data = [
        ('Finanzas',       'Reducción tiempo cierre mensual en 60%',       '# Días de cierre'),
        ('Comercial',      'Incremento análisis de rentabilidad por cliente', '# Reportes autoservicio/mes'),
        ('Operaciones',    'Control desviación presupuestal < 5%',         '% Variación Real vs. Plan'),
        ('Alta Dirección', 'Dashboard ejecutivo en tiempo real 24/7',      'NPS Usuarios / Adopción %'),
    ]
    for i, (a, b, k) in enumerate(ben_data):
        row = ben_table.rows[i + 1]
        bg = '#E8F5F0' if i % 2 == 0 else '#FFFFFF'
        for j2 in range(3):
            set_cell_bg(row.cells[j2], bg)
        for j2, tx in enumerate([a, b, k]):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name = 'Calibri'
            r2.font.size = Pt(9)
            r2.font.color.rgb = SAP_GREY
    doc.add_paragraph()

    # 3.2 Requisitos empresariales
    heading2(doc, '3.2.',
             'Descripción a alto nivel de Requisitos empresariales')
    body_text(doc,
        'Los siguientes requisitos de alto nivel fueron identificados durante el '
        'proceso de levantamiento de información con los usuarios clave de Fanalca:')

    req_data = [
        ('REQ-001', 'Modelo de Ingresos',
         'Reportar ingresos por sociedad, cliente, referencia, CEBES, moneda y '
         'ratio (precio/volumen) con comparativos Real vs. Plan vs. Forecast.'),
        ('REQ-002', 'Modelo EEFF',
         'Generar Balance General y Estado de Resultados consolidado por cuenta '
         'contable (CUENTA), sociedad y centro de beneficio para las tres unidades.'),
        ('REQ-003', 'Modelo de Costos y Gastos',
         'Analizar costos y gastos por cuenta (CUENTAS), centro de costo (CECOS), '
         'sociedad y CEBES con granularidad mensual y acumulado anual.'),
        ('REQ-004', 'Archivos de Validación',
         'Proceso de validación y conciliación de los datos cargados en SAC contra '
         'los saldos del sistema SAP ERP para garantizar integridad de la información.'),
        ('REQ-005', 'Multi-moneda',
         'Soporte para análisis en moneda local (COP) y moneda funcional/grupo '
         'a través de la dimensión MONEDA en todos los modelos.'),
        ('REQ-006', 'Versionamiento',
         'Manejo de múltiples versiones (Real, Plan, Forecast, Budget) a través '
         'de la dimensión VERSION estándar de SAC.'),
    ]
    req_table = doc.add_table(rows=len(req_data) + 1, cols=3)
    req_table.style = 'Table Grid'
    req_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(['ID', 'Requisito', 'Descripción']):
        c = req_table.cell(0, j)
        set_cell_bg(c, '#00417A')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9.5)
        r.font.name = 'Calibri'
    for i, (rid, rnom, rdesc) in enumerate(req_data):
        row = req_table.rows[i + 1]
        bg = '#E8F4FD' if i % 2 == 0 else '#FFFFFF'
        for j2 in range(3):
            set_cell_bg(row.cells[j2], bg)
        for j2, (tx, bl) in enumerate(
                zip([rid, rnom, rdesc], [True, True, False])):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name  = 'Calibri'
            r2.font.size  = Pt(9)
            r2.font.bold  = bl
            r2.font.color.rgb = SAP_BLUE if bl else SAP_GREY
    doc.add_paragraph()

    # ─── 4. Estructura organizativa relevante ─────────────────────────────
    doc.add_page_break()
    heading1(doc, '4.', 'Estructura organizativa relevante')
    add_horizontal_rule(doc)
    body_text(doc,
        'La estructura organizativa de Fanalca S.A. relevante para el modelo '
        'de SAP Analytics Cloud refleja la jerarquía de entidades contables y '
        'analíticas definidas en SAP ERP, las cuales se mapean directamente a '
        'las dimensiones de los modelos SAC:')

    doc.add_paragraph()
    # Tabla de estructura organizativa
    org_data = [
        ('Sociedad (SOCIEDAD)',
         'Entidad jurídica / legal de Fanalca. Corresponde al Mandante y '
         'Company Code en SAP FI. Dimensión compartida en todos los modelos.',
         'Metalmecánica S.A. / Honda Motos / Honda Autos'),
        ('Centro de Beneficio (CEBES)',
         'Unidad de negocio o línea de producto para el análisis de '
         'rentabilidad. Corresponde al Profit Center en SAP CO-PCA.',
         'Líneas de producto, familias de referencia'),
        ('Centro de Costo (CECOS)',
         'Unidad organizativa donde se originan los costos. Correspond al '
         'Cost Center en SAP CO-CCA. Exclusivo del modelo de Costos y Gastos.',
         'Producción, Ventas, Administración, Logística'),
        ('Cuenta Contable (CUENTA / CUENTAS)',
         'Plan de cuentas de Fanalca. CUENTA para EEFF (cuentas de balance '
         'y resultados). CUENTAS para el modelo de gastos (cuentas de costos).',
         'Plan de cuentas KOFAX / estándar SAP'),
        ('Referencia (REFERENCIA)',
         'Código de producto o referencia comercial para el análisis de '
         'ingresos. Exclusivo del modelo de Ingresos.',
         'SKUs Honda, referencias metalmecánica'),
        ('Cliente (CLIENTES)',
         'Dimensión de clientes para el análisis de ingresos por cuenta '
         'cliente. Exclusivo del modelo de Ingresos.',
         'Concesionarios, distribuidores, clientes directos'),
        ('Moneda (MONEDA)',
         'Dimensión de moneda para análisis multimoneda. COP como moneda '
         'local y USD/EUR como monedas de grupo/funcional.',
         'COP, USD, EUR'),
        ('Auditoría (AUDITORIA)',
         'Dimensión de control y trazabilidad de carga de datos. Permite '
         'identificar el origen y la fecha de carga de cada registro.',
         'Timestamp de carga, fuente de origen'),
        ('Versión (VERSION)',
         'Dimensión estándar de SAC para versionamiento de datos: Real, '
         'Plan, Forecast, Budget. Dimensión compartida en todos los modelos.',
         'Real, Plan Anual, Forecast Mensual, Budget'),
        ('Fecha (DATE)',
         'Dimensión temporal estándar SAC. Soporta granularidad año/mes. '
         'Dimensión compartida en todos los modelos.',
         'Año, Trimestre, Mes, Semana'),
        ('Ratio (RATIO)',
         'Dimensión para el análisis de ratios precio/volumen en el modelo '
         'de ingresos. Permite descomponer variaciones de ingresos.',
         'Precio Unitario, Volumen, Mix'),
    ]
    org_table = doc.add_table(rows=len(org_data) + 1, cols=3)
    org_table.style = 'Table Grid'
    org_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(['Dimensión SAC', 'Descripción', 'Valores / Referencia SAP']):
        c = org_table.cell(0, j)
        set_cell_bg(c, '#00417A')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9.5)
        r.font.name = 'Calibri'
    for i, (dim, desc, vals) in enumerate(org_data):
        row = org_table.rows[i + 1]
        is_common = any(x in dim for x in
                        ['VERSION', 'DATE', 'AUDITORIA', 'CEBES', 'MONEDA',
                         'SOCIEDAD', 'Versión', 'Fecha', 'Moneda', 'Auditoría',
                         'Centro de Ben'])
        bg = '#FFF8E6' if is_common else ('#F5F5F5' if i % 2 == 0 else '#FFFFFF')
        for j2 in range(3):
            set_cell_bg(row.cells[j2], bg)
        for j2, tx in enumerate([dim, desc, vals]):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name = 'Calibri'
            r2.font.size = Pt(9)
            r2.font.bold = (j2 == 0)
            r2.font.color.rgb = SAP_BLUE if j2 == 0 else SAP_GREY
    doc.add_paragraph()

    # ─── 5. Diseño y configuración de soluciones ─────────────────────────
    doc.add_page_break()
    heading1(doc, '5.', 'Diseño y configuración de soluciones')
    add_horizontal_rule(doc)

    # 5.1 Alcance del proceso
    heading2(doc, '5.1.', 'Alcance del proceso de solución')
    body_text(doc,
        'El siguiente flujograma representa la arquitectura completa de los modelos '
        'SAP Analytics Cloud implementados para Fanalca S.A., mostrando las fuentes '
        'de datos, los tres modelos analíticos, sus dimensiones y la capa de '
        'presentación (Stories y Dashboards):')

    # Insertar flujograma
    flowchart_buf = crear_flujograma()
    doc.add_picture(flowchart_buf, width=Inches(6.2))
    last_p = doc.paragraphs[-1]
    last_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rc = cap.add_run('Figura 1. Arquitectura de Modelos SAP Analytics Cloud – Fanalca S.A.')
    rc.font.italic = True
    rc.font.size   = Pt(9)
    rc.font.color.rgb = SAP_GREY

    doc.add_paragraph()
    body_text(doc,
        'Los tres modelos SAC definidos para Fanalca son modelos de tipo Planning '
        '(habilitado para escritura), lo que permite su uso tanto para carga de '
        'datos reales desde SAP ERP como para la captura de datos de planeación '
        'directamente en SAC. A continuación se describe cada modelo:')

    # Detalle de modelos
    models_detail = [
        {
            'nombre': 'Modelo de Ingresos Fanalca',
            'tipo': 'Planning Model (Read/Write)',
            'medida': 'Importe — Decimal',
            'dims': [
                ('Version',    'Estándar SAC', 'Versión de datos (Real/Plan/Forecast)'),
                ('RATIO',      'Genérica',     'Ratio precio/volumen para análisis de variaciones'),
                ('Date',       'Estándar SAC', 'Dimensión temporal (Año/Mes)'),
                ('AUDITORIA',  'Genérica',     'Control y trazabilidad de carga de datos'),
                ('CEBES',      'Genérica',     'Centro de Beneficio / Profit Center SAP CO'),
                ('CLIENTES',   'Genérica',     'Maestro de clientes SAP SD'),
                ('MONEDA',     'Genérica',     'Dimensión de moneda (COP/USD/EUR)'),
                ('REFERENCIA', 'Genérica',     'Referencia / SKU de producto'),
                ('SOCIEDAD',   'Genérica',     'Sociedad / Company Code SAP FI'),
            ],
            'color': '#00417A',
            'bg': '#E8F4FD',
        },
        {
            'nombre': 'Modelo EEFF Fanalca',
            'tipo': 'Planning Model (Read/Write)',
            'medida': 'Importe — Decimal',
            'dims': [
                ('Version',   'Estándar SAC', 'Versión de datos (Real/Plan/Forecast)'),
                ('CUENTA',    'Genérica',     'Cuenta contable del Plan de Cuentas SAP FI'),
                ('Date',      'Estándar SAC', 'Dimensión temporal (Año/Mes)'),
                ('AUDITORIA', 'Genérica',     'Control y trazabilidad de carga de datos'),
                ('CEBES',     'Genérica',     'Centro de Beneficio / Profit Center SAP CO'),
                ('MONEDA',    'Genérica',     'Dimensión de moneda (COP/USD/EUR)'),
                ('SOCIEDAD',  'Genérica',     'Sociedad / Company Code SAP FI'),
            ],
            'color': '#107454',
            'bg': '#E8F5F0',
        },
        {
            'nombre': 'Modelo Costos y Gastos Fanalca',
            'tipo': 'Planning Model (Read/Write)',
            'medida': 'Importe — Decimal',
            'dims': [
                ('Version',   'Estándar SAC', 'Versión de datos (Real/Plan/Forecast)'),
                ('CUENTAS',   'Genérica',     'Cuenta contable de costos/gastos SAP FI/CO'),
                ('Date',      'Estándar SAC', 'Dimensión temporal (Año/Mes)'),
                ('AUDITORIA', 'Genérica',     'Control y trazabilidad de carga de datos'),
                ('CEBES',     'Genérica',     'Centro de Beneficio / Profit Center SAP CO'),
                ('CECOS',     'Genérica',     'Centro de Costo / Cost Center SAP CO'),
                ('MONEDA',    'Genérica',     'Dimensión de moneda (COP/USD/EUR)'),
                ('SOCIEDAD',  'Genérica',     'Sociedad / Company Code SAP FI'),
            ],
            'color': '#5C3A8C',
            'bg': '#F0EAF8',
        },
    ]

    for m in models_detail:
        # Encabezado del modelo
        model_head = doc.add_paragraph()
        apply_paragraph_format(model_head, space_before=8, space_after=2)
        rh = model_head.add_run(f"  {m['nombre']}  ")
        rh.font.name = 'Calibri'
        rh.font.size = Pt(11)
        rh.font.bold = True
        rh.font.color.rgb = SAP_WHITE

        # Colorear el párrafo del encabezado
        pPr = model_head._p.get_or_add_pPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        col_hex = m['color'].lstrip('#')
        shd.set(qn('w:fill'), col_hex)
        pPr.append(shd)

        # Sub-info
        si = doc.add_paragraph()
        apply_paragraph_format(si, space_before=1, space_after=2)
        si.paragraph_format.left_indent = Cm(0.5)
        rs = si.add_run(f"Tipo: {m['tipo']}   |   Medida principal: {m['medida']}")
        rs.font.name = 'Calibri'
        rs.font.size = Pt(9)
        rs.font.italic = True
        rs.font.color.rgb = RGBColor(
            *[int(m['color'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)])

        # Tabla de dimensiones
        dim_table = doc.add_table(rows=len(m['dims']) + 1, cols=3)
        dim_table.style = 'Table Grid'
        dim_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, h in enumerate(['Dimensión', 'Tipo', 'Descripción / Equivalente SAP']):
            c = dim_table.cell(0, j)
            col_rgb = RGBColor(
                *[int(m['color'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)])
            set_cell_bg(c, m['color'].lstrip('#'))
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r2 = p.add_run(h)
            r2.font.bold = True
            r2.font.color.rgb = SAP_WHITE
            r2.font.size = Pt(9)
            r2.font.name = 'Calibri'
        for i, (dname, dtype, ddesc) in enumerate(m['dims']):
            row = dim_table.rows[i + 1]
            is_cmn = dname in ['Version', 'Date', 'AUDITORIA', 'CEBES',
                                'MONEDA', 'SOCIEDAD']
            bg = '#FFF8E6' if is_cmn else (m['bg'] if i % 2 == 0 else '#FFFFFF')
            for j2 in range(3):
                set_cell_bg(row.cells[j2], bg)
            for j2, (tx, bl) in enumerate(
                    zip([dname, dtype, ddesc], [True, False, False])):
                p2 = row.cells[j2].paragraphs[0]
                r2 = p2.add_run(tx)
                r2.font.name = 'Calibri'
                r2.font.size = Pt(9)
                r2.font.bold = bl
                col_rgb = RGBColor(
                    *[int(m['color'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)])
                r2.font.color.rgb = col_rgb if bl else SAP_GREY
        doc.add_paragraph()

    # 5.2 Valor de Actividad de Configuración
    doc.add_page_break()
    heading2(doc, '5.2.', 'Valor de Actividad de Configuración')
    body_text(doc,
        'La siguiente tabla resume las actividades de configuración en SAP Analytics '
        'Cloud, su estado y la estimación de esfuerzo para cada componente:')

    conf_data = [
        ('Creación de Modelos (3)',       'Modelado SAC', 'Completo', 'Alta',
         '3 Modelos Planning creados en ambiente de Desarrollo'),
        ('Configuración de Dimensiones',  'Modelado SAC', 'Completo', 'Alta',
         'Version, Date (std) + 9 dims genéricas configuradas'),
        ('Carga de Datos Maestros',       'Datos Maestros', 'En Progreso', 'Alta',
         'Archivos CSV/OData desde SAP ERP para cada dimensión'),
        ('Integración SAP ERP → SAC',     'Integración', 'En Progreso', 'Alta',
         'Conexión Live Data / Import Data desde SAP BW o HANA'),
        ('Archivos de Validación',        'Calidad de Datos', 'En Progreso', 'Media',
         'Reconciliación SAC vs. SAP FI por período y sociedad'),
        ('Creación de Stories/Dashboards','Reporting', 'Pendiente', 'Media',
         'Visualizaciones financieras y comerciales por unidad'),
        ('Perfilamiento de Acceso',       'Seguridad', 'Pendiente', 'Alta',
         'Roles y restricciones de datos por sociedad/CEBES'),
        ('Pruebas de Usuario (UAT)',       'Calidad', 'Pendiente', 'Alta',
         'Validación con key users de las 3 unidades de negocio'),
        ('Formación y Capacitación',      'Change Mgmt', 'Pendiente', 'Media',
         'Talleres SAC para usuarios finales y administradores'),
        ('Pase a Producción (Go-Live)',    'Despliegue', 'Pendiente', 'Alta',
         'Migración de configuración DEV → QA → PRD'),
    ]
    conf_table = doc.add_table(rows=len(conf_data) + 1, cols=5)
    conf_table.style = 'Table Grid'
    conf_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(['Actividad', 'Área', 'Estado', 'Prioridad', 'Notas']):
        c = conf_table.cell(0, j)
        set_cell_bg(c, '#00417A')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9)
        r.font.name = 'Calibri'
    estado_colors = {
        'Completo': '#107454', 'En Progreso': '#0070BF', 'Pendiente': '#888888'
    }
    for i, (act, area, est, prio, nota) in enumerate(conf_data):
        row = conf_table.rows[i + 1]
        bg = '#F5F5F5' if i % 2 == 0 else '#FFFFFF'
        for j2 in range(5):
            set_cell_bg(row.cells[j2], bg)
        for j2, tx in enumerate([act, area, est, prio, nota]):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name = 'Calibri'
            r2.font.size = Pt(9)
            if j2 == 2:
                ec = estado_colors.get(est, '#888888').lstrip('#')
                r2.font.color.rgb = RGBColor(
                    *[int(ec[k:k+2], 16) for k in (0, 2, 4)])
                r2.font.bold = True
            elif j2 == 3 and prio == 'Alta':
                r2.font.color.rgb = RGBColor(0xCC, 0x33, 0x00)
                r2.font.bold = True
            else:
                r2.font.color.rgb = SAP_GREY
    doc.add_paragraph()

    # 5.3 Roles
    heading2(doc, '5.3.', 'Roles')
    body_text(doc,
        'Los siguientes roles son necesarios para la operación, mantenimiento '
        'y gobierno de los modelos SAP Analytics Cloud en Fanalca S.A.:')

    roles_data = [
        ('SAC Administrator',
         'Administrador de la plataforma SAC. Gestión de tenants, usuarios, '
         'roles de acceso, conexiones a datos y ciclos de release.',
         'TI / BASIS', 'Fanalca TI'),
        ('SAC Modeler',
         'Responsable de la creación y mantenimiento de los modelos analíticos, '
         'dimensiones y métricas calculadas.',
         'TI / Analytics CoE', 'Fanalca TI / Consultor SAP'),
        ('SAC Story Developer',
         'Desarrollador de Stories, dashboards y reportes analíticos. '
         'Configuración de visualizaciones y KPIs.',
         'Analytics CoE', 'Consultor SAP / Fanalca Analítica'),
        ('Finance Key User',
         'Usuario clave del área Financiera. Valida modelos EEFF y de Costos, '
         'aprueba datos de cierre y supervisa la integridad de la información.',
         'Finanzas', 'Fanalca Finanzas'),
        ('Commercial Key User',
         'Usuario clave del área Comercial. Valida el modelo de Ingresos, '
         'gestiona dimensiones de clientes y referencias de producto.',
         'Comercial / Ventas', 'Fanalca Comercial'),
        ('Data Owner',
         'Responsable de la calidad y gobierno de los datos maestros '
         '(clientes, cuentas, centros de costo/beneficio, etc.).',
         'Varias áreas', 'Dirección de cada área'),
        ('End User / Viewer',
         'Consumidor de reportes y dashboards en SAC. Sin acceso de escritura '
         'o modificación de modelos.',
         'Toda la organización', 'Usuarios finales'),
    ]
    roles_table = doc.add_table(rows=len(roles_data) + 1, cols=4)
    roles_table.style = 'Table Grid'
    roles_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(['Rol SAC', 'Responsabilidades', 'Área', 'Asignación Fanalca']):
        c = roles_table.cell(0, j)
        set_cell_bg(c, '#00417A')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9)
        r.font.name = 'Calibri'
    for i, (rol, resp, area, asig) in enumerate(roles_data):
        row = roles_table.rows[i + 1]
        bg = '#F5F5F5' if i % 2 == 0 else '#FFFFFF'
        for j2 in range(4):
            set_cell_bg(row.cells[j2], bg)
        for j2, (tx, bl) in enumerate(
                zip([rol, resp, area, asig], [True, False, False, False])):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name = 'Calibri'
            r2.font.size = Pt(9)
            r2.font.bold = bl
            r2.font.color.rgb = SAP_BLUE if bl else SAP_GREY
    doc.add_paragraph()

    # 5.4 Inventario de datos maestros
    heading2(doc, '5.4.',
             'Inventario de datos maestros susceptibles de migración')
    body_text(doc,
        'Los siguientes datos maestros deben ser migrados / cargados en SAP Analytics '
        'Cloud como dimensiones de los modelos. Para cada maestro se indica la '
        'fuente de origen en SAP ERP y el método de carga recomendado:')

    maestros_data = [
        ('Clientes (CLIENTES)',           'SD – KNA1',          'Odata / Import CSV',
         'Fanalca Supermotos / Autos Honda', 'Alto'),
        ('Cuentas Contables (CUENTA)',     'FI – SKA1/SKB1',     'Import CSV / BW',
         'Todas las sociedades',            'Alto'),
        ('Cuentas de Costos (CUENTAS)',    'CO – CSKA/CSKB',     'Import CSV / BW',
         'Fanalca Metalmecánica',           'Alto'),
        ('Centros de Costo (CECOS)',       'CO – CSKS',          'Import CSV / OData',
         'Fanalca Metalmecánica',           'Alto'),
        ('Centros de Beneficio (CEBES)',   'CO-PCA – CEPC',      'Import CSV / OData',
         'Todas las unidades',              'Alto'),
        ('Sociedades (SOCIEDAD)',          'FI – T001',          'Import CSV manual',
         'Todas las unidades',              'Medio'),
        ('Referencias de Producto (REF)', 'MM – MARA/MVKE',     'Import CSV / BW',
         'Fanalca Supermotos / Autos',      'Alto'),
        ('Monedas (MONEDA)',               'FI – TCURC',         'Import CSV manual',
         'Todas las unidades',              'Bajo'),
        ('Dimensión Auditoría (AUD)',      'Definición manual',  'Carga manual SAC',
         'Equipo de TI',                    'Bajo'),
        ('Versiones (VERSION)',            'Estándar SAC',       'Configuración SAC',
         'Equipo de implementación',        'Bajo'),
    ]
    maest_table = doc.add_table(rows=len(maestros_data) + 1, cols=5)
    maest_table.style = 'Table Grid'
    maest_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(['Dato Maestro', 'Fuente SAP', 'Método de Carga',
                             'Alcance', 'Complejidad']):
        c = maest_table.cell(0, j)
        set_cell_bg(c, '#00417A')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9)
        r.font.name = 'Calibri'
    comp_colors = {'Alto': 'CC3300', 'Medio': 'F0AB00', 'Bajo': '107454'}
    for i, row_d in enumerate(maestros_data):
        row = maest_table.rows[i + 1]
        bg = '#F5F5F5' if i % 2 == 0 else '#FFFFFF'
        for j2 in range(5):
            set_cell_bg(row.cells[j2], bg)
        for j2, tx in enumerate(row_d):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name = 'Calibri'
            r2.font.size = Pt(9)
            r2.font.bold = (j2 == 0)
            if j2 == 4:
                cc = comp_colors.get(tx, '888888')
                r2.font.color.rgb = RGBColor(
                    *[int(cc[k:k+2], 16) for k in (0, 2, 4)])
                r2.font.bold = True
            else:
                r2.font.color.rgb = SAP_BLUE if j2 == 0 else SAP_GREY
    doc.add_paragraph()

    # 5.5 Componente de Solución Técnica
    doc.add_page_break()
    heading2(doc, '5.5.', 'Componente de Solución Técnica Relacionada')
    body_text(doc,
        'La arquitectura técnica de la solución SAP Analytics Cloud para Fanalca S.A. '
        'comprende los siguientes componentes de plataforma y conectividad:')

    comp_data = [
        ('SAP Analytics Cloud (SAC)',
         'Plataforma principal de analítica y planificación en la nube (SaaS). '
         'Alojada en SAP BTP (Business Technology Platform) en la región '
         'us10 (América).',
         'SAP BTP – SaaS', 'Producción / QA / Desarrollo'),
        ('SAP S/4HANA / ERP On-Premise',
         'Sistema fuente de datos transaccionales. Módulos FI (Contabilidad), '
         'CO (Controlling), SD (Ventas) y MM (Materiales) como fuentes primarias '
         'de datos para los modelos SAC.',
         'On-Premise Colombia', 'Release SAP compatible'),
        ('SAP BW/4HANA (Data Warehouse)',
         'Capa de Data Warehouse para consolidación, transformación y carga '
         'de datos hacia SAC. Provee las InfoProviders y DataFlows para '
         'la alimentación de los modelos.',
         'On-Premise / Cloud', 'BW/4HANA 2.0+'),
        ('SAP Data Services / SLT',
         'Herramienta de replicación y transformación de datos desde '
         'SAP ERP hacia SAP BW/4HANA o directamente a SAC vía OData.',
         'On-Premise', 'SAP Data Services 4.3+'),
        ('SAP Analytics Cloud – Import Connection',
         'Conector de importación de datos para la carga batch de datos '
         'históricos y maestros. Soporta archivos CSV, conexiones OData '
         'y conectores SAP BW.',
         'SAC (cloud)', 'Estándar SAC'),
        ('SAP Analytics Cloud – Live Connection',
         'Conexión en tiempo real hacia SAP BW/4HANA o SAP HANA para '
         'análisis ad-hoc sin replicación de datos.',
         'SAC ↔ BW/HANA', 'Requiere SAP Connector'),
        ('SAP Identity Authentication Service (IAS)',
         'Servicio de autenticación y SSO para el acceso de usuarios '
         'de Fanalca a SAP Analytics Cloud.',
         'SAP BTP', 'SAP IAS Cloud'),
        ('SAP Analytics Cloud – Transport',
         'Gestión del ciclo de vida de contenido SAC. Transporte de '
         'modelos, stories y configuraciones entre ambientes '
         'DEV → QA → PRD.',
         'SAC', 'SAC Lifecycle Management'),
    ]
    comp_table = doc.add_table(rows=len(comp_data) + 1, cols=4)
    comp_table.style = 'Table Grid'
    comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(['Componente', 'Descripción', 'Entorno', 'Versión / Nota']):
        c = comp_table.cell(0, j)
        set_cell_bg(c, '#00417A')
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = SAP_WHITE
        r.font.size = Pt(9)
        r.font.name = 'Calibri'
    for i, (comp, desc, env, ver) in enumerate(comp_data):
        row = comp_table.rows[i + 1]
        bg = '#F5F5F5' if i % 2 == 0 else '#FFFFFF'
        for j2 in range(4):
            set_cell_bg(row.cells[j2], bg)
        for j2, (tx, bl) in enumerate(
                zip([comp, desc, env, ver], [True, False, False, False])):
            p2 = row.cells[j2].paragraphs[0]
            r2 = p2.add_run(tx)
            r2.font.name = 'Calibri'
            r2.font.size = Pt(9)
            r2.font.bold = bl
            r2.font.color.rgb = SAP_BLUE if bl else SAP_GREY
    doc.add_paragraph()

    # ── Notas sobre videos (limitación de transcripción) ─────────────────
    info_box(doc,
        '⚠  Nota sobre videos del proyecto:',
        [
            'La carpeta del proyecto contiene los siguientes videos de sesiones de trabajo:',
            '  • Fanalca Metalmecanica.mp4 – Configuración de modelos unidad Metalmecánica',
            '  • Fanalca Supermotos.mp4 – Configuración de modelos unidad Honda Supermotos',
            '  • Fanlaca Autos Honda.mp4 – Configuración de modelos unidad Autos Honda',
            '  • Fanalca archivos de validacion.mp4 – Proceso de validación y conciliación',
            '',
            'El contenido de este documento se elaboró a partir de las capturas de pantalla '
            'de los modelos SAC (imágenes PNG) y el conocimiento del equipo de implementación. '
            'Los videos contienen grabaciones de las sesiones de configuración en vivo.',
        ],
        color_hex='#FFF8E6', border_hex='#F0AB00')

    # ── Pie de página ─────────────────────────────────────────────────────
    section = doc.sections[0]
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rf = fp.add_run(
        'Fanalca S.A.  |  SAP Analytics Cloud – Documento de Diseño de Solución  '
        '|  Versión 1.0  |  Confidencial')
    rf.font.name  = 'Calibri'
    rf.font.size  = Pt(8)
    rf.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    out_path = '/home/user/Johnmeg/SAC_Fanalca_Diseño_Solucion.docx'
    doc.save(out_path)
    print(f'Documento guardado: {out_path}')
    return out_path


if __name__ == '__main__':
    path = build_document()
    size = os.path.getsize(path) / 1024
    print(f'Tamaño: {size:.1f} KB')
