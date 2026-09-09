# -*- coding: utf-8 -*-
"""Especificación Funcional (Documento Funcional) DILIGENCIADA para TRANSPRENSA S.A.S.
Modelos de planeación (Ingresos, Costos/Gastos, EEFF) en SAP Analytics Cloud.
Contenido real levantado en las sesiones de transferencia de conocimiento."""
import sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'generador_diseno'))
from docx_helpers import Builder, NAVY, NAVY2, BLUE_D, RED, GREEN, GREY
from docx.shared import Pt, RGBColor

TPL=os.path.join(HERE,'template_funcional.docx')
LOGO_BUILD=os.path.join(HERE,'logos','build.png')
LOGO_FAN=os.path.join(HERE,'logos','fanalca.png')
IMG=os.path.join(HERE,'..','generador_diseno','img')

b=Builder(TPL); b.setup_headers(LOGO_FAN)
hp=b.doc.sections[0].header.paragraphs[0]
for r in hp.runs:
    if 'Documento de Diseño' in r.text:
        r.text='Especificación Funcional · Transprensa S.A.S. · SAP Analytics Cloud'
    elif 'Programa SAP BUILD' in r.text:
        r.text='\tPrograma SAP BUILD — Grupo Fanalca'

def fm(text):
    p=b.doc.add_paragraph()
    p.paragraph_format.space_before=Pt(10); p.paragraph_format.space_after=Pt(5)
    r=p.add_run(text); r.font.name='Arial'; r.font.size=Pt(13); r.font.bold=True
    r.font.color.rgb=RGBColor.from_string(BLUE_D); b._bottom_border(p); return p

# =====================================================================
# PORTADA
# =====================================================================
b.spacer(30)
b.cover_logo(LOGO_BUILD, width=3.0)
b.spacer(16)
b.cover_title([
    ("ESPECIFICACIÓN FUNCIONAL", 22, BLUE_D, True, 4),
    ("Modelos de Planeación Financiera — Transprensa S.A.S.", 14, NAVY, False, 3),
    ("Ingresos · Costos y Gastos · Estados Financieros en SAP Analytics Cloud", 11, NAVY, False, 2),
    ("Programa SAP BUILD · Grupo Fanalca", 11, GREY, False, 20),
])
b.meta_table([
    ("Sociedad", "Transprensa S.A.S. (logística y transporte de carga)"),
    ("Proceso", "Planeación financiera: Ingresos, Costos y Gastos, Estados Financieros"),
    ("Plataforma", "SAP Analytics Cloud (SAC) · SAP DataSphere · SAP S/4HANA · Silotrans"),
    ("Versión", "1.0 — Diligenciada"),
    ("Fecha", "(por confirmar)"),
    ("Estado", "Borrador para revisión y aprobación"),
    ("Clasificación", "Confidencial"),
])
b.spacer(26)
b.cover_logo(LOGO_FAN, width=2.9)
b.page_break()

# =====================================================================
# FRONT MATTER
# =====================================================================
fm("Control de versiones")
b.table(["Versión","Fecha","Autor","Descripción del cambio","Estado"],
        [["1.0","(fecha)","Equipo SAP BUILD","Versión inicial diligenciada para Transprensa","Borrador"]],
        widths=[0.8,1.0,1.4,2.6,0.8])
fm("Documentos relacionados")
b.table(["ID","Documento","Versión","Ubicación"],
        [["DOC-01","Documento de Diseño de Solución — SAC (Fanalca, Ciudad Limpia, Transprensa)","2.0","(repositorio)"],
         ["DOC-02","Plan de seguimiento de la configuración de SAC","1.0","(repositorio)"]],
        widths=[0.7,3.0,0.8,2.1])
fm("Contenido")
b.toc()
b.page_break()

# =====================================================================
# 1. INTRODUCCIÓN
# =====================================================================
b.h1("Introducción")
b.h2("Propósito del documento")
b.para("Este documento especifica, a nivel funcional, los tres modelos de planeación financiera "
       "—Ingresos, Costos y Gastos, y Estados Financieros— de Transprensa S.A.S. que se construyen en "
       "SAP Analytics Cloud (SAC). Traduce el proceso presupuestal actual de la compañía a requerimientos "
       "y reglas funcionales que el equipo de configuración implementará mediante modelos, plantillas de "
       "carga, Data Actions, versiones, reportes y seguridad. Complementa el Documento de Diseño de "
       "Solución (DOC-01) con el nivel de detalle necesario para construir, probar y aceptar la solución.")

