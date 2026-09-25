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
const HDR = ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL', 'Ene 2026', 'Feb 2026'];
const CTX = [['Moneda:', 'COP'], ['Auditoría:', 'PRESUPUESTO_EXCEL']];

test('validador: archivo correcto genera registros con constantes y versión', () => {
  const r = run('CL_GASTOS', 'PL-03', [...CTX, HDR, ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', '1.000,5', null]]);
  assert.equal(r.ok, true, JSON.stringify(r.issues));
  assert.equal(r.records.length, 1);
  assert.deepEqual(r.records[0], {
    Moneda_CL: 'COP', Auditoria_CL: 'PRESUPUESTO_EXCEL', Version: 'public.Plan', Sociedad_CL: 'CL_BOG',
    Cecos_CL: 'CECO_ADMIN', Cebes_CL: 'RECOLECCION', Cuentas_Egresos_CL: '5105_SALARIOS', Date: '202601', Importe: 1000.5,
  });
  assert.equal(r.summary.skippedBlank, 1);
  assert.equal(r.summary.totalsByPeriod['202601'], 1000.5);
});

test('validador: errores de estructura detienen la validación', () => {
  assert.ok(codes(run('CL_GASTOS', 'PL-03', [['x', 'y'], ['1', '2']])).includes('ENC_NO_ENCONTRADO'));
  assert.ok(codes(run('CL_GASTOS', 'PL-03', [HDR, ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2]])).includes('COL_FALTANTE')); // sin Moneda/Auditoría
  assert.ok(codes(run('CL_GASTOS', 'PL-03', [...CTX, [...HDR, 'Responsable'], ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2, 'x']])).includes('COL_DESCONOCIDA'));
  assert.ok(codes(run('CL_GASTOS', 'PL-03', [...CTX, [...HDR, 'Ene 2026'], ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2, 3]])).includes('PER_DUPLICADO'));
  assert.ok(codes(run('CL_GASTOS', 'PL-03', [...CTX, [...HDR, null], ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2, 3]])).includes('ENC_VACIO'));
  assert.ok(codes(run('CL_GASTOS', 'PL-03', [...CTX, ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL'], ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS']])).includes('PER_SIN_COLUMNAS'));
});

test('validador: versión obligatoria, bloqueada, distinta o inexistente', () => {
  const rows = [...CTX, HDR, ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2]];
  assert.ok(codes(run('CL_GASTOS', 'PL-03', rows, { version: '' })).includes('VERSION_REQUERIDA'));
  assert.ok(codes(run('CL_GASTOS', 'PL-03', rows, { version: 'public.Actual' })).includes('VERSION_BLOQUEADA'));
  assert.ok(codes(run('CL_GASTOS', 'PL-03', rows, { version: 'public.Inventada' })).includes('VERSION_INEXISTENTE'));
  assert.ok(codes(run('CL_GASTOS', 'PL-03', [['Versión:', 'Forecast'], ...rows])).includes('VERSION_DIFERENTE'));
  assert.equal(run('CL_GASTOS', 'PL-03', [['Versión:', 'Plan'], ...rows]).ok, true);
});

test('validador: errores por fila (miembros, vacíos, números, duplicados, permitidos)', () => {
  const r = run('CL_GASTOS', 'PL-03', [...CTX, HDR,
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2],
    ['cl_bog', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2],
    ['CL_BOG', '', 'RECOLECCION', '5105_SALARIOS', 1, 2],
    ['CL_BOG', 'CECO_OPER', 'RECOLECCION', '5105_SALARIOS', 'diez', { excelError: '#REF!' }],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 5, 6],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', 'X'.repeat(50), 1, 2],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', 'a\tb', 1, 2],
  ]);
  const c = codes(r);
  for (const k of ['MIEMBRO_INEXISTENTE', 'VAL_OBLIGATORIO', 'NUM_INVALIDO', 'CLAVE_DUPLICADA', 'VAL_LONGITUD', 'VAL_CARACTERES']) assert.ok(c.includes(k), `falta ${k}: ${c}`);
  assert.match(r.issues.find((i) => i.code === 'MIEMBRO_INEXISTENTE').message, /¿Quiso decir "CL_BOG"\?/);
  assert.equal(r.ok, false);

  const bad = run('CL_GASTOS', 'PL-03', [['Moneda:', 'COP'], ['Auditoría:', 'OTRA'], HDR, ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 1, 2]]);
  assert.ok(codes(bad).includes('VAL_NO_PERMITIDO'));
});

test('validador: PL-02 no admite negativos e ignora Tipo_Residuo con aviso', () => {
  const r = run('CL_INGRESOS', 'PL-02', [
    ['Moneda:', 'COP'], ['Auditoría:', 'PXQ'],
    ['Sociedad_CL', 'Cebes_CL', 'Cliente', 'Tipo_Residuo', 'Ratio_CL', 'Ene 2026'],
    ['CL_BOG', 'RECOLECCION', 'CLI_001', 'Ordinario', 'TARIFA', -5],
  ]);
  const c = codes(r);
  assert.ok(c.includes('NUM_NEGATIVO'));
  assert.ok(c.includes('COL_IGNORADA'));
});

test('validador: formato largo (GENERICO) y periodo inválido', () => {
  const H = ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL', 'Moneda_CL', 'Auditoria_CL', 'Date', 'Importe'];
  const ok = run('CL_GASTOS', 'GENERICO', [H, ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 'COP', 'MANUAL', 'Mar 2026', '10']]);
  assert.equal(ok.ok, true, JSON.stringify(ok.issues));
  assert.equal(ok.summary.layout, 'long');
  assert.equal(ok.records[0].Date, '202603');
  const bad = run('CL_GASTOS', 'GENERICO', [H, ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', 'COP', 'MANUAL', '2026-13', '10']]);
  assert.ok(codes(bad).includes('PER_INVALIDO'));
});

test('validador: archivo sin valores y miembro "#" (sin asignar)', () => {
  const r = run('CL_GASTOS', 'PL-03', [...CTX, HDR, ['CL_BOG', '#', 'RECOLECCION', '5105_SALARIOS', null, '']]);
  assert.deepEqual(codes(r), ['SIN_REGISTROS']);
});
