# Documento de Diseño de Solución — SAP Analytics Cloud (unificado)

Entregable: **`../Documento_Diseno_SAC_Unificado.docx`**

Documento único de diseño que consolida los modelos de planeación SAC de tres
sociedades del Grupo Fanalca —**Fanalca S.A.**, **Ciudad Limpia** y
**Transprensa S.A.S.**— aplicando el formato del *Documento de Diseño Funcional*
(SAP Activate · Proyecto Build · Fanalca / Accenture).

## Qué se hizo

- Se tomaron los tres documentos de diseño de origen (Fanalca, Ciudad Limpia,
  Transprensa) y se reorganizaron en un **único documento** con el formato del
  *Diseño Funcional*: portada de marca, control de versiones, distribución,
  índice automático, encabezados/pies y la estructura de secciones
  (Propósito → Cómo usar → un capítulo por sociedad con Escenario, Estructura
  organizativa y Diseño y configuración).
- Se reutilizan los **estilos del template**: títulos numerados (Heading 1-3),
  el estilo de tabla *Fanalca* (cabecera azul corporativo) y los logotipos.
- Se **rediseñaron los flujogramas** (10 diagramas vectoriales nuevos): visión
  general del programa, y por sociedad la arquitectura de la solución, el flujo
  de cálculo/consolidación y la metodología P×Q.
- Se **excluyó** todo lo relativo a *Parking Lot* y a *Próximos Pasos / pasos a
  seguir*, y se depuró/normalizó la redacción.

## Cómo regenerar

```bash
pip install python-docx lxml Pillow matplotlib
python gen_diagrams.py     # genera img/*.png (flujogramas)
python build_doc.py        # genera el .docx (requiere el template en src/)
```

> Nota: al abrir en Word, actualice el índice con clic derecho ▸ *Actualizar
> campos* (o F9) para poblar la Tabla de Contenido.

## Archivos

| Archivo | Descripción |
|---|---|
| `build_doc.py` | Construye el documento Word con el contenido de las tres sociedades. |
| `docx_helpers.py` | Utilidades de construcción (tablas de marca, callouts, figuras, encabezados). |
| `flowcharts.py` | Librería de flujogramas (paleta de marca). |
| `gen_diagrams.py` | Genera los 10 diagramas. |
| `img/` | Flujogramas generados (PNG). |
