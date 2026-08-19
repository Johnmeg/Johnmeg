const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, TableOfContents,
  Header, Footer, PageNumber, TabStopType, TabStopPosition, LevelFormat, convertInchesToTwip,
  PositionalTab, PositionalTabAlignment, PositionalTabLeader, VerticalAlign,
} = require("docx");

// ---- Paleta corporativa (estilo SAP) ----
const NAVY = "1D2D44";     // azul profundo cabeceras
const SAPBLUE = "0A6ED1";  // azul SAP
const GOLD = "C88A00";     // ámbar SAP (acento)
const LIGHT = "F2F6FB";    // fondo claro de celdas
const GREYTXT = "5B6B7B";  // texto secundario
const HEADSHADE = "0A6ED1";
const ZEBRA = "EEF3FA";
const BORDER = "C9D6E5";

const FONT = "Calibri";
const HFONT = "Calibri";

// ---- Helpers ----
function t(text, opts = {}) { return new TextRun({ text, font: FONT, ...opts }); }

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 140 },
    children: [new TextRun({ text, bold: true, color: NAVY, size: 30, font: HFONT })],
    border: { bottom: { color: GOLD, style: BorderStyle.SINGLE, size: 14, space: 6 } },
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 90 },
    children: [new TextRun({ text, bold: true, color: SAPBLUE, size: 24, font: HFONT })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 160, after: 60 },
    children: [new TextRun({ text, bold: true, color: NAVY, size: 21, font: HFONT })],
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    children: Array.isArray(text) ? text : [t(text, { size: 21, color: "222B36", ...opts })],
  });
}
function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 60, line: 264 },
    children: Array.isArray(text) ? text : [t(text, { size: 21, color: "222B36" })],
  });
}
function num(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "steps", level },
    spacing: { after: 60, line: 264 },
    children: Array.isArray(text) ? text : [t(text, { size: 21, color: "222B36" })],
  });
}

// Callout / nota
function callout(label, text, color = SAPBLUE, bg = LIGHT) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: [140, 9520],
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
      right: { style: BorderStyle.NONE },
      left: { style: BorderStyle.SINGLE, size: 24, color },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [
        new TableCell({ width: { size: 140, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: bg }, children: [new Paragraph("")] }),
        new TableCell({
          width: { size: 9520, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: bg },
          margins: { top: 100, bottom: 100, left: 160, right: 160 },
          children: [new Paragraph({
            spacing: { after: 0 },
            children: [t(label + "  ", { bold: true, color, size: 20 }), t(text, { size: 20, color: "2A3644" })],
          })],
        }),
      ],
    })],
  });
}

// Tabla genérica con cabecera
function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const headRow = new TableRow({
    tableHeader: true,
    children: headers.map((hh, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: HEADSHADE },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 70, bottom: 70, left: 110, right: 110 },
      children: [new Paragraph({ spacing: { after: 0 }, children: [t(hh, { bold: true, color: "FFFFFF", size: 19 })] })],
    })),
  });
  const bodyRows = rows.map((r, ri) => new TableRow({
    children: r.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: ri % 2 ? ZEBRA : "FFFFFF" },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 60, bottom: 60, left: 110, right: 110 },
      children: [new Paragraph({
        spacing: { after: 0 },
        children: Array.isArray(c) ? c : [t(String(c), { size: 19, color: "2A3644" })],
      })],
    })),
  }));
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
      left: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
      right: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
      insideVertical: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
    },
    rows: [headRow, ...bodyRows],
  });
}

function spacer(after = 120) { return new Paragraph({ spacing: { after }, children: [t("", {})] }); }

