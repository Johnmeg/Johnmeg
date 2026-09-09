#!/usr/bin/env python3
"""Helpers de construcción para el Documento de Diseño (formato Diseño Funcional)."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY = "1F3864"
NAVY2 = "2E5496"
BLUE_D = "002060"
RED = "C00000"
GREEN = "375623"
GREY = "595959"
LIGHT = "F2F6FC"
LIGHTGREY = "F2F2F2"

CONTENT_W = 6.6  # ancho útil aprox. (Letter, márgenes 0.95)


# ---------- utilidades XML ----------
def _shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tcPr.append(shd)


def _set_cell_margins(cell, top=40, bottom=40, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    m = OxmlElement('w:tcMar')
    for tag, val in (('top', top), ('bottom', bottom), ('start', left), ('end', right)):
        e = OxmlElement(f'w:{tag}')
        e.set(qn('w:w'), str(val))
        e.set(qn('w:type'), 'dxa')
        m.append(e)
    tcPr.append(m)


def _no_autofit(table):
    table.autofit = False
    table.allow_autofit = False
    tblPr = table._tbl.tblPr
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    tblPr.append(layout)


def _set_widths(table, widths):
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Inches(w)


def _cell_text(cell, text, *, bold=False, color=None, size=8.6, align='left',
               italic=False, font='Arial'):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                   'right': WD_ALIGN_PARAGRAPH.RIGHT}[align]
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    # soporta saltos de línea con \n
    parts = str(text).split('\n')
    for j, part in enumerate(parts):
        run = p.add_run(part)
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        if color:
            run.font.color.rgb = RGBColor.from_string(color)
        if j < len(parts) - 1:
            run.add_break()
    return p


# ---------- API de alto nivel ----------
class Builder:
    def __init__(self, template_path):
        self.doc = Document(template_path)
        self._clear_body()

    def _clear_body(self):
        body = self.doc.element.body
        for child in list(body):
            if child.tag in (qn('w:p'), qn('w:tbl')):
                body.remove(child)
        # queda solo el sectPr de cuerpo

    # --- secciones / página ---
    def page_break(self):
        from docx.enum.text import WD_BREAK
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def spacer(self, pts=6):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(pts)
        p.paragraph_format.space_before = Pt(0)
        return p

    # --- títulos ---
    def h1(self, text):
        p = self.doc.add_paragraph(text, style='Heading 1')
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        return p

    def h2(self, text):
        p = self.doc.add_paragraph(text, style='Heading 2')
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        return p

    def h3(self, text):
        p = self.doc.add_paragraph(text, style='Heading 3')
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        return p

    def para(self, text, *, italic=False, size=10, color=None, bold=False,
             align='justify', space_after=6):
        p = self.doc.add_paragraph()
        amap = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                'justify': WD_ALIGN_PARAGRAPH.JUSTIFY, 'right': WD_ALIGN_PARAGRAPH.RIGHT}
        p.alignment = amap[align]
        p.paragraph_format.space_after = Pt(space_after)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(size)
        run.font.italic = italic
        run.font.bold = bold
        if color:
            run.font.color.rgb = RGBColor.from_string(color)
        return p

    def bullets(self, items, *, size=10, color=None):
        for it in items:
            p = self.doc.add_paragraph(style='List Paragraph')
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0.3)
            pPr = p._p.get_or_add_pPr()
            numPr = OxmlElement('w:numPr')
            ilvl = OxmlElement('w:ilvl'); ilvl.set(qn('w:val'), '0'); numPr.append(ilvl)
            nId = OxmlElement('w:numId'); nId.set(qn('w:val'), '0'); numPr.append(nId)
            # usa viñeta simple mediante símbolo
            run = p.add_run('▪  ' + it)
            run.font.name = 'Arial'; run.font.size = Pt(size)
            if color:
                run.font.color.rgb = RGBColor.from_string(color)

    # --- tabla de datos con cabecera de marca ---
    def table(self, headers, rows, widths=None, *, header_fill=NAVY,
              size=8.6, header_size=8.8, zebra=True, first_col_bold=False,
              align_first='left'):
        ncol = len(headers)
        t = self.doc.add_table(rows=1, cols=ncol)
        try:
            t.style = 'Fanalca'
        except Exception:
            t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        _no_autofit(t)
        if widths is None:
            widths = [CONTENT_W / ncol] * ncol
        # cabecera
        hdr = t.rows[0]
        self._mark_header(hdr)
        for i, h in enumerate(headers):
            _shade(hdr.cells[i], header_fill)
            _cell_text(hdr.cells[i], h, bold=True, color='FFFFFF',
                       size=header_size, align='center')
            _set_cell_margins(hdr.cells[i])
        # filas
        for r, row in enumerate(rows):
            cells = t.add_row().cells
            for i, val in enumerate(row):
                a = align_first if i == 0 else ('left' if i == 0 else 'left')
                b = first_col_bold and i == 0
                _cell_text(cells[i], val, size=size, align=a, bold=b,
                           color=NAVY if b else None)
                _set_cell_margins(cells[i])
                if zebra and r % 2 == 1:
                    _shade(cells[i], LIGHT)
        _set_widths(t, widths)
        self.spacer(4)
        return t

    def _mark_header(self, row):
        trPr = row._tr.get_or_add_trPr()
        h = OxmlElement('w:tblHeader'); h.set(qn('w:val'), 'true')
        trPr.append(h)
        # evita que la fila se parta
        cant = OxmlElement('w:cantSplit'); cant.set(qn('w:val'), 'true')
        trPr.append(cant)

    # --- callout / panel informativo (tabla 1 celda con cabecera) ---
    def callout(self, title, body_lines, *, accent=NAVY, fill="EAF1FB",
                icon="●"):
        t = self.doc.add_table(rows=2, cols=1)
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        _no_autofit(t); _set_widths(t, [CONTENT_W])
        # borde de color
        self._color_borders(t, accent)
        top = t.rows[0].cells[0]
        _shade(top, accent)
        _cell_text(top, f"{icon}  {title}", bold=True, color='FFFFFF', size=9.2)
        _set_cell_margins(top, top=50, bottom=50)
        bot = t.rows[1].cells[0]
        _shade(bot, fill)
        bot.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p0 = bot.paragraphs[0]
        p0.paragraph_format.space_after = Pt(2)
        if isinstance(body_lines, str):
            body_lines = [body_lines]
        for k, line in enumerate(body_lines):
            p = p0 if k == 0 else bot.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(0)
            run = p.add_run(("▸  " if len(body_lines) > 1 else "") + line)
            run.font.name = 'Arial'; run.font.size = Pt(8.8)
        _set_cell_margins(bot, top=60, bottom=60)
        self.spacer(6)
        return t

    def _color_borders(self, table, color):
        tblPr = table._tbl.tblPr
        borders = OxmlElement('w:tblBorders')
        for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            e = OxmlElement(f'w:{edge}')
            e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '8')
            e.set(qn('w:space'), '0'); e.set(qn('w:color'), color)
            borders.append(e)
        tblPr.append(borders)

    # --- figura con leyenda ---
    def figure(self, path, caption, width=CONTENT_W):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run()
        run.add_picture(path, width=Inches(width))
        # borde sutil a la imagen
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(10)
        r = cap.add_run(caption)
        r.font.name = 'Arial'; r.font.size = Pt(8.5); r.font.italic = True
        r.font.color.rgb = RGBColor.from_string(GREY)
        return p

    # --- portada ---
    def cover_logo(self, path, width):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(6)
        p.add_run().add_picture(path, width=Inches(width))
        return p

    def cover_title(self, lines):
        for txt, size, color, bold, sp in lines:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(sp)
            run = p.add_run(txt)
            run.font.name = 'Arial'; run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = RGBColor.from_string(color)

    def meta_table(self, pairs):
        t = self.doc.add_table(rows=len(pairs), cols=2)
        try:
            t.style = 'Fanalca'
        except Exception:
            t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        _no_autofit(t); _set_widths(t, [2.0, 4.2])
        for i, (k, v) in enumerate(pairs):
            c0, c1 = t.rows[i].cells
            _shade(c0, NAVY)
            _cell_text(c0, k, bold=True, color='FFFFFF', size=9.5)
            _set_cell_margins(c0)
            _cell_text(c1, v, size=9.5)
            _set_cell_margins(c1)
        return t

    # --- TOC automático ---
    def toc(self):
        p = self.doc.add_paragraph()
        run = p.add_run()
        fldBegin = OxmlElement('w:fldChar'); fldBegin.set(qn('w:fldCharType'), 'begin')
        instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve')
        instr.text = 'TOC \\o "1-3" \\h \\z \\u'
        fldSep = OxmlElement('w:fldChar'); fldSep.set(qn('w:fldCharType'), 'separate')
        t = OxmlElement('w:t'); t.text = "Actualice este índice en Word: clic derecho ▸ Actualizar campos (o F9)."
        fldEnd = OxmlElement('w:fldChar'); fldEnd.set(qn('w:fldCharType'), 'end')
        r = run._r
        r.append(fldBegin); r.append(instr); r.append(fldSep); r.append(t); r.append(fldEnd)
        return p

    # --- encabezado / pie ---
    def setup_headers(self, logo_path):
        sec = self.doc.sections[0]
        sec.different_first_page_header_footer = True
        sec.top_margin = Inches(0.95); sec.bottom_margin = Inches(0.9)
        sec.left_margin = Inches(0.95); sec.right_margin = Inches(0.95)
        sec.header_distance = Inches(0.5); sec.footer_distance = Inches(0.4)
        # header (páginas 2+)
        hdr = sec.header
        hp = hdr.paragraphs[0]
        hp.text = ""
        self._tabs(hp)
        r1 = hp.add_run("Documento de Diseño de Solución · SAP Analytics Cloud")
        r1.font.name = 'Arial'; r1.font.size = Pt(8); r1.font.color.rgb = RGBColor.from_string(GREY)
        r2 = hp.add_run("\tPrograma SAP BUILD — Grupo Fanalca")
        r2.font.name = 'Arial'; r2.font.size = Pt(8); r2.font.color.rgb = RGBColor.from_string(GREY)
        self._bottom_border(hp)
        # footer (páginas 2+)
        ftr = sec.footer
        fp = ftr.paragraphs[0]; fp.text = ""
        self._tabs(fp)
        self._top_border(fp)
        rL = fp.add_run("Confidencial — Grupo Fanalca / Accenture")
        rL.font.name = 'Arial'; rL.font.size = Pt(8); rL.font.color.rgb = RGBColor.from_string(GREY)
        fp.add_run("\t").font.size = Pt(8)
        self._page_field(fp)

    def _tabs(self, p):
        pPr = p._p.get_or_add_pPr()
        tabs = OxmlElement('w:tabs')
        for pos, val in ((4680, 'center'), (9360, 'right')):
            tab = OxmlElement('w:tab'); tab.set(qn('w:val'), val); tab.set(qn('w:pos'), str(pos))
            tabs.append(tab)
        pPr.append(tabs)

    def _page_field(self, p):
        def fld(instr):
            run = p.add_run(); r = run._r
            b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'), 'begin')
            it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = instr
            e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), 'end')
            r.append(b); r.append(it); r.append(e)
            run.font.name = 'Arial'; run.font.size = Pt(8); run.font.color.rgb = RGBColor.from_string(GREY)
        rr = p.add_run("Página "); rr.font.name = 'Arial'; rr.font.size = Pt(8); rr.font.color.rgb = RGBColor.from_string(GREY)
        fld('PAGE')
        rr = p.add_run(" de "); rr.font.name = 'Arial'; rr.font.size = Pt(8); rr.font.color.rgb = RGBColor.from_string(GREY)
        fld('NUMPAGES')

    def _bottom_border(self, p):
        pPr = p._p.get_or_add_pPr()
        pbdr = OxmlElement('w:pBdr')
        b = OxmlElement('w:bottom'); b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '6')
        b.set(qn('w:space'), '4'); b.set(qn('w:color'), NAVY)
        pbdr.append(b); pPr.append(pbdr)

    def _top_border(self, p):
        pPr = p._p.get_or_add_pPr()
        pbdr = OxmlElement('w:pBdr')
        b = OxmlElement('w:top'); b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '6')
        b.set(qn('w:space'), '4'); b.set(qn('w:color'), NAVY)
        pbdr.append(b); pPr.append(pbdr)

    def save(self, path):
        self.doc.save(path)
