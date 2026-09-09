# -*- coding: utf-8 -*-
"""Documento Funcional: Carga del Presupuesto Comercial a SAP Datasphere.
Consumo en Power BI o SAC; integración del real desde S/4HANA para Real vs. Presupuesto;
4 propuestas de carga + propuesta recomendada (mejor opción), con flujogramas."""
import sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'generador_diseno'))
from docx_helpers import Builder, NAVY, NAVY2, BLUE_D, RED, GREEN, GREY
from docx.shared import Pt, RGBColor
from openpyxl import load_workbook

TPL=os.path.join(HERE,'..','plan_fs','template_funcional.docx')
LOGO_BUILD=os.path.join(HERE,'..','plan_fs','logos','build.png')
LOGO_FAN=os.path.join(HERE,'..','plan_fs','logos','fanalca.png')
IMG=os.path.join(HERE,'img_ds')
SRC="/tmp/claude-0/-home-user-Johnmeg/75057f83-9833-5a60-bea8-f642bffd6fbf/scratchpad/in/campos.xlsx"

ws=load_workbook(SRC, data_only=True)["Campos presupuesto comercial"]
ORGS={2:"Autos N&U",3:"Autos Serv/Rep",4:"Motos",5:"Motos Rep.",6:"Tubos",7:"Defensas",
      8:"Carrocerías",9:"Autopartes",10:"Metalsur",11:"CGS",12:"RH",13:"Ciudad Limpia",14:"Transprensa"}
def applic(rowlabel):
    for r in range(3, ws.max_row+1):
        if ws.cell(r,1).value==rowlabel:
            return [ORGS[c] for c in range(2,15) if str(ws.cell(r,c).value).strip().lower()=="x"]
    return []
def aptext(rowlabel):
    o=applic(rowlabel); n=len(o)
    if n==0: return "(por confirmar)"
    if n>=12: return f"Todas ({n} de 13)"
    if n<=4: return "Solo " + ", ".join(o)
    return f"{n} de 13 organizaciones"

b=Builder(TPL); b.setup_headers(LOGO_FAN)
hp=b.doc.sections[0].header.paragraphs[0]
for r in hp.runs:
    if 'Documento de Diseño' in r.text: r.text='Documento Funcional · Carga del Presupuesto Comercial a SAP Datasphere'
    elif 'Programa SAP BUILD' in r.text: r.text='\tPrograma SAP BUILD — Grupo Fanalca'

def fm(text):
    p=b.doc.add_paragraph(); p.paragraph_format.space_before=Pt(10); p.paragraph_format.space_after=Pt(5)
    r=p.add_run(text); r.font.name='Arial'; r.font.size=Pt(13); r.font.bold=True
    r.font.color.rgb=RGBColor.from_string(BLUE_D); b._bottom_border(p); return p
def fig(name, n, desc): b.figure(os.path.join(IMG,name), f"Figura {n}. {desc}")

# =============== PORTADA ===============
b.spacer(30); b.cover_logo(LOGO_BUILD, width=3.0); b.spacer(16)
b.cover_title([
    ("DOCUMENTO FUNCIONAL", 22, BLUE_D, True, 4),
    ("Carga del Presupuesto Comercial a SAP Datasphere", 15, NAVY, False, 3),
    ("Real vs. Presupuesto · Consumo en Power BI o SAC · Propuestas de carga", 11, NAVY, False, 2),
    ("Programa SAP BUILD · Grupo Fanalca", 11, GREY, False, 20)])
b.meta_table([
    ("Objeto","Carga del presupuesto comercial a SAP Datasphere y reporte Real vs. Presupuesto"),
    ("Origen","Presupuesto: archivo Excel de campos  ·  Real: SAP S/4HANA"),
    ("Destino","SAP Datasphere (tablas + vista Real vs. Presupuesto)"),
    ("Consumo","Power BI o SAP Analytics Cloud (SAC)"),
    ("Sociedades","Fanalca (8 líneas) · Metalsur · CGS · RH · Ciudad Limpia · Transprensa"),
    ("Versión","2.0 — Borrador para revisión"),
    ("Fecha","(por confirmar)"),
    ("Clasificación","Confidencial")])
