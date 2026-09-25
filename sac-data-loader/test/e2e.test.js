'use strict';

// Prueba de extremo a extremo: navegador simulado -> aplicación -> SAC simulado.
// Cubre inicio de sesión OAuth (PKCE), validación, validación en SAC, carga,
// borrado y reemplazo, rechazo en SAC, permisos y renovación del token.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createMockSac, CLIENT_ID, CLIENT_SECRET } = require('./mockSac');
const { loadTemplates } = require('../src/config');
const { createApp } = require('../src/app');

const SAMPLES = path.join(__dirname, '..', 'samples');

const http = require('http');

// Se abre el puerto antes de crear la app porque la URL (puerto) forma parte de su configuración.
function listen(handler) {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, '127.0.0.1', () => resolve({ server, url: `http://127.0.0.1:${server.address().port}` }));
  });
}

async function startStack({ validateMembers = true, tokenTtlSec = 3600 } = {}) {
  const mockHolder = {};
  const mockStarted = await listen((req, res, next) => mockHolder.app(req, res, next));
  const mock = createMockSac({ baseUrl: mockStarted.url, tokenTtlSec });
  mockHolder.app = mock.app;

  const appHolder = {};
  const appStarted = await listen((req, res, next) => appHolder.app(req, res, next));
  const events = [];
  const cfg = {
    port: 0, baseUrl: appStarted.url,
    sac: {
      tenantUrl: mockStarted.url, authorizeUrl: `${mockStarted.url}/oauth/authorize`, tokenUrl: `${mockStarted.url}/oauth/token`,
      clientId: CLIENT_ID, clientSecret: CLIENT_SECRET, scope: '', usePkce: true,
    },
    sessionSecret: crypto.randomBytes(32).toString('hex'), cookieSecure: false, sessionMinutes: 60,
    maxFileMb: 1, maxRows: 1000, chunkSize: 7, numberLocale: 'es', blockedVersions: ['public.Actual'],
    validateMembers, templates: loadTemplates(path.join(__dirname, '..', 'config', 'templates.json')),
  };
  appHolder.app = createApp(cfg, { audit: (e) => events.push(e), logger: { error() {} } });
  return {
    mock, events, appUrl: appStarted.url, sacUrl: mockStarted.url,
    close() { appHolder.app.locals.stop(); appStarted.server.closeAllConnections(); appStarted.server.close(); mockStarted.server.closeAllConnections(); mockStarted.server.close(); },
  };
}

// Navegador mínimo con cookies por host
function browser() {
  const jar = new Map();
  return async function go(url, opts = {}) {
    const u = new URL(url);
    const cookies = jar.get(u.host) || {};
    const headers = { ...(opts.headers || {}) };
    const c = Object.entries(cookies).map(([k, v]) => `${k}=${v}`).join('; ');
    if (c) headers.Cookie = c;
    const res = await fetch(url, { ...opts, headers, redirect: 'manual' });
    for (const sc of res.headers.getSetCookie()) {
      const [pair] = sc.split(';'); const i = pair.indexOf('=');
      jar.set(u.host, { ...(jar.get(u.host) || {}), [pair.slice(0, i)]: pair.slice(i + 1) });
    }
    return res;
  };
}

async function login(stack, username = 'ana') {
  const go = browser();
  const r1 = await go(`${stack.appUrl}/auth/login`);
  assert.equal(r1.status, 302);
  const authUrl = new URL(r1.headers.get('location'));
  assert.equal(authUrl.origin, stack.sacUrl);
  assert.equal(authUrl.searchParams.get('code_challenge_method'), 'S256');
  const form = new URLSearchParams(Object.fromEntries(authUrl.searchParams));
  form.set('username', username); form.set('password', 'demo');
  const r2 = await go(`${stack.sacUrl}/oauth/authorize`, { method: 'POST', body: form });
  assert.equal(r2.status, 302);
  const back = r2.headers.get('location');
  assert.ok(back.startsWith(`${stack.appUrl}/auth/callback?code=`));
  const r3 = await go(back);
  assert.equal(r3.status, 302);
  assert.equal(r3.headers.get('location'), '/');

  const json = async (method, p, body) => {
    const opts = { method, headers: { 'X-Requested-With': 'sac-loader' } };
    if (body instanceof FormData) opts.body = body;
    else if (body) { opts.body = JSON.stringify(body); opts.headers['Content-Type'] = 'application/json'; }
    const res = await go(`${stack.appUrl}${p}`, opts);
    const text = await res.text();
    return { status: res.status, body: text.startsWith('{') ? JSON.parse(text) : text };
  };
  return { go, json };
}

