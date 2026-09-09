# -*- coding: utf-8 -*-
"""Documento Funcional: Carga del Presupuesto Comercial a SAP Datasphere.
Incluye detalle de campos (derivado del archivo fuente), modelo de datos destino,
4 propuestas de carga con flujogramas de arquitectura, comparación y recomendación."""
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
SRC=os.path.join(HERE,'..','..','..','..','..','tmp','claude-0','-home-user-Johnmeg',
                 '75057f83-9833-5a60-bea8-f642bffd6fbf','scratchpad','in','campos.xlsx')
SRC="/tmp/claude-0/-home-user-Johnmeg/75057f83-9833-5a60-bea8-f642bffd6fbf/scratchpad/in/campos.xlsx"

# ---- derivar aplicabilidad del archivo fuente ----
ws=load_workbook(SRC, data_only=True)["Campos presupuesto comercial"]
ORGS={2:"Autos N&U",3:"Autos Serv/Rep",4:"Motos",5:"Motos Rep.",6:"Tubos",7:"Defensas",
      8:"Carrocerías",9:"Autopartes",10:"Metalsur",11:"CGS",12:"RH",13:"Ciudad Limpia",14:"Transprensa"}
def applic(rowlabel):
    for r in range(3, ws.max_row+1):
        if ws.cell(r,1).value==rowlabel:
            orgs=[ORGS[c] for c in range(2,15) if str(ws.cell(r,c).value).strip().lower()=="x"]
            return orgs
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
def fig(name, n, desc):
    b.figure(os.path.join(IMG,name), f"Figura {n}. {desc}")

# =============== PORTADA ===============
b.spacer(30); b.cover_logo(LOGO_BUILD, width=3.0); b.spacer(16)
b.cover_title([
    ("DOCUMENTO FUNCIONAL", 22, BLUE_D, True, 4),
    ("Carga del Presupuesto Comercial a SAP Datasphere", 15, NAVY, False, 3),
    ("Detalle de campos · Propuestas de arquitectura de carga", 12, NAVY, False, 2),
    ("Programa SAP BUILD · Grupo Fanalca", 11, GREY, False, 20)])
b.meta_table([
    ("Objeto","Carga del presupuesto comercial (multi-sociedad) a SAP Datasphere"),
    ("Origen","Archivo Excel «Campos para cargar presupuestos comerciales»"),
    ("Destino","SAP Datasphere (tabla local + vista) · consumo en SAP Analytics Cloud"),
    ("Sociedades","Fanalca (8 líneas) · Metalsur · CGS · RH · Ciudad Limpia · Transprensa"),
    ("Versión","1.0 — Borrador para revisión"),
    ("Fecha","(por confirmar)"),
    ("Clasificación","Confidencial")])
b.spacer(24); b.cover_logo(LOGO_FAN, width=2.9); b.page_break()

# =============== FRONT MATTER ===============
fm("Control de versiones")
b.table(["Versión","Fecha","Autor","Descripción"],
        [["1.0","(fecha)","Equipo SAP BUILD","Versión inicial: campos, modelo destino y propuestas de carga"]],
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
       "Fanalca en SAP Datasphere, a partir del archivo de detalle de campos, y presentar varias "
       "propuestas de arquitectura para llevar ese archivo directamente a SAP Datasphere, con sus "
       "ventajas, limitaciones y una recomendación.")
b.para("Alcance. Cubre la descripción del origen (campos y aplicabilidad por sociedad), el modelo de datos "
       "destino en Datasphere, y cuatro opciones de carga (manual, almacenamiento en la nube, esquema Open "
       "SQL y orquestación con Integration Suite). El consumo posterior (modelos y reportes) se realiza en "
       "SAP Analytics Cloud y se aborda en el documento de diseño (DOC-01).", size=9.5)

# =============== 2. ORIGEN ===============
b.h1("Descripción del origen: el presupuesto comercial")
b.para("El archivo fuente define los campos del presupuesto comercial y su aplicabilidad por sociedad y "
       "línea de negocio, mediante una matriz en la que se marca con «x» cada campo que aplica a cada "
       "organización. Las organizaciones son: Fanalca (Autos Nuevos y Usados, Autos Servicios/Repuestos, "
       "Motos, Motos Repuestos, Tubos, Defensas, Carrocerías, Autopartes), Metalsur, CGS, RH, Ciudad Limpia "
       "(las 3) y Transprensa.")