b.spacer(20); b.cover_logo(LOGO_FAN, width=2.9); b.page_break()

# =============== FRONT MATTER ===============
fm("Control de versiones")
b.table(["Versión","Fecha","Autor","Descripción"],
        [["1.0","(fecha)","Equipo SAP BUILD","Versión inicial: campos, modelo destino y propuestas de carga"],
         ["2.0","(fecha)","Equipo SAP BUILD","Consumo en Power BI/SAC; integración del real desde S/4HANA (Real vs. Presupuesto); propuesta recomendada"]],
        widths=[0.8,1.1,1.6,3.1])
fm("Documentos relacionados")
b.table(["ID","Documento","Ubicación"],
        [["DOC-01","Documento de Diseño de Solución — SAC (Fanalca, Ciudad Limpia, Transprensa)","(repositorio)"],
         ["DOC-02","Archivo fuente: Campos para cargar presupuestos comerciales.xlsx","(adjunto)"]],
        widths=[0.7,4.1,1.8])
fm("Contenido"); b.toc(); b.page_break()

# =============== 1. OBJETIVO ===============
b.h1("Objetivo y alcance")
b.para("Definir, a nivel funcional, cómo cargar el presupuesto comercial de las sociedades del Grupo "
       "Fanalca en SAP Datasphere y cómo integrar los datos reales desde SAP S/4HANA, de modo que se "
       "puedan generar reportes de ejecución (Real) frente al Presupuesto. El consumo de la información se "
       "realiza en Power BI o en SAP Analytics Cloud (SAC). Adicionalmente, se presentan varias propuestas "
       "de carga del archivo y una propuesta recomendada (mejor opción).")
b.para("Alcance. Cubre: la arquitectura general; la descripción del origen (campos y aplicabilidad por "
       "sociedad); la integración del real desde S/4HANA; el modelo de datos destino (presupuesto, real y "
       "vista Real vs. Presupuesto); las opciones de carga del archivo con sus flujogramas; la propuesta "
       "recomendada; y el consumo en Power BI o SAC.", size=9.5)

# =============== 2. ARQUITECTURA GENERAL ===============
b.h1("Arquitectura general")
b.para("La solución integra dos fuentes en SAP Datasphere: el presupuesto comercial (desde el archivo) y "
       "los datos reales (desde SAP S/4HANA). Ambos se materializan como tablas en un mismo Space y se "
       "combinan en una vista analítica «Real vs. Presupuesto», alineada por sociedad, periodo y "
       "dimensiones comunes. El consumo se realiza indistintamente en Power BI o en SAP Analytics Cloud, lo "
       "que permite generar los reportes de real frente a presupuesto.")
fig("arch_e2e.png", 1, "Arquitectura end-to-end: presupuesto (archivo) y real (S/4HANA) → Real vs. Presupuesto → Power BI o SAC.")

# =============== 3. ORIGEN ===============
b.h1("Descripción del origen: el presupuesto comercial")
b.para("El archivo fuente define los campos del presupuesto comercial y su aplicabilidad por sociedad y "
       "línea de negocio mediante una matriz que marca con «x» cada campo que aplica a cada organización. "
       "Las organizaciones son: Fanalca (Autos Nuevos y Usados, Autos Servicios/Repuestos, Motos, Motos "
       "Repuestos, Tubos, Defensas, Carrocerías, Autopartes), Metalsur, CGS, RH, Ciudad Limpia (las 3) y "
       "Transprensa. Cada registro combina dimensiones (canal, sector, cliente, material, vendedor, etc.) "
       "más el periodo (Año y Mes) y las medidas Cantidad y Valor.")
