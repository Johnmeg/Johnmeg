'use strict';

const engine = require('./engine');
const loader = require('../loader');
const { buildMeta } = require('../meta');
const { norm } = require('../validator');

// Ejecuta un caso de prueba de un data action contra SAC:
//   1. valida la definición        5. ejecuta la multi action (API pública) y espera
//   2. lee la estructura del modelo 6. lee los resultados (Data Export API, FactData)
//   3. resuelve los miembros        7. compara contra lo esperado
//   4. limpia el alcance de la versión de pruebas y carga los datos aleatorios
// Con { preview: true } se detiene después de generar los datos (no escribe en SAC).

const STEPS = [
  ['definicion', 'Validar la definición'],
  ['modelo', 'Leer la estructura del modelo'],
  ['miembros', 'Resolver miembros'],
  ['datos', 'Generar datos aleatorios y valores esperados'],
  ['carga', 'Limpiar la versión de pruebas y cargar las entradas'],
  ['ejecucion', 'Ejecutar la multi action'],
  ['lectura', 'Leer los resultados en SAC'],
  ['comparacion', 'Comparar esperado vs. real'],
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function newReport(seed) {
  return {
    seed, ok: false, state: 'RUNNING', startedAt: new Date().toISOString(), ms: 0,
    steps: STEPS.map(([id, label]) => ({ id, label, status: 'pending', ms: null, detail: '' })),
    summary: null, groups: [], inputs: null, multiAction: null, error: null,
  };
}

async function runCase(client, rawCase, { seed = 1, blockedVersions = [], chunkSize = 10000, preview = false, pollMs = 2000, onUpdate = () => {} } = {}) {
  const report = newReport(seed);
  const t0 = Date.now();
  let current = null;
  const step = async (id, fn) => {
    const s = report.steps.find((x) => x.id === id);
    current = s; s.status = 'running'; onUpdate(report);
    const st = Date.now();
    const detail = await fn(s);
    s.ms = Date.now() - st; s.status = 'ok'; if (detail) s.detail = detail;
    onUpdate(report);
  };

  try {
    let c; let meta; let resolved; let inputs; let expected;
    await step('definicion', () => {
      c = engine.normalizeCase(rawCase);
      report.case = { id: c.id, nombre: c.nombre, modelo: c.modelo, multiAction: c.multiAction, version: c.version, periodos: c.periodos };
      const blocked = new Set(blockedVersions.map(norm));
      if (blocked.has(norm(c.version))) throw new engine.CaseError(`La versión ${c.version} está bloqueada; use una versión de pruebas.`);
      return `${c.entradas.length} entrada(s), ${c.esperado.length} resultado(s), ${c.periodos.length} periodo(s)`;
    });

    await step('modelo', async () => {
      meta = buildMeta(await client.getMetadata(c.modelo), { measure: c.medida || undefined });
      const dims = new Set(meta.keys);
      for (const g of [...c.entradas, ...c.esperado]) {
        for (const d of Object.keys({ ...c.comun, ...g.fijo, ...g.variar })) {
          if (!dims.has(d)) throw new engine.CaseError(`${g.nombre}: la dimensión "${d}" no existe en el modelo (dimensiones: ${meta.keys.join(', ')}).`);
          if (d === meta.versionColumn || d === meta.dateColumn) throw new engine.CaseError(`${g.nombre}: no indique ${d}; se toma de "version" y "periodos".`);
        }
      }
      for (const p of c.parametros.filter((x) => x.tipo === 'miembro')) {
        if (!dims.has(p.dimension)) throw new engine.CaseError(`Parámetro ${p.etiqueta}: la dimensión "${p.dimension}" no existe en el modelo.`);
      }
      return `Dimensiones: ${meta.keys.filter((k) => k !== meta.versionColumn && k !== meta.dateColumn).join(', ')} · medida ${meta.measure}`;
    });

    await step('miembros', async () => {
      const masters = new Map();
      const master = async (dim) => {
        if (!masters.has(dim)) masters.set(dim, await client.getMasterRows(c.modelo, dim));
        return masters.get(dim);
      };
      resolved = await engine.resolveMembers(c, {
        seed,
        pickMembers: async (dim, filtro = {}) => {
          const rows = await master(dim);
          if (!rows) throw new engine.CaseError(`SAC no expone el maestro de ${dim}; indique los miembros en una lista.`);
          return rows.filter((r) => Object.entries(filtro).every(([p, v]) => String(r[p] ?? r[`${dim}.${p}`] ?? '') === String(v)))
            .map((r) => String(r.ID ?? r.id ?? r[`${dim}___ID`]));
        },
      });
      // Verifica que existan todos los miembros indicados (fijos y en listas)
      const used = new Map();
      const add = (d, m) => { if (m !== '#') { if (!used.has(d)) used.set(d, new Set()); used.get(d).add(m); } };
      for (const p of c.parametros.filter((x) => x.tipo === 'miembro')) p.valor.forEach((m) => add(p.dimension, m));
      for (const g of [...c.entradas, ...c.esperado]) {
        for (const [d, m] of Object.entries({ ...c.comun, ...g.fijo })) add(d, m);
        for (const [d, list] of Object.entries(resolved.get(g.nombre))) list.forEach((m) => add(d, m));
      }
      const missing = [];
      for (const [d, set] of used) {
        const rows = await master(d);
        if (!rows) continue;
        const ids = new Set(rows.map((r) => String(r.ID ?? r.id ?? r[`${d}___ID`])));
        for (const m of set) if (!ids.has(m)) missing.push(`${d}=${m}`);
      }
      if (missing.length) throw new engine.CaseError(`Estos miembros no existen en el modelo: ${missing.slice(0, 15).join(', ')}${missing.length > 15 ? '…' : ''}`);
      return [...used].map(([d, s]) => `${d}: ${s.size}`).join(' · ');
    });

    await step('datos', () => {
      inputs = engine.generateInputs(c, resolved, seed);
      expected = engine.computeExpected(c, resolved, inputs);
      report.inputs = { count: inputs.length, sample: inputs.slice(0, 300) };
      report.expectedCount = expected.length;
      const errors = expected.filter((e) => e.error);
      if (errors.length === expected.length) throw new engine.CaseError(`Todas las fórmulas fallaron: ${errors[0].error}`);
      return `${inputs.length} celda(s) de entrada · ${expected.length} celda(s) esperada(s)`;
    });

    if (preview) {
      report.groups = c.esperado.map((g) => ({
        nombre: g.nombre, formula: g.formula,
        cells: expected.filter((e) => e.nombre === g.nombre).slice(0, 300),
      }));
      report.state = 'PREVIEW';
      report.ok = true;
      for (const s of report.steps) if (s.status === 'pending') s.status = 'skipped';
      return finish();
    }

    await step('carga', async () => {
      const records = engine.toImportRecords(inputs, meta, c.version);
      const scope = c.limpieza && c.limpieza.length ? c.limpieza : [meta.versionColumn, meta.dateColumn];
      const jobSettings = { importMethod: 'CleanAndReplace', executeWithFailedRows: false, ignoreAdditionalColumns: false, dimensionScope: scope };
      const p = await loader.prepare(client, { modelId: c.modelo, importType: 'factData', records, jobSettings, chunkSize });
      if (!p.ok) {
        const first = p.rejected?.[0];
        throw new engine.CaseError(`${p.message}${first ? ` Primer rechazo: ${first._REJECTION_REASON || JSON.stringify(first)}` : ''}`);
      }
      const r = await loader.run(client, p.jobId, { pollMs: 1000, timeoutMs: 10 * 60 * 1000 });
      if (r.jobStatus !== 'COMPLETED') throw new engine.CaseError(`La carga de las entradas terminó en estado ${r.jobStatus}.`);
      const deleted = p.cleanAndReplaceAffectedRows?.[0]?.numberOfRowsToBeDeleted;
      return `${records.length} registro(s) cargados · alcance limpiado: ${scope.join(' + ')}${deleted !== undefined ? ` (${deleted} borrados)` : ''}`;
    });

    await step('ejecucion', async (s) => {
      const params = engine.parameterValues(c);
      report.parameterValues = params;
      const executionId = await client.runMultiAction(c.multiAction, params);
      report.multiAction = { executionId, status: 'running', messages: [] };
      const limit = Date.now() + c.esperaMaxSeg * 1000;
      let st;
      for (;;) {
        await sleep(pollMs);
        st = await client.multiActionStatus(c.multiAction, executionId);
        const status = String(st?.status || '').toLowerCase();
        report.multiAction = { executionId, status, messages: st?.executionResult?.messages || [] };
        s.detail = `Estado: ${status || '¿?'} (${Math.round((Date.now() + c.esperaMaxSeg * 1000 - limit) / 1000)} s)`;
        onUpdate(report);
        if (status && status !== 'running') break;
        if (Date.now() > limit) throw new engine.CaseError(`La multi action sigue en ejecución después de ${c.esperaMaxSeg} s.`);
      }
      if (report.multiAction.status === 'failed') {
        const msg = report.multiAction.messages.map((m) => m.message).filter(Boolean).join(' | ');
        throw new engine.CaseError(`La multi action falló en SAC${msg ? `: ${msg}` : '.'}`);
      }
      return `Ejecución ${executionId}: ${report.multiAction.status}`;
    });

    await step('lectura', async () => {
      let total = 0;
      report.rawGroups = [];
      for (const g of c.esperado) {
        const rows = await client.getFactData(c.modelo, engine.factFilter(c, g, resolved, meta));
        total += rows.length;
        report.rawGroups.push({ g, rows });
      }
      return `${total} fila(s) leídas`;
    });

    await step('comparacion', () => {
      report.groups = report.rawGroups.map(({ g, rows }) => {
        const cmp = engine.compareGroup(expected.filter((e) => e.nombre === g.nombre), rows, meta);
        return { nombre: g.nombre, formula: g.formula, cells: [...cmp], extra: cmp.extra };
      });
      delete report.rawGroups;
      report.summary = engine.summarize(report.groups);
      report.ok = report.summary.ok;
      return `${report.summary.passed}/${report.summary.cells} celda(s) correctas`;
    });
    report.state = report.ok ? 'PASSED' : 'FAILED';
  } catch (e) {
    if (current && current.status === 'running') { current.status = 'error'; current.detail = e.message; }
    report.error = e.message;
    report.state = 'ERROR';
    report.ok = false;
    delete report.rawGroups;
  }
  return finish();

  function finish() {
    report.ms = Date.now() - t0;
    for (const s of report.steps) if (s.status === 'pending') s.status = 'skipped';
    onUpdate(report);
    return report;
  }
}

// CSV (separador ;) con todas las celdas comparadas
function reportCsv(reports) {
  const dims = new Set();
  for (const r of reports) for (const g of r.groups) for (const x of g.cells) Object.keys(x.coords).forEach((d) => dims.add(d));
  const cols = [...dims];
  const esc = (v) => {
    const s = v === null || v === undefined ? '' : String(v);
    return /[;"\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const num = (n) => (typeof n === 'number' ? String(Math.round(n * 1e6) / 1e6).replace('.', ',') : '');
  const lines = [['Caso', 'Semilla', 'Resultado', 'Periodo', ...cols, 'Esperado', 'Real', 'Diferencia', 'Estado', 'Detalle'].join(';')];
  for (const r of reports) {
    for (const g of r.groups) {
      for (const x of g.cells) {
        lines.push([r.case?.id, r.seed, g.nombre, x.date, ...cols.map((d) => x.coords[d] ?? ''),
          num(x.expected), num(x.real), num(x.diff), x.ok === undefined ? '' : (x.ok ? 'OK' : 'ERROR'), x.error || ''].map(esc).join(';'));
      }
    }
  }
  return `﻿${lines.join('\r\n')}\r\n`;
}

module.exports = { runCase, reportCsv, STEPS };
