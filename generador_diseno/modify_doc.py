# -*- coding: utf-8 -*-
"""Modifica el documento V2 (con comentarios) para:
 - Agregar Alcance del proyecto y de la solución SAC (1.x)
 - Insertar 'Proceso actual (AS-IS)' en Ciudad Limpia y Transprensa
 - Agregar Glosario
 - Agregar Respuestas a Comentarios de Revisión (los 47 comentarios)
Trabaja sobre el docx subido, preservando su contenido y comentarios."""
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
import docx_helpers as H
from docx_helpers import NAVY, BLUE_D, RED, GREEN, GREY, LIGHT

d = Document('uploadv2/v2.docx')
CW = 6.6
CREATED = []   # elementos de nivel cuerpo creados en el bloque actual (referencias estables)
AMAP = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER,
        'justify': WD_ALIGN_PARAGRAPH.JUSTIFY, 'right': WD_ALIGN_PARAGRAPH.RIGHT}

# ---------- creadores (agregan al final; luego se mueven si hace falta) ----------
def mk_heading(text, level):
    p = d.add_paragraph(text, style='Heading %d' % level)
    CREATED.append(p._p)
    pf = p.paragraph_format; pf.keep_with_next = True
    pf.space_before = Pt(12 if level == 1 else 9 if level == 2 else 7)
    pf.space_after = Pt(5 if level == 1 else 4 if level == 2 else 3)
    return p

def mk_para(text, italic=False, size=10, bold=False, color=None, align='justify', space_after=6):
    p = d.add_paragraph(); p.alignment = AMAP[align]
    CREATED.append(p._p)
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text); r.font.name = 'Arial'; r.font.size = Pt(size)
    r.font.italic = italic; r.font.bold = bold
    if color: r.font.color.rgb = RGBColor.from_string(color)
    return p

def mk_table(headers, rows, widths=None, size=8.6, header_size=8.8, zebra=True):
    ncol = len(headers)
    t = d.add_table(rows=1, cols=ncol)
    CREATED.append(t._tbl)
    try: t.style = 'Fanalca'
    except Exception: t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    H._no_autofit(t)
    if widths is None: widths = [CW / ncol] * ncol
    hdr = t.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    th = hdr._tr.makeelement(qn('w:tblHeader'), {qn('w:val'): 'true'}); trPr.append(th)
    for i, htext in enumerate(headers):
        H._shade(hdr.cells[i], NAVY)
        H._cell_text(hdr.cells[i], htext, bold=True, color='FFFFFF', size=header_size, align='center')
        H._set_cell_margins(hdr.cells[i])
    for r, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            H._cell_text(cells[i], val, size=size, align='left')
            H._set_cell_margins(cells[i])
            if zebra and r % 2 == 1: H._shade(cells[i], LIGHT)
    H._set_widths(t, widths)
    mk_spacer(4)
    return t

def mk_spacer(pts=6):
    p = d.add_paragraph(); CREATED.append(p._p); p.paragraph_format.space_after = Pt(pts)
    p.paragraph_format.space_before = Pt(0); return p

def mk_callout(title, lines, accent=NAVY, fill="EAF1FB", icon="●"):
    t = d.add_table(rows=2, cols=1); t.style = 'Table Grid'; CREATED.append(t._tbl)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER; H._no_autofit(t); H._set_widths(t, [CW])
    color_borders(t, accent)
    top = t.rows[0].cells[0]; H._shade(top, accent)
    H._cell_text(top, "%s  %s" % (icon, title), bold=True, color='FFFFFF', size=9.2)
    H._set_cell_margins(top, top=50, bottom=50)
    bot = t.rows[1].cells[0]; H._shade(bot, fill); bot.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p0 = bot.paragraphs[0]; p0.paragraph_format.space_after = Pt(2)
    if isinstance(lines, str): lines = [lines]
    for k, line in enumerate(lines):
        p = p0 if k == 0 else bot.add_paragraph()
        p.paragraph_format.space_after = Pt(2); p.paragraph_format.space_before = Pt(0)
        run = p.add_run(("▸  " if len(lines) > 1 else "") + line)
        run.font.name = 'Arial'; run.font.size = Pt(8.8)
    H._set_cell_margins(bot, top=60, bottom=60)
    mk_spacer(6); return t

def color_borders(table, color):
    from docx.oxml import OxmlElement
    tblPr = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement('w:%s' % edge)
        e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '8')
        e.set(qn('w:space'), '0'); e.set(qn('w:color'), color)
        borders.append(e)
    tblPr.append(borders)

def _top(o): return o._tbl if isinstance(o, Table) else o._p

def move_before(target_el, objs):
    for o in objs:
        target_el.addprevious(_top(o))

# ---------- localizar objetivos de inserción ----------
def find_targets():
    t = {'alcance': None, 'cl': None, 'trans': None}
    state = None
    for p in d.paragraphs:
        st = p.style.name; tx = p.text.strip()
        if st == 'Heading 1':
            if tx == 'Cómo usar el documento' and t['alcance'] is None:
                t['alcance'] = p._p
            state = tx
        elif st == 'Heading 3' and tx.startswith('Objetivos empresariales'):
            if state == 'Ciudad Limpia' and t['cl'] is None: t['cl'] = p._p
            elif state.startswith('Transprensa') and t['trans'] is None: t['trans'] = p._p
    return t