b.callout("Naturaleza del dato", [
    "El presupuesto comercial se compone de registros con una combinación de dimensiones (canal, sector, "
    "cliente, material, vendedor, etc.) más el periodo (Año y Mes) y las medidas Cantidad y Valor.",
    "No todos los campos aplican a todas las organizaciones: la matriz del archivo indica la aplicabilidad. "
    "El modelo destino contempla todos los campos y se poblan según corresponda a cada sociedad.",
], accent=NAVY2)

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
        [[a,b_,c,d,e] for (a,b_,c,d,e) in FIELDS],
        widths=[1.7,1.1,0.8,2.0,1.0], size=8.2)
b.para("Nota: la aplicabilidad se derivó de la matriz del archivo fuente. El detalle completo por "
       "organización se conserva en dicho archivo (DOC-02).", italic=True, size=9, color=GREY)

# =============== 3. MODELO DESTINO ===============
b.h1("Modelo de datos destino en SAP Datasphere")
b.para("Se propone una tabla local (de hechos) en el Space de Datasphere que contenga todas las "
       "dimensiones y medidas, más columnas de control. Los campos no aplicables a una organización quedan "
       "vacíos. Sobre la tabla se construye una vista analítica para el consumo en SAC.")
b.table(["Columna","Tipo (Datasphere)","Rol","Clave"],
        [["SOCIEDAD","NVARCHAR(20)","Dimensión","Sí"],
         ["ORGANIZACION_VENTAS","NVARCHAR(40)","Dimensión","Sí"],
         ["ANIO","INTEGER","Tiempo","Sí"],
         ["MES","INTEGER","Tiempo","Sí"],
         ["CANAL / SECTOR / OFICINA_VENTAS","NVARCHAR","Dimensión","—"],
         ["CENTRO_BENEFICIO / GRUPO_VENDEDORES / VENDEDOR","NVARCHAR","Dimensión","—"],
         ["CLIENTE / GRUPO_CLIENTES / SUCURSAL_CLIENTE","NVARCHAR","Dimensión","—"],
         ["MATERIAL / GRUPO_MATERIALES / JERARQUIA_MATERIALES","NVARCHAR","Dimensión","—"],
         ["FAMILIA / LINEA / TIPO_INVENTARIO","NVARCHAR","Dimensión","—"],
         ["UNIDAD_MEDIDA","NVARCHAR(10)","Atributo","—"],
         ["CANTIDAD","DECIMAL(23,3)","Medida","—"],
         ["VALOR","DECIMAL(23,2)","Medida","—"],
         ["VERSION","NVARCHAR(20)","Control (p. ej. «Comercial»)","—"],
         ["FECHA_CARGA / ORIGEN","TIMESTAMP / NVARCHAR","Control / auditoría","—"]],
        widths=[2.9,1.4,1.4,0.9], size=8.2)
b.callout("Granularidad y clave", "El grano del registro es la combinación de todas las dimensiones "
          "informadas más Año y Mes. Se recomienda una clave técnica (ID) o la combinación "
          "Sociedad + Organización + Año + Mes + dimensiones para evitar duplicados en las recargas.",
          accent=NAVY2)

# =============== 4. OPCIONES DE CARGA ===============
b.h1("Opciones de carga a SAP Datasphere")
b.para("A continuación se presentan cuatro propuestas para llevar el archivo directamente a SAP "
       "Datasphere. Todas desembocan en una tabla y una vista dentro del Space, listas para el consumo en "
       "SAC. La figura siguiente resume las opciones.")
fig("p0_overview.png", 1, "Opciones de arquitectura para cargar el presupuesto comercial a SAP Datasphere.")

b.h2("Propuesta 1 — Carga manual (Import CSV a tabla local)")
b.para("El negocio exporta el archivo a CSV (UTF-8) y lo importa desde el Data Builder de Datasphere a una "
       "tabla local, sobre la que se crea la vista analítica.")