b.h2("Alcance funcional")
b.table(["Incluye","Excluye"],
        [["Modelos de Ingresos, Costos/Gastos y EEFF; carga del plan por plantillas; cálculo P×Q y de "
          "costos por Data Actions; integración del histórico desde Silotrans y del real desde S/4HANA "
          "(vía DataSphere); versiones (Comercial, Financiero, Forecast); reportes y dashboards por "
          "regional y servicio; seguridad por Data Access Control.",
          "Modelo de Talento Humano y Flujo de Caja diario (en diseño); cierre contable y ejecución "
          "transaccional (permanecen en el ERP); presupuestación cliente por cliente (se presupuesta por "
          "regional y por negocio, no por cliente, salvo los negocios especiales)."]],
        widths=[3.3,3.3])

b.h2("Audiencia")
b.para("Dirigido al equipo funcional y de configuración de SAC, al área de Planeación Financiera de "
       "Transprensa, a la Gerencia y Gerencia Comercial (validación de reglas), y al equipo de pruebas "
       "(UAT).", size=9.5)

b.h2("Definiciones, acrónimos y glosario")
b.table(["Término / Acrónimo","Definición"],
        [["P×Q","Precio × Cantidad: ingreso = tarifa (pesos/kg) × kilogramos."],
         ["CRM","Centro de Recibo de Mercancía (punto físico de recepción); Transprensa opera 46. No es «Customer Relationship Management»."],
         ["Silotrans / Silotrack","Software logístico: kilogramos, remesas, tarifas y ventas por CRM."],
         ["ICTC","Índice de Costos del Transporte de Carga (combustible, salario mínimo, inflación)."],
         ["N-1","Año anterior; base histórica (2025) para proyectar el presupuesto."],
         ["CIES / SIESA","Sistemas legados de nómina (CIES) y contabilidad (SIESA)."],
         ["Data Action","Proceso de cálculo en SAC (Advanced Formulas / Cross-Model Copy)."],
         ["DAC","Data Access Control: control de acceso a datos por dimensión (p. ej. Sociedad/Regional)."],
         ["PCGA","Principios de Contabilidad Generalmente Aceptados (base del P&G administrativo)."]],
        widths=[1.5,5.1])

b.h2("Supuestos y restricciones")
b.table(["ID","Supuesto / Restricción","Impacto si no se cumple"],
        [["SUP-01","Los 3 modelos, sus dimensiones y la vinculación con SAP DataSphere ya están configurados (base).","Retraso en la fase de construcción."],
         ["SUP-02","El histórico 2025 (kilogramos y pesos por regional/CRM) está disponible y depurado en Silotrans.","Reprocesos y cálculos P×Q inexactos."],
         ["SUP-03","Los maestros (regionales, CRM, servicios, cuentas) provienen de S/4HANA/DataSphere.","Retrabajo en la carga y descuadres."],
         ["SUP-04","Las metas de crecimiento por regional (volumen y tarifa) las define la Gerencia.","No se puede cerrar el presupuesto comercial."]],
        widths=[0.7,3.7,2.2])

b.h2("Dependencias")
b.table(["ID","Dependencia","Tipo","Responsable"],
        [["DEP-01","Flujos de DataSphere para histórico (Silotrans) y real (S/4HANA).","Externa","Integración / TI"],
         ["DEP-02","Actualización pendiente de Silotrans a un nuevo software logístico.","Externa","TI Transprensa"],
         ["DEP-03","Calendario de refresco del real y de los maestros.","Interna","Consultor DataSphere"]],
        widths=[0.7,3.3,1.2,1.4])

# =====================================================================
# 2. CONTEXTO Y OBJETIVOS
# =====================================================================
b.h1("Contexto y objetivos del negocio")
b.h2("Descripción del proceso actual (AS-IS)")
b.para("El presupuesto de Transprensa se construye de forma centralizada por el equipo financiero, a "
       "partir de las directrices de la Gerencia General y la Gerencia Comercial (que definen el "
       "crecimiento por regional), usando Excel y reportes en Power BI. La información operativa "
       "—kilogramos, remesas, pesos, tarifas y la discriminación crédito/contado por CRM— proviene del "
       "software logístico Silotrans; la información contable y de nómina proviene de SIESA y CIES. El "
       "presupuesto se arma por negocio y por regional, no cliente por cliente.")
