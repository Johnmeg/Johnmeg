'use strict';

// Marcas (BRAND): textos, logos, colores y catálogo de modelos por empresa.

const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('http');
const crypto = require('crypto');
const { loadBrand, listBrands, renderIndex } = require('../src/brand');
const { loadConfig, loadTemplates } = require('../src/config');
const { createApp } = require('../src/app');

const ENV = {
  SAC_TENANT_URL: 'https://tenant.example', SAC_AUTHORIZE_URL: 'https://auth.example/oauth/authorize',
  SAC_TOKEN_URL: 'https://auth.example/oauth/token', SAC_CLIENT_ID: 'id', SAC_CLIENT_SECRET: 'secret',
  SESSION_SECRET: crypto.randomBytes(32).toString('hex'),
};

test('marca: ciudadlimpia por defecto y fanalca disponible', () => {
  assert.deepEqual(listBrands().sort(), ['ciudadlimpia', 'fanalca']);
  assert.equal(loadBrand().name, 'Ciudad Limpia');
  assert.equal(loadBrand('Fanalca').id, 'fanalca');
  assert.throws(() => loadBrand('otra'), /no existe/);
  assert.throws(() => loadBrand('../config'), /no existe/);
});

test('marca: cada BRAND trae sus modelos de SAC', () => {
  const cl = loadConfig({ ...ENV });
  assert.ok(cl.templates.some((t) => t.id === 'CL_GASTOS'));
  const fn = loadConfig({ ...ENV, BRAND: 'fanalca' });
  assert.equal(fn.brand.name, 'Fanalca');
  assert.deepEqual(fn.templates.map((t) => t.model.name).filter(Boolean),
    ['Modelo Ingresos FANALCA', 'Modelo Gastos FANALCA', 'Modelo EEFF FANALCA']);
  assert.ok(fn.templates.every((t) => !t.model.id || /^C[a-z0-9]{20,}$/.test(t.model.id)));
  // TEMPLATES_FILE sigue teniendo prioridad
  const otro = loadConfig({ ...ENV, BRAND: 'fanalca', TEMPLATES_FILE: cl.templatesFile });
  assert.ok(otro.templates.some((t) => t.id === 'CL_GASTOS'));
});

test('marca: los textos se escapan al armar la página', () => {
  const html = renderIndex('<title>{{name}}</title>{{desconocido}}', { name: '<b>A&B</b>' });
  assert.equal(html, '<title>&lt;b&gt;A&amp;B&lt;/b&gt;</title>{{desconocido}}');
});

test('marca: la aplicación sirve página, colores y logos de Fanalca', async () => {
  const cfg = loadConfig({ ...ENV, BRAND: 'fanalca' });
  const app = createApp(cfg, { logger: { error() {} } });
  const server = http.createServer(app);
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const page = await (await fetch(`${base}/`)).text();
    assert.match(page, /<title>Carga de datos a SAC · Fanalca<\/title>/);
    assert.match(page, /class="brand-fanalca"/);
    assert.doesNotMatch(page, /\{\{\w+\}\}|Ciudad Limpia/);
    const css = await fetch(`${base}/brand/theme.css`);
    assert.equal(css.status, 200);
    assert.match(await css.text(), /#071d49/i);
    for (const img of ['logo.png', 'logo-blanco.png', 'favicon.png']) {
      const r = await fetch(`${base}/brand/img/${img}`);
      assert.equal(r.status, 200, img);
      assert.equal(r.headers.get('content-type'), 'image/png');
    }
    assert.equal((await fetch(`${base}/brand/brand.json`)).status, 404);
    assert.equal((await fetch(`${base}/brand/templates.json`)).status, 404);
  } finally {
    app.locals.stop();
    server.close();
  }
});

test('marca: catálogo de Fanalca válido para el cargador', () => {
  const t = loadTemplates(loadBrand('fanalca').templatesFile);
  const ing = t.find((x) => x.id === 'FN_INGRESOS');
  assert.deepEqual(ing.cleanAndReplaceScope, ['Version', 'Date', 'Sociedades', 'Auditoria']);
  assert.deepEqual(ing.defaultValues, { Clientes: '#', Referencias: '#' });
});