targets = find_targets()
assert all(targets.values()), "targets no encontrados: %s" % {k: bool(v) for k, v in targets.items()}
print("targets OK")

body = d.element.body
sectPr = body.find(qn('w:sectPr'))

def build_and_place(anchor_el, build_fn):
    CREATED.clear()
    build_fn()
    for el in list(CREATED):
        anchor_el.addprevious(el)

# =====================================================================
# 1.1  ALCANCE  (insertar al final de la sección 1, antes de "Cómo usar")
# =====================================================================
def blk_alcance():
    mk_heading("Alcance del proyecto y de la solución SAC", 2)
    mk_para(
        "El programa SAP BUILD reemplaza el proceso de presupuestación y forecast basado en hojas de "
        "cálculo por SAP Analytics Cloud (SAC), integrado con SAP S/4HANA a través de SAP DataSphere. "
        "Para cada sociedad, el alcance cubre el diseño y la construcción de tres modelos de planeación "
        "(Ingresos, Costos/Gastos y Estados Financieros), la carga del plan mediante plantillas, el "
        "cálculo mediante Data Actions, la integración del dato real, la gestión de versiones, los "
        "reportes y dashboards, y la seguridad de acceso.")
    mk_callout("Capacidades de SAP Analytics Cloud incluidas en el alcance", [
        "Modelos de planificación (Planning Models) con dimensiones, jerarquías y medidas.",
        "Data Actions (Advanced Formulas y Cross-Model Copy) para cálculos y consolidación entre modelos.",
        "Plantillas de entrada (Input Forms) y complemento de Excel (SAC Add-in) para la carga del plan.",
        "Stories y Analytic Applications para reportes y dashboards; exportación a PDF/PPT.",
        "Gestión de versiones (Actual, Presupuesto, Forecast; públicas y privadas) y copia de versiones para escenarios.",
        "Integración con SAP S/4HANA vía SAP DataSphere (CDS Views / OData) para el dato real.",
        "Seguridad mediante Data Access Control (DAC) por Sociedad y demás dimensiones.",
    ], accent=NAVY)
    mk_para(
        "Quedan fuera del alcance actual, por sociedad: en Transprensa, los modelos de Talento Humano y "
        "de Flujo de Caja Diario (en diseño); en Fanalca, el módulo de Renting y el Flujo de Caja se "
        "encuentran en definición; en Ciudad Limpia, el modelo detallado de personal se aborda mediante "
        "un modelo referencial. El cierre contable y la ejecución transaccional permanecen en el ERP; "
        "SAC consume el resultado para análisis, planeación y reporte.", size=9.5)

# =====================================================================
# 4.1.1  CIUDAD LIMPIA — PROCESO ACTUAL (AS-IS)
# =====================================================================
def blk_cl_asis():
    mk_heading("Proceso actual (AS-IS) de la planeación financiera", 3)
    mk_para(
        "Actualmente, todo el proceso presupuestal de Ciudad Limpia se realiza en hojas de cálculo Excel "
        "con macros, y la consolidación es manual a cargo del área de Planeación Financiera. A "
        "continuación se describe el proceso tal como opera hoy, identificado en las sesiones de "
        "levantamiento, como línea base sobre la cual SAC aporta automatización de la consolidación, el "
        "cálculo, el forecast y el reporte.")
    mk_para("Ingresos ordinarios (Bogotá, Neiva, Huila). El Jefe Nacional de Tarifas calcula los ingresos "
            "ordinarios a partir de variables tarifarias regulatorias: toneladas, usuarios, kilómetros, "
            "metros cuadrados, número de árboles, estratos, subsidios, contribuciones, IPC y factores por "
            "componente de servicio. Cada componente tiene su propia métrica —Recolección (toneladas), "
            "Barrido (kilómetros), Corte de césped (m²) y Poda (número de árboles)—. La facturación no es "
            "directa: el recaudo se realiza a través de terceros (el cobro se incluye en el recibo de "
            "servicios públicos). El equipo de tarifas entrega a Planeación Financiera un resumen con el "
            "valor total en dinero por componente y mes; ese es el dato que hoy se sube al ERP y el que se "
            "cargará en SAC. Para el real, se recibe un informe por componente con el valor ejecutado.",
            size=9.5)
    mk_para("Ingresos de CGS y RH. A diferencia de los ordinarios, en CGS y RH sí es posible el cálculo "
            "P×Q (tarifa × toneladas/kilos) por cliente y tipo de residuo, con seguimiento de las "
            "cantidades gestionadas.", size=9.5)
    mk_para("Costos y gastos. La mano de obra representa cerca del 80% del costo total. Planeación "
            "Financiera distribuye una macro de Excel a cada jefe de área; Talento Humano precarga en esa "
            "macro la base de empleados con salarios, bonificaciones y contribuciones. Los costos de flota "
            "se llevan con un centro de costo (CECO) por vehículo (repuestos, llantas, combustibles y "
            "lubricantes). El resto de gastos —depreciaciones, TIC, servicios públicos, arrendamientos, "
            "dotación, seguros y gastos generales— se recogen en plantillas por parte de las "
            "aproximadamente 17 áreas, y Planeación Financiera consolida.", size=9.5)
    mk_para("Estados financieros. El P&G se arma a partir de la consolidación de ingresos y gastos; el "
            "Balance y el Flujo de Caja incorporan cuentas adicionales de forma manual (activos fijos, "
            "cartera, deuda, CAPEX e inversiones de flota).", size=9.5)
    mk_callout("Sistemas y artefactos que se operan hoy (línea base)", [
        "Macro de tarifas (ingresos ordinarios por componente y mes) — Jefatura de Tarifas.",
        "Macro de personal precargada por Talento Humano y distribuida a cada jefe de área.",
        "Plantillas de gastos por área (≈17 áreas) consolidadas por Planeación Financiera.",
        "Informe de recaudo de terceros (recibos de servicios públicos).",
        "Informe de ejecución (real) por componente de servicio.",
        "Consolidado de presupuesto y Estados Financieros en Excel.",
    ], accent=GREEN, fill="EAF3E6")
    mk_para("Puntos de dolor: fragmentación en decenas de archivos Excel, consolidación lenta y manual, "
            "trazabilidad limitada del origen del dato, riesgo de error en el cierre y poca agilidad para "
            "actualizar el forecast.", italic=True, size=9, color=GREY)