b.para("Líneas de negocio. Paqueteo (CV paqueteo), masivo (CB masivo), vehículos dedicados, "
       "almacenamiento e ingredientes; más tres negocios especiales —Ingreso, T1 y Soy Más— que "
       "representan cerca del 30% de los ingresos, se manejan por licitación y quedan por fuera de la "
       "fuerza comercial.", size=9.5)
b.para("Ingresos (P×Q). Se parte de la ejecución real del año anterior (N-1, 2025) en kilogramos y pesos "
       "por regional. Se calcula el indicador pesos/kilogramo (tarifa implícita) y se proyecta el año "
       "aplicando un crecimiento en volumen (porcentaje de kg por regional; por ejemplo +21% global) y en "
       "tarifa (por ejemplo +15%, basado en IPC e ICTC). El total anual se distribuye mes a mes según la "
       "estacionalidad del negocio y se discrimina crédito (B2B) frente a contado/contraentrega (originado "
       "en los 46 CRM). Ejemplo levantado en sesión: Antioquia generó en abril remesas por $2.254 "
       "millones, equivalentes a 1.559 toneladas.", size=9.5)
b.para("Costos. Las dos variables principales son el flete (según los kg se define el número de vehículos "
       "y la distribución origen-destino) y la mano de obra, variable y ligada al volumen de kg (índice "
       "persona/kg). Se suman comisiones (CRM externos y fuerza de ventas), arrendamientos (IPC) y gastos "
       "fijos (histórico N-1 × IPC). En el servicio masivo, el ingreso se define como el costo del flete "
       "cotizado a terceros más un margen objetivo (15%–18%). El P&G administrativo (PCGA) se abre por "
       "regional.", size=9.5)
b.callout("Puntos de dolor (motivan la solución)", [
    "Armado y consolidación manual en Excel, con múltiples archivos por negocio y regional.",
    "Dependencia de descargas de Silotrans y reprocesos; trazabilidad limitada.",
    "Dificultad para actualizar el forecast y para simular escenarios (nuevas licitaciones) de forma ágil.",
], accent=RED, fill="FDECEA")

b.h2("Objetivos y beneficios esperados")
b.table(["ID","Objetivo","Beneficio esperado","Métrica"],
        [["OE-01","Unificar el presupuesto en SAC (hoy Excel + Power BI).","Fuente única y menos reprocesos.","N.º de archivos / horas de consolidación"],
         ["OE-02","Automatizar el cálculo (P×Q y costos) y la consolidación del EEFF.","Cierre de presupuesto de semanas a minutos.","Tiempo de consolidación"],
         ["OE-03","Habilitar un forecast ágil intra-año.","Reacción rápida ante desviaciones.","N.º de forecast/año"],
         ["OE-04","Simular escenarios (nueva licitación / cliente grande).","Mejores decisiones comerciales.","N.º de simulaciones"]],
        widths=[0.7,2.3,2.2,1.4])

b.h2("Indicadores de éxito (KPIs)")
b.table(["KPI","Definición","Meta","Fuente"],
        [["Tiempo de consolidación","Días para cerrar el presupuesto consolidado","≤ 2 días","SAC"],
         ["Exactitud del cálculo","Diferencia del P×Q frente al histórico validado","0%","SAC vs. Silotrans"],
         ["Cobertura de seguridad","Modelos con DAC por sociedad/regional","100%","SAC"]],
        widths=[1.6,2.7,0.9,1.4])

b.h2("Actores, roles y responsabilidades (RACI)")
b.table(["Actividad / Entregable","R","A","C","I"],
        [["Metas de crecimiento por regional","Gerencia Comercial","Gerencia General","Regionales","Planeación"],
         ["Carga y cálculo del presupuesto","Planeación Transprensa","Gerencia","Comercial","Dirección"],
         ["Aprobación del presupuesto financiero","Planeación Transprensa","Gerencia General","—","Regionales"]],
        widths=[2.6,1.1,1.1,0.9,0.9])

