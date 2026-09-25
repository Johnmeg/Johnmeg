'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const ExcelJS = require('exceljs');
const { parseNumber } = require('../src/numbers');
const { toPeriod } = require('../src/periods');
const { parseFile, detectDelimiter } = require('../src/parser');
const { buildMeta } = require('../src/meta');
const { validate } = require('../src/validator');
const { loadTemplates } = require('../src/config');
const { metadataOf, MODELS, VERSIONS } = require('./mockSac');

// ---------------------------------------------------------------- números
test('números: formato es-CO, inglés, negativos y errores', () => {
  const v = (raw, loc) => parseNumber(raw, loc).value;
  assert.equal(v('1.234.567,89'), 1234567.89);
  assert.equal(v('1,234,567.89', 'en'), 1234567.89);
  assert.equal(v('1,234,567.89'), 1234567.89);   // ambos separadores: el último es decimal
  assert.equal(v('(1.500)'), -1500);
  assert.equal(v('1500-'), -1500);
  assert.equal(v('$ 2.000'), 2000);
  assert.equal(v('0,5'), 0.5);
  assert.equal(v('12,5'), 12.5);
  assert.equal(v('1E+3'), 1000);
  assert.equal(v(42), 42);
  assert.equal(parseNumber('1.234').ambiguous, true);
  assert.equal(parseNumber('1.234').value, 1234);
  assert.equal(parseNumber('1.234', 'en').value, 1.234);
  assert.equal(parseNumber('').blank, true);
  assert.equal(parseNumber(null).blank, true);
  assert.ok(parseNumber('abc').error);
  assert.ok(parseNumber('1,2,3').error);
  assert.ok(parseNumber('1.23.4').error);
  assert.ok(parseNumber('1,234.5,6').error);
});

// ---------------------------------------------------------------- periodos
test('periodos: encabezados y valores comunes', () => {
  for (const x of ['Ene 2026', 'ene-26', 'Enero 2026', 'Jan 2026', '202601', 202601, '2026-01', '01/2026', 'ene2026', '2026.01']) {
    assert.equal(toPeriod(x), '202601', `falló con ${x}`);
  }
  assert.equal(toPeriod('Sept 2026'), '202609');
  assert.equal(toPeriod('Dic 2026'), '202612');
  assert.equal(toPeriod(new Date(Date.UTC(2026, 2, 1))), '202603');
  assert.equal(toPeriod(46023), '202601'); // serie Excel 2026-01-01
  assert.equal(toPeriod('202613'), null);
  assert.equal(toPeriod('Total'), null);
  assert.equal(toPeriod('Sociedad_CL'), null);
  assert.equal(toPeriod('2026', 4), '2026');
  assert.equal(toPeriod('20260230', 8), null);
  assert.equal(toPeriod('20260228', 8), '20260228');
});

// ---------------------------------------------------------------- archivos
test('parser: CSV con punto y coma, BOM, comillas y saltos de línea', async () => {
  const text = '﻿A;B;C\r\n"x;1";"dijo ""hola""";"línea\nnueva"\r\n\r\nz;2;3\r\n';
  const g = await parseFile({ filename: 'a.csv', buffer: Buffer.from(text) });
  assert.equal(g.info.delimiter, 'punto y coma');
  assert.equal(g.info.encoding, 'UTF-8 (BOM)');
  assert.deepEqual(g.rows[1].cells, ['x;1', 'dijo "hola"', 'línea\nnueva']);
  assert.equal(g.rows[2].n, 5); // numeración real de la fila del archivo
});

test('parser: Windows-1252, tabuladores y archivos inválidos', async () => {
  const g = await parseFile({ filename: 'a.txt', buffer: Buffer.from([0x41, 0x75, 0x64, 0x69, 0x74, 0x6f, 0x72, 0xed, 0x61, 0x09, 0x42, 0x0a, 0x31, 0x09, 0x32]) });
  assert.equal(g.info.encoding, 'Windows-1252');
  assert.equal(g.rows[0].cells[0], 'Auditoría');
  assert.equal(detectDelimiter('a|b|c\n1|2|3'), '|');
  await assert.rejects(parseFile({ filename: 'a.xls', buffer: Buffer.from('x') }), { code: 'ARCH_FORMATO' });
  await assert.rejects(parseFile({ filename: 'a.exe', buffer: Buffer.from('x') }), { code: 'ARCH_FORMATO' });
  await assert.rejects(parseFile({ filename: 'a.xlsx', buffer: Buffer.from('no es zip') }), { code: 'ARCH_FORMATO' });
  await assert.rejects(parseFile({ filename: 'a.csv', buffer: Buffer.from('a;"b\n1;2') }), { code: 'ARCH_COMILLAS' });
  await assert.rejects(parseFile({ filename: 'a.csv', buffer: Buffer.alloc(0) }), { code: 'ARCH_VACIO' });
});