b.h2("Campos del presupuesto comercial")
FIELDS=[
 ("Sociedad","Clave / Dimensión","Texto","Sociedad o compañía del Grupo.","Todas (13 de 13)"),
 ("Organización de ventas","Clave / Dimensión","Texto","Línea de negocio dentro de la sociedad.","Todas (13 de 13)"),
 ("Canal","Dimensión","Texto","Canal de distribución de la venta.",aptext("Canal")),
 ("Sector","Dimensión","Texto","Sector / división del negocio.",aptext("Sector")),
 ("Oficina de ventas","Dimensión","Texto","Oficina de ventas responsable.",aptext("Oficina de ventas")),
 ("FI Centro de beneficios","Dimensión","Texto","Centro de beneficio (Profit Center) contable.",aptext("FI Centro de beneficios")),
 ("Grupo de vendedores","Dimensión","Texto","Agrupación de vendedores.",aptext("Grupo de vendedores")),
 ("Vendedor","Dimensión","Texto","Vendedor responsable.",aptext("Vendedor")),
 ("Cliente","Dimensión","Texto","Cliente.",aptext("Cliente")),
 ("Grupo de clientes","Dimensión","Texto","Grupo / segmento de clientes.",aptext("Grupo de clientes (todos)")),
 ("Sucursal cliente","Dimensión","Texto","Sucursal del cliente.",aptext("Sucursal cliente")),
 ("Material","Dimensión","Texto","Material / producto.",aptext("Material")),
 ("Grupo de materiales","Dimensión","Texto","Grupo de materiales.",aptext("Grupo de materiales (todos)")),
 ("Jerarquía de materiales","Dimensión","Texto","Nivel de la jerarquía de materiales.",aptext("Jerarquía de materiales")),
 ("Familia (clasificación MM)","Dimensión","Texto","Familia del material (sistema de clasificación).","Casos puntuales"),
 ("Línea (clasificación MM)","Dimensión","Texto","Línea del material (Tubos, Defensas, Metalsur).","Solo Tubos, Defensas, Metalsur"),
 ("Tipo de inventario (MM)","Dimensión","Texto","Diferencia usados, retomas y consignaciones.","Casos puntuales (por confirmar)"),
 ("Año","Clave / Tiempo","Entero","Año del presupuesto.",aptext("Año")),
 ("Mes","Clave / Tiempo","Entero","Mes del presupuesto (1–12).",aptext("Mes")),
 ("Cantidad","Medida","Decimal","Cantidad presupuestada.",aptext("Cantidad")),
 ("Unidad de medida","Atributo","Texto","Unidad de medida (p. ej. Kilos) para las líneas que lo requieren.",aptext("Unidad de medida Kilos (Tubos-Defensas-Metalsur-Autopartes)")),
 ("Valor $","Medida","Decimal","Valor monetario presupuestado (COP).",aptext("Valor $")),
]
b.table(["Campo","Rol","Tipo","Descripción","Aplicabilidad"],
        [[a,b_,c,d,e] for (a,b_,c,d,e) in FIELDS], widths=[1.7,1.1,0.8,2.0,1.0], size=8.2)
b.para("Nota: la aplicabilidad se derivó de la matriz del archivo fuente; el detalle completo por "
       "organización se conserva en dicho archivo (DOC-02).", italic=True, size=9, color=GREY)

# =============== 4. REAL DESDE S/4HANA ===============
b.h1("Integración de datos reales desde SAP S/4HANA")
b.para("Para comparar la ejecución contra el presupuesto, los datos reales se integran desde SAP S/4HANA "
       "hacia SAP Datasphere. La ingesta se realiza mediante una conexión a S/4HANA y un Replication Flow "
       "(o Data Flow) que extrae la información financiera/comercial —por ejemplo, desde el documento "
       "contable (ACDOCA) o desde vistas CDS analíticas habilitadas para extracción vía ODP/CDS—. El real "
       "se materializa como una «Tabla Real» en el mismo Space del presupuesto.")