fig("p1_manual.png", 2, "Propuesta 1 — Carga manual mediante importación de CSV.")
b.bullets(["Exportar la hoja del presupuesto a CSV (UTF-8) con encabezados normalizados.",
           "En Data Builder: «Importar tabla local desde archivo CSV» y mapear columnas/tipos.",
           "Crear la vista analítica (definir medidas y atributos) y exponerla para consumo."])
b.callout("Cuándo usarla", "Cargas puntuales, piloto o primera carga; volumen bajo; sin necesidad de "
          "automatización. Ventaja: rápida, sin infraestructura. Limitación: manual, no automatizable, "
          "requiere convertir Excel→CSV.", accent=GREEN, fill="EAF3E6")

b.h2("Propuesta 2 — Almacenamiento en la nube + Replication Flow (recomendada)")
b.para("El archivo (convertido a CSV o Parquet) se deposita en un almacenamiento de objetos en la nube "
       "(Amazon S3, Azure Blob, Google Cloud Storage o SFTP). En Datasphere se crea una conexión a ese "
       "almacenamiento y un Replication Flow (o Data Flow) programado que ingiere el/los archivo(s) a la "
       "tabla local.")
fig("p2_cloudstorage.png", 3, "Propuesta 2 — Almacenamiento en la nube + Replication Flow (recomendada).")
b.bullets(["Definir una convención de nombres/carpetas por sociedad, año y mes.",
           "Crear la conexión de almacenamiento en Datasphere (credenciales gobernadas por TI).",
           "Construir el Replication/Data Flow y programarlo (carga por periodo, append/upsert).",
           "Publicar la tabla y la vista analítica para consumo."])
b.callout("Cuándo usarla", "Carga recurrente (mensual/anual) y productiva. Ventaja: automatizable, "
          "programada, mayor volumen y trazabilidad; separa la responsabilidad (el negocio deposita el "
          "archivo, Datasphere lo ingiere). Requiere: servicio de almacenamiento y su configuración.",
          accent=NAVY2, fill="EAF1FB")

b.h2("Propuesta 3 — Open SQL Schema + carga programática (Python)")
b.para("Se habilita un Open SQL Schema (usuario de base de datos) en el Space. Un script de Python lee el "
       "Excel con pandas, valida y normaliza (incluida la lógica de la matriz de aplicabilidad y el pivoteo "
       "de meses), y carga los datos con hdbcli / hana_ml (o JDBC/ODBC) en una tabla que se expone al "
       "Space.")
fig("p3_opensql.png", 4, "Propuesta 3 — Open SQL Schema con carga programática en Python.")
b.bullets(["Crear el usuario/esquema Open SQL y otorgar los permisos mínimos necesarios.",
           "Desarrollar el script Python: lectura, validaciones (tipos, catálogos), normalización y carga.",
           "Programar la ejecución (job/CI) y exponer la tabla al Space; crear la vista analítica."])
b.callout("Cuándo usarla", "Cuando hay capacidad de desarrollo y se requieren validaciones o "
          "transformación en la carga, o integración con otros procesos. Ventaja: control total e "
          "integrable. Requiere: desarrollo y gobierno de credenciales.", accent=GREEN, fill="EAF3E6")

b.h2("Propuesta 4 — SAP Integration Suite / ETL (empresarial)")
b.para("Una plataforma de integración (SAP Integration Suite — iFlow, o una herramienta ETL como SAP Data "
       "Intelligence o de un socio) orquesta la toma del archivo y su carga en Datasphere (vía Open SQL u "
       "Object Store), con monitoreo y reintentos.")
fig("p4_integrationsuite.png", 5, "Propuesta 4 — Orquestación con SAP Integration Suite / ETL.")
b.bullets(["Construir el iFlow / pipeline que lea el archivo y lo transforme.",
           "Cargar en Datasphere (Open SQL u Object Store) con manejo de errores y reintentos.",
           "Monitorear la ejecución desde la plataforma de integración."])
