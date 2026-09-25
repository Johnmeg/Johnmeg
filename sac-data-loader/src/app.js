'use strict';

const crypto = require('crypto');
const path = require('path');
const express = require('express');
const session = require('express-session');
const multer = require('multer');

const oauth = require('./oauth');
const { SacClient, SacError } = require('./sacClient');
const { parseFile, ParseError, ALLOWED_EXT } = require('./parser');
const { buildMeta, ConfigError } = require('./meta');
const { validate, norm } = require('./validator');
const loader = require('./loader');

// Servidor web: inicio de sesión OAuth por usuario, validación local del
// archivo, validación en SAC y carga (Data Import API) en dos pasos.
//
// Los tokens de SAC y el client secret NUNCA llegan al navegador: se guardan en
// memoria del servidor ("bóveda") asociados a la sesión del usuario.

const UPLOAD_TTL_MS = 30 * 60 * 1000;
const MEMBER_TTL_MS = 10 * 60 * 1000;
const PREVIEW_ROWS = 20;

function createApp(cfg, { audit = () => {}, logger = console } = {}) {
  const app = express();
  const vault = new Map();   // vaultKey -> { tokens, user, sac: {csrf, cookies}, lastSeen, refreshing }
  const uploads = new Map(); // uploadId -> datos del archivo validado y del job
  const memberCache = new Map(); // `${modelId}|${dim}` -> { at, set }
  const templates = new Map(cfg.templates.map((t) => [t.id, t]));

  if (cfg.trustProxy) app.set('trust proxy', 1);
  app.disable('x-powered-by');

  // ------------------------------------------------------------ cabeceras de seguridad
  app.use((req, res, next) => {
    res.set({
      'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'",
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'Referrer-Policy': 'no-referrer',
      'Cache-Control': 'no-store',
    });
    if (cfg.cookieSecure) res.set('Strict-Transport-Security', 'max-age=31536000');
    next();
  });

  app.use(session({
    name: 'sacloader.sid',
    secret: cfg.sessionSecret,
    resave: false,
    saveUninitialized: false,
    rolling: true,
    cookie: {
      httpOnly: true,
      sameSite: 'lax', // "lax" permite volver desde la página de login de SAC (/auth/callback)
      secure: cfg.cookieSecure,
      maxAge: cfg.sessionMinutes * 60 * 1000,
    },
  }));

  app.use(express.json({ limit: '100kb' }));
  app.use(express.static(path.join(__dirname, '..', 'public'), { index: 'index.html' }));

  // Limpieza periódica de sesiones de SAC y archivos validados vencidos
  const sweeper = setInterval(() => {
    const now = Date.now();
    for (const [k, v] of vault) if (now - v.lastSeen > cfg.sessionMinutes * 60 * 1000) vault.delete(k);
    for (const [k, u] of uploads) {
      if (now - u.createdAt > UPLOAD_TTL_MS && u.job?.state !== 'RUNNING') {
        if (u.job?.state === 'PREPARED') discardJob(u);
        uploads.delete(k);
      }
    }
    for (const [k, m] of memberCache) if (now - m.at > MEMBER_TTL_MS) memberCache.delete(k);
  }, 60 * 1000);
  sweeper.unref();

  // ------------------------------------------------------------ utilidades
  const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

  function currentAuth(req) {
    const key = req.session?.vaultKey;
    const entry = key && vault.get(key);
    if (!entry) return null;
    entry.lastSeen = Date.now();
    return entry;
  }

  function requireAuth(req, res, next) {
    const entry = currentAuth(req);
    if (!entry) return res.status(401).json({ error: 'Debe iniciar sesión con su usuario de SAP Analytics Cloud.' });
    req.auth = entry;
    req.vaultKey = req.session.vaultKey;
    return next();
  }

  // Toda petición que modifica algo debe traer esta cabecera: un formulario de
  // otro sitio no puede enviarla sin una verificación CORS (que no se permite).
  function requireAjax(req, res, next) {
    if (req.get('X-Requested-With') !== 'sac-loader') {
      return res.status(403).json({ error: 'Solicitud no permitida.' });
    }
    return next();
  }

  async function getToken(entry) {
    const t = entry.tokens;
    if (Date.now() < t.expiresAt - 60 * 1000) return t.accessToken;
    if (!t.refreshToken) throw new SacError(401, 'La sesión con SAP Analytics Cloud expiró. Inicie sesión nuevamente.');
    if (!entry.refreshing) {
      entry.refreshing = oauth.refresh(cfg, t.refreshToken)
        .then((nt) => { entry.tokens = { ...nt, refreshToken: nt.refreshToken || t.refreshToken }; })
        .catch(() => { throw new SacError(401, 'La sesión con SAP Analytics Cloud expiró. Inicie sesión nuevamente.'); })
        .finally(() => { entry.refreshing = null; });
    }
    await entry.refreshing;
    return entry.tokens.accessToken;
  }

  function clientFor(entry) {
    return new SacClient({ tenantUrl: cfg.sac.tenantUrl, getToken: () => getToken(entry), state: entry.sac });
  }

  function getUpload(req, res) {
    const id = String(req.params.uploadId || req.body?.uploadId || '');
    const u = uploads.get(id);
    if (!u || u.vaultKey !== req.vaultKey) {
      res.status(404).json({ error: 'El archivo validado no existe o expiró. Vuelva a validarlo.' });
      return null;
    }
    return u;
  }

  async function resolveModel(client, template, requestedId) {
    if (template.model?.selectable) {
      if (!requestedId) throw new ConfigError('Seleccione el modelo de destino.');
      const models = await client.listModels();
      const m = models.find((x) => x.id === requestedId);
      if (!m) throw new ConfigError('El modelo seleccionado no existe o su usuario no tiene acceso.');
      return m;
    }
    if (template.model?.id) return { id: template.model.id, name: template.model.name || template.model.id };
    const models = await client.listModels();
    const wanted = norm(template.model?.name);
    const hits = models.filter((m) => norm(m.name) === wanted);
    if (!hits.length) {
      throw new ConfigError(`No se encontró el modelo "${template.model?.name}" en SAC o su usuario no tiene acceso a él.`);
    }
    if (hits.length > 1) {
      throw new ConfigError(`Hay ${hits.length} modelos llamados "${template.model?.name}". Configure "model.id" en la plantilla ${template.id}.`);
    }
    return hits[0];
  }

  async function membersOf(client, modelId, dim) {
    const key = `${modelId}|${dim}`;
    const hit = memberCache.get(key);
    if (hit && Date.now() - hit.at < MEMBER_TTL_MS) return hit.set;
    const set = await client.getMembers(modelId, dim);
    memberCache.set(key, { at: Date.now(), set });
    return set;
  }

  function templateView(t) {
    return {
      id: t.id, name: t.name, description: t.description || '',
      model: t.model?.selectable ? null : (t.model?.name || t.model?.id),
      selectableModel: Boolean(t.model?.selectable),
      sheet: t.sheet || null, layout: t.layout,
      importMethods: t.importMethods || ['Update'],
      cleanAndReplaceScope: t.cleanAndReplaceScope || null,
    };
  }

  function discardJob(u) {
    const entry = vault.get(u.vaultKey);
    if (entry && u.job?.jobId) loader.safeDelete(clientFor(entry), u.job.jobId);
  }

  // ------------------------------------------------------------ autenticación
  app.get('/auth/login', (req, res) => {
    const state = oauth.randomToken();
    const pkce = cfg.sac.usePkce ? oauth.pkcePair() : null;
    req.session.oauth = { state, verifier: pkce?.verifier || null, at: Date.now() };
    res.redirect(oauth.buildAuthorizeUrl(cfg, { state, codeChallenge: pkce?.challenge }));
  });

  app.get('/auth/callback', wrap(async (req, res) => {
    const pending = req.session.oauth;
    const { code, state, error, error_description: errorDescription } = req.query;
    if (error) return res.redirect(`/?error=${encodeURIComponent(errorDescription || error)}`);
    if (!pending || !state || state !== pending.state || Date.now() - pending.at > 10 * 60 * 1000) {
      return res.redirect(`/?error=${encodeURIComponent('La solicitud de inicio de sesión no es válida o expiró. Intente de nuevo.')}`);
    }
    let tokens;
    try {
      tokens = await oauth.exchangeCode(cfg, { code: String(code || ''), codeVerifier: pending.verifier });
    } catch (e) {
      logger.error('[oauth]', e.message);
      return res.redirect(`/?error=${encodeURIComponent('SAC no aceptó el inicio de sesión. Verifique la configuración del cliente OAuth.')}`);
    }
    const user = oauth.userFromTokens(tokens);
    // Nueva sesión tras autenticarse (evita fijación de sesión)
    await new Promise((resolve, reject) => req.session.regenerate((err) => (err ? reject(err) : resolve())));
    const vaultKey = oauth.randomToken();
    vault.set(vaultKey, { tokens, user, sac: { csrf: null, cookies: {} }, lastSeen: Date.now(), refreshing: null });
    req.session.vaultKey = vaultKey;
    audit({ event: 'LOGIN', user: user.id });
    return res.redirect('/');
  }));

  app.post('/auth/logout', requireAjax, (req, res) => {
    const entry = currentAuth(req);
    if (entry) {
      audit({ event: 'LOGOUT', user: entry.user.id });
      for (const [k, u] of uploads) {
        if (u.vaultKey === req.session.vaultKey && u.job?.state !== 'RUNNING') {
          if (u.job?.state === 'PREPARED') discardJob(u);
          uploads.delete(k);
        }
      }
      vault.delete(req.session.vaultKey);
    }
    req.session.destroy(() => {
      res.clearCookie('sacloader.sid');
      res.json({ ok: true });
    });
  });

  app.get('/api/me', (req, res) => {
    const entry = currentAuth(req);
    if (!entry) return res.json({ authenticated: false });
    return res.json({
      authenticated: true,
      user: entry.user,
      tenant: cfg.sac.tenantUrl,
      limits: { maxFileMb: cfg.maxFileMb, maxRows: cfg.maxRows, extensions: [...ALLOWED_EXT] },
      blockedVersions: cfg.blockedVersions,
      numberLocale: cfg.numberLocale,
    });
  });

  // ------------------------------------------------------------ catálogos
  app.get('/api/templates', requireAuth, (req, res) => {
    res.json({ templates: cfg.templates.map(templateView) });
  });

  app.get('/api/models', requireAuth, wrap(async (req, res) => {
    const models = await clientFor(req.auth).listModels();
    res.json({ models: models.sort((a, b) => a.name.localeCompare(b.name)) });
  }));

  app.get('/api/versions', requireAuth, wrap(async (req, res) => {
    const template = templates.get(String(req.query.template || ''));
    if (!template) return res.status(400).json({ error: 'Plantilla desconocida.' });
    const client = clientFor(req.auth);
    const model = await resolveModel(client, template, String(req.query.modelId || ''));
    const meta = buildMeta(await client.getMetadata(model.id), template);
    const set = await membersOf(client, model.id, meta.versionColumn).catch(() => null);
    const blocked = new Set(cfg.blockedVersions.map((v) => norm(v)));
    const versions = set ? [...set].sort().map((id) => ({ id, blocked: blocked.has(norm(id)) })) : null;
    return res.json({ model, versionColumn: meta.versionColumn, versions });
  }));

  // ------------------------------------------------------------ validación local
  const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: cfg.maxFileMb * 1024 * 1024, files: 1, fields: 10, fieldSize: 1024 },
    fileFilter: (req, file, cb) => {
      const ext = path.extname(file.originalname || '').toLowerCase();
      if (!ALLOWED_EXT.has(ext) && ext !== '.xls') {
        return cb(new ParseError('ARCH_FORMATO', `Extensión "${ext || 'sin extensión'}" no permitida. Use .xlsx, .xlsm, .csv o .txt.`));
      }
      return cb(null, true);
    },
  });

  app.post('/api/validate', requireAjax, requireAuth, upload.single('file'), wrap(async (req, res) => {
    const started = Date.now();
    const template = templates.get(String(req.body.template || ''));
    if (!template) return res.status(400).json({ error: 'Seleccione una plantilla válida.' });
    if (!req.file) return res.status(400).json({ error: 'Adjunte el archivo a cargar.' });

    const version = String(req.body.version || '').trim();
    const importMethod = String(req.body.importMethod || 'Update');
    const allowedMethods = template.importMethods || ['Update'];
    if (!allowedMethods.includes(importMethod)) {
      return res.status(400).json({ error: `El método "${importMethod}" no está habilitado para la plantilla ${template.id}.` });
    }

    const client = clientFor(req.auth);
    const model = await resolveModel(client, template, String(req.body.modelId || ''));
    const meta = buildMeta(await client.getMetadata(model.id), template);
    const grid = await parseFile({
      filename: req.file.originalname, buffer: req.file.buffer, preferredSheet: template.sheet, maxRows: cfg.maxRows,
    });

    // Miembros de cada dimensión (Data Export API) para validar códigos antes de enviar
    const members = new Map();
    const extraIssues = [];
    if (grid.info?.warning) {
      extraIssues.push({ severity: 'warning', code: 'ARCH_HOJA', title: 'Hoja leída', message: grid.info.warning });
    }
    if (cfg.validateMembers) {
      const dims = meta.keys.filter((k) => k !== meta.dateColumn && k !== meta.measure);
      const results = await Promise.all(dims.map((d) => membersOf(client, model.id, d)
        .then((set) => ({ d, set }))
        .catch((e) => ({ d, set: null, err: e }))));
      const skipped = [];
      for (const { d, set, err } of results) {
        if (set) members.set(d, set);
        else if (d !== meta.versionColumn) skipped.push(err ? `${d} (${err.status || 'error'})` : d);
      }
      if (skipped.length) {
        extraIssues.push({
          severity: 'warning', code: 'MIEMBROS_NO_VERIFICADOS', title: 'Miembros no verificados localmente',
          message: `No se pudo leer el maestro de: ${skipped.join(', ')}. Esos códigos los validará SAC en el siguiente paso.`,
        });
      }
    }

    const result = validate({
      grid, template, meta, members,
      options: {
        version, numberLocale: template.numberLocale || cfg.numberLocale,
        maxRows: cfg.maxRows, blockedVersions: cfg.blockedVersions,
      },
    });

    const importType = version.toLowerCase().startsWith('private.') ? 'privateFactData' : (template.importType || 'factData');
    const sha256 = crypto.createHash('sha256').update(req.file.buffer).digest('hex');
    const uploadId = oauth.randomToken(18);
    const issues = [...extraIssues, ...result.issues];
    result.summary.warnings += extraIssues.length;
    uploads.set(uploadId, {
      uploadId, vaultKey: req.vaultKey, createdAt: Date.now(),
      template, model, meta, importType, version, importMethod,
      fileName: req.file.originalname, sha256,
      ok: result.ok, records: result.ok ? result.records : [], issues, summary: result.summary, job: null,
    });

    audit({
      event: 'VALIDACION', user: req.auth.user.id, template: template.id, model: model.name, modelId: model.id,
      version, importMethod, file: req.file.originalname, sha256, ok: result.ok,
      records: result.records.length, errors: result.summary.errors, warnings: result.summary.warnings,
      ms: Date.now() - started,
    });

    return res.json({
      uploadId, ok: result.ok,
      model, importType, importMethod, version,
      columns: [...meta.keys, meta.measure],
      summary: { ...result.summary, fileName: req.file.originalname, sizeBytes: req.file.size, sha256 },
      issues,
      preview: result.records.slice(0, PREVIEW_ROWS),
    });
  }));

  // Reporte de hallazgos en CSV (separador ";" y BOM para abrir directo en Excel es-CO)
  app.get('/api/report/:uploadId', requireAuth, (req, res) => {
    const u = getUpload(req, res);
    if (!u) return;
    const q = (v) => {
      let s = v === null || v === undefined ? '' : String(v);
      if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`; // evita inyección de fórmulas en Excel
      return `"${s.replace(/"/g, '""')}"`;
    };
    const lines = [['Severidad', 'Código', 'Tipo', 'Fila', 'Columna', 'Valor', 'Detalle'].map(q).join(';')];
    for (const i of u.issues) {
      lines.push([i.severity === 'error' ? 'Error' : 'Advertencia', i.code, i.title, i.row, i.column, i.value, i.message].map(q).join(';'));
    }
    for (const r of u.job?.rejected || []) {
      const { _REJECTION_REASON: reason, ...row } = r;
      lines.push(['Error', 'RECHAZO_SAC', 'Fila rechazada por SAC', '', '', JSON.stringify(row), reason].map(q).join(';'));
    }
    const base = path.basename(u.fileName, path.extname(u.fileName)).replace(/[^\w.-]+/g, '_');
    res.set('Content-Type', 'text/csv; charset=utf-8');
    res.set('Content-Disposition', `attachment; filename="validacion_${base}.csv"`);
    res.send(`﻿${lines.join('\r\n')}\r\n`);
  });

  // ------------------------------------------------------------ SAC: preparar (validar en SAC) y ejecutar
  app.post('/api/sac/prepare', requireAjax, requireAuth, wrap(async (req, res) => {
    const u = getUpload(req, res);
    if (!u) return;
    if (!u.ok) return res.status(409).json({ error: 'Corrija los errores de la validación local antes de continuar.' });
    if (u.job && ['PREPARING', 'PREPARED', 'RUNNING', 'COMPLETED'].includes(u.job.state)) {
      return res.status(409).json({ error: 'Este archivo ya fue enviado a SAC.' });
    }
    u.job = { state: 'PREPARING', progress: null };
    const client = clientFor(req.auth);
    const jobSettings = loader.jobSettingsFor({ importMethod: u.importMethod, template: u.template, meta: u.meta });
    let r;
    try {
      r = await loader.prepare(client, {
        modelId: u.model.id, importType: u.importType, records: u.records, jobSettings,
        chunkSize: cfg.chunkSize, onProgress: (p) => { u.job.progress = p; },
      });
    } catch (e) {
      u.job = { state: 'ERROR', message: e.message };
      throw e;
    }
    audit({
      event: 'PREPARACION', user: req.auth.user.id, template: u.template.id, modelId: u.model.id, version: u.version,
      importMethod: u.importMethod, sha256: u.sha256, ok: r.ok, stage: r.stage || null, jobId: r.jobId || null,
      rows: r.totalRows ?? u.records.length, rejected: r.rejected?.length || 0,
    });
    if (!r.ok) {
      u.job = { state: 'REJECTED', stage: r.stage, message: r.message, rejected: r.rejected };
      return res.json({ ok: false, stage: r.stage, message: r.message, rejected: r.rejected.slice(0, 200), rejectedCount: r.rejected.length });
    }
    u.job = {
      state: 'PREPARED', jobId: r.jobId, totalRows: r.totalRows, preparedAt: Date.now(),
      cleanAndReplaceAffectedRows: r.cleanAndReplaceAffectedRows,
    };
    return res.json({
      ok: true, totalRows: r.totalRows, importMethod: u.importMethod,
      jobSettings, cleanAndReplaceAffectedRows: r.cleanAndReplaceAffectedRows,
    });
  }));

  app.post('/api/sac/run', requireAjax, requireAuth, (req, res) => {
    const u = getUpload(req, res);
    if (!u) return;
    if (u.job?.state !== 'PREPARED') return res.status(409).json({ error: 'Primero valide el archivo en SAC.' });
    if (u.importMethod === 'CleanAndReplace' && req.body?.confirmCleanAndReplace !== true) {
      return res.status(400).json({ error: 'Confirme que acepta borrar los datos existentes del alcance indicado.' });
    }
    const entry = req.auth;
    const { jobId } = u.job;
    u.job = { ...u.job, state: 'RUNNING', startedAt: Date.now(), status: null };
    loader.run(clientFor(entry), jobId, { onStatus: (s) => { u.job.status = s; } })
      .then((s) => {
        u.job = { ...u.job, state: s.jobStatus === 'COMPLETED' ? 'COMPLETED' : s.jobStatus, status: s, rejected: s.rejected || [], finishedAt: Date.now() };
      })
      .catch((e) => {
        u.job = { ...u.job, state: 'ERROR', message: e.message, finishedAt: Date.now() };
      })
      .finally(() => {
        audit({
          event: 'CARGA', user: entry.user.id, template: u.template.id, modelId: u.model.id, version: u.version,
          importMethod: u.importMethod, sha256: u.sha256, jobId, state: u.job.state,
          rows: u.job.status?.totalNumberRowsInJob ?? u.job.totalRows, failed: u.job.status?.failedNumberRows ?? null,
          ms: u.job.finishedAt - u.job.startedAt,
        });
      });
    res.status(202).json({ ok: true, state: 'RUNNING' });
  });

  app.get('/api/sac/status/:uploadId', requireAuth, (req, res) => {
    const u = getUpload(req, res);
    if (!u) return;
    const j = u.job || { state: 'NONE' };
    res.json({
      state: j.state, progress: j.progress || null, status: j.status || null, message: j.message || null,
      totalRows: j.totalRows ?? null, rejected: (j.rejected || []).slice(0, 200), rejectedCount: (j.rejected || []).length,
    });
  });

  app.post('/api/sac/cancel', requireAjax, requireAuth, wrap(async (req, res) => {
    const u = getUpload(req, res);
    if (!u) return;
    if (u.job?.state !== 'PREPARED') return res.status(409).json({ error: 'No hay una carga pendiente por cancelar.' });
    await loader.safeDelete(clientFor(req.auth), u.job.jobId);
    audit({ event: 'CANCELACION', user: req.auth.user.id, jobId: u.job.jobId, sha256: u.sha256 });
    u.job = { state: 'CANCELLED' };
    res.json({ ok: true });
  }));

  // ------------------------------------------------------------ errores
  app.use('/api', (req, res) => res.status(404).json({ error: 'Ruta no encontrada.' }));

  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    if (err instanceof multer.MulterError) {
      const msg = err.code === 'LIMIT_FILE_SIZE' ? `El archivo supera el máximo de ${cfg.maxFileMb} MB.` : `Archivo no aceptado (${err.code}).`;
      return res.status(413).json({ error: msg });
    }
    if (err instanceof ParseError) return res.status(422).json({ error: err.message, code: err.code });
    if (err instanceof ConfigError) return res.status(422).json({ error: err.message });
    if (err instanceof SacError) {
      if (err.status === 401) vault.delete(req.session?.vaultKey);
      return res.status(err.status === 401 ? 401 : 502).json({ error: err.message, sacStatus: err.status });
    }
    if (err instanceof TypeError && /fetch failed/i.test(err.message)) {
      return res.status(502).json({ error: 'No fue posible conectarse con SAP Analytics Cloud. Verifique la red o la URL del tenant.' });
    }
    if (err?.name === 'TimeoutError') return res.status(504).json({ error: 'SAP Analytics Cloud no respondió a tiempo. Intente de nuevo.' });
    if (err?.type === 'entity.parse.failed') return res.status(400).json({ error: 'Solicitud inválida.' });
    logger.error('[error]', err);
    return res.status(500).json({ error: 'Error interno. Revise el log del servidor.' });
  });

  app.locals.stop = () => clearInterval(sweeper);
  return app;
}

module.exports = { createApp };