// =====================================================================
// PORTADA
// =====================================================================
const cover = [
  new Paragraph({ spacing: { before: 400 }, children: [] }),
  // Banda superior
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: [9660],
    borders: { top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideHorizontal:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE} },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: 9660, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: NAVY },
      margins: { top: 300, bottom: 300, left: 300, right: 300 },
      children: [
        new Paragraph({ spacing:{after:40}, children: [t("SAP ANALYTICS CLOUD", { bold: true, color: "FFFFFF", size: 22, characterSpacing: 40 })] }),
        new Paragraph({ children: [t("Business Intelligence · Planning · Predictive", { color: "C7D6EA", size: 16, italics: true })] }),
      ],
    })]})],
  }),
  new Paragraph({ spacing: { before: 900 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 60 }, children: [t("DOCUMENTO TÉCNICO DE ENTREGA", { bold: true, color: GOLD, size: 26, characterSpacing: 30 })] }),
  new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 120 }, children: [t("Cierre de Implementación", { bold: true, color: NAVY, size: 56 })] }),
  new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 400 }, children: [t("Documentación técnica de la solución desplegada en SAP Analytics Cloud", { color: GREYTXT, size: 24, italics: true })] }),
  // línea dorada
  new Paragraph({ spacing: { after: 300 }, border: { bottom: { color: GOLD, style: BorderStyle.SINGLE, size: 18, space: 4 } }, children: [] }),
  // Datos del proyecto
  new Table({
    width: { size: 70, type: WidthType.PERCENTAGE },
    columnWidths: [2400, 4360],
    borders: { top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideHorizontal:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE} },
    rows: [
      ["Proyecto", "«Nombre del proyecto»"],
      ["Cliente", "«Nombre del cliente»"],
      ["Versión del documento", "1.0"],
      ["Fecha de entrega", "«DD/MM/AAAA»"],
      ["Clasificación", "Confidencial"],
    ].map(([k, v]) => new TableRow({ children: [
      new TableCell({ width:{size:2400,type:WidthType.DXA}, margins:{top:40,bottom:40}, children:[new Paragraph({spacing:{after:0},children:[t(k, {bold:true,color:NAVY,size:20})]})] }),
      new TableCell({ width:{size:4360,type:WidthType.DXA}, margins:{top:40,bottom:40}, children:[new Paragraph({spacing:{after:0},children:[t(v, {color:GREYTXT,size:20})]})] }),
    ]})),
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// =====================================================================
// CONTROL DE VERSIONES + APROBACIONES
// =====================================================================
const control = [
  h1("Control del documento"),
  h2("Historial de versiones"),
  table(
    ["Versión", "Fecha", "Autor", "Descripción del cambio"],
    [
      ["0.1", "«DD/MM/AAAA»", "«Autor»", "Versión inicial / borrador"],
      ["0.9", "«DD/MM/AAAA»", "«Autor»", "Revisión interna del equipo técnico"],
      ["1.0", "«DD/MM/AAAA»", "«Autor»", "Versión aprobada para entrega"],
    ],
    [1100, 1700, 2400, 4460]
  ),
  spacer(),
  h2("Aprobaciones"),
  table(
    ["Rol", "Nombre", "Organización", "Firma / Fecha"],
    [
      ["Responsable técnico (Consultora)", "«Nombre»", "«Consultora»", ""],
      ["Jefe de proyecto (Cliente)", "«Nombre»", "«Cliente»", ""],
      ["Responsable de BI / Datos (Cliente)", "«Nombre»", "«Cliente»", ""],
      ["Responsable de Seguridad / TI", "«Nombre»", "«Cliente»", ""],
    ],
    [3200, 2200, 2160, 2100]
  ),
  spacer(),
  h2("Distribución y confidencialidad"),
  callout("Aviso:", "Este documento contiene información técnica y de configuración de carácter confidencial. Su distribución queda limitada a las personas expresamente autorizadas por el cliente y la consultora.", GOLD, "FBF3E2"),
  new Paragraph({ children: [new PageBreak()] }),
];

// =====================================================================
// ÍNDICE
// =====================================================================
const toc = [
  h1("Índice de contenidos"),
  new TableOfContents("Tabla de contenidos", {
    hyperlink: true,
    headingStyleRange: "1-3",
    stylesWithLevels: [],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// =====================================================================
// SECCIONES
// =====================================================================
const body = [];

// 1. Introducción
body.push(h1("1. Introducción"));
body.push(h2("1.1 Objeto del documento"));
body.push(p("El presente documento constituye la entrega técnica de la implementación de la solución de analítica sobre SAP Analytics Cloud (SAC). Recoge la arquitectura desplegada, los objetos construidos, las conexiones a las fuentes de datos, el modelo de seguridad y las consideraciones de operación y mantenimiento necesarias para que el equipo del cliente pueda administrar, evolucionar y dar soporte a la solución de forma autónoma."));
body.push(h2("1.2 Audiencia"));
body.push(p("Está dirigido a perfiles técnicos: administradores de la plataforma SAC, equipo de BI y modelado de datos, administradores de seguridad e identidades, y responsables de soporte y operación."));
body.push(h2("1.3 Referencias"));
body.push(table(
  ["Ref.", "Documento", "Versión"],
  [
    ["[R1]", "Documento de alcance / SOW", "«v»"],
    ["[R2]", "Diseño funcional (Blueprint)", "«v»"],
    ["[R3]", "Diseño técnico / arquitectura", "«v»"],
    ["[R4]", "Plan y actas de pruebas (UAT)", "«v»"],
    ["[R5]", "Matriz de roles y autorizaciones", "«v»"],
  ],
  [900, 6360, 2400]
));
body.push(h2("1.4 Glosario y acrónimos"));
body.push(table(
  ["Término", "Definición"],
  [
    ["SAC", "SAP Analytics Cloud"],
    ["Live Connection", "Conexión en vivo; los datos permanecen en el sistema origen y no se replican."],
    ["Import Connection", "Adquisición de datos; los datos se cargan y persisten en el modelo SAC."],
    ["Model", "Modelo semántico de datos (dimensiones, medidas, jerarquías)."],
    ["Story", "Historia; documento de visualización y análisis."],
    ["Analytic Application", "Aplicación analítica creada con Application Design (interactividad avanzada, scripting)."],
    ["DAC", "Data Access Control; control de acceso a nivel de fila/miembro de dimensión."],
    ["TMS / Content Network", "Mecanismos de transporte de contenido entre tenants."],
  ],
  [2200, 7460]
));

// 2. Resumen ejecutivo
body.push(h1("2. Resumen ejecutivo"));
body.push(p("Descripción breve, orientada a gestión, de la solución entregada: objetivos de negocio cubiertos, principales cuadros de mando y capacidades habilitadas (reporting, planificación, predictivo), y estado final de la implementación."));
body.push(h2("2.1 Alcance implementado"));
body.push(table(
  ["Ámbito", "Entregado", "Observaciones"],
  [
    ["Modelos de datos", "«N»", "«…»"],
    ["Historias (Stories)", "«N»", "«…»"],
    ["Analytic Applications", "«N»", "«…»"],
    ["Conexiones a fuentes", "«N»", "«Live / Import»"],
    ["Modelo de planificación", "Sí / No", "«…»"],
    ["Escenarios predictivos (Smart Predict)", "Sí / No", "«…»"],
  ],
  [3200, 1800, 4660]
));
body.push(h2("2.2 Fuera de alcance"));
body.push(bullet("Relación explícita de funcionalidades o requisitos no incluidos en esta fase."));
body.push(bullet("Integraciones o fuentes previstas para fases posteriores."));

// 3. Arquitectura de la solución
body.push(h1("3. Arquitectura de la solución"));
body.push(h2("3.1 Visión general"));
body.push(p("Descripción del landscape completo: tenant(s) de SAC, sistemas origen, capa de integración/modelado (p. ej. SAP Datasphere, SAP BW/4HANA, S/4HANA) y flujo de datos de extremo a extremo. Se recomienda incluir aquí el diagrama de arquitectura."));
body.push(callout("Diagrama:", "Insertar el diagrama de arquitectura de la solución (origen → integración → SAC → consumo).", SAPBLUE));
body.push(h2("3.2 Tenants y entornos"));
body.push(table(
  ["Entorno", "URL del tenant", "Data Center / Región", "Uso"],
  [
    ["Desarrollo / QA", "«https://…»", "«DC»", "Construcción y pruebas"],
    ["Producción", "«https://…»", "«DC»", "Operación"],
  ],
  [2000, 3260, 2200, 2200]
));
body.push(h2("3.3 Estrategia de conexión"));
body.push(p([
  t("Se documenta el modo de consumo de datos elegido: ", { size: 21 }),
  t("Live Connection", { bold: true, size: 21, color: NAVY }),
  t(" (los datos no se replican, se consultan en tiempo real en el origen) frente a ", { size: 21 }),
  t("Import / Data Acquisition", { bold: true, size: 21, color: NAVY }),
  t(" (los datos se cargan y persisten en el modelo). Debe justificarse la decisión por dominio de datos.", { size: 21 }),
]));

// 4. Conexiones y fuentes de datos
body.push(h1("4. Conexiones y fuentes de datos"));
body.push(h2("4.1 Inventario de conexiones"));
body.push(table(
  ["Nombre conexión", "Tipo", "Sistema origen", "Método", "Responsable"],
  [
    ["«CONN_DSP»", "Live", "SAP Datasphere", "Tunnel / directo", "«…»"],
    ["«CONN_S4»", "Live", "S/4HANA", "SAP HANA / InA", "«…»"],
    ["«CONN_BW»", "Import", "BW/4HANA", "BW Query", "«…»"],
    ["«CONN_FILE»", "Import", "Ficheros / OData", "Data flow", "«…»"],
  ],
  [2200, 1200, 2260, 2000, 2000]
));
body.push(h2("4.2 Agente de nube (SAP Cloud Connector) y conectividad"));
body.push(bullet("Detalle del SAP Cloud Connector / Cloud Agent, hosts, puertos y location ID cuando aplique."));
body.push(bullet("Cuentas técnicas / de servicio empleadas para cada conexión."));
body.push(bullet("Certificados y su vigencia (fecha de caducidad)."));
body.push(h2("4.3 Cargas y programación (para conexiones Import)"));
body.push(table(
  ["Modelo / Flujo", "Frecuencia", "Ventana", "Tipo de carga", "Dependencias"],
  [
    ["«…»", "Diaria", "«hh:mm»", "Delta / Full", "«…»"],
    ["«…»", "Horaria", "«…»", "Delta", "«…»"],
  ],
  [2600, 1500, 1400, 1900, 2260]
));

// 5. Modelo de datos
body.push(h1("5. Modelo de datos"));
body.push(h2("5.1 Inventario de modelos"));
body.push(table(
  ["Modelo", "Tipo", "Conexión / Origen", "Descripción", "Propietario"],
  [
    ["«M_Ventas»", "Analítico (Live)", "«CONN_S4»", "Ventas y márgenes", "«…»"],
    ["«M_Plan»", "Planificación", "Import", "Presupuesto y forecast", "«…»"],
  ],
  [2000, 1700, 2000, 2260, 1700]
));
body.push(h2("5.2 Dimensiones, jerarquías y medidas"));
body.push(bullet("Dimensiones y sus atributos; dimensiones de cuenta vs. medidas."));
body.push(bullet("Jerarquías (padre-hijo y por niveles) y su mantenimiento."));
body.push(bullet("Medidas calculadas y restringidas, con su fórmula y significado de negocio."));
body.push(bullet("Unidades, monedas y conversión de divisa aplicada."));
body.push(h2("5.3 Diccionario de medidas clave"));
body.push(table(
  ["Medida / KPI", "Definición de negocio", "Fórmula / origen"],
  [
    ["«Margen %»", "Rentabilidad sobre ventas", "(Ventas − Coste) / Ventas"],
    ["«Desviación vs. Plan»", "Real frente a presupuesto", "Real − Plan"],
  ],
  [2600, 3600, 3460]
));

// 6. Historias y aplicaciones
body.push(h1("6. Historias y aplicaciones analíticas"));
body.push(h2("6.1 Inventario de Stories y Analytic Applications"));
body.push(table(
  ["Nombre", "Tipo", "Modelos usados", "Audiencia", "Descripción"],
  [
    ["«Dashboard Ventas»", "Story", "«M_Ventas»", "Dirección comercial", "«…»"],
    ["«App Planning»", "Analytic App", "«M_Plan»", "Controlling", "«…»"],
  ],
  [2200, 1300, 1900, 1900, 2360]
));
body.push(h2("6.2 Diseño y estándares visuales"));
body.push(bullet("Plantillas, tema corporativo, paleta y tipografías aplicadas."));
body.push(bullet("Convenciones de nomenclatura de objetos (modelos, historias, widgets)."));
body.push(bullet("Filtros, prompts, enlaces (linked analysis) y navegación entre páginas."));
body.push(h2("6.3 Scripting (Application Design)"));
body.push(p("Cuando se han utilizado Analytic Applications, se documentan los eventos y scripts principales (onInitialization, onSelect, funciones globales), variables de script y componentes personalizados."));

// 7. Planificación (si aplica)
body.push(h1("7. Planificación (si aplica)"));
body.push(bullet("Modelos de planificación, versiones (Actual, Budget, Forecast) y categorías."));
body.push(bullet("Data Actions y Multi Actions: propósito, secuencia y parámetros."));
body.push(bullet("Reglas de asignación (Allocations) y advanced formulas."));
body.push(bullet("Value Driver Trees y bloqueos de datos (Data Locking) por usuario/versión."));
body.push(bullet("Calendario de planificación (Calendar): tareas, procesos y responsables."));

// 8. Predictivo (si aplica)
body.push(h1("8. Analítica predictiva (si aplica)"));
body.push(bullet("Escenarios de Smart Predict (clasificación, regresión, series temporales)."));
body.push(bullet("Datasets de entrenamiento, variables de entrada e influencers."));
body.push(bullet("Métricas de calidad del modelo y política de reentrenamiento."));
body.push(bullet("Uso de Smart Insights / Search-to-Insight habilitados."));

// 9. Seguridad y autorizaciones
body.push(h1("9. Seguridad y autorizaciones"));
body.push(h2("9.1 Autenticación e identidad"));
body.push(bullet("Proveedor de identidad (SAP Cloud Identity / IdP corporativo) y SSO (SAML 2.0)."));
body.push(bullet("Aprovisionamiento de usuarios (SCIM / manual) y política de contraseñas y MFA."));
body.push(h2("9.2 Roles y equipos"));
body.push(table(
  ["Rol", "Tipo", "Permisos clave", "Asignado a (Team)"],
  [
    ["Administrador", "Estándar", "Gestión del tenant, conexiones, seguridad", "«Team Admin»"],
    ["Modelador BI", "Personalizado", "Crear/editar modelos e historias", "«Team BI»"],
    ["Analista / Consumidor", "Personalizado", "Ejecutar y comentar historias", "«Team Negocio»"],
    ["Planificador", "Personalizado", "Introducir datos de plan", "«Team Planning»"],
  ],
  [1900, 1500, 3800, 2460]
));
body.push(h2("9.3 Seguridad a nivel de datos (Data Access Control)"));
body.push(p("Descripción del control de acceso por fila/miembro de dimensión (DAC), tanto de lectura como de escritura, y cómo se relaciona con los equipos y usuarios. En conexiones Live, se documenta si la seguridad se delega en el sistema origen (p. ej. análisis de autorizaciones de BW/HANA)."));
body.push(callout("Buenas prácticas:", "Asignar permisos siempre a Teams, nunca a usuarios individuales, para facilitar el mantenimiento y las altas/bajas.", SAPBLUE));
body.push(h2("9.4 Matriz de segregación de funciones"));
body.push(p("Referencia a la matriz completa de roles/autorizaciones [R5] y a los controles de segregación de funciones (SoD) aplicados."));

// 10. Rendimiento
body.push(h1("10. Rendimiento y optimización"));
body.push(bullet("Buenas prácticas aplicadas en el diseño de historias (número de widgets, consultas por página)."));
body.push(bullet("Optimización del modelo/consulta en el origen (Datasphere / HANA / BW)."));
body.push(bullet("Uso de Optimized Story Experience / Optimized Design Experience."));
body.push(bullet("Resultados de las pruebas de rendimiento (tiempos de apertura y refresco)."));
body.push(table(
  ["Historia / App", "Tiempo de apertura", "Tiempo de refresco", "Objetivo (SLA)"],
  [["«…»", "«s»", "«s»", "< «s»"], ["«…»", "«s»", "«s»", "< «s»"]],
  [3260, 2200, 2200, 2000]
));

// 11. Gobierno y calidad
body.push(h1("11. Gobierno del dato y calidad"));
body.push(bullet("Convenciones de nomenclatura y carpetas / catálogo (Catalog) de contenido."));
body.push(bullet("Ciclo de vida del contenido y propiedad (ownership) de objetos."));
body.push(bullet("Controles de calidad de datos y conciliación con el sistema origen."));
body.push(bullet("Política de comentarios, colaboración y publicación de historias."));

// 12. Transporte y ciclo de vida
body.push(h1("12. Transporte y gestión del ciclo de vida"));
body.push(p("Procedimiento de promoción de contenido entre entornos utilizando Content Network / Transport Management, incluyendo el tratamiento de dependencias (modelos, conexiones) y la gestión de contenido de sistema."));
body.push(table(
  ["Paso", "Actividad", "Herramienta", "Responsable"],
  [
    ["1", "Exportar paquete de contenido de QA", "Content Network", "«…»"],
    ["2", "Importar en Producción y remapear conexiones", "Content Network", "«…»"],
    ["3", "Validación post-transporte", "Checklist", "«…»"],
  ],
  [800, 4400, 2200, 2260]
));

// 13. Pruebas
body.push(h1("13. Pruebas y validación"));
body.push(h2("13.1 Estrategia de pruebas"));
body.push(bullet("Pruebas unitarias de modelos y medidas."));
body.push(bullet("Pruebas de integración de conexiones y cargas."));
body.push(bullet("Pruebas de aceptación de usuario (UAT) y validación de datos."));
body.push(bullet("Pruebas de seguridad (acceso por rol y por fila)."));
body.push(h2("13.2 Resumen de resultados"));
body.push(table(
  ["ID", "Caso de prueba", "Resultado", "Incidencias"],
  [
    ["TC-01", "Refresco de modelo de ventas", "OK", "—"],
    ["TC-02", "Acceso restringido por DAC", "OK", "—"],
    ["TC-03", "Ciclo de planificación (Data Action)", "OK", "«…»"],
  ],
  [900, 4600, 1700, 2460]
));

// 14. Operación y mantenimiento
body.push(h1("14. Operación y mantenimiento"));
body.push(h2("14.1 Tareas recurrentes"));
body.push(table(
  ["Tarea", "Frecuencia", "Responsable"],
  [
    ["Monitorización de cargas / schedules", "Diaria", "«…»"],
    ["Revisión de conexiones y certificados", "Mensual", "«…»"],
    ["Gestión de altas/bajas de usuarios y teams", "Bajo demanda", "«…»"],
    ["Revisión de novedades del release trimestral (QRC)", "Trimestral", "«…»"],
  ],
  [4800, 2400, 2460]
));
body.push(h2("14.2 Gestión de releases de SAC"));
body.push(p("SAP Analytics Cloud recibe actualizaciones periódicas (ciclo QRC). Se documenta la planificación de revisión de novedades, pruebas de regresión y comunicación de cambios a los usuarios."));
body.push(h2("14.3 Soporte y escalado"));
body.push(table(
  ["Nivel", "Alcance", "Contacto", "SLA"],
  [
    ["N1", "Soporte a usuario / accesos", "«…»", "«…»"],
    ["N2", "Contenido, modelos y conexiones", "«…»", "«…»"],
    ["N3", "SAP / consultora", "«…»", "«…»"],
  ],
  [1200, 4200, 2000, 2260]
));
body.push(h2("14.4 Copias de seguridad y recuperación"));
body.push(bullet("Estrategia de exportación periódica de contenido crítico (Content Network)."));
body.push(bullet("Consideraciones de continuidad para modelos de planificación (datos introducidos por usuarios)."));

// 15. Riesgos y pendientes
body.push(h1("15. Riesgos, pendientes y lecciones aprendidas"));
body.push(h2("15.1 Puntos pendientes (backlog)"));
body.push(table(
  ["ID", "Descripción", "Prioridad", "Responsable", "Fecha objetivo"],
  [
    ["P-01", "«…»", "Alta", "«…»", "«…»"],
    ["P-02", "«…»", "Media", "«…»", "«…»"],
  ],
  [800, 4100, 1500, 1800, 1460]
));
body.push(h2("15.2 Riesgos identificados"));
body.push(table(
  ["Riesgo", "Impacto", "Probabilidad", "Mitigación"],
  [["«…»", "Alto", "Media", "«…»"], ["«…»", "Medio", "Baja", "«…»"]],
  [3400, 1600, 1800, 2860]
));
body.push(h2("15.3 Lecciones aprendidas"));
body.push(bullet("Aspectos que funcionaron bien y conviene repetir."));
body.push(bullet("Dificultades encontradas y recomendaciones para futuras fases."));

// 16. Anexos
body.push(h1("16. Anexos"));
body.push(bullet("Anexo A — Diagramas de arquitectura en alta resolución."));
body.push(bullet("Anexo B — Matriz completa de roles y autorizaciones."));
body.push(bullet("Anexo C — Diccionario de datos y catálogo de medidas."));
body.push(bullet("Anexo D — Manual de usuario / guía rápida."));
body.push(bullet("Anexo E — Actas de pruebas y aceptación (UAT)."));
body.push(spacer(200));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 300 }, border: { top: { color: GOLD, style: BorderStyle.SINGLE, size: 12, space: 8 } }, children: [t("— Fin del documento —", { italics: true, color: GREYTXT, size: 18 })] }));