# =====================================================================
# 5.1.1  TRANSPRENSA — PROCESO ACTUAL (AS-IS)
# =====================================================================
def blk_trans_asis():
    mk_heading("Proceso actual (AS-IS) de la planeación financiera", 3)
    mk_para(
        "El presupuesto de Transprensa se construye de forma centralizada por el equipo financiero, a "
        "partir de las directrices de la Gerencia General y la Gerencia Comercial (que definen el "
        "crecimiento por regional), utilizando Excel y reportes en Power BI. La información operativa "
        "—kilogramos, remesas, pesos, tarifas y la discriminación crédito/contado por CRM— proviene del "
        "software logístico Silotrans/Silotrack; la información contable y de nómina proviene de los "
        "sistemas legados (SIESA y CIES). El presupuesto se arma por negocio y por regional, no cliente "
        "por cliente.")
    mk_para("Líneas de negocio presupuestadas. Paqueteo (CV paqueteo), masivo (CB masivo), vehículos "
            "dedicados, almacenamiento e ingredientes; más tres negocios especiales —Ingreso, T1 y Soy "
            "Más— que representan cerca del 30% de los ingresos, se manejan por licitación y quedan por "
            "fuera de la gestión de la fuerza comercial.", size=9.5)
    mk_para("Ingresos (metodología P×Q). Se parte de la ejecución real del año anterior (N-1, 2025) en "
            "kilogramos y pesos por regional, tomada de Silotrans. Se calcula el indicador pesos/kilogramo "
            "(la tarifa implícita) y se proyecta el año aplicando un crecimiento en volumen (porcentaje de "
            "kg por regional, definido por la gerencia; por ejemplo +21% global) y un crecimiento en "
            "tarifa (por ejemplo +15%) basado en el IPC y en el ICTC (índice de costos del transporte de "
            "carga, que recoge combustible, salario mínimo e inflación). El total anual se distribuye mes "
            "a mes según la estacionalidad propia del negocio. Se discrimina crédito (B2B, ligado a los "
            "ejecutivos comerciales) frente a contado/contraentrega (originado en los 46 CRM). Ejemplo "
            "levantado en sesión: Antioquia generó en abril remesas por $2.254 millones, equivalentes a "
            "1.559 toneladas.", size=9.5)
    mk_para("Servicio masivo y clientes especiales. En el masivo se parte de los kilogramos para "
            "dimensionar el vehículo por ruta (origen-destino): el ingreso se define como el costo del "
            "flete cotizado a terceros más un margen objetivo (entre 15% y 18%). En los clientes "
            "especiales (Ingreso, T1, Soy Más) los kilos nacen de la licitación y crecen alrededor de "
            "1,5%–2% anual; algunos tienen estacionalidad marcada (por ejemplo, sin operación en enero y "
            "diciembre). Si durante el año se gana una licitación grande, se incorpora como un escenario "
            "adicional.", size=9.5)
    mk_para("Costos y gastos. Las dos variables principales son el flete (según los kg se define el número "
            "de vehículos y la distribución origen-destino) y la mano de obra, que es variable y está "
            "ligada al volumen de kg (en el paqueteo intervienen personas y plataformas; en almacenamiento, "
            "el alistamiento, el cargue y el estampillado). Se suman las comisiones (a CRM externos y a la "
            "fuerza de ventas), los arrendamientos (indexados al IPC) y los gastos fijos (histórico N-1 × "
            "IPC).", size=9.5)
    mk_para("Resultados y versiones. Se calculan el margen bruto y el margen operativo, y el P&G "
            "administrativo (PCGA) se abre por regional. La Gerencia y la Gerencia Comercial fijan las "
            "metas por regional (presupuesto comercial) y el área financiera construye el presupuesto "
            "financiero oficial; durante el año se actualiza el forecast.", size=9.5)
    mk_callout("Sistemas y artefactos que se operan hoy (línea base)", [
        "Silotrans/Silotrack (software logístico): kilogramos, remesas, facturación, tarifas y crédito/contado por CRM.",
        "SIESA (contabilidad) y CIES (nómina): datos contables y de personal.",
        "Archivos Excel de presupuesto por negocio y regional (paqueteo, masivo, especiales).",
        "Reportes y tableros en Power BI para seguimiento de ejecución.",
    ], accent=GREEN, fill="EAF3E6")
    mk_para("Puntos de dolor: armado y consolidación manual en Excel, múltiples archivos por negocio y "
            "regional, dependencia de descargas de Silotrans y reprocesos, y dificultad para simular "
            "escenarios (nuevas licitaciones o clientes grandes) de forma ágil.",
            italic=True, size=9, color=GREY)