b.callout("Cuándo usarla", "Paisajes con integración corporativa ya establecida y necesidad de "
          "orquestación/monitoreo centralizados. Ventaja: gobierno y robustez. Requiere: plataforma, "
          "licencias y equipo especializado.", accent=GREEN, fill="EAF3E6")

# =============== 5. COMPARACIÓN ===============
b.h1("Comparación de propuestas y recomendación")
b.table(["Criterio","P1 Manual","P2 Cloud Storage","P3 Open SQL + Python","P4 Integration Suite"],
        [["Automatización","Baja (manual)","Alta (programada)","Alta (job/CI)","Alta (orquestada)"],
         ["Volumen soportado","Bajo","Medio-alto","Medio-alto","Alto"],
         ["Esfuerzo de implementación","Muy bajo","Medio","Medio-alto","Alto"],
         ["Infraestructura adicional","Ninguna","Almacenamiento en la nube","Usuario de BD / entorno Python","Plataforma de integración"],
         ["Validación / transformación","Manual","En el flujo","En el script (alta)","En el iFlow (alta)"],
         ["Gobierno / monitoreo","Limitado","Bueno","Medio","Muy bueno"],
         ["Recomendado para","Piloto / cargas puntuales","Operación recurrente","Integración con validaciones","Paisaje corporativo"]],
        widths=[1.5,1.2,1.3,1.4,1.2], size=8.0)
b.callout("Recomendación", [
    "Para arrancar rápido y validar el modelo: Propuesta 1 (carga manual) como primera carga o piloto.",
    "Para la operación recurrente del presupuesto comercial: Propuesta 2 (Cloud Storage + Replication "
    "Flow), por su automatización, trazabilidad y bajo acoplamiento con el negocio.",
    "Si se requiere lógica de validación/normalización (matriz de aplicabilidad, pivoteo de meses) o "
    "integración con otros procesos: Propuesta 3 (Open SQL + Python).",
], accent=NAVY, icon="★")

# =============== 6. CONSIDERACIONES ===============
b.h1("Consideraciones")
b.table(["Tema","Recomendación"],
        [["Calidad del dato","Validar catálogos (sociedad, canal, material…) y tipos antes de cargar; rechazar/registrar filas inválidas."],
         ["Aplicabilidad por sociedad","Poblar solo los campos que aplican a cada organización (según la matriz); documentar las excepciones."],
         ["Periodicidad y recarga","Definir la frecuencia (mensual/anual) y la estrategia de recarga (reemplazo por periodo o upsert) para evitar duplicados."],
         ["Seguridad","Gobernar credenciales de conexiones/usuarios; aplicar control de acceso por Space y por dato en Datasphere."],
         ["Versionado","Marcar la versión (p. ej. «Comercial») y la fecha de carga para trazabilidad y comparaciones."],
         ["Convención de archivos","Nombrar los archivos por sociedad/año/mes para automatizar y auditar la ingesta (Propuestas 2 y 4)."]],
        widths=[1.7,4.9], size=8.6)

# =============== 7. PASOS SIGUIENTES ===============
b.h1("Pasos siguientes")
b.bullets(["Confirmar la propuesta a implementar (recomendada: P2 para operación; P1 para el piloto).",
           "Validar y cerrar el modelo de datos destino (tipos, claves, campos de control).",
           "Definir la convención de archivos y el calendario de carga.",
           "Construir la tabla, la conexión/flujo (o script) y la vista analítica en Datasphere.",
           "Ejecutar una carga de prueba y conciliar contra el archivo fuente.",
           "Conectar el consumo en SAP Analytics Cloud."])

# =============== 8. REFERENCIAS ===============
b.h1("Referencias")
b.bullets(["Archivo fuente: «Campos para cargar presupuestos comerciales.xlsx» (matriz de campos por sociedad).",
           "Documentación de SAP Datasphere: importación de CSV a tabla local; conexiones de almacenamiento en la nube; Replication Flows y Data Flows; Open SQL Schema / acceso a la base de datos del Space.",
           "Documentación de SAP Integration Suite (Cloud Integration) para la orquestación de cargas."])

fn=os.path.join(HERE,'Documento_Funcional_Carga_Presupuesto_Comercial_Datasphere.docx')
b.save(fn); print("GUARDADO:", fn)