// =====================================================================
// DOCUMENTO
// =====================================================================
const doc = new Document({
  creator: "Equipo de Consultoría SAC",
  title: "Documento Técnico de Entrega — SAP Analytics Cloud",
  description: "Plantilla de documentación técnica post-implementación de SAP Analytics Cloud",
  styles: {
    default: {
      document: { run: { font: FONT, size: 21, color: "222B36" } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: HFONT } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: HFONT } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: HFONT } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { run: { color: SAPBLUE }, paragraph: { indent: { left: 460, hanging: 260 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 900, hanging: 260 } } } },
      ]},
      { reference: "steps", levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { run: { bold: true, color: SAPBLUE }, paragraph: { indent: { left: 460, hanging: 260 } } } },
      ]},
    ],
  },
  sections: [
    // Sección 1: portada sin cabecera/pie
    {
      properties: { page: { margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
      children: cover,
    },
    // Sección 2: resto con cabecera y pie + numeración
    {
      properties: { page: { margin: { top: 1240, bottom: 1200, left: 1180, right: 1180 } } },
      headers: {
        default: new Header({ children: [
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            columnWidths: [6000, 3660],
            borders: { top:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideHorizontal:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE},
              bottom:{style:BorderStyle.SINGLE,size:6,color:GOLD} },
            rows: [new TableRow({ children: [
              new TableCell({ width:{size:6000,type:WidthType.DXA}, margins:{bottom:60}, borders:{top:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE}}, children:[new Paragraph({spacing:{after:0},children:[t("SAP Analytics Cloud — Documento Técnico de Entrega", {size:15,color:NAVY,bold:true})]})] }),
              new TableCell({ width:{size:3660,type:WidthType.DXA}, margins:{bottom:60}, borders:{top:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE}}, children:[new Paragraph({alignment:AlignmentType.RIGHT,spacing:{after:0},children:[t("Confidencial", {size:14,color:GREYTXT,italics:true})]})] }),
            ]})],
          }),
        ]}),
      },
      footers: {
        default: new Footer({ children: [
          new Paragraph({
            spacing: { before: 40 },
            border: { top: { color: BORDER, style: BorderStyle.SINGLE, size: 4, space: 6 } },
            tabStops: [{ type: TabStopType.RIGHT, position: 9660 }],
            children: [
              t("«Cliente» · «Proyecto»", { size: 15, color: GREYTXT }),
              new TextRun({ text: "\t", font: FONT }),
              new TextRun({ children: ["Página ", PageNumber.CURRENT, " de ", PageNumber.TOTAL_PAGES], size: 15, color: GREYTXT, font: FONT }),
            ],
          }),
        ]}),
      },
      children: [...control, ...toc, ...body],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("/home/user/Johnmeg/out/Documento_Tecnico_SAC.docx", buf);
  console.log("OK", buf.length, "bytes");
});