b.table(["Modo de integración","Descripción","Cuándo usarlo"],
        [["Replicación (Replication Flow)","Copia programada de los datos a una tabla en Datasphere (snapshot o delta).","Recomendado: mejor desempeño y desacople de S/4HANA para el reporte."],
         ["Federación (vista remota)","Acceso en tiempo real a S/4HANA sin persistir los datos.","Cuando se requiere el dato más reciente y el volumen/latencia lo permiten."]],
        widths=[1.7,2.9,2.0], size=8.4)
b.callout("Requisitos y armonización", [
    "Conexión a S/4HANA (con SAP Cloud Connector si es on-premise) y autorizaciones de extracción.",
    "Vistas CDS habilitadas para extracción (ODP) o acceso a las tablas/vistas del real.",
    "Armonizar las dimensiones comunes entre real y presupuesto —sociedad, periodo (año/mes) y las llaves "
    "de negocio pertinentes (cuenta, material, cliente, centro)— para el comparativo.",
], accent=RED, fill="FDECEA")

# =============== 5. MODELO DESTINO ===============
b.h1("Modelo de datos destino en SAP Datasphere")
b.para("En el Space se definen dos tablas —Presupuesto y Real— con dimensiones y medidas armonizadas, y "
       "una vista analítica que las combina para el reporte Real vs. Presupuesto. La dimensión «Versión» "
       "distingue el origen (Presupuesto / Real).")
b.h2("Tabla de Presupuesto (desde el archivo)")
b.table(["Columna","Tipo (Datasphere)","Rol","Clave"],
        [["SOCIEDAD","NVARCHAR(20)","Dimensión","Sí"],
         ["ORGANIZACION_VENTAS","NVARCHAR(40)","Dimensión","Sí"],
         ["ANIO / MES","INTEGER","Tiempo","Sí"],
         ["CANAL / SECTOR / OFICINA_VENTAS …","NVARCHAR","Dimensión","—"],
         ["CLIENTE / MATERIAL / VENDEDOR …","NVARCHAR","Dimensión","—"],
         ["FAMILIA / LINEA / TIPO_INVENTARIO","NVARCHAR","Dimensión","—"],
         ["UNIDAD_MEDIDA","NVARCHAR(10)","Atributo","—"],
         ["CANTIDAD / VALOR","DECIMAL","Medida","—"],
         ["VERSION","NVARCHAR(20)","Control = «Presupuesto»","—"],
         ["FECHA_CARGA / ORIGEN","TIMESTAMP / NVARCHAR","Auditoría","—"]],
        widths=[2.9,1.4,1.5,0.8], size=8.2)
b.h2("Tabla de Real (desde S/4HANA) y vista Real vs. Presupuesto")
b.para("La Tabla Real replica del real las mismas dimensiones comunes y las medidas Cantidad y Valor "
       "(VERSION = «Real»). La vista «Real vs. Presupuesto» combina ambas tablas por sociedad, periodo y "
       "dimensiones comunes, y expone las medidas Real, Presupuesto y su Variación ($ y %).", size=9.5)
b.callout("Vista Real vs. Presupuesto", [
    "Entrada: Tabla Presupuesto (VERSION=Presupuesto) + Tabla Real (VERSION=Real).",
    "Combinación por: Sociedad, Año, Mes y las dimensiones comunes armonizadas.",
    "Salida: medidas Real, Presupuesto, Variación ($) = Real − Presupuesto, y Variación (%).",
], accent=NAVY2)

# =============== 6. OPCIONES DE CARGA ===============
b.h1("Opciones de carga del archivo a SAP Datasphere")
b.para("Se presentan cuatro opciones para llevar el archivo del presupuesto a Datasphere. Todas desembocan "
       "en la Tabla Presupuesto del Space, que luego se combina con la Tabla Real. La figura resume las "
       "opciones; la sección siguiente detalla la opción recomendada.")
fig("p0_overview.png", 2, "Opciones de carga del archivo del presupuesto (todas desembocan en Datasphere → Power BI/SAC).")