# =====================================================================
# 3. REQUERIMIENTOS
# =====================================================================
b.h1("Requerimientos")
b.h2("Requerimientos funcionales")
b.table(["ID","Requerimiento","Modelo","Prioridad","Criterio de aceptación"],
        [["RF-001","Calcular ingresos por P×Q por regional y tipo de servicio.","Ingresos","Must","Coincide con el histórico N-1 validado"],
         ["RF-002","Presupuestar los negocios especiales (Ingreso, T1, Soy Más) de forma individual por licitación.","Ingresos","Must","Cada negocio con su curva propia"],
         ["RF-003","Discriminar ventas a crédito (B2B) vs. contado/contraentrega por CRM.","Ingresos","Must","Suma por CRM = total regional"],
         ["RF-004","Aplicar crecimiento en volumen (% kg) por regional definido por la Gerencia.","Ingresos","Must","% aplicado por regional"],
         ["RF-005","Aplicar crecimiento en tarifa (IPC + ICTC).","Ingresos","Must","Tarifa_N = Tarifa_{N-1}×(1+IPC+ICTC)"],
         ["RF-006","Distribuir el total anual a meses según estacionalidad histórica.","Ingresos","Must","Suma mensual = total anual"],
         ["RF-007","Servicio masivo: ingreso = costo de flete (tercero) + margen objetivo.","Ingresos","Should","Margen dentro de 15%–18%"],
         ["RF-008","Presupuestar fletes por kg (vehículos y distribución origen-destino).","Costos","Must","Costo por ruta cotizado"],
         ["RF-009","Presupuestar mano de obra variable (índice persona/kg) alineada a la estacionalidad.","Costos","Must","MO sigue la curva de kg"],
         ["RF-010","Presupuestar comisiones, arrendamientos (IPC) y gastos fijos (N-1×IPC).","Costos","Should","Reglas aplicadas por rubro"],
         ["RF-011","Consolidar el EEFF (P&G administrativo PCGA) por regional.","EEFF","Must","P&G por regional cuadra con la suma"],
         ["RF-012","Gestionar versiones: Presupuesto Comercial, Financiero y Forecast.","Todos","Must","3 versiones disponibles"],
         ["RF-013","Simular el impacto de una nueva licitación / cliente grande.","Todos","Should","Genera versión de escenario"],
         ["RF-014","Comparar presupuesto vs. real ($ y %) por regional y servicio en SAC.","Todos","Must","Variación calculada en SAC"],
         ["RF-015","Integrar el histórico desde Silotrans y el real desde S/4HANA.","Todos","Must","Datos disponibles en el modelo"]],
        widths=[0.7,3.0,0.8,0.8,1.3], size=8.2)

b.h2("Reglas de negocio")
b.table(["ID","Regla","Descripción / fórmula","Aplica a"],
        [["RN-001","Tarifa implícita","Tarifa = Pesos_{N-1} / Kg_{N-1} (por regional)","Ingresos"],
         ["RN-002","Crecimiento de volumen","Kg_N = Kg_{N-1} × (1 + % crecimiento_regional)","Ingresos"],
         ["RN-003","Crecimiento de tarifa","Tarifa_N = Tarifa_{N-1} × (1 + IPC + ICTC)","Ingresos"],
         ["RN-004","Estacionalidad","Valor_mes = Valor_anual × % estacional_mes (histórico N-1)","Ingresos / Costos"],
         ["RN-005","Negocios especiales","Kg crecen 1,5%–2% anual sobre la licitación; estacionalidad propia (p. ej. Ingreso sin operación en enero y diciembre)","Ingresos"],
         ["RN-006","Masivo","Ingreso = Costo_flete_tercero × (1 + margen), margen 15%–18%","Ingresos / Costos"],
         ["RN-007","Mano de obra","Costo_MO = Índice_persona_kg × Kg_proyectados","Costos"],
         ["RN-008","Gastos fijos","Gasto_N = Gasto_{N-1} × (1 + IPC)","Costos"]],
        widths=[0.7,1.5,3.2,1.2], size=8.2)