test('parser: Excel con fórmulas, errores y hoja preferida', async () => {
  const wb = new ExcelJS.Workbook();
  wb.addWorksheet('Indice').getCell('A1').value = 'Instrucciones';
  const ws = wb.addWorksheet('PL-03');
  ws.addRow(['Cuenta', 'Ene 2026', 'Total']);
  ws.addRow(['5105', 10, { formula: 'B2', result: 10 }]);
  ws.addRow(['5205', { error: '#N/A' }, null]);
  const buffer = Buffer.from(await wb.xlsx.writeBuffer());
  const g = await parseFile({ filename: 'x.xlsx', buffer, preferredSheet: 'pl-03' });
  assert.equal(g.sheetName, 'PL-03');
  assert.equal(g.rows[1].cells[2], 10);
  assert.deepEqual(g.rows[2].cells[1], { excelError: '#N/A' });
  await assert.rejects(parseFile({ filename: 'x.xlsx', buffer, preferredSheet: 'PL-09' }), { code: 'ARCH_HOJA' });

  const one = new ExcelJS.Workbook();
  one.addWorksheet('Hoja1').addRow(['a']);
  const g2 = await parseFile({ filename: 'y.xlsx', buffer: Buffer.from(await one.xlsx.writeBuffer()), preferredSheet: 'PL-03' });
  assert.equal(g2.sheetName, 'Hoja1');
  assert.match(g2.info.warning, /única hoja/);
});

// ---------------------------------------------------------------- validador
const templates = new Map(loadTemplates(require('path').join(__dirname, '..', 'config', 'templates.json')).map((t) => [t.id, t]));

function run(modelId, templateId, lines, { version = 'public.Plan', members = true, templateOverride = {} } = {}) {
  const template = { ...templates.get(templateId), ...templateOverride };
  const meta = buildMeta(metadataOf(modelId), template);
  const m = new Map();
  if (members) {
    for (const [k, v] of Object.entries(MODELS[modelId].dims)) m.set(k, new Set(v));
    m.set('Version', new Set(VERSIONS));
  }
  const grid = { sheetName: null, rows: lines.map((cells, i) => ({ n: i + 1, cells })), info: {} };
  return validate({ grid, template, meta, members: m, options: { version, blockedVersions: ['public.Actual'] } });
}
const codes = (r) => r.issues.map((i) => i.code);
const HDR = ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL', 'Auditoria_CL', 'Moneda_CL', 'Ene 2026', 'Feb 2026'];
const ROW = ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 'PRESUPUESTO_EXCEL', 'COP'];

test('validador: archivo correcto con las dimensiones reales del modelo', () => {
  const r = run('CL_GASTOS', 'CL_GASTOS', [HDR, [...ROW, '1.000,5', null]]);
  assert.equal(r.ok, true, JSON.stringify(r.issues));
  assert.equal(r.records.length, 1);
  assert.deepEqual(r.records[0], {
    Version: 'public.Plan', Sociedad_CL: 'CL_BOG', Cecos_CL: 'CECO_ADMIN', Cebes_CL: 'RECOLECCION',
    Cuentas_Egresos_CL: '5105_SALARIOS', Auditoria_CL: 'PRESUPUESTO_EXCEL', Moneda_CL: 'COP', Date: '202601', Importe: 1000.5,
  });
  assert.equal(r.summary.skippedBlank, 1);
  assert.equal(r.summary.totalsByPeriod['202601'], 1000.5);
});

test('validador: errores de estructura detienen la validación', () => {
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', [['x', 'y'], ['1', '2']])).includes('ENC_NO_ENCONTRADO'));
  const sinMoneda = run('CL_GASTOS', 'CL_GASTOS', [HDR.filter((h) => h !== 'Moneda_CL'), [...ROW.slice(0, 5), 1, 2]]);
  assert.ok(sinMoneda.issues.some((i) => i.code === 'COL_FALTANTE' && i.column === 'Moneda_CL'));
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', [[...HDR, 'Responsable'], [...ROW, 1, 2, 'x']])).includes('COL_DESCONOCIDA'));
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', [[...HDR, 'Enr 2026'], [...ROW, 1, 2, 3]])).includes('COL_DESCONOCIDA')); // mes mal escrito
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', [[...HDR, 'Ene 2026'], [...ROW, 1, 2, 3]])).includes('PER_DUPLICADO'));
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', [[...HDR, null], [...ROW, 1, 2, 3]])).includes('ENC_VACIO'));
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', [HDR.slice(0, 6), ROW])).includes('PER_SIN_COLUMNAS'));
  const ign = run('CL_GASTOS', 'CL_GASTOS', [[...HDR, 'Total', 'Observaciones'], [...ROW, 1, 2, 3, 'nota']]);
  assert.equal(ign.ok, true);
  assert.deepEqual(codes(ign), ['COL_IGNORADA', 'COL_IGNORADA']);
});

