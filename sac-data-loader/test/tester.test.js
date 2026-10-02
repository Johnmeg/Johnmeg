'use strict';

// Probador de data actions: motor (sin SAC) y ejecución completa contra el SAC simulado
// (carga de entradas, multi action, lectura de FactData y comparación).

const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('http');
const path = require('path');
const engine = require('../src/tester/engine');
const { runCase, reportCsv } = require('../src/tester/runner');
const { SacClient } = require('../src/sacClient');
const { createMockSac, CLIENT_ID, CLIENT_SECRET } = require('./mockSac');

const catalog = (brand) => require(path.join(__dirname, '..', 'brands', brand, 'pruebas.json')).casos;
const caseOf = (brand, id) => structuredClone(catalog(brand).find((c) => c.id === id));

// ---------------------------------------------------------------- motor
test('probador: semilla reproducible y datos dentro del rango', async () => {
  const c = engine.normalizeCase(caseOf('fanalca', 'FN_PXQ_VENTAS'));
  const pool = { Sociedades: ['S1', 'S2', 'S3'], Cebes: ['C1', 'C2', 'C3', 'C4'], Clientes: ['K1', 'K2'], Referencias: ['R1', 'R2', 'R3'] };
  const pickMembers = async (dim) => pool[dim];
  const r1 = await engine.resolveMembers(c, { seed: 7, pickMembers });
  const r2 = await engine.resolveMembers(c, { seed: 7, pickMembers });
  assert.deepEqual([...r1], [...r2]);
  assert.equal(r1.get('PRECIO').Cebes.length, 2);
  assert.deepEqual(r1.get('VENTAS'), r1.get('PRECIO'), '@PRECIO comparte los mismos miembros');
  const a = engine.generateInputs(c, r1, 7);
  const b = engine.generateInputs(c, r1, 7);
  assert.deepEqual(a, b);
  assert.notDeepEqual(a, engine.generateInputs(c, r1, 8));
  for (const x of a.filter((i) => i.nombre === 'PRECIO')) assert.ok(x.value >= 5000000 && x.value <= 15000000 && Number.isInteger(x.value));
  assert.equal(a.length, 2 * 3 * 2 * 1 * 2); // 2 entradas × 3 periodos × 2 Cebes × 1 cliente × 2 referencias
  const exp = engine.computeExpected(c, r1, a);
  const p = a.find((i) => i.nombre === 'PRECIO');
  const u = a.find((i) => i.nombre === 'UNIDADES' && i.date === p.date && i.coords.Cebes === p.coords.Cebes && i.coords.Referencias === p.coords.Referencias);
  const e = exp.find((i) => i.date === p.date && i.coords.Cebes === p.coords.Cebes && i.coords.Referencias === p.coords.Referencias);
  assert.equal(e.expected, p.value * u.value);
});

test('probador: validación de la definición con mensajes claros', () => {
  const base = caseOf('fanalca', 'FN_PXQ_VENTAS');
  const bad = (patch, re) => assert.throws(() => engine.normalizeCase({ ...structuredClone(base), ...patch }), re);
  bad({ multiAction: 'sin-dos-puntos' }, /formato <paquete>:<ID>/);
  bad({ version: 'Plan' }, /versión pública de pruebas/);
  bad({ version: 'private.Mia' }, /versión pública de pruebas/);
  bad({ periodos: ['2026-01'] }, /Periodo inválido/);
  bad({ periodos: { desde: '202603', hasta: '202601' } }, /posterior/);
  bad({ esperado: [{ nombre: 'X', formula: 'v("PRECIO" *' }] }, /no es válida/);
  bad({ entradas: [{ nombre: 'A B' }] }, /nombre es obligatorio/);
  assert.deepEqual(engine.expandPeriods({ desde: '202611', hasta: '202702' }), ['202611', '202612', '202701', '202702']);
});