build_and_place(targets['alcance'], blk_alcance)
build_and_place(targets['cl'], blk_cl_asis)
build_and_place(targets['trans'], blk_trans_asis)
print("bloques AS-IS y Alcance insertados")

# =====================================================================
# 6.  GLOSARIO   (al final)
# =====================================================================
GLOSARIO = [
    ["SAP Analytics Cloud (SAC)", "Plataforma en la nube de SAP para planificación, análisis y reporte (planning, stories y dashboards)."],
    ["SAP S/4HANA", "Sistema ERP de SAP; fuente del dato contable y transaccional (real) y de datos maestros."],
    ["SAP DataSphere", "Capa de integración y virtualización de datos entre S/4HANA y SAC; aplica transformaciones (ETL/CDS)."],
    ["SAP BW/4HANA", "Data warehouse de SAP usado para cargar el real desde el ERP."],
    ["SAP BPC", "Business Planning and Consolidation: herramienta de planeación actual de Fanalca, a migrar a SAC."],
    ["SAP BTP", "Business Technology Platform: nube donde se ejecutan SAC y DataSphere."],
    ["Modelo (Planning Model)", "Contenedor de datos de SAC definido por dimensiones y medidas; habilita capacidades de planificación."],
    ["Dimensión", "Eje de análisis del modelo (p. ej. Cuenta, Sociedad, CEBE, Fecha, Versión)."],
    ["Medida", "Valor numérico que se planea o analiza (p. ej. Importe, Cantidad, Tarifa)."],
    ["Data Action", "Proceso de cálculo en SAC (Advanced Formulas o Cross-Model Copy) que reemplaza los scripts/macros."],
    ["Story", "Reporte o dashboard interactivo de SAC."],
    ["Analytic Application", "Aplicación analítica de SAC con mayor interactividad (botones, scripts) que una Story."],
    ["Input Form / Plantilla", "Formulario de entrada de datos en SAC para la captura y carga del plan."],
    ["SAC Add-in (Excel)", "Complemento de Excel que permite leer y escribir datos de SAC desde Excel."],
    ["Versión", "Escenario de datos (Actual/Real, Presupuesto/Plan, Forecast); puede ser pública o privada."],
    ["Data Access Control (DAC)", "Control de acceso a los datos por miembros de una dimensión (p. ej. por Sociedad)."],
    ["Currency Translation", "Función de SAC para convertir importes entre monedas."],
    ["CDS View", "Core Data Services: vista de S/4HANA que expone datos para su consumo/integración."],
    ["OData", "Protocolo estándar de servicios de datos usado para integrar SAC con SAP."],
    ["ETL", "Extract-Transform-Load: extracción, transformación y carga de datos (se realiza en DataSphere)."],
    ["BPF", "Business Process Flow: flujo guiado de tareas de planeación en SAC/BPC."],
    ["P×Q", "Precio × Cantidad: metodología de cálculo de ingresos (p. ej. tarifa por kg × kilogramos)."],
    ["N-1", "Año inmediatamente anterior; base histórica para proyectar el presupuesto."],
    ["Presupuesto / Plan", "Cifras objetivo aprobadas para un período."],
    ["Forecast (FCST)", "Proyección actualizada durante el año a partir de la ejecución."],
    ["Real / Actual", "Ejecución contable efectiva del período, integrada desde el ERP."],
    ["EEFF", "Estados Financieros: P&G, Balance General y Flujo de Caja."],
    ["P&G / PYG", "Estado de Pérdidas y Ganancias (Estado de Resultados)."],
    ["EBITDA", "Utilidad antes de intereses, impuestos, depreciaciones y amortizaciones."],
    ["PCGA", "Principios de Contabilidad Generalmente Aceptados (base del P&G administrativo)."],
    ["CEBE", "Centro de Beneficio (Profit Center); en CL y Transprensa agrupa componente de servicio/regional."],
    ["CECO", "Centro de Costo (Cost Center); unidad para asignar costos (p. ej. un CECO por vehículo)."],
    ["Sociedad (NIT)", "Entidad jurídica de reporte financiero."],
    ["Cuenta", "Cuenta contable del plan de cuentas (tablas SKA1/SKB1 en SAP)."],
    ["AUDITORIA", "Dimensión que registra el origen del dato (real, presupuesto, cálculo, manual) para trazabilidad."],
    ["CRM", "Centro de Recibo de Mercancía (Transprensa); punto físico de recepción, no ‘Customer Relationship Management’."],
    ["Remesa", "Documento logístico que soporta el envío/transporte de mercancía (se genera en Silotrans)."],
    ["Silotrans / Silotrack", "Software logístico de Transprensa: kilogramos, remesas, tarifas y ventas por CRM."],
    ["SIESA / CIES", "Sistemas legados de Transprensa: contabilidad (SIESA) y nómina (CIES)."],
    ["UNOE", "Sistema de presupuesto de gastos de Fanalca; origen del modelo de Costos y Gastos."],
    ["IPC", "Índice de Precios al Consumidor; usado para indexar tarifas y gastos."],
    ["ICTC / ICPC", "Índice de Costos del Transporte de Carga; recoge combustible, salario mínimo e inflación."],
    ["TRM / IBR / SOFR", "Tasa Representativa del Mercado (USD/COP) e indicadores de tasa de interés (local/externa)."],
    ["CKD / CBU", "Vehículos/motos importados desarmados (CKD) o armados (CBU) — línea de motos y autos de Fanalca."],
    ["KPI / Dashboard", "Indicador clave de desempeño / tablero visual de indicadores."],
    ["UAT", "User Acceptance Testing: pruebas de aceptación por parte de los usuarios."],
]

