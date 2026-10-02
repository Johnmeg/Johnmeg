'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const tester = require('./runner');
const { CaseError } = require('./engine');
const { buildMeta } = require('../meta');
const { norm } = require('../validator');

// Rutas de la aplicación "Probador de data actions" (APP_MODE=probador).

const RUN_TTL_MS = 2 * 60 * 60 * 1000;
const LIST_TTL_MS = 10 * 60 * 1000;

function register(app, { cfg, brand, audit, requireAuth, requireAjax, wrap, clientFor }) {
  const testRuns = new Map(); // runId -> { vaultKey, state, reports, current, ... }
  const lists = new Map();    // caché de versiones y miembros por usuario y modelo
  const catalogFile = path.join(brand.dir, 'pruebas.json');
  const loadCatalog = () => {
    try { return JSON.parse(fs.readFileSync(catalogFile, 'utf8')); } catch { return { casos: [] }; }
  };

  const sweeper = setInterval(() => {
    const now = Date.now();
    for (const [k, r] of testRuns) if (r.state === 'DONE' && now - r.createdAt > RUN_TTL_MS) testRuns.delete(k);
    for (const [k, l] of lists) if (now - l.at > LIST_TTL_MS) lists.delete(k);
  }, 60 * 1000);
  sweeper.unref();

  async function cached(key, fn) {
    const hit = lists.get(key);
    if (hit && Date.now() - hit.at < LIST_TTL_MS) return hit.value;
    const value = await fn();
    lists.set(key, { at: Date.now(), value });
    return value;
  }
  const modelId = (req) => {
    const id = String(req.query.modelo || '').trim();
    if (!/^[A-Za-z0-9_.-]{1,80}$/.test(id)) throw new CaseError('Indique el ID del modelo.');
    return id;
  };

  app.get('/api/tests/catalog', requireAuth, (req, res) => {
    const cat = loadCatalog();
    res.json({ casos: Array.isArray(cat.casos) ? cat.casos : [], plantilla: cat.plantilla || null, blockedVersions: cfg.blockedVersions });
  });

  // Estructura del modelo: dimensiones (para los parámetros) y versiones disponibles
  app.get('/api/tests/model', requireAuth, wrap(async (req, res) => {
    const id = modelId(req);
    const client = clientFor(req.auth);
    const out = await cached(`${req.vaultKey}|model|${id}`, async () => {
      const meta = buildMeta(await client.getMetadata(id), {});
      const rows = await client.getMasterRows(id, meta.versionColumn).catch(() => null);
      const blocked = new Set(cfg.blockedVersions.map(norm));
      const versions = rows
        ? rows.map((r) => String(r.ID ?? r.id ?? '')).filter(Boolean).sort().map((v) => ({ id: v, blocked: blocked.has(norm(v)) || !/^public\./.test(v) }))
        : null;
      return {
        dimensions: meta.keys.filter((k) => k !== meta.versionColumn && k !== meta.dateColumn),
        versionColumn: meta.versionColumn, dateColumn: meta.dateColumn, measure: meta.measure, versions,
      };
    });
    res.json(out);
  }));

  // Miembros de una dimensión (para elegir los valores de los parámetros)
  app.get('/api/tests/members', requireAuth, wrap(async (req, res) => {
    const id = modelId(req);
    const dim = String(req.query.dim || '').trim();
    if (!/^[A-Za-z0-9_]{1,80}$/.test(dim)) throw new CaseError('Indique la dimensión.');
    const client = clientFor(req.auth);
    const members = await cached(`${req.vaultKey}|members|${id}|${dim}`, async () => {
      const rows = await client.getMasterRows(id, dim);
      if (!rows) return null;
      return rows.map((r) => ({
        id: String(r.ID ?? r.id ?? ''),
        description: String(r.Description ?? r.DESCRIPTION ?? r.description ?? ''),
      })).filter((m) => m.id).slice(0, 20000);
    });
    if (!members) return res.status(404).json({ error: `SAC no expone el maestro de la dimensión ${dim}.` });
    return res.json({ members });
  }));

  function caseFromBody(body) {
    const c = body?.case;
    if (!c || typeof c !== 'object' || Array.isArray(c)) throw new CaseError('Envíe la definición del caso de prueba (JSON).');
    if (JSON.stringify(c).length > 200000) throw new CaseError('La definición del caso es demasiado grande.');
    return c;
  }
  const seedOf = (x) => (Number.isInteger(Number(x)) && Number(x) > 0 ? Number(x) : Math.floor(Math.random() * 1e9) + 1);

  app.post('/api/tests/preview', requireAjax, requireAuth, wrap(async (req, res) => {
    const report = await tester.runCase(clientFor(req.auth), caseFromBody(req.body), {
      seed: seedOf(req.body.seed), blockedVersions: cfg.blockedVersions, preview: true,
    });
    res.json(report);
  }));

  app.post('/api/tests/run', requireAjax, requireAuth, wrap(async (req, res) => {
    const raw = caseFromBody(req.body);
    if (req.body.confirmVersion !== true) {
      return res.status(400).json({ error: 'Confirme que la versión es de pruebas: la prueba borra los datos de su alcance antes de cargar.' });
    }
    for (const r of testRuns.values()) {
      if (r.vaultKey === req.vaultKey && r.state === 'RUNNING') return res.status(409).json({ error: 'Ya tiene una prueba en curso; espere a que termine.' });
    }
    const reps = Math.min(Math.max(Number.parseInt(req.body.repeticiones, 10) || 1, 1), 20);
    const seed = seedOf(req.body.seed);
    const runId = crypto.randomBytes(12).toString('hex');
    const run = { vaultKey: req.vaultKey, state: 'RUNNING', reps, seed, reports: [], current: null, createdAt: Date.now() };
    testRuns.set(runId, run);
    const entry = req.auth;
    (async () => {
      for (let i = 0; i < reps; i++) {
        const report = await tester.runCase(clientFor(entry), raw, {
          seed: seed + i, blockedVersions: cfg.blockedVersions, chunkSize: cfg.chunkSize,
          onUpdate: (r) => { run.current = r; },
        });
        run.reports.push(report);
        run.current = null;
        audit({
          event: 'PRUEBA_DATA_ACTION', user: entry.user.id, caso: report.case?.id || raw.id, modelId: report.case?.modelo,
          multiAction: report.case?.multiAction, version: report.case?.version, seed: report.seed, state: report.state,
          cells: report.summary?.cells ?? null, failed: report.summary?.failed ?? null, ms: report.ms,
        });
        if (report.state !== 'PASSED' && req.body.detenerEnFallo !== false) break;
      }
      run.state = 'DONE';
    })().catch((e) => { run.state = 'DONE'; run.error = e.message; });
    res.status(202).json({ runId, seed, repeticiones: reps });
  }));

  function getRun(req, res) {
    const run = testRuns.get(String(req.params.runId || ''));
    if (!run || run.vaultKey !== req.vaultKey) { res.status(404).json({ error: 'La prueba no existe o expiró.' }); return null; }
    return run;
  }

  app.get('/api/tests/status/:runId', requireAuth, (req, res) => {
    const run = getRun(req, res);
    if (!run) return;
    const slim = (r) => r && ({ ...r, groups: r.groups.map((g) => ({ ...g, cells: g.cells.slice(0, 2000) })) });
    res.json({ state: run.state, reps: run.reps, seed: run.seed, error: run.error || null, current: slim(run.current), reports: run.reports.map(slim) });
  });

  app.get('/api/tests/report/:runId', requireAuth, (req, res) => {
    const run = getRun(req, res);
    if (!run) return;
    res.set('Content-Disposition', `attachment; filename="prueba-data-action-${run.seed}.csv"`);
    res.type('text/csv; charset=utf-8').send(tester.reportCsv(run.reports));
  });

  return { stop: () => clearInterval(sweeper) };
}

module.exports = { register };
