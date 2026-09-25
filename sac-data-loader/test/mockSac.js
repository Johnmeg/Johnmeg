'use strict';

const crypto = require('crypto');
const express = require('express');

// Simulador de SAP Analytics Cloud para pruebas y demostración:
//   - Servidor OAuth (authorize con página de login + token con PKCE y refresh)
//   - Data Import API (/api/v1/dataimport) con CSRF, jobs, validate, run, status
//   - Data Export API (/api/v1/dataexport) para leer miembros, paginado
// Imita las respuestas documentadas por SAP; no es un SAC real.

const CLIENT_ID = 'sac-loader-demo';
const CLIENT_SECRET = 'demo-secret';
const USERS = {
  ana: { password: 'demo', given_name: 'Ana', family_name: 'Planeación', email: 'ana@ciudadlimpia.test' },
  luis: { password: 'demo', given_name: 'Luis', family_name: 'Sin Permisos', email: 'luis@ciudadlimpia.test', readOnly: true },
};

const VERSIONS = ['public.Actual', 'public.Plan', 'public.Forecast'];
const COMMON = {
  Sociedad_CL: ['CL_BOG', 'CL_NEI', 'CL_MED'],
  Cebes_CL: ['RECOLECCION', 'BARRIDO', 'DISPOSICION', 'CORPORATIVO'],
  Moneda_CL: ['COP', 'USD'],
};

const MODELS = {
  CL_INGRESOS: {
    name: 'Modelo Ingreso Ciudad Limpia',
    dims: {
      ...COMMON,
      Cliente: ['CLI_001', 'CLI_002', 'CLI_003'],
      Regional: ['REG_CENTRO', 'REG_NORTE'],
      Ratio_CL: ['ING_RECOLECCION', 'ING_BARRIDO', 'ING_DISPOSICION', 'TARIFA', 'CANTIDAD'],
      Auditoria_CL: ['PRESUPUESTO_TARIFAS', 'PXQ', 'MANUAL', 'AJUSTE', 'CALCULADO'],
    },
  },
  CL_GASTOS: {
    name: 'Modelo Gastos Ciudad Limpia',
    dims: {
      ...COMMON,
      Cecos_CL: ['CECO_ADMIN', 'CECO_OPER', 'VEH_ABC123', 'VEH_XYZ789'],
      Cuentas_Egresos_CL: ['5105_SALARIOS', '5205_SERV_PUBLICOS', '5210_COMBUSTIBLE', '5260_DEPRECIACION', ...Array.from({ length: 120 }, (_, i) => `59${String(i).padStart(2, '0')}_OTROS`)],
      Auditoria_CL: ['PRESUPUESTO_EXCEL', 'MANUAL', 'AJUSTE', 'CALCULADO'],
    },
  },
  CL_EEFF: {
    name: 'Modelo EEFF Ciudad Limpia',
    dims: {
      ...COMMON,
      Cuentas_EF_CL: ['1105_CAJA', '1305_CLIENTES', '1524_EQUIPO', '2205_PROVEEDORES', 'FC_CAPEX'],
      Cecos_CL: ['CECO_ADMIN', 'CECO_OPER'],
      Auditoria_CL: ['MANUAL', 'AJUSTE', 'CALCULADO'],
    },
  },
};

function metadataOf(modelId) {
  const m = MODELS[modelId];
  const columns = [
    { columnName: 'Version', columnDataType: 'string', maxLength: 300, isKey: true },
    { columnName: 'Date', columnDataType: 'string', maxLength: 6, isKey: true },
    ...Object.keys(m.dims).map((d) => ({ columnName: d, columnDataType: 'string', maxLength: 40, isKey: true })),
    { columnName: 'Importe', columnDataType: 'decimal', maxLength: 31, isKey: false },
  ];
  return { factData: { keys: columns.filter((c) => c.isKey).map((c) => c.columnName), columns } };
}

const b64url = (s) => Buffer.from(s).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