def blk_glosario():
    mk_heading("Glosario de términos", 1)
    mk_para("Este glosario reúne los términos técnicos de SAP/SAC y del negocio empleados en el "
            "documento, para facilitar su lectura por parte de todos los perfiles.", size=10)
    mk_table(["Término", "Definición"], GLOSARIO, widths=[1.9, 4.7], size=8.4)

build_and_place(sectPr, blk_glosario)
print("glosario agregado")

# =====================================================================
# 7.  RESPUESTAS A LOS COMENTARIOS DE REVISIÓN   (al final)
# =====================================================================
RESP_HDR = ["#", "Autor", "Comentario (resumen)", "Respuesta"]
RW = [0.45, 1.25, 2.05, 2.85]

GENERALES = [
    ["3", "E. Beltrán", "Colocar el alcance que tiene SAC para entender si el documento lo abarca.",
     "Se agregó la sección 1.1 «Alcance del proyecto y de la solución SAC», con las capacidades de SAC incluidas (modelos, Data Actions, plantillas, Stories/dashboards, versiones, DAC) y lo que queda fuera de alcance por sociedad."],
    ["448", "E. Beltrán", "¿Cuál es el alcance en SAC? (arquitectura Transprensa).",
     "Ver 1.1. Para Transprensa el alcance cubre los modelos de Ingresos, Costos/Gastos y EEFF; Talento Humano y Flujo de Caja Diario están en diseño (fuera del alcance actual)."],
    ["181", "L. Miranda", "Agregar un glosario y el alcance del proyecto.",
     "Se incorporó el Glosario (sección 6) y la sección 1.1 de Alcance."],
    ["217", "L. Miranda", "Detallar cómo se migra el presupuesto a SAC.",
     "Se detalla en 1.1 y en los procesos AS-IS: el plan se carga por plantillas/Input Forms en SAC; el real se integra desde S/4HANA vía DataSphere; los cálculos actuales (macros) se replican como Data Actions. La construcción se realiza en la fase de realización (2–3 meses)."],
]
FANALCA = [
    ["5", "J. G. Moreno", "¿Escenario es complemento de la dimensión Versión?",
     "Sí. Los escenarios (Pesimista/Optimista/Medio, Plan Bancos 1-2, Forecast 1-N) se modelan como versiones dentro de la dimensión Version; el presupuesto aprobado es una versión pública inmutable y los escenarios son versiones adicionales."],
    ["7", "J. G. Moreno", "El cierre financiero lo hacen en informes.",
     "Correcto; se aclara: SAC no ejecuta el cierre contable (permanece en el ERP). El beneficio es disponer del EEFF consolidado (real vs. presupuesto) para análisis y reporte, reduciendo la construcción manual de informes."],
    ["176", "J. G. Moreno", "Faltan los scripts del modelo de gastos y de EEFF.",
     "Se complementa: Costos y Gastos usa el paquete UNOE→Gastos y la distribución de CECOS transversales (PDB, PPC); el EEFF se alimenta con los paquetes de envío desde Ingresos y Costos/Gastos (Data Actions de consolidación). Ver 3.3.4 y la figura de flujo de cálculo."],
]
CL = [
    ["230", "E. Beltrán", "¿Es el único proceso? Enlistar reportes/archivos que se operan hoy.",
     "Se agregó 4.1.1 «Proceso actual (AS-IS)» con el detalle del proceso y el inventario de artefactos/sistemas actuales (macro de tarifas, macro de personal de TH, plantillas de gastos por área, informe de recaudo de terceros, informe de ejecución por componente, consolidado y EEFF en Excel)."],
    ["238", "L. Miranda", "¿Cómo se realizaría la carga en SAC?",
     "Mediante plantillas de carga (Input Forms) por categoría, cargadas en SAC Data Management por Planeación Financiera; el real se integra desde S/4HANA (DataSphere). Ver 4.3.4 y 4.1.1."],
    ["296", "E. Beltrán", "¿No se debería considerar DataSphere?",
     "Sí; se corrigió la arquitectura (Figura 5): la integración del real desde S/4HANA se realiza vía SAP DataSphere. Las plantillas de presupuesto se cargan directamente en SAC."],
    ["297", "L. Miranda", "Más detalle de los objetivos OE-01/02/03 y sus beneficios.",
     "Se ampliaron: OE-01 unifica la fuente y elimina la dispersión en decenas de Excel (el montaje inicial se apoya en plantillas, pero la consolidación, el cálculo y el forecast se automatizan). OE-02: la consolidación pasa de semanas a minutos y facilita el empalme del ppto 2027. OE-03: forecast ágil de Ingresos, Mano de Obra, Dotación, Consumibles y Mantenimiento."],
    ["301", "L. Miranda", "Gestión de versiones: cuántas, pública/privada, copias.",
     "SAC gestiona versiones Actual, Presupuesto y Forecast. El presupuesto aprobado es una versión pública; el forecast admite varias versiones (privadas de trabajo y públicas publicadas). SAC permite copiar versiones (Copy) y usar «copy from actual» como base. Regla: se conserva el dato final autorizado (opción Reemplazar)."],
    ["302", "L. Miranda", "Especificar las opciones de carga.",
     "Opciones en SAC: Reemplazar (Overwrite), Acumular (Add/Sum) y Borrar y recargar. Estándar acordado: Reemplazar con el dato definitivo; los ajustes puntuales se hacen en la plantilla SAC sin recargar el archivo."],
    ["303", "L. Miranda", "¿Cuáles reportes, KPI y dashboards genera SAC?",
     "Reporte de Ingresos, Estado de Resultados, Balance, Flujo de Efectivo, comparación presupuesto vs. real ($ y %), versiones de Forecast, ejecución presupuestal por área/sociedad y KPIs operativos (toneladas, km, usuarios, árboles), con dashboards dinámicos exportables a PDF/PPT."],
    ["305", "L. Miranda", "¿Solo Sociedad y CEBE? ¿Y CECO, Cuenta, Moneda, Regional?",
     "La 4.2 describe la estructura organizativa; el detalle completo de dimensiones (CECO_CL, CUENTA, MONEDA, AUDITORIA, Version, Date, CLIENTE) está en 4.3.2 «Modelos SAC y dimensiones» y en «Dimensiones compartidas». Una dimensión Regional/Municipio se puede incorporar (ver 315)."],
    ["306", "E. Beltrán", "¿Estos no vienen de S/4HANA? ¿No requieren ETL en DataSphere?",
     "Sí; los componentes de servicio (CEBE) provienen de S/4HANA (CEPC). La integración del real y de maestros se realiza vía SAP DataSphere, donde se aplican las transformaciones (ETL/CDS Views) antes de exponerlos a SAC."],
    ["307", "L. Pérez", "¿Esto hace referencia a servicios / asesorías?",
     "El componente señalado corresponde a un servicio/otros ingresos de la operación de aseo (p. ej. comercialización de aprovechables), no a asesorías. Se confirmará el nombre exacto con el cliente para evitar ambigüedad."],
    ["311", "L. Miranda", "¿El ppto se carga en DataSphere o en SAC? ¿«Dimensiones compartidas»? ¿Dashboards por CEBE/CECO/Regional?",
     "Se aclara: el presupuesto se carga directamente en SAC (por plantillas); de S/4HANA, vía DataSphere, proviene solo el ejecutado (real). «Dimensiones compartidas» = dimensiones comunes reutilizadas por los tres modelos (mismos maestros), no necesariamente públicas. Los dashboards filtran por Sociedad, CEBE, CECO y, si se habilita, por Regional/Municipio."],
    ["314", "E. Beltrán", "No se ve dónde se estructura el esquema de scripts de la solución.",
     "El esquema de cálculo (Data Actions) se documenta en 4.3.3 «Flujo de cálculo y consolidación» (Figuras 6 y 7). En la fase de realización se detalla cada Data Action (Advanced Formulas / Cross-Model Copy)."],
    ["315", "L. Miranda", "¿Se puede adicionar la dimensión Regional?",
     "Sí. SAC permite agregar una dimensión Regional/Municipio (genérica u organizativa). Para CL Bogotá (ingresos por Bogotá y Cali además del CEBE) puede modelarse como jerarquía dentro de CEBE_CL o como dimensión propia; se recomienda evaluarla por el reporte de balance por municipio (vigilado vs. no vigilado)."],
    ["316", "L. Miranda", "Más detalle de la carga en SAC; ¿es el mismo proceso actual?",
     "La carga del plan se hace por plantillas/Input Forms en SAC (no macros); el proceso de entrada por área se mantiene conceptualmente, pero la consolidación y el cálculo se automatizan. Ver 4.3.4 y 4.1.1."],
    ["317", "E. Beltrán", "El proceso de carga no debería ir aquí; ¿esta sección es la configuración?",
     "Se aclara la separación: «Modelos y dimensiones» describe el diseño (configuración); el método de carga se consolida en 4.3.4 «Integración y plantillas de carga». La «Lógica de carga por sociedad» se conserva como contexto funcional."],
    ["318", "L. Miranda", "SAC no resolvería el montaje del ppto actual; detallar la plantilla genérica.",
     "En el primer año SAC aporta sobre todo en consolidación, cálculo, forecast y reporte; el montaje del plan se apoya en plantillas. La «plantilla genérica» es un formato estándar de Input (Sociedad | CECO | CEBE | Cuenta | Ene–Dic) que cada área diligencia y Planeación carga en SAC (Excel Add-in o Input Form). Ver 4.3.4."],
    ["319", "L. Miranda", "¿A través de qué medio se integran los EEFF?",
     "El EEFF no se integra por interfaz externa: se construye dentro de SAC. El P&G fluye desde Ingresos y Gastos/Costos mediante Data Actions (Cross-Model Copy); las cuentas propias de balance se cargan de S/4HANA (DataSphere) o manualmente. Ver 4.3.3."],
    ["320", "L. Miranda", "¿Cómo sería la lógica de integración? No es clara.",
     "Real desde S/4HANA vía DataSphere (CDS Views); plan por plantillas; consolidación entre modelos por Data Actions, con trazabilidad por AUDITORIA. Ver 4.3.3/4.3.4."],
    ["321", "L. Miranda", "Las cargas manuales, ¿por plantilla o registro directo en SAC?",
     "Ambas: para volúmenes se usa plantilla (Input Form / Excel Add-in); para ajustes puntuales se hace registro directo en la celda de la Story/plantilla SAC, sin recargar el archivo."],
    ["322", "E. Beltrán", "¿Se conecta con la tabla anterior? ¿La lógica de alimentación abarca las dimensiones?",
     "Sí; la tabla de «Lógica de construcción del EEFF» se relaciona con la de dimensiones: cada componente del EEFF se alimenta por las dimensiones compartidas (Cuenta, CEBE, Sociedad, Moneda, Versión, Fecha, Auditoría). Se enlazó la redacción de ambas tablas."],
    ["323", "L. Miranda", "¿A qué hace referencia (SKA1/SKB1)?",
     "SKA1/SKB1 son las tablas de SAP donde reside el plan de cuentas (SKA1 a nivel de mandante; SKB1 a nivel de sociedad). Se añadió al Glosario."],
    ["324", "L. Miranda", "El Estado de Resultados es parte del EEFF; ¿por qué no tendría CECO?",
     "El modelo EEFF se mantiene «ligero» para consolidación/lectura y no lleva CECO; el análisis por CECO se hace en el modelo de Costos y Gastos (que sí incluye CECO_CL) y se consolida al EEFF por CEBE/Cuenta. Esto preserva el rendimiento."],
    ["325", "L. Miranda", "El ER contempla ingresos; ¿por qué no cliente, cantidades y tarifas?",
     "Análogamente, el detalle de cliente, cantidad y tarifa (P×Q de CGS/RH) vive en el modelo de Ingresos; el EEFF recibe el resultado consolidado por Cuenta/CEBE/Sociedad, evitando la explosión de dimensionalidad."],
    ["327", "L. Miranda", "¿Cómo se integra el PYG con los demás modelos (cálculos)?",
     "El P&G del EEFF se integra por Data Actions (Cross-Model Copy) que traen los resultados de Ingresos y de Costos/Gastos; los cálculos (P×Q, distribuciones, consolidación) ocurren en los modelos de origen y en el EEFF. Ver Figura 6."],
    ["328", "L. Miranda", "¿Cómo se carga: Input en SAC o carga de plantilla manual?",
     "Las cuentas propias de balance/flujo se cargan por plantilla (Input Form) o por integración desde S/4HANA; los ajustes se ingresan directamente en SAC. Ver 4.3.4."],
    ["329", "L. Miranda", "Depreciaciones acumuladas (¿Balance y PYG?); mano de obra → modelo de personal, ¿cómo se integra?",
     "La depreciación del período impacta el P&G y la acumulada el Balance; en SAC ambas se derivan del rubro de depreciación del modelo de gastos (la del período fluye al P&G y se acumula en balance por Data Action). La mano de obra se modela con una plantilla de personal (modelo referencial) cargada en Costos y Gastos por Input Form o Excel Add-in."],
    ["331", "L. Miranda", "¿Una sola plantilla para todos los costos/gastos con estructuras distintas?",
     "No necesariamente: se define una plantilla genérica base (Sociedad|CECO|CEBE|Cuenta|meses) y variantes específicas cuando la estructura lo exige (mantenimiento de flota por vehículo, personal, dotación, TIC). Se documenta en 4.3.4."],
    ["333", "L. Miranda", "Agregar un ítem con los reportes iniciales que generaría SAC.",
     "Incorporado (ver también 303): Reporte de Ingresos, Estado de Resultados, Balance, Flujo de Efectivo, comparación presupuesto vs. real ($ y %), versiones de Forecast, ejecución presupuestal por área, gráficas y dashboards dinámicos para toma de decisiones."],
    ["335", "L. Miranda", "¿Gerentes/directores/jefes necesitan licencia para consultar?",
     "Sí; todo acceso a SAC requiere licencia. Para consulta se asigna una licencia de tipo BI/visualización (solo lectura), de menor costo que la de planificación. La política concentra las licencias de planificación en Planeación Financiera y asigna solo lectura a gerentes/directores según necesidad."],
]
TRANS = [
    ["432", "M. C. Moreno", "Integrar más detalle del proceso de negocio actual (usar las sesiones).",
     "Se agregó 5.1.1 «Proceso actual (AS-IS)» con lo levantado en sesión: presupuesto por negocio y regional (paqueteo, masivo, dedicados, almacenamiento, especiales Ingreso/T1/Soy Más), metodología P×Q desde el histórico N-1 de Silotrans, estacionalidad, crédito vs. contado por CRM, y costos (fletes y mano de obra)."],
    ["434", "M. C. Moreno", "Detallar gestión de versiones; ¿Excel interno?; ¿remesas de Silotrans a SAC?",
     "Versiones: Presupuesto Comercial (metas de gerencia/comercial), Presupuesto Financiero (oficial) y Forecast. El objetivo es reemplazar los Excel de armado. Las remesas/guías se toman de Silotrans (que hoy genera remesas y factura) y se integran como ejecutado vía S/4HANA/DataSphere; el presupuesto se arma directamente en SAC."],
    ["435", "M. C. Moreno", "¿Cómo medir la reducción de errores? ¿P×Q es tarifa/ingresos/fletes? ¿Solo P×Q?",
     "P×Q de ingresos = kilogramos × tarifa (pesos/kg). Hay más cálculos: dimensionamiento de fletes por kg/ruta (costo del tercero + margen), mano de obra variable por kg, comisiones, arrendamientos y gastos fijos. La reducción de errores se mide por eliminar la consolidación manual en Excel y la trazabilidad única del dato (menos reprocesos y descuadres)."],
    ["436", "M. C. Moreno", "¿Qué escenarios de Forecast/Plan y qué simulaciones?",
     "Escenarios: Presupuesto Comercial, Presupuesto Financiero, Forecast y Real. Las simulaciones evalúan el impacto de eventos como ganar una nueva licitación o un cliente grande (p. ej. tipo Falabella) sobre kilos, ingresos, costos y márgenes, y su efecto en el tiempo, generando una versión de Forecast/Plan con esos supuestos."],
    ["437", "M. C. Moreno", "El beneficio de comparar presupuesto vs. real sería en la propia SAC.",
     "Correcto; la comparación presupuesto vs. real se realiza dentro de SAC (mismo modelo, versiones Real y Presupuesto), con variaciones en $ y % por regional y servicio, sin exportar a Excel. Se complementó la redacción."],
    ["438", "M. C. Moreno", "Detallar la optimización de la mano de obra según la estacionalidad de ingresos.",
     "La mano de obra temporal es variable y se liga al volumen (índice persona/kg). Como los kg siguen una estacionalidad mensual, el modelo ajusta el personal temporal mes a mes según los kg proyectados, optimizando el costo en meses de mayor/menor operación."],
    ["440", "M. C. Moreno", "P×Q no es solo por regional, también por servicio y clientes especiales.",
     "Correcto; en 5.1.1 el P×Q se calcula por regional y por tipo de servicio (paqueteo, masivo, dedicados, almacenamiento), y los negocios especiales (Ingreso, T1, Soy Más) se presupuestan de forma individual por licitación."],
    ["441", "M. C. Moreno", "También debe ir por regional.",
     "Confirmado: toda la proyección se abre por regional (21 regionales), además de por servicio y cliente especial."],
    ["442", "M. C. Moreno", "¿Qué se presupuesta: kilos, COP, tarifas? Discriminado por regional.",
     "Se presupuestan kilogramos y pesos (COP), con la tarifa (pesos/kg) como driver, todo discriminado por regional y tipo de servicio. Ver 5.1.1."],
    ["443", "M. C. Moreno", "Detallar más el proceso N-1.",
     "N-1 = ejecución real del año anterior (2025) de Silotrans, en kilogramos y pesos por regional. Se calcula el indicador pesos/kilogramo, se aplica el crecimiento en volumen (% kg por regional, definido por gerencia) y en tarifa (IPC + ICTC), y el total anual se distribuye a los 12 meses según la estacionalidad histórica."],
    ["444", "M. C. Moreno", "El histórico proviene de Silotrans y el presupuesto se hace directamente en SAC.",
     "Confirmado y reflejado en el diseño: el histórico proviene de Silotrans y el presupuesto se elabora directamente en SAC (Input Forms/plantillas); el real queda integrado desde S/4HANA vía DataSphere."],
]

def blk_respuestas():
    mk_heading("Respuestas a los comentarios de revisión", 1)
    mk_para("Esta sección consolida y responde los 47 comentarios registrados en la revisión del "
            "documento, agrupados por sección. Los ajustes derivados se incorporaron en los apartados "
            "correspondientes (Alcance, procesos AS-IS, dimensiones, flujos de cálculo y glosario).", size=10)
    mk_heading("Generales y alcance", 2)
    mk_table(RESP_HDR, GENERALES, widths=RW, size=8.2)
    mk_heading("Fanalca S.A.", 2)
    mk_table(RESP_HDR, FANALCA, widths=RW, size=8.2)
    mk_heading("Ciudad Limpia", 2)
    mk_table(RESP_HDR, CL, widths=RW, size=8.0)
    mk_heading("Transprensa S.A.S.", 2)
    mk_table(RESP_HDR, TRANS, widths=RW, size=8.2)

build_and_place(sectPr, blk_respuestas)
print("respuestas agregadas")

d.save('Documento_Diseno_SAC_Unificado_V2_comentado.docx')
print("GUARDADO. Tablas:", len(d.tables), "| Párrafos:", len(d.paragraphs))