b.h2("Propuesta 1 — Carga manual (Import CSV a tabla local)")
b.para("El negocio exporta el archivo a CSV (UTF-8) y lo importa desde el Data Builder de Datasphere a una "
       "tabla local, sobre la que se crea la vista analítica.")
fig("p1_manual.png", 3, "Propuesta 1 — Carga manual mediante importación de CSV.")
b.bullets(["Exportar la hoja del presupuesto a CSV (UTF-8) con encabezados normalizados.",
           "En Data Builder: «Importar tabla local desde archivo CSV» y mapear columnas/tipos.",
           "Crear la vista analítica y combinarla con la Tabla Real."])
b.callout("Cuándo usarla", "Cargas puntuales, piloto o primera carga; volumen bajo; sin automatización. "
          "Ventaja: rápida, sin infraestructura. Limitación: manual, no automatizable, requiere Excel→CSV.",
          accent=GREEN, fill="EAF3E6")

b.h2("Propuesta 2 — Almacenamiento en la nube + Replication/Data Flow")
b.para("El archivo (CSV/Parquet) se deposita en un almacenamiento de objetos en la nube (Amazon S3, Azure "
       "Blob, Google Cloud Storage o SFTP). En Datasphere se crea una conexión a ese almacenamiento y un "
       "Replication/Data Flow programado que ingiere el/los archivo(s) a la Tabla Presupuesto.")
fig("p2_cloudstorage.png", 4, "Propuesta 2 — Almacenamiento en la nube + Replication/Data Flow.")
b.bullets(["Definir una convención de nombres/carpetas por sociedad, año y mes.",
           "Crear la conexión de almacenamiento en Datasphere (credenciales gobernadas por TI).",
           "Construir el flujo y programarlo (carga por periodo, append/upsert)."])
b.callout("Cuándo usarla", "Carga recurrente y productiva. Es la base de la propuesta recomendada (ver "
          "sección siguiente).", accent=NAVY2, fill="EAF1FB")

b.h2("Propuesta 3 — Open SQL Schema + carga programática (Python)")
b.para("Se habilita un Open SQL Schema (usuario de base de datos) en el Space. Un script de Python lee el "
       "Excel con pandas, valida y normaliza (aplicabilidad y pivoteo de meses) y carga con hdbcli / "
       "hana_ml (o JDBC/ODBC) en una tabla que se expone al Space.")
fig("p3_opensql.png", 5, "Propuesta 3 — Open SQL Schema con carga programática en Python.")
b.bullets(["Crear el usuario/esquema Open SQL con permisos mínimos.",
           "Desarrollar el script: lectura, validaciones, normalización y carga.",
           "Programar la ejecución (job/CI) y exponer la tabla; crear la vista."])
b.callout("Cuándo usarla", "Cuando hay capacidad de desarrollo y se requieren validaciones/transformación "
          "o integración con otros procesos. Ventaja: control total. Requiere: desarrollo y gobierno de "
          "credenciales.", accent=GREEN, fill="EAF3E6")

b.h2("Propuesta 4 — SAP Integration Suite / ETL (empresarial)")
b.para("Una plataforma de integración (SAP Integration Suite — iFlow, o una herramienta ETL como SAP Data "
       "Intelligence o de un socio) orquesta la toma del archivo y su carga en Datasphere, con monitoreo y "
       "reintentos.")
fig("p4_integrationsuite.png", 6, "Propuesta 4 — Orquestación con SAP Integration Suite / ETL.")
b.bullets(["Construir el iFlow / pipeline que lea y transforme el archivo.",
           "Cargar en Datasphere (Open SQL u Object Store) con manejo de errores.",
           "Monitorear la ejecución desde la plataforma."])
b.callout("Cuándo usarla", "Paisajes con integración corporativa establecida y necesidad de "
          "orquestación/monitoreo centralizados. Requiere: plataforma, licencias y equipo especializado.",
          accent=GREEN, fill="EAF3E6")