function fileForm(fields, file) {
  const f = new FormData();
  for (const [k, v] of Object.entries(fields)) f.append(k, v);
  f.append('file', new Blob([fs.readFileSync(path.join(SAMPLES, file))]), file);
  return f;
}

async function waitFinal(json, uploadId) {
  for (let i = 0; i < 50; i++) {
    const s = await json('GET', `/api/sac/status/${uploadId}`);
    if (s.body.state !== 'RUNNING') return s.body;
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error('timeout');
}

test('flujo completo: login, validar, validar en SAC, cargar', async (t) => {
  const stack = await startStack();
  t.after(() => stack.close());

  const anon = await fetch(`${stack.appUrl}/api/templates`);
  assert.equal(anon.status, 401);

  const { json } = await login(stack);
  const me = await json('GET', '/api/me');
  assert.equal(me.body.user.name, 'Ana Planeación');

  const tpl = await json('GET', '/api/templates');
  assert.ok(tpl.body.templates.some((x) => x.id === 'CL_INGRESO'));

  const vers = await json('GET', '/api/versions?template=CL_INGRESO');
  assert.equal(vers.body.model.id, 'CL_INGRESOS'); // el ID configurado no existe en el simulador: se encontró por nombre
  assert.deepEqual(vers.body.expectedColumns.filter((c) => c.optional).map((c) => c.name).sort(), ['Cliente', 'Regional']);
  assert.ok(vers.body.expectedColumns.some((c) => c.name === 'Ratio_CL' && !c.optional));
  assert.deepEqual(vers.body.versions.find((v) => v.id === 'public.Actual'), { id: 'public.Actual', blocked: true });

  // Sin cabecera anti-CSRF: rechazado
  const { go } = await login(stack);
  const noHeader = await go(`${stack.appUrl}/api/validate`, { method: 'POST', body: fileForm({ template: 'CL_INGRESO', version: 'public.Plan' }, 'Ingreso_CL_valido.xlsx') });
  assert.equal(noHeader.status, 403);

  const v = await json('POST', '/api/validate', fileForm({ template: 'CL_INGRESO', version: 'public.Plan', importMethod: 'Update' }, 'Ingreso_CL_valido.xlsx'));
  assert.equal(v.status, 200, JSON.stringify(v.body));
  assert.equal(v.body.ok, true, JSON.stringify(v.body.issues));
  assert.equal(v.body.summary.records, 48);
  assert.equal(v.body.preview[0].Cliente, '#');

  const report = await json('GET', `/api/report/${v.body.uploadId}`);
  assert.match(report.body, /^\ufeff?"Severidad";"Código"/);

  const p = await json('POST', '/api/sac/prepare', { uploadId: v.body.uploadId });
  assert.equal(p.body.ok, true, JSON.stringify(p.body));
  assert.equal(p.body.totalRows, 48);
  assert.equal(stack.mock.facts.size, 0, 'nada escrito antes de confirmar');

  const again = await json('POST', '/api/sac/prepare', { uploadId: v.body.uploadId });
  assert.equal(again.status, 409);

  const run = await json('POST', '/api/sac/run', { uploadId: v.body.uploadId });
  assert.equal(run.status, 202);
  const final = await waitFinal(json, v.body.uploadId);
  assert.equal(final.state, 'COMPLETED', JSON.stringify(final));
  assert.equal(stack.mock.facts.get('CL_INGRESOS').size, 48);
  const row = [...stack.mock.facts.get('CL_INGRESOS').values()].find((x) => x.Sociedad_CL === 'CL_BOG' && x.Cebes_CL === 'RECOLECCION' && x.Date === '202601');
  assert.equal(row.Importe, 1250000.5);
  assert.equal(row.Version, 'public.Plan');
  assert.equal(row.Auditoria_CL, 'PRESUPUESTO_TARIFAS');

  assert.deepEqual(stack.events.map((e) => e.event).filter((e) => e !== 'LOGIN'), ['VALIDACION', 'PREPARACION', 'CARGA']);
  assert.ok(stack.events.every((e) => !('Importe' in e)));

  // Otro usuario no puede ver el archivo validado de Ana
  const other = await login(stack, 'ana');
  const foreign = await other.json('GET', `/api/sac/status/${v.body.uploadId}`);
  assert.equal(foreign.status, 404);
});

test('archivo con errores: no se envía nada a SAC', async (t) => {
  const stack = await startStack();
  t.after(() => stack.close());
  const { json } = await login(stack);
  const v = await json('POST', '/api/validate', fileForm({ template: 'CL_INGRESO', version: 'public.Plan' }, 'Ingreso_CL_con_errores.xlsx'));
  assert.equal(v.body.ok, false);
  const c = v.body.issues.map((i) => i.code);
  for (const k of ['MIEMBRO_INEXISTENTE', 'VAL_OBLIGATORIO', 'NUM_INVALIDO', 'CLAVE_DUPLICADA']) assert.ok(c.includes(k), k);
  const p = await json('POST', '/api/sac/prepare', { uploadId: v.body.uploadId });
  assert.equal(p.status, 409);
  assert.equal(stack.mock.jobs.size, 0);

  const blocked = await json('POST', '/api/validate', fileForm({ template: 'CL_GASTOS', version: 'public.Actual' }, 'Gastos_CL_valido.xlsx'));
  assert.ok(blocked.body.issues.some((i) => i.code === 'VERSION_BLOQUEADA'));

  const method = await json('POST', '/api/validate', fileForm({ template: 'CL_GASTOS', version: 'public.Plan', importMethod: 'CleanAndReplace' }, 'Gastos_CL_valido.xlsx'));
  assert.equal(method.status, 400);

  const ext = await json('POST', '/api/validate', (() => { const f = new FormData(); f.append('template', 'CL_GASTOS'); f.append('version', 'public.Plan'); f.append('file', new Blob(['x']), 'datos.exe'); return f; })());
  assert.equal(ext.status, 422);

  const big = await json('POST', '/api/validate', (() => { const f = new FormData(); f.append('template', 'CL_GASTOS'); f.append('version', 'public.Plan'); f.append('file', new Blob([Buffer.alloc(2 * 1024 * 1024, 65)]), 'grande.csv'); return f; })());
  assert.equal(big.status, 413);
});

test('CleanAndReplace exige confirmación e informa lo que se borra', async (t) => {
  const stack = await startStack();
  t.after(() => stack.close());
  const { json } = await login(stack);
  const load = async (importMethod) => {
    const v = await json('POST', '/api/validate', fileForm({ template: 'CL_INGRESO', version: 'public.Plan', importMethod }, 'Ingreso_CL_valido.xlsx'));
    assert.equal(v.body.ok, true);
    const p = await json('POST', '/api/sac/prepare', { uploadId: v.body.uploadId });
    assert.equal(p.body.ok, true);
    return { v, p };
  };
  const first = await load('Update');
  await json('POST', '/api/sac/run', { uploadId: first.v.body.uploadId });
  assert.equal((await waitFinal(json, first.v.body.uploadId)).state, 'COMPLETED');

  const { v, p } = await load('CleanAndReplace');
  assert.deepEqual(p.body.jobSettings.dimensionScope, ['Version', 'Date', 'Sociedad_CL', 'Auditoria_CL']);
  assert.equal(p.body.cleanAndReplaceAffectedRows[0].numberOfRowsToBeDeleted, 48);
  const noConfirm = await json('POST', '/api/sac/run', { uploadId: v.body.uploadId });
  assert.equal(noConfirm.status, 400);
  const ok = await json('POST', '/api/sac/run', { uploadId: v.body.uploadId, confirmCleanAndReplace: true });
  assert.equal(ok.status, 202);
  assert.equal((await waitFinal(json, v.body.uploadId)).state, 'COMPLETED');

  // Cancelar un job preparado lo elimina en SAC
  const c = await load('Update');
  const jobsBefore = stack.mock.jobs.size;
  const cancel = await json('POST', '/api/sac/cancel', { uploadId: c.v.body.uploadId });
  assert.equal(cancel.body.ok, true);
  assert.equal(stack.mock.jobs.size, jobsBefore - 1);
});

test('SAC rechaza filas: se cancela el job completo (sin validación local de miembros)', async (t) => {
  const stack = await startStack({ validateMembers: false });
  t.after(() => stack.close());
  const { json } = await login(stack);
  const v = await json('POST', '/api/validate', fileForm({ template: 'OTRO', modelId: 'CL_GASTOS', version: 'public.Plan' }, 'Gastos_CL_formato_largo.csv'));
  assert.equal(v.body.ok, true, JSON.stringify(v.body.issues));
  // CL_MED existe; forzar un miembro inválido cambiando el archivo:
  const bad = fs.readFileSync(path.join(SAMPLES, 'Gastos_CL_formato_largo.csv'), 'utf8').replace(/CL_MED/g, 'CL_XXX');
  const f = new FormData();
  f.append('template', 'OTRO'); f.append('modelId', 'CL_GASTOS'); f.append('version', 'public.Plan');
  f.append('file', new Blob([bad]), 'malo.csv');
  const v2 = await json('POST', '/api/validate', f);
  assert.equal(v2.body.ok, true);
  const p = await json('POST', '/api/sac/prepare', { uploadId: v2.body.uploadId });
  assert.equal(p.body.ok, false);
  assert.equal(p.body.stage, 'ENVIO');
  assert.match(p.body.rejected[0]._REJECTION_REASON, /CL_XXX/);
  assert.equal(stack.mock.jobs.size, 0, 'el job se eliminó');
  assert.equal(stack.mock.facts.size, 0, 'nada se escribió');
  const rep = await json('GET', `/api/report/${v2.body.uploadId}`);
  assert.match(rep.body, /RECHAZO_SAC/);
});

test('permisos de SAC y renovación de token', async (t) => {
  const stack = await startStack({ tokenTtlSec: 30 }); // expira dentro del margen: se renueva en cada llamada
  t.after(() => stack.close());
  const luis = await login(stack, 'luis');
  const v = await luis.json('POST', '/api/validate', fileForm({ template: 'CL_GASTOS', version: 'public.Plan' }, 'Gastos_CL_valido.xlsx'));
  assert.equal(v.body.ok, true, JSON.stringify(v.body.issues));
  const p = await luis.json('POST', '/api/sac/prepare', { uploadId: v.body.uploadId });
  assert.equal(p.status, 502);
  assert.match(p.body.error, /no tiene permisos/);
  assert.ok(stack.mock.log.filter((l) => l === 'POST /oauth/token').length >= 3, 'se renovó el token');

  // Token vencido: la app lo renueva con el refresh token sin pedir login de nuevo
  const ana = await login(stack, 'ana');
  stack.mock.expireAllTokens();
  const models = await ana.json('GET', '/api/models');
  assert.equal(models.status, 200, 'renovó con refresh token');
});

test('logout y token revocado cierran la sesión', async (t) => {
  const stack = await startStack();
  t.after(() => stack.close());
  const { json } = await login(stack);
  assert.equal((await json('GET', '/api/me')).status, 200);
  assert.equal((await json('POST', '/auth/logout')).status, 200);
  assert.equal((await json('GET', '/api/me')).body.authenticated, false);

  // Token revocado en SAC antes de su vencimiento -> 401 y se exige iniciar sesión otra vez
  const other = await login(stack);
  stack.mock.expireAllTokens();
  const r = await other.json('GET', '/api/models');
  assert.equal(r.status, 401);
  assert.match(r.body.error, /expiró/);
  assert.equal((await other.json('GET', '/api/me')).body.authenticated, false);
});