test('validador: versión obligatoria, bloqueada, distinta o inexistente', () => {
  const rows = [HDR, [...ROW, 1, 2]];
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', rows, { version: '' })).includes('VERSION_REQUERIDA'));
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', rows, { version: 'public.Actual' })).includes('VERSION_BLOQUEADA'));
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', rows, { version: 'public.Inventada' })).includes('VERSION_INEXISTENTE'));
  assert.ok(codes(run('CL_GASTOS', 'CL_GASTOS', [['Versión:', 'Forecast'], ...rows])).includes('VERSION_DIFERENTE'));
  assert.equal(run('CL_GASTOS', 'CL_GASTOS', [['Versión:', 'Plan'], ...rows]).ok, true);
  // Columna Version en el archivo: debe coincidir con la seleccionada
  const conVersion = run('CL_GASTOS', 'CL_GASTOS', [['Version', ...HDR], ['public.Forecast', ...ROW, 1, 2]]);
  assert.ok(codes(conVersion).includes('VERSION_DIFERENTE'));
});

test('validador: errores por fila (miembros, vacíos, números, duplicados, longitud)', () => {
  const r = run('CL_GASTOS', 'CL_GASTOS', [HDR,
    [...ROW, 1, 2],
    ['cl_bog', ...ROW.slice(1), 1, 2],
    ['CL_BOG', '', ...ROW.slice(2), 1, 2],
    ['CL_BOG', 'CECO_OPER', ...ROW.slice(2), 'diez', { excelError: '#REF!' }],
    [...ROW, 5, 6],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', 'X'.repeat(50), 'PRESUPUESTO_EXCEL', 'COP', 1, 2],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', 'a\tb', 'PRESUPUESTO_EXCEL', 'COP', 1, 2],
  ]);
  const c = codes(r);
  for (const k of ['MIEMBRO_INEXISTENTE', 'VAL_OBLIGATORIO', 'NUM_INVALIDO', 'CLAVE_DUPLICADA', 'VAL_LONGITUD', 'VAL_CARACTERES']) assert.ok(c.includes(k), `falta ${k}: ${c}`);
  assert.match(r.issues.find((i) => i.code === 'MIEMBRO_INEXISTENTE').message, /¿Quiso decir "CL_BOG"\?/);
  assert.equal(r.ok, false);
});

test('validador: Ingreso usa "#" para Cliente/Regional si no vienen, y el archivo manda si vienen', () => {
  const H = ['Sociedad_CL', 'Cebes_CL', 'Ratio_CL', 'Auditoria_CL', 'Moneda_CL', 'Ene 2026'];
  const sin = run('CL_INGRESOS', 'CL_INGRESO', [H, ['CL_BOG', 'RECOLECCION', 'TARIFA', 'PXQ', 'COP', 10]]);
  assert.equal(sin.ok, true, JSON.stringify(sin.issues));
  assert.equal(sin.records[0].Cliente, '#');
  assert.equal(sin.records[0].Regional, '#');
  const con = run('CL_INGRESOS', 'CL_INGRESO', [[...H, 'Cliente'], ['CL_BOG', 'RECOLECCION', 'TARIFA', 'PXQ', 'COP', 10, 'CLI_002']]);
  assert.equal(con.ok, true, JSON.stringify(con.issues));
  assert.equal(con.records[0].Cliente, 'CLI_002');
  assert.equal(con.records[0].Regional, '#');
  const neg = run('CL_INGRESOS', 'CL_INGRESO', [H, ['CL_BOG', 'RECOLECCION', 'TARIFA', 'PXQ', 'COP', -5]], { templateOverride: { rules: { allowNegative: false } } });
  assert.ok(codes(neg).includes('NUM_NEGATIVO'));
});

test('validador: formato largo (Date + Importe) y periodo inválido', () => {
  const H = [...HDR.slice(0, 6), 'Date', 'Importe'];
  const ok = run('CL_GASTOS', 'CL_GASTOS', [H, [...ROW, 'Mar 2026', '10']]);
  assert.equal(ok.ok, true, JSON.stringify(ok.issues));
  assert.equal(ok.summary.layout, 'long');
  assert.equal(ok.records[0].Date, '202603');
  const bad = run('CL_GASTOS', 'CL_GASTOS', [H, [...ROW, '2026-13', '10']]);
  assert.ok(codes(bad).includes('PER_INVALIDO'));
});

test('validador: archivo sin valores y miembro "#" (sin asignar)', () => {
  const r = run('CL_EEFF', 'CL_EEFF', [
    ['Sociedad_CL', 'Cuentas_EF_CL', 'Cebes_CL', 'Cecos_CL', 'Auditoria_CL', 'Moneda_CL', 'Ene 2026'],
    ['CL_BOG', '1105_CAJA', 'CORPORATIVO', '#', 'MANUAL', 'COP', null],
  ]);
  assert.deepEqual(codes(r), ['SIN_REGISTROS']);
});