# =============== 7. PROPUESTA RECOMENDADA ===============
b.h1("Propuesta recomendada (mejor opción)")
b.para("Con base en las capacidades de SAP Datasphere y en las características de este caso —archivo "
       "propiedad del negocio, carga periódica (mensual/anual) y necesidad de convivir con el real de "
       "S/4HANA—, la mejor opción para cargar el archivo es el almacenamiento en la nube (SFTP u Object "
       "Store) combinado con un Data Flow (o Replication Flow) programado en Datasphere.")
fig("recomendada.png", 7, "Propuesta recomendada — Almacenamiento en la nube + Data Flow programado, integrado con el real.")
b.h2("Por qué es la mejor opción")
b.bullets(["File-based: el negocio conserva la propiedad del archivo (Excel→CSV) y solo lo deposita; no hay paso manual en la interfaz cada periodo.",
           "Automatizable y programable: se ajusta al ciclo mensual/anual y deja trazabilidad de cada carga.",
           "Un Data Flow permite validar y normalizar (aplicabilidad por sociedad, pivoteo de meses); un Replication Flow basta si el CSV ya viene normalizado.",
           "Convive naturalmente con el real de S/4HANA: ambos son tablas del mismo Space, listas para la vista Real vs. Presupuesto.",
           "Menor costo y complejidad que una plataforma de integración completa, y menos propenso a error que la carga manual."])
b.h2("Pasos de implementación")
b.table(["#","Paso","Detalle"],
        [["1","Convención de archivos","Nombrar los archivos por sociedad/año/mes, p. ej. PPTO_COM_<sociedad>_<AAAA>_<MM>.csv."],
         ["2","Almacenamiento","Aprovisionar SFTP u Object Store (S3 / Azure Blob / GCS) y sus credenciales (gobernadas por TI)."],
         ["3","Conexión","Crear la conexión de almacenamiento en SAP Datasphere."],
         ["4","Data Flow","Origen archivo → validaciones (tipos, catálogos, aplicabilidad) → normalización (pivotear meses si el archivo es ancho) → Tabla Presupuesto (VERSION = «Presupuesto»)."],
         ["5","Programación y recarga","Programar por periodo y definir la estrategia de recarga (reemplazo por sociedad/periodo o upsert) para evitar duplicados."],
         ["6","Vista Real vs. Presupuesto","Combinar la Tabla Presupuesto con la Tabla Real (S/4HANA) por sociedad, periodo y dimensiones comunes."],
         ["7","Consumo","Exponer la vista y conectar el consumo en Power BI o SAC."]],
        widths=[0.5,1.9,4.2], size=8.4)
b.callout("Cuándo optar por otra opción", "Si la lógica de validación/normalización es muy compleja o se "
          "requiere integración con otros procesos, usar la Propuesta 3 (Open SQL + Python). Para la "
          "primera carga o un piloto rápido, la Propuesta 1 (carga manual).", accent=NAVY2)

# =============== 8. CONSUMO ===============
b.h1("Consumo y reportes: Real vs. Presupuesto en Power BI o SAC")
b.para("La vista «Real vs. Presupuesto» de Datasphere se consume desde Power BI o desde SAP Analytics "
       "Cloud, según la herramienta que use cada área. El reporte compara Real y Presupuesto por sociedad, "
       "periodo y dimensiones comunes, con la variación en $ y %.")
b.table(["Herramienta","Método de conexión","Uso"],
        [["Power BI","Conector de Power BI para SAP Datasphere (o conector de SAP HANA sobre el endpoint SQL/Open SQL del Space, o vía OData).","Informes y dashboards de Real vs. Presupuesto."],
         ["SAP Analytics Cloud (SAC)","Conexión en vivo (live) al modelo/vista de Datasphere.","Historias y análisis reutilizando el modelo semántico."]],
        widths=[1.5,3.3,1.8], size=8.4)
b.callout("Beneficio", "Al centralizar presupuesto y real en Datasphere y exponer una única vista, ambos "
          "consumos (Power BI y SAC) usan la misma definición de negocio, evitando discrepancias entre "
          "reportes.", accent=NAVY2)

