#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construye el Documento de Diseño de Solución unificado (Fanalca · Ciudad Limpia · Transprensa)
con el formato del 'Documento de Diseño Funcional'. Sin Parking Lot ni Próximos Pasos."""
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx_helpers import Builder, NAVY, BLUE_D, RED, GREEN, GREY

TPL = "src/template_funcional.docx"
LOGO_BUILD = "src/tpl_media/word/media/image2.png"   # Proyecto Build
LOGO_FAN = "src/tpl_media/word/media/image3.png"      # Fanalca | accenture
IMG = "img"

b = Builder(TPL)
b.setup_headers(LOGO_FAN)


def fm_heading(text):
    p = b.doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(text)
    r.font.name = 'Arial'; r.font.size = Pt(13); r.font.bold = True
    r.font.color.rgb = RGBColor.from_string(BLUE_D)
    b._bottom_border(p)
    return p


# =====================================================================
# PORTADA
# =====================================================================
b.spacer(30)
b.cover_logo(LOGO_BUILD, width=3.1)
b.spacer(16)
b.cover_title([
    ("DOCUMENTO DE DISEÑO DE SOLUCIÓN", 22, BLUE_D, True, 5),
    ("Modelos de Planeación Financiera en SAP Analytics Cloud", 14, NAVY, False, 3),
    ("Programa SAP BUILD · Grupo Fanalca", 12, GREY, False, 22),
])
b.meta_table([
    ("Sociedades", "Fanalca S.A.  ·  Ciudad Limpia  ·  Transprensa S.A.S."),
    ("Programa", "SAP BUILD — Implementación de SAP S/4HANA + SAP Analytics Cloud"),
    ("Plataforma", "SAP Analytics Cloud (SAC) sobre SAP BTP  ·  SAP DataSphere"),
    ("Versión", "2.0 — Documento unificado de diseño"),
    ("Fecha", "08 de junio de 2026"),
    ("Estado", "Borrador para revisión y aprobación"),
    ("Clasificación", "Confidencial"),
])
b.spacer(34)
b.cover_logo(LOGO_FAN, width=2.9)
b.page_break()

# =====================================================================
# CONTROL DE VERSIONES / DISTRIBUCIÓN / DOCUMENTOS RELACIONADOS
# =====================================================================
fm_heading("Control de Versiones")
b.table(
    ["Versión", "Estado", "Fecha", "Autor", "Descripción del cambio"],
    [
        ["1.0", "Borrador", "Jun-2026", "Equipo SAP BUILD",
         "Versiones individuales de diseño por sociedad (Fanalca, Ciudad Limpia, Transprensa)."],
        ["2.0", "Borrador para revisión", "08-Jun-2026", "Equipo SAP BUILD",
         "Documento unificado bajo el formato de Diseño Funcional. Flujogramas rediseñados. "
         "Se consolidan las tres sociedades en un único entregable."],
    ],
    widths=[0.7, 1.3, 0.9, 1.3, 2.4], size=8.6)

b.spacer(4)
fm_heading("Distribución del Documento")
b.table(
    ["Nombre / Rol", "Organización", "Propósito"],
    [
        ["Líder Funcional del Programa", "Grupo Fanalca", "Validación de alcance y aprobación"],
        ["Arquitecto / Consultor SAC", "Accenture", "Diseño y construcción de la solución"],
        ["Equipo de Planeación Financiera", "Cada sociedad", "Validación de reglas de negocio y UAT"],
        ["Equipo de TI / Transformación Digital", "Grupo Fanalca", "Integración S/4HANA · DataSphere · BW"],
    ],
    widths=[2.6, 1.8, 2.2], size=8.6)

b.spacer(4)
fm_heading("Documentos Relacionados")
b.table(
    ["Documento", "Descripción"],
    [
        ["Actas de Sesiones de Diseño (Sesión N°1, 22-May-2026)", "Levantamiento del proceso de negocio por sociedad."],
        ["Modelos SAC (ambiente de Desarrollo)", "Modelos de Ingresos, Costos/Gastos y EEFF configurados."],
        ["Inventario de scripts / paquetes SAP BPC", "Lógica de cálculo de referencia para los Data Actions."],
    ],
    widths=[3.3, 3.3], size=8.6)
b.page_break()

# =====================================================================
# TABLA DE CONTENIDO
# =====================================================================
fm_heading("Tabla de Contenido")
b.para("El índice se genera automáticamente a partir de los títulos del documento.",
       italic=True, size=9, color=GREY, align='left', space_after=4)
b.toc()
b.page_break()

# =====================================================================
# 1. PROPÓSITO DEL DOCUMENTO
# =====================================================================
b.h1("Propósito del documento")
b.para(
    "Este documento describe el diseño y la configuración de la solución SAP Analytics Cloud (SAC) "
    "para el Programa SAP BUILD de Grupo Fanalca. Reúne en un único entregable el diseño de los "
    "modelos de planeación financiera de tres sociedades del grupo —Fanalca S.A., Ciudad Limpia y "
    "Transprensa S.A.S.— bajo un patrón de arquitectura común: tres modelos de planeación (Ingresos, "
    "Costos/Gastos y Estados Financieros) que se integran con SAP S/4HANA a través de SAP DataSphere.")
b.para(
    "Para cada sociedad se documentan los objetivos de negocio, la estructura organizativa relevante, "
    "la arquitectura de modelos, las dimensiones y medidas, los flujos de cálculo y consolidación, los "
    "componentes técnicos y el inventario de datos maestros. El documento constituye el blueprint de "
    "diseño que guía la construcción, la configuración y las pruebas de la solución en SAC.")
b.callout("Patrón de diseño común a las tres sociedades",
          ["Tres modelos de planeación: Ingresos y Costos/Gastos que consolidan en el modelo de EEFF.",
           "Dimensiones compartidas (Sociedad, Centro de beneficio, Cuenta, Moneda, Auditoría, Versión, Fecha).",
           "Integración con SAP S/4HANA vía SAP DataSphere y consolidación mediante Data Actions.",
           "Trazabilidad del dato mediante la dimensión AUDITORIA (real, presupuesto, cálculo, manual)."],
          accent=NAVY)
b.figure(f"{IMG}/00_programa_overview.png",
         "Figura 1. Programa SAP BUILD — patrón de diseño común aplicado a las tres sociedades de Grupo Fanalca.")

# =====================================================================
# 2. CÓMO USAR EL DOCUMENTO
# =====================================================================
b.h1("Cómo usar el documento")
b.para(
    "El documento se organiza en una introducción común (secciones 1 y 2) y un capítulo por sociedad "
    "(secciones 3, 4 y 5). Cada capítulo sigue la misma estructura del formato de Diseño Funcional: "
    "escenario de negocio, estructura organizativa y diseño y configuración de la solución. Utilice la "
    "Tabla de Contenido para navegar directamente a la sección de interés.")
b.table(
    ["Perfil", "Uso recomendado del documento", "Secciones clave"],
    [
        ["Arquitectos SAP / SAC", "Revisión del diseño técnico de modelos, dimensiones y flujos de cálculo.", "x.3"],
        ["Analistas funcionales", "Validación del mapeo de requisitos de negocio y metodología P×Q.", "x.1, x.3"],
        ["Equipo de TI / BASIS", "Integración SAP S/4HANA ↔ DataSphere ↔ SAC y carga de datos.", "x.3"],
        ["Usuarios clave (Key Users)", "Validación de reglas de negocio, datos maestros y pruebas UAT.", "x.1, x.2, x.3"],
        ["Gestión del proyecto", "Seguimiento del alcance, actividades, roles y entregables.", "x.3"],
    ],
    widths=[1.7, 3.6, 1.3], size=8.6)
b.para("Convención de lectura: en cada capítulo, «x» corresponde al número de la sociedad "
       "(3 = Fanalca, 4 = Ciudad Limpia, 5 = Transprensa).",
       italic=True, size=9, color=GREY, align='left')


# =====================================================================
# 3. FANALCA S.A.
# =====================================================================
b.page_break()
b.h1("Fanalca S.A.")
b.para(
    "Fanalca S.A. es un conglomerado industrial colombiano con más de 70 años de trayectoria, "
    "conformado por tres grandes vicepresidencias: Metalmecánica (transformación de acero), Honda "
    "Supermotos/Motos y Honda Autos. La compañía requiere una plataforma de analítica centralizada "
    "que integre los datos financieros y operativos de sus divisiones para soportar la toma de "
    "decisiones gerenciales en tiempo real, migrando su planeación actual desde SAP BPC hacia SAC.")

b.h2("Escenario / Proceso de negocio")
b.para(
    "El proceso de presupuestación inicia en agosto–septiembre del año en curso para el año siguiente "
    "(N+1), se aprueba ante la Junta Directiva entre diciembre y enero, y se complementa con una "
    "proyección a cinco años que se presenta en asamblea en marzo. Adicionalmente se maneja un "
    "forecast mensual (Forecast 1 a N) y escenarios para bancos (Plan Bancos 1 en marzo, Plan Bancos 2 "
    "en junio).")
b.table(
    ["Unidad de negocio", "Líneas de negocio", "Proceso clave en SAC", "Sistema fuente"],
    [
        ["Metalmecánica\n(transformación de acero)",
         "PMF · Ensamble Medellín · Autopartes · Defensas · Ambiental · Tubería · Metal Sur · Mecanizado",
         "Costos de producción por CECOS/CEBES · P&G por línea · capital de trabajo",
         "BPC / UNOE → SAC\nS/4HANA (futuro)"],
        ["Honda Supermotos / Motos",
         "Motos CKD (HMC) · CBU (HOC/HOD/HON) · Repuestos (HRC) · Motopartes (MPC/MPCE)",
         "Ingresos P×Q por referencia, cliente y CEBE · juego de cartera e inventario",
         "NIGURI / BPC → SAC\nS/4HANA + DataSphere"],
        ["Honda Autos\n(34 CEBEs)",
         "HAC (importador) · 16 agencias · HPC (repuestos) · 16 talleres · Renting",
         "P×Q por referencia y agencia · EEFF · capital de trabajo HAC/agencias/HPC",
         "Excel / BPC → SAC\nS/4HANA + DataSphere"],
    ],
    widths=[1.5, 2.1, 1.9, 1.1], size=8.0)

b.para("Ciclo de planeación y versiones", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Versión", "Descripción", "Período de elaboración", "Escenarios"],
    [
        ["Presupuesto (Plan)", "Presupuesto anual aprobado por Junta Directiva", "Agosto–Enero", "Pesimista · Optimista · Medio"],
        ["Forecast 1-N", "Proyección mensual actualizada (rolling)", "Mensual", "1 versión activa por mes"],
        ["Plan Bancos 1", "Proyección a 5 años para presentación a bancos", "Marzo", "5 años calendario"],
        ["Plan Bancos 2", "Actualización del Plan Bancos a mitad de año", "Junio", "5 años (revisado)"],
        ["Real / Actual", "Ejecución contable real desde SAP FI/BW", "Mensual (cierre)", "Un único real por período"],
        ["Plan 3 años", "Presupuesto estratégico de largo plazo", "Q4", "Consolidado de 3 años"],
    ],
    widths=[1.3, 2.5, 1.5, 1.3], size=8.2)

b.h3("Objetivos empresariales y beneficios esperados")
b.table(
    ["#", "Objetivo empresarial", "Beneficio esperado"],
    [
        ["1", "Visibilidad financiera consolidada multi-sociedad",
         "Vista unificada de resultados de las NITs FANALCA, Supermotos, SIM y Metal Sur en tiempo real."],
        ["2", "Análisis de ingresos granular por referencia y cliente",
         "P×Q desagregado por modelo de moto/auto, cliente (distribuidor/agencia), CEBE y mes."],
        ["3", "Migración BPC → SAC preservando la lógica de scripts",
         "Replicar los scripts T01, T02, cartera e inventario como Data Actions, sin pérdida de lógica."],
        ["4", "Control de costos por línea de Metalmecánica",
         "Seguimiento de CECOS/CEBES (PMF, Tubería, Autopartes, Ambiental) con tarifas reales vs. estándar."],
        ["5", "Cierre financiero ágil con EEFF consolidado",
         "Reducción del tiempo de cierre mensual mediante el envío automático desde los modelos de origen."],
        ["6", "Planeación xP&A integrada a 5 años",
         "Horizontes de 1, 3 y 5 años en SAC para presentaciones ejecutivas y bancarias."],
    ],
    widths=[0.4, 2.7, 3.5], size=8.4)

b.h3("Descripción a alto nivel de requisitos empresariales")
b.table(
    ["ID", "Requisito", "Descripción", "Modelo"],
    [
        ["REQ-001", "P×Q de ingresos por referencia",
         "Ingresos = Unidades × Precio de venta, por referencia (moto/auto), CEBE y mes. Incluye IVA (19%), "
         "impuesto al consumo (8%) y recuperación de fletes.", "Ingresos"],
        ["REQ-002", "Juego de cartera por entidad",
         "Saldo inicial + Facturación con IVA − Recaudos = Saldo final. Tasas 50/50 HAC, 80/20 agencias, "
         "75/25 talleres. Cartera de renting separada.", "Ingresos"],
        ["REQ-003", "Juego de inventarios motos/autos",
         "Inventario inicial + Compras/producción − Despachos = Inventario final, en unidades y pesos. "
         "Valoración a costo promedio y estándar. Inventario HAC en zona franca.", "Ingresos"],
        ["REQ-004", "EEFF consolidado por sociedad",
         "Estado de Resultados (P&G) y Balance por cuenta, CEBE y sociedad. P&G «sábana» (con CSC "
         "discriminados) y P&G NIT (sin ventas internas).", "EEFF"],
        ["REQ-005", "Costos de conversión por CEBE de PMF",
         "Tarifas de mano de obra directa y CIF por centro de trabajo, distribuidas a las líneas cliente "
         "mediante alícuotas y centros transversales.", "Costos"],
        ["REQ-006", "Flujo de caja directo",
         "Recaudos, pagos de MP exterior, nómina, impuestos bimestrales, giros financiados en USD y caja "
         "mínima operativa.", "EEFF"],
        ["REQ-007", "Variables macroeconómicas",
         "TRM (USD/COP), IBR + spread, SOFR + spread, IPC y tasas de cobertura, parametrizadas por escenario.",
         "Todos"],
        ["REQ-008", "Versionamiento y escenarios",
         "Real, Plan (pesimista/optimista/medio), Forecast 1-N y Plan Bancos 1-2. El presupuesto aprobado es "
         "inmutable; los escenarios son versiones adicionales.", "Todos"],
        ["REQ-009", "Separación de scripts por línea",
         "El script T01 (motos + autos) debe separarse para evitar sobreescritura entre líneas cuando los "
         "datos están incompletos en alguna unidad.", "Ingresos"],
    ],
    widths=[0.7, 1.7, 3.5, 0.7], size=8.0)

b.h2("Estructura organizativa relevante")
b.para(
    "La estructura organizativa de Fanalca S.A. está conformada por múltiples entidades jurídicas (NITs) "
    "y centros de beneficio (CEBEs) que se mapean directamente a las dimensiones SOCIEDAD y CEBES de los "
    "modelos SAC.")
b.para("Entidades jurídicas (dimensión SOCIEDAD)", bold=True, size=10, align='left', space_after=3)
b.table(
    ["NIT / Sociedad", "Descripción", "Modelos SAC", "Estado en SAP"],
    [
        ["FANALCA S.A.", "NIT principal. Consolida motos, autos y toda la transformación de acero.",
         "Ingresos · EEFF · Costos", "S/4HANA en implementación"],
        ["Supermotos", "Canal tradicional de motos Honda (B2C). Tiene SAP ERP propio.",
         "EEFF · Ingresos (carga BW)", "SAP ERP con ODS/BW"],
        ["SIM — Servicios Industriales Metalmecánicos", "Fabrica piezas plásticas para ensamble de motos.",
         "EEFF · Costos", "En alcance del proyecto"],
        ["Metal Sur", "Tubería de diferente diámetro, dos plantas físicas.",
         "Ingresos · EEFF · Costos", "NIT independiente — en alcance"],
        ["FN Servicios", "Tiene SAP ERP. Carga del real automática vía BW.",
         "EEFF", "SAP ERP con ODS/BW"],
        ["Compañía 6", "Sociedad virtual de ajustes y eliminaciones de consolidación.",
         "EEFF (eliminaciones)", "Pendiente de definición"],
    ],
    widths=[1.6, 2.6, 1.4, 1.0], size=7.9)

b.para("Centros de beneficio — Honda Supermotos / Motos", bold=True, size=10, align='left', space_after=3)
b.table(
    ["CEBE", "Nombre", "Descripción del proceso"],
    [
        ["HMC", "Honda Motos CKD", "Importación CKD y ensamble en planta Yumbo. Venta B2B al canal tradicional."],
        ["HOC", "Honda CBU Consolidado", "Importación de motos armadas (CBU). CEBE padre de HOD y HON."],
        ["HOD", "Honda CBU Canal Tradicional", "Ventas CBU al canal tradicional (distribuidores y red propia)."],
        ["HON", "Honda CBU Negocios Especiales", "Ventas CBU a negocios especiales e institucionales."],
        ["MPC", "Motopartes", "Fabricación y compra de piezas para integración nacional. Venta interna a HMC."],
        ["MPCE", "Motopartes Externo", "Ventas externas de motopartes a otras ensambladoras."],
        ["HRC", "Repuestos Motos Honda", "Importación y comercialización de repuestos, llantas, cascos y aceites."],
    ],
    widths=[0.7, 1.9, 4.0], size=8.1)

b.para("Centros de beneficio — Metalmecánica / Transformación de acero", bold=True, size=10, align='left', space_after=3)
b.table(
    ["CEBE", "Nombre", "Descripción del proceso", "Tratamiento SAC"],
    [
        ["PMF", "Planta Metalmecánica Fanalca", "Gran planta de manufactura que presta servicios a todas las líneas. Su ingreso = costo absorbido.", "Costo absorbido → EEFF"],
        ["EMM", "Ensamble Medellín", "Servicio de ensamble de autopartes (cliente Renault/Sofasa). 12 referencias.", "P×Q → Ingresos · EEFF"],
        ["AUC", "Autopartes", "158 referencias (73 nacionales + 85 exportación). Clientes Renault, Hino, Superpolo.", "P×Q × referencia → Ingresos"],
        ["DEF", "Defensas Viales", "Fabricación de defensas viales en acero. Referencias agrupadas.", "P×Q directo → EEFF"],
        ["AMB", "Ambiental / Carrocerías", "Cajas compactadoras de residuos. Venta nacional + CKD exportación.", "P×Q → Ingresos · EEFF"],
        ["TUP", "Tubería Fanalca", "Lámina importada → cold roll, galvanizado, estructural. El script corre dos veces.", "P×Q (2 corridas) → EEFF"],
        ["MSR", "Metal Sur", "Tubería de otros diámetros, dos plantas. Proceso idéntico a TUP.", "P×Q (2 corridas) → EEFF"],
        ["PDB", "Ingeniería (transversal)", "Se distribuye 97% a Autopartes y 3% a Defensas como alícuota de costo.", "Costos y Gastos"],
        ["PPC", "Mantenimiento y Calidad", "Áreas transversales (~10-12 CECOS) distribuidas por % a cada línea productiva.", "Costos y Gastos"],
    ],
    widths=[0.6, 1.7, 3.0, 1.3], size=7.8)

b.para("Centros de beneficio — Honda Autos (34 CEBEs)", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Grupo", "Descripción", "Impuestos / proceso"],
    [
        ["HAC (importador)", "Importa vehículos de Brasil, EE.UU., Canadá, Japón y Tailandia. Venta interna sin IVA a agencias. Inventario en zona franca.", "Sin IVA en factura interna. FOB + factor de internamiento"],
        ["HPC (repuestos)", "90% venta interna a talleres propios y 10% a distribuidores externos. Margen 48%.", "IVA 19% en ventas a distribuidores"],
        ["Agencias (16)", "Agencias propias que facturan al cliente final. Tienen taller y gestión de usados.", "IVA 19% + IC 8% = 27% (5% en usados)"],
        ["Talleres (16)", "Ligados a las 16 agencias. Servicios de MO, lámina, pintura, eléctrica y repuestos.", "Recaudo 75/25/10 en tres meses"],
        ["Renting", "Empresa del grupo que compra autos a las agencias. Cartera separada que no se recauda en proyección.", "Cartera de renting aislada"],
    ],
    widths=[1.2, 3.6, 1.8], size=7.9)

b.callout("Estructura de centros de costo (CECOS) — dimensión Costos y Gastos",
          ["CECOS 11 — Mano de obra directa (PMF): tarifas estándar por centro de trabajo y referencia.",
           "CECOS 12 — Servicios a la producción y administrativos operativos de planta.",
           "CECOS 2 — Centros de costo administrativos (gerencias, finanzas, recursos humanos).",
           "CECOS PPC (mantenimiento/calidad) y PDB (ingeniería): distribuidos por alícuota a las líneas productivas.",
           "Metal Sur: CECOS identificados por planta 1 / planta 2 para la distribución de MO y CIF."],
          accent=GREEN, fill="EAF3E6")

b.h2("Diseño y configuración de soluciones")
b.h3("Arquitectura de la solución")
b.para(
    "La solución contempla tres modelos de planeación interconectados, migrados desde SAP BPC. Los "
    "modelos de Ingresos y Costos/Gastos alimentan el modelo de EEFF mediante Data Actions, replicando "
    "la lógica de «destination app» existente en BPC. La integración con SAP S/4HANA se realiza a través "
    "de SAP DataSphere, evitando replicar datos cuando es posible.")
b.figure(f"{IMG}/fanalca_arq.png",
         "Figura 2. Arquitectura de la solución SAP Analytics Cloud — Fanalca S.A.")

b.h3("Modelos SAC y dimensiones")
b.para("Modelo 1 — Ingresos Fanalca (9 dimensiones). Planning Model (Read/Write). Medida: Importe "
       "(decimal). Soporta P×Q y capital de trabajo.", size=9.5, align='left', space_after=3)
b.table(
    ["Dimensión", "Tipo", "Descripción / uso", "Fuente"],
    [
        ["Version", "Estándar", "Plan / Forecast 1-N / Real / Plan Bancos 1-2.", "Estándar SAC"],
        ["RATIO", "Genérica", "≈30 ratios P×Q por unidad: ventas brutas, precio, IVA, unidades, costo, cartera, inventario.", "Definición manual"],
        ["Date", "Estándar", "Dimensión temporal mensual (Año/Mes).", "Estándar SAC"],
        ["AUDITORIA", "Genérica", "Origen del dato: «script» (calculado) vs. «ajuste» (manual).", "Definición manual"],
        ["CEBES", "Genérica", "CEBEs de motos y autos (HMC…HRC, HAC, agencias, HPC, talleres).", "CO-PCA · CEPC"],
        ["CLIENTES", "Genérica", "Distribuidores de motos, agencias de autos y clientes de Autopartes.", "SD · KNA1"],
        ["MONEDA", "Genérica", "COP para motos/autos; USD para exportación de autopartes.", "FI · TCURC"],
        ["REFERENCIA", "Genérica", "Familias de moto, modelos de auto y 158 referencias de autopartes.", "MM · MARA/MVKE"],
        ["SOCIEDAD", "Genérica", "FANALCA · SUPERMOTOS · SIM · METAL SUR.", "FI · T001"],
    ],
    widths=[1.1, 0.9, 3.6, 1.0], size=7.9)

b.para("Modelo 2 — EEFF Fanalca (7 dimensiones). Estado de Resultados + Balance + Flujo de Caja.",
       size=9.5, align='left', space_after=3)
b.table(
    ["Dimensión", "Tipo", "Descripción / uso", "Fuente"],
    [
        ["Version", "Estándar", "Misma configuración que el modelo de Ingresos.", "Estándar SAC"],
        ["CUENTA", "Genérica", "Cuentas de P&G y Balance. P&G «sábana» (con CSC) y P&G NIT (sin ventas internas).", "FI · SKA1/SKB1"],
        ["Date", "Estándar", "Dimensión temporal mensual.", "Estándar SAC"],
        ["AUDITORIA", "Genérica", "Script (envío desde origen) · Ajuste (manual).", "Definición manual"],
        ["CEBES", "Genérica", "Todos los CEBEs. El EEFF recibe de Ingresos y de Costos/Gastos.", "CO-PCA · CEPC"],
        ["MONEDA", "Genérica", "COP principal; giros financiados en USD.", "FI · TCURC"],
        ["SOCIEDAD", "Genérica", "FANALCA · SUPERMOTOS · SIM · METAL SUR · Compañía 6 (eliminaciones).", "FI · T001"],
    ],
    widths=[1.1, 0.9, 3.6, 1.0], size=7.9)

b.para("Modelo 3 — Costos y Gastos Fanalca (8 dimensiones). Nómina · CIF · OPEX desde UNOE.",
       size=9.5, align='left', space_after=3)
b.table(
    ["Dimensión", "Tipo", "Descripción / uso", "Fuente"],
    [
        ["Version", "Estándar", "Plan / Forecast / Real.", "Estándar SAC"],
        ["CUENTAS", "Genérica", "Cuentas de costos/gastos CO: MO directa (11), CIF (12), administrativos (2), financieros.", "CO · CSKA/CSKB"],
        ["Date", "Estándar", "Dimensión temporal mensual.", "Estándar SAC"],
        ["AUDITORIA", "Genérica", "Script (calculado) · Ajuste (manual desde UNOE).", "Definición manual"],
        ["CEBES", "Genérica", "PMF, EMM, AUC, DEF, AMB, TUP, MSR, PDB, PPC y transversales.", "CO-PCA · CEPC"],
        ["CECOS", "Genérica", "Centros de costo de producción, servicios, administrativos, mantenimiento e ingeniería.", "CO-CCA · CSKS"],
        ["MONEDA", "Genérica", "COP principal; USD para exportación.", "FI · TCURC"],
        ["SOCIEDAD", "Genérica", "FANALCA · SIM · METAL SUR.", "FI · T001"],
    ],
    widths=[1.1, 0.9, 3.6, 1.0], size=7.9)

b.h3("Flujo de cálculo y consolidación")
b.para(
    "El cálculo se distribuye entre los modelos de origen (Ingresos y Costos/Gastos) y el modelo de "
    "EEFF, que consolida. En SAP BPC actual se emplea la técnica de «destination app» en cada script; "
    "en SAC esta lógica se replica con Data Actions de escritura cruzada.")
b.figure(f"{IMG}/fanalca_flujo.png",
         "Figura 3. Flujo de cálculo y consolidación de modelos — Fanalca S.A.")
b.figure(f"{IMG}/fanalca_pxq.png",
         "Figura 4. Metodología de cálculo P×Q y juegos de cartera e inventario — Fanalca S.A.")

b.h3("Scripts y actividades de configuración")
b.para("Los siguientes paquetes/scripts identificados en SAP BPC se replican como Data Actions en SAC. "
       "Se listan por unidad de negocio.", size=9.5, align='left', space_after=4)
b.para("Scripts — Honda Supermotos / Motos", bold=True, size=9.5, align='left', space_after=2)
b.table(
    ["Data Action", "Descripción funcional", "Modelos", "Prioridad"],
    [
        ["T01 Motos (separar)", "Cálculo P×Q de ventas y costos de motos; genera facturación con IVA y envía a EEFF. Debe separarse del T01 de autos.", "Ingresos → EEFF", "Crítica"],
        ["Cartera motos", "Saldo inicial + Facturación con IVA − Recaudo = Saldo final del período siguiente.", "Ingresos", "Alta"],
        ["Inventarios motos", "Juego de inventarios en unidades y pesos; alimenta el balance del EEFF.", "Ingresos → EEFF", "Alta"],
        ["Ingresos HRC", "Ingresos y costos de repuestos (HRC): 13 agrupadores de referencias.", "Ingresos → EEFF", "Alta"],
        ["P01 Motopartes", "Compras nacionales de motopartes (MPC): MP + MO + CIF separados.", "Ingresos → EEFF", "Alta"],
        ["IVA descontable motos", "IVA descontable bimestral. Mejora propuesta: usar unidades de venta en vez de pago.", "Flujo de caja", "Media"],
    ],
    widths=[1.4, 3.4, 1.1, 0.7], size=7.9)
b.para("Scripts — Metalmecánica / Transformación de acero", bold=True, size=9.5, align='left', space_after=2)
b.table(
    ["Data Action", "Descripción funcional", "Modelos", "Prioridad"],
    [
        ["T02 EMM", "P×Q de Ensamble Medellín (12 referencias, cliente Renault/Sofasa).", "Ingresos → EEFF", "Alta"],
        ["Script autopartes", "P×Q de 158 referencias por cliente. Costo: MP + conversión (PMF) + alícuotas PDB/PPC.", "Ingresos → EEFF", "Alta"],
        ["Script TUP (×2)", "Tubería: 1ª corrida costo de lámina (CFR × factor); 2ª corrida precio de venta con margen.", "Ingresos → EEFF", "Alta"],
        ["Script Metal Sur (×2)", "Idéntico a TUP; dos plantas → distribución de MO/CIF por planta.", "Ingresos → EEFF", "Alta"],
        ["Script Ambiental", "P×Q de cajas compactadoras nacionales + CKD; lámina + kit hidráulico + MO/CIF de PMF.", "Ingresos → EEFF", "Alta"],
        ["Paquete UNOE → Gastos", "Importación de gastos desde UNOE al modelo de Costos y Gastos.", "Costos → EEFF", "Alta"],
        ["Distribución de transversales", "Alícuota de PPC (mantenimiento/calidad) y PDB (ingeniería) a las líneas productivas.", "Costos", "Alta"],
    ],
    widths=[1.4, 3.4, 1.1, 0.7], size=7.9)
b.para("Scripts — Honda Autos", bold=True, size=9.5, align='left', space_after=2)
b.table(
    ["Data Action", "Descripción funcional", "Modelos", "Prioridad"],
    [
        ["T01 Autos (separar)", "P×Q de vehículos HAC: FOB × factor × TRM = costo; precio × unidades = ingresos. Separar del T01 de motos.", "Ingresos → EEFF", "Crítica"],
        ["Inventario HAC", "Saldo inicial + Compras − Despachos a agencias = Saldo final. Inventario en zona franca.", "Ingresos → EEFF", "Alta"],
        ["Cartera HAC", "Cartera comercial (50/50) + cartera de renting ($12.000M, no se recauda en proyección).", "Ingresos", "Alta"],
        ["Cartera agencias", "Juego de cartera por agencia (80/20). Mejora: correr por jerarquía en SAC.", "Ingresos", "Alta"],
        ["Ingresos HPC + Talleres", "P×Q de HPC (margen 48%) e ingresos de talleres por tipo de servicio.", "Ingresos → EEFF", "Alta"],
        ["Costo de oportunidad", "(Cartera − Renting) × (IBR+spread) + (Inventario − Proveedores) × (SOFR+spread).", "Ingresos → EEFF", "Media"],
    ],
    widths=[1.4, 3.4, 1.1, 0.7], size=7.9)

b.para("Actividades de configuración en SAC", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Actividad", "Área", "Estado", "Prioridad"],
    [
        ["Creación de los 3 modelos SAC Planning", "Modelado SAC", "Completo", "Alta"],
        ["Separación del script T01 (motos / autos)", "Data Actions", "Pendiente", "Crítica"],
        ["Apertura de HOC en HOD / HON", "Modelado SAC", "Pendiente", "Alta"],
        ["Migración BPC → SAC (17+ scripts)", "Data Actions", "En progreso", "Alta"],
        ["Plantillas SAC instanciables (BPF)", "Planning", "En progreso", "Alta"],
        ["Integración S/4HANA → DataSphere → SAC", "Integración", "En progreso", "Alta"],
        ["Carga automática del real BW → SAC", "Integración", "Completo", "Alta"],
        ["Definición de jerarquías SD/FI/CO en S/4HANA", "Maestros", "Pendiente", "Alta"],
        ["Perfilamiento de acceso y roles SAC (DAC por sociedad)", "Seguridad", "Pendiente", "Alta"],
    ],
    widths=[3.4, 1.4, 1.0, 0.8], size=8.1)

b.h3("Roles")
b.table(
    ["Perfil", "Responsabilidad en SAC", "Unidad", "Acceso SAC"],
    [
        ["Key User Motos", "Mantiene datos de motos (CKD, CBU, repuestos, motopartes); valida plantillas y scripts.", "Supermotos / Motos", "Read/Write"],
        ["Key User Autos", "Mantiene datos de HAC, agencias, HPC, talleres y renting.", "Honda Autos", "Read/Write"],
        ["Líder funcional del proyecto", "Coordina sesiones técnicas, valida la arquitectura y define mejoras de configuración.", "Programa SAP BUILD", "Modeler / Admin"],
        ["Key Users Transformación de Acero", "Responsables de tubería, Metal Sur, PMF, ensamble Medellín, autopartes, defensas y ambiental.", "Metalmecánica", "Read/Write"],
        ["Equipo de TI / Transformación Digital", "Administra conectores SAC ↔ BW/DataSphere y desarrolla Data Actions.", "Transformación Digital", "Admin / Modeler"],
        ["Área de Costos y Contabilidad", "Entrega tarifas, costos promedio y reales mensuales para la versión Real.", "Finanzas / FI", "Viewer"],
        ["Consultor SAP / SAC", "Diseño y construcción de modelos, Data Actions y Stories; soporte técnico.", "Programa SAP BUILD", "Admin / Developer"],
    ],
    widths=[1.7, 3.0, 1.2, 0.7], size=7.9)

b.h3("Inventario de datos maestros susceptibles de migración")
b.para(
    "Los datos maestros se cargan en SAC desde los sistemas SAP (S/4HANA, FI, CO, SD, MM) mediante "
    "archivos CSV o conectores OData. Nota crítica: los identificadores de referencias en BPC no "
    "coinciden con los códigos del ERP; se requiere una tabla de mapeo antes de la carga.")
b.table(
    ["Dato maestro / dimensión", "Fuente SAP", "Método de carga", "Volumen", "Complejidad"],
    [
        ["SOCIEDAD", "FI · T001", "CSV manual", "≈7 sociedades", "Baja"],
        ["CEBES", "CO-PCA · CEPC", "CSV / OData", "≈50+ CEBEs", "Alta"],
        ["CECOS", "CO-CCA · CSKS", "CSV / OData", "≈40+ CECOS", "Alta"],
        ["CUENTA (EEFF)", "FI · SKA1/SKB1", "CSV / BW", "Plan de cuentas FI", "Alta"],
        ["CUENTAS (C&G)", "CO · CSKA/CSKB", "CSV / BW", "Plan de cuentas CO", "Alta"],
        ["CLIENTES", "SD · KNA1", "OData / CSV", "Red de distribuidores + agencias", "Alta"],
        ["REFERENCIA", "MM · MARA/MVKE", "CSV / BW", "158+ SKUs (mapeo BPC→SAP)", "Muy alta"],
        ["MONEDA", "FI · TCURC", "CSV manual", "COP · USD · EUR", "Baja"],
        ["TRM / Macroeconómicas", "Tesorería / DIAN", "CSV por escenario", "TRM · IBR · SOFR · IPC", "Media"],
    ],
    widths=[1.9, 1.3, 1.3, 1.3, 0.8], size=7.9)
b.callout("Prioridad de carga de datos maestros — Fanalca S.A.",
          ["Fase 1 (crítica, pre Go-Live): SOCIEDAD, CEBES, MONEDA, Version y AUDITORIA — sin estas no corren los scripts.",
           "Fase 2 (configuración de modelos): CECOS, CUENTA, CUENTAS y CLIENTES.",
           "Fase 3 (históricos y transaccionales 2024–2025): REFERENCIA, RATIO y datos reales.",
           "Habilitador clave: tabla de mapeo entre los identificadores BPC y los códigos del ERP S/4HANA."],
          accent=NAVY)

b.h3("Componentes de solución técnica")
b.para(
    "La arquitectura técnica se basa en SAP BTP como plataforma central, con SAP DataSphere como capa "
    "de integración y transformación entre SAP S/4HANA y SAC. La migración desde SAP BPC implica "
    "replicar la lógica de scripts y plantillas en sus equivalentes de SAC.")
b.table(
    ["Componente", "Descripción", "Estado"],
    [
        ["SAP Analytics Cloud (SAC)", "Plataforma SaaS en SAP BTP (DEV/QA/PRD). Planning, Stories, Data Actions y BPF.", "Activo (2024.Q4+)"],
        ["SAP S/4HANA", "ERP en implementación; fuente futura del real y de los datos maestros (FI, CO, SD, MM).", "En implementación"],
        ["SAP BPC", "Sistema de planeación actual (17+ scripts). Referencia para la migración a SAC.", "A migrar"],
        ["SAP BW/4HANA", "Data Warehouse para la carga del real (Supermotos, FN Servicios ya conectados).", "Activo (parcial)"],
        ["SAP DataSphere", "Capa de integración/transformación entre S/4HANA y SAC; evita replicar datos.", "En configuración"],
        ["UNOE", "Sistema de presupuesto de gastos; origen del modelo de Costos y Gastos.", "Activo"],
        ["SAC Excel Add-in", "Carga de datos desde plantillas. Requiere Office 365 de 64 bits.", "Validado con key users"],
        ["SAP IAS / SSO", "Single Sign-On para el acceso a SAC mediante SAP Identity Authentication Service.", "Activo"],
    ],
    widths=[1.8, 3.8, 1.0], size=7.9)
b.para("Decisiones de diseño y mejoras de arquitectura", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Decisión / mejora", "Descripción"],
    [
        ["Separar T01 en dos Data Actions", "El script T01 cubre motos y autos; al correr parcialmente puede sobreescribir datos. SAC debe tener dos Data Actions independientes."],
        ["Apertura de HOC en HOD/HON", "El P&G de CBU debe reflejar los tres CEBEs (HOC compra; HOD/HON venden)."],
        ["Correr scripts por jerarquía", "Algunos paquetes corren individualmente por CEBE; SAC permite correr sobre la jerarquía completa, reduciendo tiempos."],
        ["Plantillas instanciables para autos", "Migrar las consultas Excel fijas a plantillas SAC instanciables con BPF y selector de CEBE/escenario."],
        ["Referencia dummy para IVA", "Usar una referencia genérica para que el script aplique IVA a todas, reduciendo entradas manuales."],
    ],
    widths=[1.9, 4.7], size=8.1)


# =====================================================================
# 4. CIUDAD LIMPIA
# =====================================================================
b.page_break()
b.h1("Ciudad Limpia")
b.para(
    "Ciudad Limpia es una empresa de servicios públicos de aseo urbano que opera en Bogotá, Neiva, "
    "Huila y otros municipios. Sus empresas relacionadas CGS y RH gestionan residuos peligrosos y "
    "aprovechamiento. El proceso presupuestal actual está íntegramente basado en macros de Excel, con "
    "consolidación manual a cargo de Planeación Financiera; el proyecto lo migra a SAP Analytics Cloud.")

b.h2("Escenario / Proceso de negocio")
b.para(
    "La operación requiere un control financiero riguroso sobre ingresos, costos y gastos, así como la "
    "generación de estados financieros consolidados. Los ingresos ordinarios se calculan a partir de "
    "variables tarifarias complejas (toneladas, usuarios, kilómetros, metros cuadrados, estratos, "
    "subsidios e IPC); el equipo de tarifas entrega a Planeación Financiera el valor total por "
    "componente, que es el dato que se carga en SAC. Las empresas CGS y RH sí permiten calcular P×Q "
    "(tarifa × cantidad) por cliente y tipo de residuo.")

b.h3("Objetivos empresariales y beneficios esperados")
b.table(
    ["Código", "Objetivo", "Beneficio esperado"],
    [
        ["OE-01", "Centralizar la información financiera en SAC", "Fin de la fragmentación en decenas de hojas de Excel."],
        ["OE-02", "Automatizar la consolidación del presupuesto", "Proceso de semanas reducido a horas/minutos."],
        ["OE-03", "Habilitar un forecast ágil", "Actualización rápida ante cambios de tarifa o dotación."],
        ["OE-04", "Visibilidad en tiempo real para los gerentes", "Cada área consulta SAC sin intermediar a Planeación."],
        ["OE-05", "Auditoría y trazabilidad completa", "Origen claro de cada dato: real, presupuesto o manual."],
        ["OE-06", "Generar EEFF con mínima intervención manual", "Reducción de errores en el cierre mensual."],
    ],
    widths=[0.8, 2.9, 2.9], size=8.4)

b.h3("Descripción a alto nivel de requisitos empresariales")
b.table(
    ["Código", "Requisito", "Descripción"],
    [
        ["RE-01", "Ingresos ordinarios de Ciudad Limpia", "Cargar el valor total por componente desde el resumen del jefe de tarifas, sin replicar el cálculo tarifario complejo."],
        ["RE-02", "Ingresos CGS y RH (P×Q)", "Cálculo tarifa × toneladas/kilos por cliente y tipo de residuo, con seguimiento de cantidades."],
        ["RE-03", "Plantilla genérica de gastos", "Una plantilla Excel estándar para las ≈17 áreas; Planeación Financiera consolida y carga."],
        ["RE-04", "Costos de flota", "Un centro de costo por vehículo. Rubros: repuestos, llantas, combustibles y lubricantes."],
        ["RE-05", "Mano de obra y gasto de personal", "Representa ≈80% del costo total. Se modela con una plantilla de personal basada en un modelo referencial; el nivel de detalle se afina con Talento Humano."],
        ["RE-06", "Estados financieros", "El P&G fluye automáticamente; el Balance y el Flujo de Caja incorporan cuentas adicionales por carga manual."],
        ["RE-07", "Multimoneda", "Soporte de múltiples monedas por sociedad."],
        ["RE-08", "Gestión de versiones", "Actual / Presupuesto / Forecast. Regla: siempre el dato final autorizado, sin acumulación."],
        ["RE-09", "Auditoría", "Dimensión AUDITORIA para identificar el origen de cada dato."],
        ["RE-10", "Opciones de carga", "Reemplazar / Acumular / Borrar y recargar. Estándar acordado: Reemplazar con el dato definitivo."],
        ["RE-11", "Dashboards y KPIs", "Filtros por sociedad/área/período, exportables a PDF/PPT. KPIs: toneladas, km, usuarios, árboles."],
    ],
    widths=[0.8, 2.0, 3.8], size=8.0)

b.h2("Estructura organizativa relevante")
b.para("Sociedades", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Sociedad", "Empleados", "Descripción"],
    [
        ["Ciudad Limpia Bogotá", "≈1.900", "Principal. Ingresos ordinarios complejos."],
        ["Ciudad Limpia Neiva", "≈500", "Particularidades tarifarias propias."],
        ["Ciudad Limpia Huila", "≈37", "Operación pequeña."],
        ["CGS", "≈182", "Residuos peligrosos y aseo en municipios. Modelo P×Q."],
        ["RH", "En proceso", "Residuos peligrosos. Ingresando a nómina web."],
    ],
    widths=[1.9, 1.2, 3.5], size=8.4)
b.para("Componentes de servicio (centros de beneficio)", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Componente", "Métrica de seguimiento", "Observación"],
    [
        ["Recolección", "Toneladas recolectadas", "CEBE específico en S/4HANA"],
        ["Barrido de vías", "Kilómetros barridos", "CEBE específico"],
        ["Corte de césped", "Metros cuadrados cortados", "CEBE específico"],
        ["Poda de árboles", "Cantidad de árboles podados", "CEBE específico"],
        ["Aprovechamiento", "Toneladas aprovechadas", "CGS / RH"],
        ["Comercialización", "Valor facturado", "Otros ingresos"],
    ],
    widths=[1.7, 2.5, 2.4], size=8.4)

b.h2("Diseño y configuración de soluciones")
b.h3("Arquitectura de la solución")
b.para(
    "La arquitectura integra las fuentes de datos, una capa de dimensiones compartidas, los tres "
    "modelos SAC y las salidas de consumo. Los datos reales provienen de SAP S/4HANA mediante conexión "
    "nativa (CDS Views); el presupuesto se carga por plantillas Excel y los ajustes se ingresan "
    "directamente en SAC.")
b.figure(f"{IMG}/ciudad_arq.png",
         "Figura 5. Arquitectura de la solución SAP Analytics Cloud — Ciudad Limpia.")

b.h3("Modelos SAC y dimensiones")
b.para("Modelo de Ingresos — captura, planificación y análisis de ingresos operativos. Soporta carga "
       "de ingresos ordinarios (valor total) y cálculo P×Q para CGS y RH.", size=9.5, align='left', space_after=3)
b.table(
    ["Medida", "Tipo de dato", "Descripción"],
    [
        ["Importe", "Decimal (moneda)", "Valor monetario del ingreso."],
        ["Cantidad", "Decimal", "Toneladas / kilos (aplica a CGS/RH para P×Q)."],
        ["Tarifa", "Decimal (moneda)", "Precio unitario por tipo de residuo (CGS/RH)."],
    ],
    widths=[1.4, 1.8, 3.4], size=8.4)
b.table(
    ["Dimensión", "Tipo SAC", "Pública", "Notas"],
    [
        ["Version", "Version", "No", "Actual / Presupuesto / Forecast."],
        ["CUENTA", "Account", "Sí", "Ingresos por componente. Jerarquías EEFF y de gestión."],
        ["Date", "Date", "No", "Granularidad mensual."],
        ["CEBE_CL", "Generic", "Sí", "Componente de servicio (Recolección, Barrido…)."],
        ["AUDITORIA", "Generic", "Sí", "Origen: REAL_S4 / PRESUPUESTO_TARIFAS / PXQ."],
        ["MONEDA", "Generic", "Sí", "Moneda de la transacción."],
        ["CLIENTE", "Generic", "No", "Solo CGS/RH — cliente y tipo de residuo."],
        ["SOCIEDAD_CL", "Organization", "Sí", "Data Access Control por entidad legal."],
    ],
    widths=[1.4, 1.2, 0.8, 3.2], size=8.2)
b.para("Lógica de carga por sociedad", bold=True, size=9.5, align='left', space_after=2)
b.table(
    ["Sociedad", "Método", "Responsable del dato"],
    [
        ["CL Bogotá / Neiva / Huila", "Valor total por componente desde el Excel del jefe de tarifas", "Jefe Nacional de Tarifas → Planeación Financiera"],
        ["CGS / RH", "Cálculo P×Q: tarifa × toneladas/kilos por cliente y residuo", "Áreas CGS/RH → Planeación Financiera"],
    ],
    widths=[1.9, 2.9, 1.8], size=8.2)

b.para("Modelo de Gastos / Costos — planificación, control y análisis de costos operativos y gastos por "
       "centro de costo, componente de servicio, cuenta y sociedad.", size=9.5, align='left', space_after=3)
b.table(
    ["Dimensión", "Tipo SAC", "Pública", "Notas"],
    [
        ["Version", "Version", "No", "Actual / Presupuesto / Forecast."],
        ["CUENTA", "Account", "Sí", "Cuentas de costos y gastos."],
        ["Date", "Date", "No", "Mensual."],
        ["CECO_CL", "Generic", "Sí", "Centro de costo (área / vehículo de flota)."],
        ["CEBE_CL", "Generic", "Sí", "Componente de servicio / línea de negocio."],
        ["AUDITORIA", "Generic", "Sí", "Origen: REAL_S4 / PRESUPUESTO_EXCEL / MANUAL."],
        ["MONEDA", "Generic", "Sí", "Moneda."],
        ["SOCIEDAD_CL", "Organization", "Sí", "Data Access Control por entidad legal."],
    ],
    widths=[1.4, 1.2, 0.8, 3.2], size=8.2)
b.para("Categorías de gasto y método de carga", bold=True, size=9.5, align='left', space_after=2)
b.table(
    ["Categoría", "Descripción", "Método en SAC"],
    [
        ["Mano de obra", "≈80% del costo total", "Plantilla de personal (modelo referencial)"],
        ["Mantenimiento de flota", "Repuestos, llantas, combustible", "Valor por CECO (un CECO por vehículo)"],
        ["Depreciaciones", "Activos fijos", "Plantilla genérica"],
        ["TIC y tecnología", "Equipos, licencias, mantenimiento", "Plantilla genérica"],
        ["Servicios públicos", "Agua, energía, telefonía", "Plantilla genérica"],
        ["Arrendamientos", "Infraestructura y equipos", "Plantilla genérica"],
        ["Dotación de personal", "EPP, uniformes, reposiciones", "Plantilla genérica"],
        ["Seguros y gastos generales", "Pólizas, honorarios, viajes, diversos", "Plantilla genérica"],
    ],
    widths=[1.9, 2.9, 1.8], size=8.2)

b.para("Modelo de EEFF — consolida P&G, Balance General y Flujo de Caja. Alimenta reportes internos "
       "(gerentes, junta) y externos.", size=9.5, align='left', space_after=3)
b.table(
    ["Componente del EEFF", "Lógica de alimentación"],
    [
        ["Estado de Resultados (P&G)", "Fluye automáticamente desde los modelos de Ingresos y Gastos/Costos."],
        ["Balance — cuentas de P&G", "Las cuentas de resultado impactan automáticamente el balance (utilidad del período)."],
        ["Balance — cuentas propias", "Activos fijos, cartera, deuda y capital: carga manual o integración directa con S/4HANA."],
        ["Flujo de Caja", "Combinación: parte fluye del P&G, parte del balance y parte por carga manual (impuestos, CAPEX, inversiones)."],
        ["Depreciaciones acumuladas", "Fluyen desde el rubro de depreciaciones del modelo de gastos."],
        ["CAPEX / inversiones en flota", "Carga manual; proceso particular que no fluye directamente del P&G."],
    ],
    widths=[2.1, 4.5], size=8.4)

b.para("Dimensiones compartidas y maestros de datos", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Dimensión", "Tipo SAC", "Fuente maestra", "Descripción"],
    [
        ["CUENTA", "Account", "S/4HANA SKA1/SKB1", "Plan de cuentas completo. Jerarquías LR3 y de gestión interna."],
        ["CEBE_CL", "Generic", "S/4HANA CEPC", "Centros de beneficio / componentes de servicio (en los 3 modelos)."],
        ["CECO_CL", "Generic", "S/4HANA CSKS", "Centros de costo, incluido un CECO por vehículo (solo en Gastos)."],
        ["AUDITORIA", "Generic", "Maestra SAC", "REAL_S4, PRESUPUESTO_TARIFAS, PRESUPUESTO_EXCEL, PXQ, MANUAL, AJUSTE."],
        ["MONEDA", "Generic", "Maestra SAC", "Monedas operativas; evaluar Currency Translation para consolidados."],
        ["SOCIEDAD_CL", "Organization", "S/4HANA T001", "Habilita Data Access Control por entidad legal."],
    ],
    widths=[1.3, 1.1, 1.6, 2.6], size=7.9)
b.para("Resumen comparativo de modelos", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Elemento", "Gastos/Costos", "EEFF", "Ingresos"],
    [
        ["Importe (medida)", "✔", "✔", "✔"],
        ["Version · CUENTA · Date", "✔", "✔", "✔"],
        ["CEBE_CL · AUDITORIA · MONEDA · SOCIEDAD_CL", "✔", "✔", "✔"],
        ["CECO_CL", "✔", "—", "—"],
        ["CLIENTE", "—", "—", "✔ (CGS/RH)"],
        ["Cantidad y Tarifa (P×Q)", "—", "—", "✔ (CGS/RH)"],
    ],
    widths=[3.0, 1.2, 1.0, 1.4], size=8.2)

b.h3("Flujo de cálculo y consolidación")
b.para(
    "El P&G fluye automáticamente desde los modelos de Ingresos y Gastos/Costos hacia el EEFF; las "
    "cuentas propias del balance y del flujo de caja se cargan desde S/4HANA o manualmente.")
b.figure(f"{IMG}/ciudad_flujo.png",
         "Figura 6. Flujo de cálculo y consolidación de modelos — Ciudad Limpia.")
b.figure(f"{IMG}/ciudad_pxq.png",
         "Figura 7. Metodología de cálculo P×Q para CGS / RH — Ciudad Limpia.")
b.callout("Regla de diseño acordada en la Sesión N°1 (lección aprendida de BPC)",
          ["Cada responsable entrega el DATO FINAL AUTORIZADO; no se cargan versiones parciales ni acumulaciones.",
           "El sistema usa la opción de carga «Reemplazar»: el último dato cargado es el definitivo.",
           "Las modificaciones puntuales se hacen directamente en la plantilla SAC, sin recargar el archivo completo."],
          accent=RED, fill="FBEAEA")

b.h3("Integración y plantillas de carga")
b.table(
    ["Fuente", "Mecanismo", "Frecuencia", "Objetos clave"],
    [
        ["SAP S/4HANA (real)", "CDS Views / conexión nativa SAC–S4", "Diaria (fuera de horario)", "ACDOCA, SKA1, CEPC, CSKS, T001"],
        ["Excel / Plantillas (presupuesto)", "Carga de archivo en SAC Data Management", "Anual + forecast", "Plantillas estándar por categoría"],
        ["Input manual SAC (ajustes)", "Entrada directa en plantilla SAC", "Bajo demanda", "Solo Planeación Financiera"],
    ],
    widths=[1.9, 2.0, 1.5, 1.2], size=8.0)
b.table(
    ["Plantilla", "Estructura de columnas", "Responsable"],
    [
        ["Ingresos Ordinarios CL", "Sociedad | CEBE (componente) | Cuenta | Ene–Dic", "Jefe de Tarifas → Planeación Fin."],
        ["Ingresos P×Q — CGS/RH", "Sociedad | CEBE | Cliente | Tipo residuo | Cuenta | Tarifa | Cant. | Ene–Dic", "Áreas CGS/RH → Planeación Fin."],
        ["Gastos y Costos (genérica)", "Sociedad | CECO | CEBE | Cuenta | Ene–Dic", "Todas las áreas → Planeación Fin."],
    ],
    widths=[1.7, 3.4, 1.5], size=8.0)

b.h3("Roles y seguridad")
b.callout("Política de licenciamiento acordada en sesión",
          ["Las licencias SAC se asignan únicamente al equipo de Planeación Financiera.",
           "Las áreas operativas no acceden a SAC para carga directa: entregan plantillas Excel que el equipo consolida.",
           "Lección aprendida: licenciar usuarios que acceden una vez al año genera más costo de soporte que beneficio."],
          accent=NAVY)
b.table(
    ["Rol", "Nivel de acceso", "Descripción"],
    [
        ["Administrador SAC", "Total", "Configura modelos, dimensiones, conexiones y usuarios."],
        ["Planeación Financiera", "Lectura / Escritura", "Versiones de plan, carga de archivos Excel y ajustes manuales."],
        ["Gerente / Ejecutivo", "Solo lectura", "Dashboards y reportes, filtrados por la sociedad asignada."],
        ["Auditor", "Solo lectura", "Acceso histórico a todas las versiones y sociedades."],
    ],
    widths=[1.8, 1.6, 3.2], size=8.4)


# =====================================================================
# 5. TRANSPRENSA S.A.S.
# =====================================================================
b.page_break()
b.h1("Transprensa S.A.S.")
b.para(
    "Transprensa S.A.S. es una empresa de logística y transporte de carga del Grupo Fanalca, con "
    "operaciones en 21 regionales a lo largo de Colombia y 46 Centros de Recibo de Mercancía (CRM). "
    "Sus líneas de negocio son el paqueteo (B2B y B2C), el servicio masivo, los vehículos dedicados, el "
    "almacenamiento y los ingredientes/mercancías peligrosas. El proyecto migra su planificación "
    "financiera —hoy en Excel y Power BI— a SAP Analytics Cloud.")

b.h2("Escenario / Proceso de negocio")
b.para(
    "La presupuestación se realiza de forma centralizada desde el área financiera, con insumos de la "
    "gerencia general y la gerencia comercial. Los datos operativos provienen del software logístico "
    "Silotrans y del sistema contable SIESA. La metodología de ingresos es P×Q: kilogramos movilizados "
    "× tarifa por kilogramo, por regional y tipo de servicio.")

b.h3("Objetivos empresariales y beneficios esperados")
b.table(
    ["#", "Objetivo empresarial", "Beneficio esperado"],
    [
        ["1", "Centralizar la planeación financiera en SAC", "Eliminar los silos de información en Excel; control de versiones."],
        ["2", "Automatizar el cálculo P×Q por regional y servicio", "Reducción de errores y mayor velocidad en los ciclos de presupuesto."],
        ["3", "Habilitar el multi-versionamiento presupuestal", "Versión comercial vs. financiera; escenarios y simulaciones."],
        ["4", "Integrar la ejecución real desde Silotrans y S/4HANA", "Comparación presupuesto vs. real en tiempo real."],
        ["5", "Visibilidad de P&G y EBITDA por regional", "Toma de decisiones a nivel de regional y centro de beneficio."],
        ["6", "Estacionalidad y ajuste dinámico de mano de obra", "Optimización de costos de personal temporal ligado a kg."],
    ],
    widths=[0.4, 3.0, 3.2], size=8.4)

b.h3("Descripción a alto nivel de requisitos empresariales")
b.table(
    ["ID", "Área", "Requisito", "Modelo"],
    [
        ["REQ-01", "Ingresos", "Presupuestar ingresos por regional y tipo de servicio (paqueteo, masivo, almacenamiento).", "Ingresos"],
        ["REQ-02", "Ingresos", "Cálculo P×Q: kilogramos proyectados × tarifa ($/kg) por regional.", "Ingresos"],
        ["REQ-03", "Ingresos", "Discriminar ingresos por tipo: crédito (B2B) vs. contado/contraentrega (CRM).", "Ingresos"],
        ["REQ-04", "Ingresos", "Presupuestar clientes especiales por separado (Ingreso, T1, Soy Más).", "Ingresos"],
        ["REQ-05", "Ingresos", "Definir la estacionalidad mensual con base en el histórico N-1.", "Ingresos"],
        ["REQ-06", "Ingresos", "Soporte multi-versión: Presupuesto Comercial y Presupuesto Financiero.", "Ingresos"],
        ["REQ-07", "Costos", "Presupuesto de fletes de transporte por regional y destino (desde Silotrans).", "Costos"],
        ["REQ-08", "Costos", "Personal temporal variable ligado a kg: índice de personal por kg movilizado.", "Costos"],
        ["REQ-09", "Costos", "Arrendamientos por contrato: IPC + factor, ponderado por tipo de servicio.", "Costos"],
        ["REQ-10", "Costos", "Gastos fijos (histórico N-1 + IPC): honorarios, servicios públicos, ICA por ciudad.", "Costos"],
        ["REQ-11", "EEFF", "Estado de Resultados (P&G administrativo – PCGA) con apertura por regional.", "EEFF"],
    ],
    widths=[0.7, 0.9, 4.3, 0.7], size=7.9)

b.para("Metodología de cálculo de costos", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Tipo de costo", "Descripción", "Driver", "Fuente"],
    [
        ["Fletes de expedición", "Costo de flete por kg despachado por regional", "Kg × tarifa de flete por destino", "Silotrans"],
        ["Mano de obra temporal", "Personal de plataforma y ruta, variable según kg", "Índice persona/kg por regional", "Nómina SIESA"],
        ["Fletes de reexpedición", "Porción del flete a destinos sin flota propia", "% histórico de kg a terceros", "Silotrans"],
        ["Comisiones CRM externos", "Comisión pagada a CRM externos por kg", "Kg CRM ext. × tarifa de comisión", "Silotrans"],
        ["Comisiones fuerza de ventas", "Parte variable del salario comercial por kg", "Kg crédito × índice", "SIESA"],
        ["Arrendamientos", "Contrato por sede, ponderado por servicio", "IPC + factor contractual", "Contratos"],
        ["Gastos fijos (IPC)", "Honorarios, servicios públicos, asistencia técnica", "Histórico N-1 × IPC", "SIESA"],
    ],
    widths=[1.6, 2.5, 1.7, 0.8], size=7.9)

b.h2("Estructura organizativa relevante")
b.para(
    "Transprensa opera bajo una estructura matricial: una dirección nacional centralizada en Bogotá con "
    "21 regionales operativas distribuidas en el país.")
b.table(
    ["Entidad organizativa", "Descripción", "Dimensión SAC", "Ejemplos"],
    [
        ["Sociedad", "Unidad legal de reporte financiero", "SOCIEDAD_TRANS", "Transprensa S.A.S."],
        ["Regional / Sede", "21 regionales operativas en Colombia", "CEBE_TRANS", "Antioquia, Valle, Cundinamarca, Eje Cafetero"],
        ["CRM", "46 Centros de Recibo de Mercancía (propios y externos)", "CLIENTE / CEBE", "CRM Antioquia, CRM Valle, CRM Santa Marta"],
        ["Tipo de servicio", "Línea de negocio / canal de venta", "SERVICIO", "Paqueteo, Masivo, Almacenamiento, Dedicados"],
        ["Centro de costo", "Unidad funcional para asignación de costos", "CECOS_TRANS", "Plataforma Regional, Ruta, Fuerza de Ventas"],
        ["Centro de beneficio", "Agrupación por tipo de servicio / negocio", "CEBE_TRANS", "Paqueteo, Masivo, Almacenamiento"],
        ["Cliente especial", "Clientes de alta representatividad (≈30% de ingresos)", "CLIENTE", "Ingreso, T1, Soy Más (licitaciones)"],
    ],
    widths=[1.5, 2.5, 1.3, 1.3], size=7.9)
b.callout("Regiones de operación de Transprensa",
          ["Antioquia · Valle del Cauca · Cundinamarca · Eje Cafetero (Armenia, Manizales, Pereira).",
           "Santander · Nariño · Bolívar · Atlántico · Santa Marta · Tolima · Meta.",
           "21 regionales en total — cobertura nacional con 46 CRM activos.",
           "Sede operativa Funza (almacén Sodimac) para la distribución de Soy Más."],
          accent=GREEN, fill="EAF3E6")

b.h2("Diseño y configuración de soluciones")
b.h3("Arquitectura de la solución")
b.para(
    "El alcance contempla tres modelos de planeación interconectados. Los modelos de Ingresos y "
    "Gastos/Costos alimentan el modelo de EEFF, generando el P&G administrativo por regional y el "
    "consolidado. La integración con SAP S/4HANA y Silotrans se realiza a través de SAP DataSphere.")
b.figure(f"{IMG}/transprensa_arq.png",
         "Figura 8. Arquitectura de la solución SAP Analytics Cloud — Transprensa S.A.S.")

b.h3("Modelos SAC y dimensiones")
b.table(
    ["Modelo SAC", "Medida", "Dimensiones", "Capacidades"],
    [
        ["Ingresos Transprensa", "Importe (decimal)", "Version · CUENTA · Date · MONEDA · CLIENTE · SERVICIO · AUDITORIA · CEBE_TRANS · SOCIEDAD_TRANS", "P×Q por regional · multi-versión"],
        ["Gastos y Costos Transprensa", "Importe (decimal)", "Version · CUENTA · Date · MONEDA · CECOS_TRANS · AUDITORIA · CEBE_TRANS · SOCIEDAD_TRANS", "Costos variables y fijos · centros de costo"],
        ["EEFF Transprensa", "Importe (decimal)", "Version · CUENTA · Date · MONEDA · AUDITORIA · CEBE_TRANS · SOCIEDAD_TRANS", "Estado de Resultados · Balance · Flujo de Caja"],
    ],
    widths=[1.6, 1.1, 2.7, 1.2], size=7.8)
b.para("Detalle de dimensiones por modelo", bold=True, size=9.5, align='left', space_after=2)
b.table(
    ["Dimensión", "Tipo SAC", "Ingresos", "Gastos/Costos", "EEFF"],
    [
        ["Version", "Version", "✔", "✔", "✔"],
        ["CUENTA", "Account", "✔", "✔", "✔"],
        ["Date", "Date", "✔", "✔", "✔"],
        ["MONEDA", "Generic", "✔", "✔", "✔"],
        ["AUDITORIA", "Generic", "✔", "✔", "✔"],
        ["CEBE_TRANS", "Organization", "✔", "✔", "✔"],
        ["SOCIEDAD_TRANS", "Generic", "✔", "✔", "✔"],
        ["CLIENTE", "Generic", "✔", "—", "—"],
        ["SERVICIO", "Generic", "✔", "—", "—"],
        ["CECOS_TRANS", "Generic", "—", "✔", "—"],
    ],
    widths=[1.7, 1.5, 1.1, 1.3, 1.0], size=8.1)
b.para("Configuración de versiones presupuestales", bold=True, size=9.5, align='left', space_after=2)
b.table(
    ["Versión", "Descripción", "Uso"],
    [
        ["PRESUPUESTO_FIN", "Presupuesto Financiero oficial", "Base para el P&G y el seguimiento financiero."],
        ["PRESUPUESTO_COM", "Presupuesto Comercial", "Meta para la fuerza de ventas y las regionales."],
        ["REAL", "Ejecución real (actuals)", "Datos de Silotrans / SAP S/4HANA vía DataSphere."],
        ["FORECAST", "Proyección intra-año", "Actualización de estimados durante el año."],
    ],
    widths=[1.7, 2.3, 2.6], size=8.4)

b.h3("Flujo de cálculo y consolidación")
b.para(
    "Los modelos de Ingresos y Costos alimentan el EEFF con el P&G y el EBITDA por regional. El cálculo "
    "de ingresos sigue la metodología P×Q a partir del histórico N-1, los crecimientos de volumen y "
    "tarifa, la distribución CRM/Crédito y la estacionalidad mensual.")
b.figure(f"{IMG}/transprensa_flujo.png",
         "Figura 9. Flujo de cálculo y consolidación de modelos — Transprensa S.A.S.")
b.figure(f"{IMG}/transprensa_pxq.png",
         "Figura 10. Metodología de cálculo P×Q de ingresos — Transprensa S.A.S.")

b.h3("Actividades de configuración")
b.table(
    ["Actividad", "Descripción", "Prioridad", "Estado"],
    [
        ["Creación de modelos SAC", "Crear los 3 modelos Planning con sus dimensiones y medidas.", "Alta", "Completado"],
        ["Carga de datos maestros", "Cargar jerarquías de CUENTA, CEBE_TRANS, CECOS_TRANS, CLIENTE y SERVICIO.", "Alta", "Pendiente"],
        ["Configurar versiones", "Definir PRESUPUESTO_FIN, PRESUPUESTO_COM, REAL y FORECAST.", "Alta", "Pendiente"],
        ["Plantillas de entrada de datos", "Diseñar input forms para la carga por región y servicio.", "Alta", "Pendiente"],
        ["Data Actions P×Q", "Cálculo automático de ingresos (kg × tarifa).", "Alta", "Pendiente"],
        ["Data Action de personal temporal", "Ajuste del personal temporal según la variación de kg.", "Media", "Pendiente"],
        ["Conectores DataSphere", "Extracción de Silotrans y S/4HANA hacia DataSphere.", "Alta", "En definición"],
        ["Estacionalidad e históricos N-1", "Cargar factores de estacionalidad y la ejecución real 2025.", "Media", "Pendiente"],
    ],
    widths=[1.9, 3.0, 0.9, 0.8], size=7.9)

b.h3("Roles")
b.table(
    ["Rol", "Acceso SAC", "Responsabilidades"],
    [
        ["Administrador SAC", "Full admin", "Configuración de modelos, dimensiones, data actions y versiones."],
        ["Planeador Financiero", "Lectura / Escritura", "Carga y validación del presupuesto por regional y servicio."],
        ["Analista Comercial", "Lectura / Escritura", "Definición de crecimientos por regional; revisión del Presupuesto Comercial."],
        ["Gerencia Regional", "Solo lectura", "Consulta del presupuesto y la ejecución de su regional."],
        ["Gerencia General / CFO", "Solo lectura", "Reportes consolidados, P&G, EBITDA y Junta Directiva."],
    ],
    widths=[1.8, 1.5, 3.3], size=8.4)

b.h3("Inventario de datos maestros susceptibles de migración")
b.para(
    "La fuente de verdad es SAP S/4HANA; Silotrans es fuente complementaria para los datos operativos "
    "(clientes, servicios y regionales).")
b.table(
    ["Dato maestro", "Dimensión", "Fuente", "Jerarquía / niveles", "Volumen"],
    [
        ["Plan de cuentas", "CUENTA", "S/4HANA (SKA1)", "Clase → Grupo → Cuenta", "≈500 cuentas"],
        ["Centros de beneficio", "CEBE_TRANS", "S/4HANA (CEPC)", "Sociedad → Servicio → Regional", "≈30 CEBE"],
        ["Centros de costo", "CECOS_TRANS", "S/4HANA (CSKS)", "Sociedad → Área → Centro", "≈80 CECOS"],
        ["Clientes / Regionales", "CLIENTE", "Silotrans / SD", "Regional → CRM / Ejecutivo", "≈50 + especiales"],
        ["Tipos de servicio", "SERVICIO", "Silotrans", "Categoría → Subcategoría", "≈15 servicios"],
        ["Monedas", "MONEDA", "S/4HANA", "COP (principal) / USD", "2 monedas"],
        ["Sociedad", "SOCIEDAD_TRANS", "S/4HANA (T001)", "Grupo Fanalca → Transprensa", "1 sociedad"],
        ["Versiones", "Version", "SAC", "Real · Pto Fin · Pto Com · Forecast", "4 versiones"],
    ],
    widths=[1.5, 1.3, 1.2, 1.8, 0.8], size=7.9)
b.callout("Consideraciones de alineación con los módulos SAP",
          ["Coordinar con los equipos SD / FI / CO las jerarquías definitivas antes de cargar en SAC.",
           "Granularidad de CECOS_TRANS: este año sin CECOS en el presupuesto; objetivo de incluirlos en 2027.",
           "Confirmar la fuente de datos reales: SAP S/4HANA vs. Silotrans (en definición)."],
          accent=NAVY)

b.h3("Componentes de solución técnica")
b.table(
    ["Componente", "Rol en la solución", "Estado"],
    [
        ["SAP Analytics Cloud (SAC)", "Plataforma de planeación: modelos, input forms, data actions y dashboards.", "Activo"],
        ["SAP DataSphere", "Capa de integración, virtualización y maestros entre SAC y los sistemas fuente.", "En configuración"],
        ["SAP S/4HANA", "Fuente de datos contables: SKA1, CEPC, CSKS y ACDOCA.", "En implementación"],
        ["Silotrans / Silotrack", "Fuente operativa: kg, remesas, clientes, origen-destino y tarifas.", "Activo (continúa)"],
        ["SIESA (contabilidad y nómina)", "Fuente histórica de P&G y nómina hasta el Go-Live de S/4HANA.", "Activo (transitorio)"],
        ["Power BI / Excel (actual)", "Proceso actual de presupuestación, a reemplazar por SAC.", "A reemplazar"],
    ],
    widths=[1.9, 3.7, 1.0], size=7.9)
b.para("Modelos SAC en construcción (fuera del alcance actual)", bold=True, size=10, align='left', space_after=3)
b.table(
    ["Modelo", "Descripción", "Dimensiones clave", "Estado"],
    [
        ["Talento Humano", "Presupuesto de nómina a nivel de empleado; integración con SIESA Payroll.", "Empleado · CECOS · CEBE · Cargo · Contrato", "En diseño"],
        ["Flujo de Caja Diario", "Gestión de liquidez por método directo; proyección semanal/diaria.", "Fecha · Cuenta · Tipo de flujo · Sociedad", "En diseño"],
    ],
    widths=[1.4, 2.8, 1.6, 0.8], size=7.9)


# =====================================================================
b.save("Documento_Diseno_SAC_Unificado.docx")
print("DOCUMENTO GENERADO: Documento_Diseno_SAC_Unificado.docx")
print("Tablas:", len(b.doc.tables), "| Párrafos:", len(b.doc.paragraphs))