b.h2("Requerimientos no funcionales")
b.table(["ID","Categoría","Requerimiento","Métrica / meta"],
        [["RNF-01","Rendimiento","Tiempo de ejecución de cada Data Action","< 60 s"],
         ["RNF-02","Seguridad","Acceso por Data Access Control","Sociedad = Transprensa (opcional por Regional)"],
         ["RNF-03","Auditoría","Trazabilidad del origen del dato","Dimensión Auditoría (real/plan/cálculo)"],
         ["RNF-04","Usabilidad","Captura del plan","Plantillas web y complemento de Excel"]],
        widths=[0.7,1.2,2.6,2.1])

# =====================================================================
# 4. DISEÑO FUNCIONAL (TO-BE)
# =====================================================================
b.h1("Diseño funcional de la solución (TO-BE)")
b.h2("Descripción de la solución y arquitectura")
b.para("La solución se compone de tres modelos de planeación en SAC (Ingresos, Costos/Gastos y EEFF) que "
       "comparten dimensiones. El histórico operativo (kilogramos, pesos, tarifas, crédito/contado) se "
       "integra desde Silotrans y el real contable desde S/4HANA, ambos a través de SAP DataSphere. El "
       "plan se captura por plantillas (Input Forms), se calcula con Data Actions (P×Q y costos) y se "
       "consolida en el EEFF; los resultados se explotan en reportes y dashboards por regional y servicio.")
b.figure(os.path.join(IMG,'transprensa_arq.png'), "Figura 1. Arquitectura de la solución (Transprensa).")

b.h2("Diagrama de proceso / flujo funcional")
b.figure(os.path.join(IMG,'transprensa_flujo.png'), "Figura 2. Flujo funcional de cálculo y consolidación (Transprensa).")

b.h2("Modelo de datos (dimensiones y medidas)")
b.para("Dimensiones compartidas por los modelos (los maestros provienen de S/4HANA/Silotrans vía "
       "DataSphere, salvo las propias de planeación):", size=9.5, space_after=4)
b.table(["Dimensión","Tipo","Descripción","Origen del maestro"],
        [["Cuenta","Cuenta","Plan de cuentas / rubros","S/4HANA"],
         ["Sociedad","Organizativa","Transprensa S.A.S.","S/4HANA"],
         ["Regional","Genérica","21 regionales","S/4HANA / Silotrans"],
         ["Servicio (CV)","Genérica","Paqueteo, masivo, dedicados, almacenamiento, ingredientes","Silotrans"],
         ["Negocio especial","Genérica","Ingreso, T1, Soy Más","Silotrans / manual"],
         ["CRM","Genérica","46 centros de recibo de mercancía","Silotrans"],
         ["Tipo de venta","Genérica","Crédito / contado (contraentrega)","Silotrans"],
         ["Versión","Sistema","Comercial, Financiero, Forecast, Real","SAC"],
         ["Fecha","Tiempo","Mensual","SAC"],
         ["Auditoría","Genérica","Origen del dato (real/plan/cálculo)","SAC"]],
        widths=[1.3,1.0,2.7,1.6], size=8.3)
b.para("Medidas principales: Kilos, Tarifa (pesos/kg), Importe (COP) y Margen.", size=9.5)

b.h2("Lógica de cálculo (Data Actions)")
b.table(["ID","Cálculo","Descripción / fórmula","Salida"],
        [["DA-001","P×Q de ingresos","Importe = Kilos × Tarifa (por regional/servicio/CRM)","Importe (Presupuesto)"],
         ["DA-002","Crecimiento","Aplica % volumen (kg) y (IPC+ICTC) a la tarifa","Kilos y Tarifa proyectados"],
         ["DA-003","Estacionalidad","Distribuye el total anual a los 12 meses (histórico N-1)","Importe mensual"],
         ["DA-004","Fletes","Dimensiona vehículos por kg y ruta; costo tercero + margen","Costo de flete"],
         ["DA-005","Mano de obra","Índice persona/kg × kg proyectados","Costo de mano de obra"],
         ["DA-006","Consolidación EEFF","Cross-Model Copy (Ingresos + Costos → P&G) por regional","P&G administrativo (PCGA)"]],
        widths=[0.7,1.4,2.9,1.6], size=8.3)
b.figure(os.path.join(IMG,'transprensa_pxq.png'), "Figura 3. Metodología P×Q de ingresos (Transprensa).")