# =============== 9. COMPARACIÓN ===============
b.h1("Comparación de las opciones de carga")
b.table(["Criterio","P1 Manual","P2 Cloud Storage","P3 Open SQL + Python","P4 Integration Suite"],
        [["Automatización","Baja (manual)","Alta (programada)","Alta (job/CI)","Alta (orquestada)"],
         ["Volumen soportado","Bajo","Medio-alto","Medio-alto","Alto"],
         ["Esfuerzo de implementación","Muy bajo","Medio","Medio-alto","Alto"],
         ["Infraestructura adicional","Ninguna","Almacenamiento en la nube","Usuario de BD / Python","Plataforma de integración"],
         ["Validación / transformación","Manual","En el flujo","En el script (alta)","En el iFlow (alta)"],
         ["Gobierno / monitoreo","Limitado","Bueno","Medio","Muy bueno"],
         ["Recomendado para","Piloto / puntual","Operación recurrente ★","Integración con validaciones","Paisaje corporativo"]],
        widths=[1.5,1.2,1.3,1.4,1.2], size=8.0)
b.para("★ La Propuesta 2 es la base de la opción recomendada para la operación recurrente.", italic=True, size=9, color=GREY)

# =============== 10. CONSIDERACIONES ===============
b.h1("Consideraciones")
b.table(["Tema","Recomendación"],
        [["Armonización real/presupuesto","Alinear sociedad, periodo y llaves comunes (cuenta, material, cliente, centro) para el comparativo Real vs. Presupuesto."],
         ["Modo de integración del real","Preferir replicación (desempeño y desacople); usar federación si se necesita el dato en tiempo real."],
         ["Calidad del dato","Validar catálogos y tipos antes de cargar; registrar/rechazar filas inválidas."],
         ["Aplicabilidad por sociedad","Poblar solo los campos que aplican a cada organización (según la matriz); documentar excepciones."],
         ["Periodicidad y recarga","Definir la frecuencia y la estrategia de recarga (reemplazo por periodo o upsert) para evitar duplicados."],
         ["Seguridad","Gobernar credenciales de conexiones/usuarios; aplicar control de acceso por Space y por dato en Datasphere."],
         ["Consumo dual","Exponer una única vista para que Power BI y SAC usen la misma definición de negocio."]],
        widths=[1.8,4.8], size=8.5)

# =============== 11. PASOS SIGUIENTES ===============
b.h1("Pasos siguientes")
b.bullets(["Confirmar la opción de carga (recomendada: almacenamiento en la nube + Data Flow programado).",
           "Configurar la integración del real desde S/4HANA (conexión + Replication Flow).",
           "Cerrar el modelo de datos destino (tablas Presupuesto y Real, y sus dimensiones comunes).",
           "Definir la convención de archivos y el calendario de carga.",
           "Construir la Tabla Presupuesto, la Tabla Real y la vista Real vs. Presupuesto.",
           "Ejecutar cargas de prueba y conciliar contra el archivo y contra S/4HANA.",
           "Conectar el consumo en Power BI y/o SAC."])

# =============== 12. REFERENCIAS ===============
b.h1("Referencias")
b.bullets(["Archivo fuente: «Campos para cargar presupuestos comerciales.xlsx» (matriz de campos por sociedad).",
           "SAP Datasphere: importación de CSV a tabla local; conexiones de almacenamiento en la nube; Replication Flows y Data Flows; Open SQL Schema / acceso a la base de datos del Space.",
           "SAP Datasphere: integración con SAP S/4HANA (Replication Flow, extracción CDS/ODP, SAP Cloud Connector).",
           "Conector de Microsoft Power BI para SAP Datasphere; conexión en vivo de SAP Analytics Cloud a Datasphere."])

fn=os.path.join(HERE,'Documento_Funcional_Carga_Presupuesto_Comercial_Datasphere.docx')
b.save(fn); print("GUARDADO:", fn)