function createMockSac({ baseUrl, redirectUris = [], tokenTtlSec = 3600, logger = () => {} } = {}) {
  const app = express();
  const codes = new Map(); const tokens = new Map(); const refreshTokens = new Map();
  const csrfTokens = new Map(); // access token -> csrf
  const jobs = new Map();
  const facts = new Map(); // modelId -> Map(key -> row)
  const log = [];

  app.use(express.urlencoded({ extended: false }));
  app.use(express.json({ limit: '300mb' }));
  app.use((req, res, next) => { log.push(`${req.method} ${req.path}`); logger(`${req.method} ${req.originalUrl}`); next(); });

  // ------------------------------------------------------------ OAuth
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
  app.get('/oauth/authorize', (req, res) => {
    const q = req.query;
    if (q.client_id !== CLIENT_ID) return res.status(400).send('client_id inválido');
    if (redirectUris.length && !redirectUris.includes(q.redirect_uri)) return res.status(400).send('redirect_uri no registrada');
    const hidden = ['client_id', 'redirect_uri', 'state', 'code_challenge', 'code_challenge_method', 'scope']
      .map((k) => `<input type="hidden" name="${k}" value="${esc(q[k])}">`).join('');
    res.type('html').send(`<!doctype html><html lang="es"><head><meta charset="utf-8"><title>SAP Analytics Cloud (simulado)</title>
<style>body{font-family:system-ui;background:#0a6ed1;display:grid;place-items:center;min-height:100vh;margin:0}
form{background:#fff;padding:32px;border-radius:12px;width:320px;box-shadow:0 10px 30px #0004}
h1{font-size:18px;margin:0 0 4px}p{color:#555;font-size:13px;margin:0 0 16px}
label{display:block;font-size:13px;margin:10px 0 4px}input{width:100%;padding:8px;box-sizing:border-box;font-size:14px}
button{margin-top:18px;width:100%;padding:10px;background:#0a6ed1;color:#fff;border:0;border-radius:6px;font-size:15px}
.err{color:#b00;font-size:13px}</style></head><body>
<form method="post" action="/oauth/authorize">${hidden}
<h1>SAP Analytics Cloud</h1><p>Servidor simulado para demostración. Usuarios: <b>ana</b> / <b>demo</b> (planificador) o <b>luis</b> / <b>demo</b> (sin permiso de escritura).</p>
${q.err ? '<div class="err">Usuario o contraseña incorrectos.</div>' : ''}
<label for="u">Usuario</label><input id="u" name="username" autocomplete="username" autofocus>
<label for="p">Contraseña</label><input id="p" name="password" type="password" autocomplete="current-password">
<button type="submit">Iniciar sesión</button></form></body></html>`);
  });

  app.post('/oauth/authorize', (req, res) => {
    const b = req.body;
    const user = USERS[b.username];
    if (!user || user.password !== b.password) {
      const back = new URLSearchParams({ ...b, err: '1' });
      back.delete('username'); back.delete('password');
      return res.redirect(`/oauth/authorize?${back}`);
    }
    const code = crypto.randomBytes(16).toString('hex');
    codes.set(code, { username: b.username, redirectUri: b.redirect_uri, challenge: b.code_challenge || null, at: Date.now() });
    const u = new URL(b.redirect_uri);
    u.searchParams.set('code', code);
    if (b.state) u.searchParams.set('state', b.state);
    return res.redirect(u.toString());
  });

  function issueTokens(username) {
    const u = USERS[username];
    const payload = { user_name: username, given_name: u.given_name, family_name: u.family_name, email: u.email, exp: Math.floor(Date.now() / 1000) + tokenTtlSec, jti: crypto.randomUUID() };
    const access = `${b64url('{"alg":"none"}')}.${b64url(JSON.stringify(payload))}.mock`;
    const refresh = crypto.randomBytes(20).toString('hex');
    tokens.set(access, { username, exp: Date.now() + tokenTtlSec * 1000 });
    refreshTokens.set(refresh, username);
    return { access_token: access, token_type: 'bearer', expires_in: tokenTtlSec, refresh_token: refresh, scope: 'uaa.user' };
  }

  app.post('/oauth/token', (req, res) => {
    const basic = Buffer.from(String(req.get('authorization') || '').replace(/^Basic /, ''), 'base64').toString();
    if (basic !== `${CLIENT_ID}:${CLIENT_SECRET}`) return res.status(401).json({ error: 'invalid_client' });
    const b = req.body;
    if (b.grant_type === 'authorization_code') {
      const c = codes.get(b.code);
      codes.delete(b.code);
      if (!c || c.redirectUri !== b.redirect_uri) return res.status(400).json({ error: 'invalid_grant' });
      if (c.challenge) {
        const calc = crypto.createHash('sha256').update(String(b.code_verifier || '')).digest('base64url');
        if (calc !== c.challenge) return res.status(400).json({ error: 'invalid_grant', error_description: 'PKCE' });
      }
      return res.json(issueTokens(c.username));
    }
    if (b.grant_type === 'refresh_token') {
      const username = refreshTokens.get(b.refresh_token);
      if (!username) return res.status(400).json({ error: 'invalid_grant' });
      return res.json(issueTokens(username));
    }
    return res.status(400).json({ error: 'unsupported_grant_type' });
  });

  // ------------------------------------------------------------ API: autenticación + CSRF
  function auth(req, res, next) {
    const t = String(req.get('authorization') || '').replace(/^Bearer /, '');
    const info = tokens.get(t);
    if (!info || info.exp < Date.now()) return res.status(401).json({ error: { message: 'Invalid token' } });
    req.user = { ...USERS[info.username], username: info.username };
    req.token = t;
    if (req.get('x-csrf-token') === 'fetch') {
      const csrf = crypto.randomBytes(12).toString('hex');
      csrfTokens.set(t, csrf);
      res.set('x-csrf-token', csrf);
    }
    return next();
  }
  function csrf(req, res, next) {
    if (!csrfTokens.get(req.token) || req.get('x-csrf-token') !== csrfTokens.get(req.token)) {
      res.set('x-csrf-token', 'Required');
      return res.status(403).json({ error: { message: 'CSRF token validation failed' } });
    }
    return next();
  }
  function model(req, res, next) {
    if (!MODELS[req.params.modelId]) return res.status(404).json({ error: { message: `Model ${req.params.modelId} not found` } });
    return next();
  }
  function job(req, res, next) {
    const j = jobs.get(req.params.jobId);
    if (!j || j.owner !== req.user.username) return res.status(404).json({ error: { message: 'Job not found' } });
    req.job = j;
    return next();
  }

  const IMP = '/api/v1/dataimport';
  app.get(`${IMP}/models`, auth, (req, res) => {
    res.json({
      models: Object.entries(MODELS).map(([id, m]) => ({
        modelID: id, modelName: m.name, description: m.name, modelURL: `${baseUrl}${IMP}/models/${id}`,
      })),
    });
  });
  app.get(`${IMP}/models/:modelId/metadata`, auth, model, (req, res) => res.json(metadataOf(req.params.modelId)));

  app.post(`${IMP}/models/:modelId/:importType`, auth, csrf, model, (req, res) => {
    if (!['factData', 'privateFactData'].includes(req.params.importType)) return res.status(400).json({ error: { message: 'importType no soportado por el simulador' } });
    if (req.user.readOnly) return res.status(403).json({ error: { message: 'User does not have Maintain permission on model' } });
    const jobId = `JOB${crypto.randomBytes(6).toString('hex').toUpperCase()}`;
    const settings = { importMethod: 'Update', executeWithFailedRows: true, ...(req.body?.JobSettings || {}) };
    jobs.set(jobId, { id: jobId, owner: req.user.username, modelId: req.params.modelId, settings, rows: [], failed: [], status: 'READY_FOR_DATA' });
    res.json({ JobID: jobId, JobURL: `${baseUrl}${IMP}/jobs/${jobId}` });
  });

  function rowError(modelId, row) {
    const meta = metadataOf(modelId).factData;
    for (const k of meta.keys) {
      const v = row[k];
      if (v === undefined || v === null || v === '') return `Missing value for key column ${k}`;
      if (k === 'Version') { if (!VERSIONS.includes(v)) return `Invalid member ${v} for dimension Version`; continue; }
      if (k === 'Date') { if (!/^\d{6}$/.test(String(v))) return `Invalid date ${v}`; continue; }
      if (v !== '#' && !MODELS[modelId].dims[k].includes(v)) return `Invalid member ${v} for dimension ${k}`;
    }
    if (typeof row.Importe !== 'number' || !Number.isFinite(row.Importe)) return 'Invalid measure value for Importe';
    const extra = Object.keys(row).filter((c) => !meta.columns.some((x) => x.columnName === c));
    if (extra.length) return `Unknown column(s): ${extra.join(', ')}`;
    return null;
  }

  app.post(`${IMP}/jobs/:jobId`, auth, csrf, job, (req, res) => {
    const data = Array.isArray(req.body?.Data) ? req.body.Data : [];
    const failedRows = [];
    for (const row of data) {
      const reason = rowError(req.job.modelId, row);
      if (reason) failedRows.push({ row, reason }); else req.job.rows.push(row);
    }
    req.job.failed.push(...failedRows);
    res.json({
      totalNumberRowsInCurrentRequest: data.length, upsertedNumberRows: data.length - failedRows.length,
      failedNumberRows: failedRows.length, failedRows, totalNumberRowsInJob: req.job.rows.length,
    });
  });

  function scopeKey(settings, row) { return (settings.dimensionScope || []).map((d) => row[d]).join('|'); }
  function affected(j) {
    const store = facts.get(j.modelId) || new Map();
    const scopes = new Set(j.rows.map((r) => scopeKey(j.settings, r)));
    let n = 0;
    for (const r of store.values()) if (scopes.has(scopeKey(j.settings, r))) n++;
    return n;
  }

  app.post(`${IMP}/jobs/:jobId/validate`, auth, csrf, job, (req, res) => {
    const j = req.job;
    j.status = 'READY_FOR_WRITE';
    const out = {
      jobStatus: j.status, totalNumberRowsInJob: j.rows.length, failedNumberRows: j.failed.length,
      invalidRowsURL: `${baseUrl}${IMP}/jobs/${j.id}/invalidRows`, additionalInformation: {},
    };
    if (j.settings.importMethod === 'CleanAndReplace') {
      out.additionalInformation.cleanAndReplaceAffectedRows = [{ dimensionScope: j.settings.dimensionScope, numberOfRowsToBeDeleted: affected(j) }];
    }
    res.json(out);
  });

  app.get(`${IMP}/jobs/:jobId/invalidRows`, auth, job, (req, res) => {
    res.json({ failedRows: req.job.failed.map((f) => ({ ...f.row, _REJECTION_REASON: f.reason })) });
  });

  app.post(`${IMP}/jobs/:jobId/run`, auth, csrf, job, (req, res) => {
    const j = req.job;
    if (j.failed.length && !j.settings.executeWithFailedRows) {
      j.status = 'FAILED';
    } else {
      const store = facts.get(j.modelId) || new Map();
      if (j.settings.importMethod === 'CleanAndReplace') {
        const scopes = new Set(j.rows.map((r) => scopeKey(j.settings, r)));
        for (const [k, r] of store) if (scopes.has(scopeKey(j.settings, r))) store.delete(k);
      }
      const keys = metadataOf(j.modelId).factData.keys;
      for (const r of j.rows) {
        const k = keys.map((c) => r[c]).join('|');
        const prev = store.get(k);
        store.set(k, j.settings.importMethod === 'Append' && prev ? { ...r, Importe: prev.Importe + r.Importe } : { ...r });
      }
      facts.set(j.modelId, store);
      j.status = 'PROCESSING'; // pasa a COMPLETED en la siguiente consulta de estado
      j.completeOnNextStatus = true;
    }
    res.json({ jobStatus: j.status, totalNumberRowsInJob: j.rows.length, failedNumberRows: j.failed.length });
  });

  app.get(`${IMP}/jobs/:jobId/status`, auth, job, (req, res) => {
    const j = req.job;
    if (j.completeOnNextStatus) { j.status = 'COMPLETED'; j.completeOnNextStatus = false; }
    res.json({
      jobStatus: j.status, jobStatusDescription: j.status === 'COMPLETED' ? 'Job completed successfully' : j.status,
      additionalInformation: { totalNumberRowsInJob: j.rows.length, failedNumberRows: j.failed.length },
    });
  });

  app.delete(`${IMP}/jobs/:jobId`, auth, csrf, job, (req, res) => {
    jobs.delete(req.job.id);
    res.json({ message: 'Job deleted' });
  });

  // ------------------------------------------------------------ Data Export API (maestros)
  const PAGE = 50;
  app.get('/api/v1/dataexport/providers/sac/:modelId/:master', auth, model, (req, res) => {
    const dim = req.params.master.replace(/Master$/, '');
    const list = dim === 'Version' ? VERSIONS : MODELS[req.params.modelId].dims[dim];
    if (!list) return res.status(404).json({ error: { message: `Entity ${req.params.master} not found` } });
    const skip = Number(req.query.$skip || 0);
    const page = list.slice(skip, skip + PAGE).map((id) => ({ ID: id, Description: id }));
    const out = { value: page };
    if (skip + PAGE < list.length) {
      const q = new URLSearchParams(req.query); q.set('$skip', String(skip + PAGE));
      out['@odata.nextLink'] = `${req.params.master}?${q}`;
    }
    return res.json(out);
  });

  return {
    app, jobs, facts, log,
    expireAllTokens() { for (const t of tokens.values()) t.exp = 0; },
    clientId: CLIENT_ID, clientSecret: CLIENT_SECRET,
  };
}

module.exports = { createMockSac, metadataOf, MODELS, VERSIONS, CLIENT_ID, CLIENT_SECRET };