b.h2("Versiones y escenarios")
b.table(["Versión","Uso","Reglas"],
        [["Presupuesto Comercial","Metas de Gerencia y Gerencia Comercial por regional","Base para negociación"],
         ["Presupuesto Financiero","Cifra oficial construida por Planeación","Pública; bloqueo al aprobar"],
         ["Forecast","Proyección actualizada intra-año","Varias versiones (privadas/públicas)"],
         ["Real","Ejecución integrada desde S/4HANA","Solo lectura"]],
        widths=[1.6,2.9,2.1])

b.h2("Integración e interfaces")
b.table(["ID","Fuente","Contenido","Destino","Frecuencia","Método"],
        [["INT-01","Silotrans","Histórico kg, pesos, tarifas, crédito/contado por regional y CRM","Ingresos / Costos","Inicial + mensual","DataSphere"],
         ["INT-02","S/4HANA","Real contable (saldos)","EEFF","Diaria","DataSphere"],
         ["INT-03","CIES","Nómina (referencia de mano de obra)","Costos","Mensual","Archivo / DataSphere"]],
        widths=[0.7,1.0,2.4,1.1,0.8,0.6], size=8.2)

b.h2("Plantillas de entrada (Input Forms)")
b.table(["ID","Plantilla","Modelo","Contenido / dimensiones","Opción de carga"],
        [["IF-01","Metas de crecimiento por regional","Ingresos","% volumen y % tarifa por regional","Reemplazar"],
         ["IF-02","P×Q por regional y servicio","Ingresos","Kilos y tarifa por regional/servicio/CRM","Reemplazar"],
         ["IF-03","Negocios especiales","Ingresos","Kilos y tarifa por licitación (Ingreso, T1, Soy Más)","Reemplazar"],
         ["IF-04","Costos","Costos/Gastos","Fletes, mano de obra, comisiones, arrendamientos, gastos fijos","Reemplazar"]],
        widths=[0.6,1.7,1.0,2.5,0.8], size=8.3)

b.h2("Reportes y dashboards")
b.table(["ID","Reporte / Dashboard","Tipo","Audiencia","Contenido"],
        [["RPT-01","P&G administrativo por regional","Story","Gerencia","P&G (PCGA) y márgenes"],
         ["RPT-02","Presupuesto vs. Real","Story","Planeación / Gerencia","Variación $ y % por regional y servicio"],
         ["RPT-03","Kilos e ingresos por regional/servicio/CRM","Dashboard","Comercial","Volúmenes y tarifas"],
         ["RPT-04","Márgenes (bruto/operativo)","Dashboard","Gerencia","Margen por regional"]],
        widths=[0.6,2.2,0.8,1.3,1.7], size=8.3)

b.h2("Seguridad y autorizaciones")
b.table(["Rol","Modelos","Acceso","DAC","Licencia"],
        [["Planeación Transprensa","Los 3","Escritura","Sociedad = Transprensa","Planificación"],
         ["Gerencia / Dirección","Los 3","Lectura","Sociedad = Transprensa","BI / lectura"],
         ["Regionales","Ingresos / EEFF","Lectura","Regional = la propia (opcional)","BI / lectura"]],
        widths=[1.7,1.3,1.0,1.8,0.8])

b.h2("Monedas y conversión")
b.para("Moneda única de operación y reporte: peso colombiano (COP). No se requiere conversión de moneda "
       "para Transprensa en el alcance actual.", size=9.5)

b.h2("Validaciones y manejo de errores")
b.table(["ID","Validación","Condición","Acción / mensaje"],
        [["VAL-01","Kilos y tarifa positivos","Kilos > 0 y Tarifa > 0","Bloquear celda con mensaje"],
         ["VAL-02","Estacionalidad completa","Suma de % mensual = 100%","Advertir si ≠ 100%"],
         ["VAL-03","Cuadre del real","Real SAC = Real ERP","Reporte de diferencias"]],
        widths=[0.7,1.9,2.1,1.9])

# =====================================================================
# 5. ESPECIFICACIÓN POR OBJETO
# =====================================================================
b.h1("Especificación detallada por objeto")
b.para("Se incluyen dos fichas diligenciadas como referencia; el resto de objetos (Data Actions, "
       "plantillas, reportes e interfaces) se documenta con la misma estructura.", size=9.5)