test('probador: fórmulas, filtro OData, tolerancia y parámetros', async () => {
  const c = engine.normalizeCase({
    id: 'T', modelo: 'M', multiAction: 'p:X', version: 'public.PRUEBAS', periodos: ['202601'],
    entradas: [{ nombre: 'A', fijo: { Cuenta: "O'Brien" }, variar: { Ceco: ['C1', 'C2'] }, min: 1, max: 1, decimales: 0 }],
    esperado: [
      { nombre: 'OK', fijo: { Cuenta: 'R' }, variar: { Ceco: '@A' }, formula: "v('A') / sum('A')" },
      { nombre: 'MAL', fijo: { Cuenta: 'R2' }, formula: "v('NO_EXISTE')" },
    ],
  });
  const r = await engine.resolveMembers(c, { seed: 1, pickMembers: async () => [] });
  const inputs = engine.generateInputs(c, r, 1);
  const exp = engine.computeExpected(c, r, inputs);
  assert.deepEqual(exp.filter((e) => e.nombre === 'OK').map((e) => e.expected), [0.5, 0.5]);
  assert.match(exp.find((e) => e.nombre === 'MAL').error, /no es una entrada/);
  const meta = { versionColumn: 'Version', dateColumn: 'Date', measure: 'Importe', keys: ['Version', 'Date', 'Cuenta', 'Ceco'] };
  const f = engine.factFilter(c, c.entradas[0], r, meta);
  assert.equal(f, "Version eq 'public.PRUEBAS' and Date eq '202601' and Cuenta eq 'O''Brien' and (Ceco eq 'C1' or Ceco eq 'C2')");
  const cmp = engine.compareGroup(exp.filter((e) => e.nombre === 'OK'), [
    { Date: '202601', Ceco: 'C1', Cuenta: 'R', Importe: '0.505' },
    { Date: '202601', Ceco: 'C2', Cuenta: 'R', Importe: 0.52 },
    { Date: '202601', Ceco: 'C9', Cuenta: 'R', Importe: 3 },
  ], meta);
  assert.deepEqual(cmp.map((x) => x.ok), [true, false]);
  assert.equal(cmp.extra, 1);
  const params = engine.fillParameters([{ parameterId: 'TargetVersion', value: { memberIds: ['{{version}}'] } }, { parameterId: 'Per', value: { memberIds: ['{{periodos}}'] } }], c);
  assert.deepEqual(params[0].value.memberIds, ['public.PRUEBAS']);
  assert.deepEqual(params[1].value.memberIds, ['202601']);
});

// ---------------------------------------------------------------- contra el SAC simulado
async function stack(brand) {
  const holder = {};
  const server = http.createServer((req, res) => holder.app(req, res));
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const url = `http://127.0.0.1:${server.address().port}`;
  const mock = createMockSac({ baseUrl: url, brand });
  holder.app = mock.app;
  const token = async (username) => {
    const redirect = 'http://localhost/cb';
    const r1 = await fetch(`${url}/oauth/authorize`, {
      method: 'POST', redirect: 'manual', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password: 'demo', redirect_uri: redirect, client_id: CLIENT_ID }),
    });
    const code = new URL(r1.headers.get('location')).searchParams.get('code');
    const r2 = await fetch(`${url}/oauth/token`, {
      method: 'POST', headers: { Authorization: `Basic ${Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64')}`, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'authorization_code', code, redirect_uri: redirect }),
    });
    return (await r2.json()).access_token;
  };
  const clientFor = async (user = 'ana') => {
    const t = await token(user);
    return new SacClient({ tenantUrl: url, getToken: async () => t, state: {} });
  };
  return { mock, clientFor, close: () => { server.closeAllConnections(); server.close(); } };
}

const OPTS = { blockedVersions: ['public.Actual'], pollMs: 5 };

test('probador: P×Q de Ciudad Limpia pasa contra el SAC simulado', async () => {
  const s = await stack('ciudadlimpia');
  try {
    const updates = [];
    const report = await runCase(await s.clientFor(), caseOf('ciudadlimpia', 'CL_PXQ_RESIDUOS'), { ...OPTS, seed: 42, onUpdate: (r) => updates.push(r.steps.map((x) => x.status).join()) });
    assert.equal(report.state, 'PASSED', report.error || JSON.stringify(report.summary));
    assert.equal(report.summary.cells, 3 * 2);
    assert.equal(report.summary.failed, 0);
    assert.ok(report.steps.every((x) => x.status === 'ok'));
    assert.ok(updates.length > 8, 'informa el avance paso a paso');
    assert.match(reportCsv([report]), /^\uFEFFCaso;Semilla;Resultado;Periodo;Auditoria_CL;Moneda_CL;Ratio_CL;Sociedad_CL;Cebes_CL;Esperado;Real;Diferencia;Estado;Detalle\r\nCL_PXQ_RESIDUOS;42;INGRESO;202601;Input;COP;ING_RES;/);
    assert.ok(s.mock.log.includes('POST /api/v1/multiActions/t.DEMO:CL_PXQ/executions'));
  } finally { s.close(); }
});

