'use strict';

// Genera archivos de ejemplo (válidos y con errores) en ./samples para probar
// la aplicación con el simulador de SAC (npm run demo).

const fs = require('fs');
const path = require('path');
const ExcelJS = require('exceljs');

const OUT = path.join(__dirname, '..', 'samples');
const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'].map((m) => `${m} 2026`);

async function plantillaExcel(file, { sheet, title, dims, context, rows }) {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet(sheet);
  ws.getCell('A1').value = title;
  ws.getCell('A1').font = { bold: true, size: 14 };
  ws.getCell('A2').value = 'Diligencie las celdas blancas. Los códigos deben existir en SAC.';
  let r = 4;
  for (const [label, value] of context) {
    ws.getCell(r, 1).value = label; ws.getCell(r, 1).font = { bold: true };
    ws.getCell(r, 2).value = value; r++;
  }
  const headerRow = r + 1;
  const header = [...dims, ...MESES, 'Total'];
  header.forEach((h, i) => {
    const c = ws.getCell(headerRow, i + 1);
    c.value = h; c.font = { bold: true, color: { argb: 'FFFFFFFF' } };
    c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF0A6ED1' } };
  });
  rows.forEach((row, k) => {
    const n = headerRow + 1 + k;
    row.forEach((v, i) => { ws.getCell(n, i + 1).value = v; });
    const first = ws.getCell(n, dims.length + 1).address; const last = ws.getCell(n, dims.length + 12).address;
    ws.getCell(n, dims.length + 13).value = { formula: `SUM(${first}:${last})`, result: row.slice(dims.length).reduce((a, b) => a + (Number(b) || 0), 0) };
  });
  ws.columns.forEach((c, i) => { c.width = i < dims.length ? 22 : 12; });
  await wb.xlsx.writeFile(path.join(OUT, file));
}

function csv(file, lines) {
  // Windows-1252 no es necesario: se guarda en UTF-8 con BOM como lo hace Excel "CSV UTF-8"
  fs.writeFileSync(path.join(OUT, file), `﻿${lines.map((l) => l.join(';')).join('\r\n')}\r\n`);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const doce = (v) => Array(12).fill(v);

  await plantillaExcel('PL-01_ingresos_valido.xlsx', {
    sheet: 'PL-01',
    title: 'PL-01 — Ingresos Ordinarios Ciudad Limpia',
    dims: ['Sociedad_CL', 'Cebes_CL (componente)', 'Ratio_CL (cuenta)'],
    context: [['Versión:', 'public.Plan'], ['Moneda:', 'COP'], ['Auditoría:', 'PRESUPUESTO_TARIFAS'], ['Opción de carga:', 'Reemplazar']],
    rows: [
      ['CL_BOG', 'RECOLECCION', 'ING_RECOLECCION', ...doce(1250000.5)],
      ['CL_BOG', 'BARRIDO', 'ING_BARRIDO', ...doce(830000)],
      ['CL_NEI', 'RECOLECCION', 'ING_RECOLECCION', ...doce(415000)],
      ['CL_NEI', 'DISPOSICION', 'ING_DISPOSICION', 120000, 120000, 125000, 125000, 125000, 130000, 130000, 130000, 135000, 135000, 135000, 140000],
    ],
  });

  await plantillaExcel('PL-01_ingresos_con_errores.xlsx', {
    sheet: 'PL-01',
    title: 'PL-01 — Ingresos Ordinarios Ciudad Limpia (con errores a propósito)',
    dims: ['Sociedad_CL', 'Cebes_CL (componente)', 'Ratio_CL (cuenta)'],
    context: [['Versión:', 'public.Plan'], ['Moneda:', 'COP'], ['Auditoría:', 'PRESUPUESTO_TARIFAS'], ['Opción de carga:', 'Reemplazar']],
    rows: [
      ['CL_BOG', 'RECOLECCION', 'ING_RECOLECCION', ...doce(1000)],
      ['cl_bog', 'BARRIDO', 'ING_BARRIDO', ...doce(1000)],             // minúsculas: SAC distingue mayúsculas
      ['CL_CALI', 'RECOLECCION', 'ING_RECOLECCION', ...doce(1000)],    // sociedad inexistente
      ['CL_NEI', '', 'ING_RECOLECCION', ...doce(1000)],                // Cebes vacío
      ['CL_NEI', 'BARRIDO', 'ING_BARRIDO', 500, 'quinientos', ...Array(10).fill(500)], // texto en valor
      ['CL_BOG', 'RECOLECCION', 'ING_RECOLECCION', ...doce(2000)],     // combinación repetida
    ],
  });

  csv('PL-03_gastos_valido.csv', [
    ['Plantilla PL-03 Gastos y Costos'],
    ['Moneda:', 'COP'],
    ['Auditoría:', 'PRESUPUESTO_EXCEL'],
    [],
    ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL', ...MESES],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5205_SERV_PUBLICOS', ...doce('300.000,00')],
    ['CL_BOG', 'CECO_OPER', 'RECOLECCION', '5105_SALARIOS', ...doce('8.000.000')],
    ['CL_NEI', 'VEH_ABC123', 'RECOLECCION', '5210_COMBUSTIBLE', ...doce('1.500.250,75')],
    ['CL_NEI', 'CECO_ADMIN', 'CORPORATIVO', '5905_OTROS', '(25.000)', ...Array(11).fill('')],
  ]);

  csv('PL-03_gastos_con_errores.csv', [
    ['Moneda:', 'COP'],
    ['Auditoría:', 'PRESUPUESTO_EXCEL'],
    ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL', ...MESES, 'Observaciones'],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5205_SERV_PUBLICOS', ...doce('300.000'), 'revisar'],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '9999_NO_EXISTE', ...doce('10'), 'revisar'],
    ['CL_BOG', 'CECO_OPER', 'BARRIDO', '5105_SALARIOS', '1,2,3', ...Array(11).fill('5'), ''],
    ['CL_BOG', 'ceco_admin', 'RECOLECCION', '5105_SALARIOS', ...doce('100'), ''],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5205_SERV_PUBLICOS', ...doce('50'), 'duplicada'],
  ]);

  csv('GENERICO_gastos_formato_largo.csv', [
    ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL', 'Moneda_CL', 'Auditoria_CL', 'Date', 'Importe'],
    ['CL_MED', 'CECO_ADMIN', 'CORPORATIVO', '5205_SERV_PUBLICOS', 'COP', 'MANUAL', '202601', '1500000'],
    ['CL_MED', 'CECO_ADMIN', 'CORPORATIVO', '5205_SERV_PUBLICOS', 'COP', 'MANUAL', '2026-02', '1.600.000'],
    ['CL_MED', 'CECO_ADMIN', 'CORPORATIVO', '5205_SERV_PUBLICOS', 'COP', 'MANUAL', 'Mar 2026', '1.700.000,50'],
  ]);

  console.log(`Ejemplos generados en ${OUT}`);
})();