b.h2("Ficha DA-001 — P×Q de ingresos")
b.table(["Campo","Contenido"],
        [["ID / Nombre","DA-001 — P×Q de ingresos"],
         ["Tipo","Data Action (Advanced Formulas)"],
         ["Modelo","Ingresos (Transprensa)"],
         ["Descripción","Calcula el importe de ingresos multiplicando los kilogramos proyectados por la tarifa (pesos/kg), por regional, servicio y CRM."],
         ["Entradas","Medidas Kilos y Tarifa; dimensiones Regional, Servicio, CRM, Tipo de venta, Fecha."],
         ["Lógica","1) Tomar Kilos y Tarifa proyectados (DA-002). 2) Importe = Kilos × Tarifa. 3) Escribir en la versión Presupuesto."],
         ["Salida","Medida Importe en la versión Presupuesto."],
         ["Reglas asociadas","RN-001, RN-002, RN-003"],
         ["Criterio de aceptación","El total por regional coincide con el histórico N-1 crecido según los % definidos."]],
        widths=[1.6,5.0], size=8.5)
b.h2("Ficha INT-01 — Integración desde Silotrans")
b.table(["Campo","Contenido"],
        [["ID / Nombre","INT-01 — Histórico desde Silotrans"],
         ["Tipo","Interfaz de entrada (vía DataSphere)"],
         ["Origen / Destino","Silotrans → SAP DataSphere → Modelos de Ingresos y Costos"],
         ["Contenido","Kilogramos, pesos, tarifas y discriminación crédito/contado por regional y CRM."],
         ["Frecuencia","Carga inicial del histórico N-1 y actualización mensual."],
         ["Consideración","Existe una actualización pendiente de Silotrans a un nuevo software (ver riesgo R-01)."]],
        widths=[1.6,5.0], size=8.5)

b.h2("Mapeo de campos (Silotrans → SAC)")
b.table(["Campo origen (Silotrans)","Transformación","Campo destino (SAC)","Obligatorio"],
        [["Regional / sede","Mapear a la dimensión Regional","Regional","Sí"],
         ["Centro de recibo","Mapear a la dimensión CRM","CRM","Sí"],
         ["Tipo de venta","Crédito / contado","Tipo de venta","Sí"],
         ["Kilogramos","Directo","Medida Kilos","Sí"],
         ["Valor de remesa (pesos)","Directo","Medida Importe","Sí"],
         ["CV / servicio","Mapear a la dimensión Servicio","Servicio","Sí"]],
        widths=[2.0,2.0,1.7,0.9], size=8.4)

# =====================================================================
# 6. CASOS DE USO Y ESCENARIOS
# =====================================================================
b.h1("Casos de uso y escenarios")
b.h2("CU-001 — Cargar y calcular el presupuesto de ingresos por regional")
b.table(["Campo","Contenido"],
        [["Actor","Planeación Financiera Transprensa"],
         ["Precondición","Histórico N-1 integrado desde Silotrans; metas de crecimiento definidas por la Gerencia."],
         ["Flujo principal","1) Cargar metas por regional (IF-01). 2) Cargar/ajustar kilos y tarifa (IF-02, IF-03). 3) Ejecutar DA-002 (crecimiento) y DA-001 (P×Q). 4) Ejecutar DA-003 (estacionalidad). 5) Revisar el resultado por regional y servicio."],
         ["Excepciones","Kilos/tarifa inválidos (VAL-01); estacionalidad ≠ 100% (VAL-02)."],
         ["Postcondición","Presupuesto de ingresos calculado por regional, servicio, CRM y mes en la versión correspondiente."]],
        widths=[1.6,5.0], size=8.5)

b.h2("SIM-01 — Simulación de una nueva licitación")
b.table(["Campo","Contenido"],
        [["Escenario","Adjudicación de una nueva licitación / cliente grande durante el año."],
         ["Variables","Kilos, tarifa y meses de operación de la licitación; regional y servicio afectados."],
         ["Procedimiento","Copiar la versión Forecast, agregar los kilos/tarifa del nuevo negocio y recalcular (DA-001, DA-004/005)."],
         ["Resultado esperado","Impacto en ingresos, costos (fletes y mano de obra) y margen, por regional y en el tiempo."]],
        widths=[1.6,5.0], size=8.5)