test('probador: distribución por km (emisores y receptores al azar por propiedad) pasa', async () => {
  const s = await stack('ciudadlimpia');
  try {
    const report = await runCase(await s.clientFor(), caseOf('ciudadlimpia', 'CL_DISTRIB_KM'), { ...OPTS, seed: 3 });
    assert.equal(report.state, 'PASSED', report.error || JSON.stringify(report.groups.map((g) => g.cells.filter((x) => !x.ok).slice(0, 2))));
    const recibido = report.groups.find((g) => g.nombre === 'RECIBIDO');
    assert.equal(new Set(recibido.cells.map((x) => x.coords.Cecos_CL)).size, 3);
    assert.ok(recibido.cells.every((x) => /^CL01SG/.test(x.coords.Cecos_CL)), 'sólo receptores');
    assert.ok(report.groups.find((g) => g.nombre === 'SALIDA').cells.every((x) => /^CL01TR/.test(x.coords.Cecos_CL)), 'sólo emisores');
  } finally { s.close(); }
});

test('probador: detecta un data action con error y muestra las diferencias', async () => {
  const s = await stack('fanalca');
  try {
    const report = await runCase(await s.clientFor(), caseOf('fanalca', 'FN_PXQ_CON_ERROR'), { ...OPTS, seed: 11 });
    assert.equal(report.state, 'FAILED');
    assert.ok(report.summary.failed > 0);
    const bad = report.groups[0].cells.find((x) => !x.ok);
    assert.ok(Math.abs(bad.diff) > 0.01 && bad.real !== null);
    // el mismo caso con la multi action correcta pasa
    const ok = await runCase(await s.clientFor(), { ...caseOf('fanalca', 'FN_PXQ_CON_ERROR'), multiAction: 't.DEMO:FN_PXQ' }, { ...OPTS, seed: 11 });
    assert.equal(ok.state, 'PASSED', ok.error);
  } finally { s.close(); }
});

test('probador: vista previa no escribe; versión bloqueada, miembros inexistentes y permisos', async () => {
  const s = await stack('fanalca');
  try {
    const client = await s.clientFor();
    const prev = await runCase(client, caseOf('fanalca', 'FN_PXQ_VENTAS'), { ...OPTS, seed: 5, preview: true });
    assert.equal(prev.state, 'PREVIEW', prev.error);
    assert.ok(prev.inputs.count > 0 && prev.groups[0].cells[0].expected > 0);
    assert.equal(s.mock.facts.size, 0, 'la vista previa no carga datos');
    assert.ok(!s.mock.log.some((l) => /multiActions/.test(l)));

    const blocked = await runCase(client, { ...caseOf('fanalca', 'FN_PXQ_VENTAS'), version: 'public.Actual' }, { ...OPTS, seed: 5 });
    assert.equal(blocked.state, 'ERROR');
    assert.match(blocked.error, /bloqueada/);

    const c = caseOf('fanalca', 'FN_PXQ_VENTAS');
    c.entradas[0].fijo.Ratio = 'NO_EXISTE';
    const missing = await runCase(client, c, { ...OPTS, seed: 5 });
    assert.equal(missing.state, 'ERROR');
    assert.match(missing.error, /Ratio=NO_EXISTE/);
    assert.equal(missing.steps.find((x) => x.id === 'miembros').status, 'error');

    const noMa = await runCase(client, { ...caseOf('fanalca', 'FN_PXQ_VENTAS'), multiAction: 't.DEMO:NO_EXISTE' }, { ...OPTS, seed: 5 });
    assert.equal(noMa.state, 'ERROR');
    assert.equal(noMa.steps.find((x) => x.id === 'ejecucion').status, 'error');

    const viewer = await runCase(await s.clientFor('luis'), caseOf('fanalca', 'FN_PXQ_VENTAS'), { ...OPTS, seed: 5 });
    assert.equal(viewer.state, 'ERROR');
    assert.equal(viewer.steps.find((x) => x.id === 'carga').status, 'error');
  } finally { s.close(); }
});