# =====================================================================
# 7. DATOS MAESTROS
# =====================================================================
b.h1("Datos maestros y migración")
b.table(["Objeto","Descripción","Volumen","Fuente","Responsable"],
        [["Regionales","Sedes regionales","21","S/4HANA / Silotrans","TI / Planeación"],
         ["CRM","Centros de recibo de mercancía","46","Silotrans","Comercial"],
         ["Servicios (CV)","Paqueteo, masivo, dedicados, almacenamiento, ingredientes","≈5","Silotrans","Planeación"],
         ["Negocios especiales","Ingreso, T1, Soy Más","3","Silotrans / manual","Planeación"],
         ["Cuentas","Plan de cuentas","(n.º)","S/4HANA","Contabilidad"]],
        widths=[1.2,2.4,0.8,1.3,0.9], size=8.4)
b.para("Estrategia de carga inicial: el histórico N-1 (2025) y los maestros se cargan desde Silotrans y "
       "S/4HANA a través de DataSphere; se validan cuadres de kilos e importes por regional antes de "
       "habilitar el cálculo.", size=9.5)

# =====================================================================
# 8. PRUEBAS
# =====================================================================
b.h1("Criterios de aceptación y pruebas")
b.h2("Casos de prueba")
b.table(["ID","Escenario","Resultado esperado","Tipo"],
        [["CP-001","Ejecutar DA-001 (P×Q) para una regional","Importe = kilos × tarifa","Unitaria"],
         ["CP-002","Verificar estacionalidad","Suma mensual = total anual (100%)","Unitaria"],
         ["CP-003","Ejecutar DA-006 (consolidación EEFF)","P&G por regional cuadra con la suma","Integración"],
         ["CP-004","Comparar presupuesto vs. real","Variación $ y % correcta por regional","UAT"]],
        widths=[0.7,2.3,2.6,0.9], size=8.4)
b.h2("Matriz de trazabilidad")
b.table(["Requerimiento","Objeto","Caso de prueba","Estado"],
        [["RF-001","DA-001","CP-001","Pendiente"],
         ["RF-006","DA-003","CP-002","Pendiente"],
         ["RF-011","DA-006","CP-003","Pendiente"],
         ["RF-014","RPT-02","CP-004","Pendiente"]],
        widths=[1.7,1.7,1.7,1.4])

# =====================================================================
# 9. RIESGOS Y TEMAS ABIERTOS
# =====================================================================
b.h1("Riesgos y temas abiertos")
b.h2("Riesgos y mitigaciones")
b.table(["ID","Riesgo","Prob.","Impacto","Mitigación","Resp."],
        [["R-01","Migración pendiente de Silotrans a un nuevo software (afecta INT-01)","Media","Alto","Diseñar la interfaz sobre DataSphere, agnóstica a la fuente","TI"],
         ["R-02","Maestros de regionales/CRM desalineados con el ERP","Media","Medio","Depuración previa en DataSphere","Integración"],
         ["R-03","Estacionalidad histórica poco representativa en negocios nuevos","Baja","Medio","Ajuste manual por licitación","Planeación"]],
        widths=[0.6,2.4,0.7,0.7,1.6,0.6], size=8.2)
b.h2("Temas abiertos / decisiones pendientes")
b.table(["ID","Tema / decisión pendiente","Estado"],
        [["TA-01","¿La información de remesas irá directo de Silotrans a SAC o siempre vía DataSphere?","Abierto"],
         ["TA-02","Nivel de detalle de crédito/contado por CRM disponible en el real (S/4HANA vs. legado).","Abierto"],
         ["TA-03","Método de integración de la nómina (CIES): archivo vs. DataSphere.","Abierto"]],
        widths=[0.7,4.7,1.2])

# =====================================================================
# 10. ANEXOS
# =====================================================================
b.h1("Anexos")
b.bullets([
    "Glosario extendido de términos SAP/SAC y del negocio (ver DOC-01).",
    "Mockups de plantillas de carga (IF-01 a IF-04) y de reportes (RPT-01 a RPT-04).",
    "Catálogo de maestros: regionales, CRM, servicios y negocios especiales.",
    "Actas de las sesiones de levantamiento del proceso actual (AS-IS).",
])

fn=os.path.join(HERE,'Especificacion_Funcional_Transprensa_SAC.docx')
b.save(fn)
print("GUARDADO:", fn)
