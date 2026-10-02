'use strict';

const vm = require('vm');

// Motor del probador de data actions (sin acceso a SAC):
//   - valida y normaliza la definición de un caso de prueba,
//   - genera datos de entrada aleatorios reproducibles (semilla),
//   - calcula los valores esperados con la fórmula de cada resultado,
//   - compara lo esperado contra lo que SAC devolvió.
//
// Definición de un caso (JSON):
// {
//   "id": "PXQ", "nombre": "...", "modelo": "<ID del modelo>",
//   "multiAction": "<paquete>:<ID>",            // multi action que ejecuta el data action
//   "version": "public.PRUEBAS",                 // versión de pruebas (se borra su alcance)
//   "periodos": ["202601", "202602"] | { "desde": "202601", "hasta": "202603" },
//   "comun": { "Sociedades": "FN_MOTOS", ... },  // miembros fijos de todas las celdas
//   "parametros": [                              // parámetros de la multi action / data action
//     { "id": "TargetVersion", "tipo": "version" },
//     { "id": "Periodo", "tipo": "periodos" },
//     { "id": "Sociedad", "tipo": "miembro", "dimension": "Sociedades", "valor": ["FN_MOTOS"] },
//     { "id": "Factor", "tipo": "numero", "valor": 1.05 } ],
//   "entradas": [ { "nombre": "PRECIO", "fijo": {...}, "variar": {...}, "min": 1, "max": 9, "decimales": 2 } ],
//   "esperado": [ { "nombre": "INGRESO", "fijo": {...}, "variar": {...}, "formula": "v('PRECIO') * v('UNIDADES')" } ]
// }
// "variar" admite por dimensión: una lista de miembros, { "aleatorio": n, "filtro": { "PROPIEDAD": "valor" } }
// (n miembros tomados al azar del maestro del modelo), "@ENTRADA" (los mismos miembros de esa entrada)
// o "$PARAMETRO" (los miembros elegidos en ese parámetro). En "comun" y "fijo" también se admite "$PARAMETRO".

class CaseError extends Error {}

const ID_RE = /^[A-Za-z0-9_.-]{1,60}$/;
const MA_RE = /^[^\s:]+:[A-Za-z0-9_.-]+$/;
const PERIOD_RE = /^\d{6}$/;
const MAX_CELLS = 20000;

const isObj = (x) => x && typeof x === 'object' && !Array.isArray(x);

// Generador pseudoaleatorio reproducible (mulberry32)
function rng(seed) {
  let a = (Number(seed) >>> 0) || 1;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function expandPeriods(p) {
  if (Array.isArray(p)) {
    const out = p.map(String);
    for (const x of out) if (!PERIOD_RE.test(x)) throw new CaseError(`Periodo inválido "${x}" (use AAAAMM, p. ej. 202601).`);
    return [...new Set(out)];
  }
  if (isObj(p) && PERIOD_RE.test(String(p.desde)) && PERIOD_RE.test(String(p.hasta))) {
    const out = [];
    let y = Number(String(p.desde).slice(0, 4)); let m = Number(String(p.desde).slice(4));
    const end = String(p.hasta);
    if (m < 1 || m > 12 || Number(end.slice(4)) < 1 || Number(end.slice(4)) > 12) throw new CaseError('Mes inválido en "periodos".');
    while (`${y}${String(m).padStart(2, '0')}` <= end) {
      out.push(`${y}${String(m).padStart(2, '0')}`);
      if (out.length > 120) throw new CaseError('"periodos" abarca más de 120 meses.');
      m += 1; if (m > 12) { m = 1; y += 1; }
    }
    if (!out.length) throw new CaseError('"periodos": "desde" es posterior a "hasta".');
    return out;
  }
  throw new CaseError('"periodos" debe ser una lista ["202601", ...] o { "desde": "202601", "hasta": "202612" }.');
}

function checkMembers(obj, where) {
  if (obj === undefined) return {};
  if (!isObj(obj)) throw new CaseError(`${where} debe ser un objeto { "Dimensión": "miembro" }.`);
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v !== 'string' || !v.trim()) throw new CaseError(`${where}.${k} debe ser un código de miembro (texto).`);
  }
  return { ...obj };
}

function checkVariar(obj, where) {
  if (obj === undefined) return {};
  if (!isObj(obj)) throw new CaseError(`${where} debe ser un objeto { "Dimensión": [miembros] }.`);
  const out = {};
  for (const [dim, spec] of Object.entries(obj)) {
    if (Array.isArray(spec)) {
      if (!spec.length || spec.some((m) => typeof m !== 'string' || !m.trim())) throw new CaseError(`${where}.${dim} debe ser una lista de códigos de miembros.`);
      out[dim] = [...new Set(spec)];
    } else if (typeof spec === 'string' && spec.startsWith('@')) {
      out[dim] = spec;
    } else if (isObj(spec) && Number.isInteger(spec.aleatorio) && spec.aleatorio > 0 && spec.aleatorio <= 200) {
      out[dim] = { aleatorio: spec.aleatorio, filtro: spec.filtro ? checkMembers(spec.filtro, `${where}.${dim}.filtro`) : {} };
    } else {
      throw new CaseError(`${where}.${dim}: use una lista de miembros, { "aleatorio": n } o "@NOMBRE_DE_ENTRADA".`);
    }
  }
  return out;
}

function compileFormula(src, where) {
  if (typeof src !== 'string' || !src.trim()) throw new CaseError(`${where}.formula es obligatoria.`);
  if (src.length > 2000) throw new CaseError(`${where}.formula es demasiado larga.`);
  try {
    return new vm.Script(`(${src})`, { filename: where });
  } catch (e) {
    throw new CaseError(`${where}.formula no es válida: ${e.message}`);
  }
}

const PARAM_TYPES = new Set(['version', 'periodos', 'miembro', 'numero']);

// Parámetros de la multi action. Formato declarativo (se eligen en pantalla) o el
// formato de la API de SAP { "parameterId", "value" } (se envía tal cual).
function normalizeParams(list) {
  if (list === undefined) return [];
  if (!Array.isArray(list)) throw new CaseError('"parametros" debe ser una lista.');
  const ids = new Set();
  return list.map((p, i) => {
    const where = `parametros[${i}]`;
    if (!isObj(p)) throw new CaseError(`${where} debe ser un objeto.`);
    if (p.parameterId !== undefined) {
      if (typeof p.parameterId !== 'string' || !p.parameterId) throw new CaseError(`${where}.parameterId no es válido.`);
      ids.add(p.parameterId);
      return { id: p.parameterId, tipo: 'api', raw: p };
    }
    const id = String(p.id || '').trim();
    if (!/^[A-Za-z_][A-Za-z0-9_.-]{0,60}$/.test(id)) throw new CaseError(`${where}.id es obligatorio (ID del parámetro en la multi action).`);
    if (ids.has(id)) throw new CaseError(`El parámetro "${id}" está repetido.`);
    ids.add(id);
    const tipo = String(p.tipo || '');
    if (!PARAM_TYPES.has(tipo)) throw new CaseError(`${where}.tipo debe ser version, periodos, miembro o numero.`);
    const out = { id, tipo, etiqueta: String(p.etiqueta || id), jerarquia: p.jerarquia ? String(p.jerarquia) : null };
    if (tipo === 'miembro') {
      out.dimension = String(p.dimension || '').trim();
      if (!out.dimension) throw new CaseError(`${where}: indique la "dimension" del parámetro ${id}.`);
      out.multiple = p.multiple !== false;
      const valor = p.valor === undefined || p.valor === null ? [] : (Array.isArray(p.valor) ? p.valor : [p.valor]);
      if (valor.some((m) => typeof m !== 'string' || !m.trim())) throw new CaseError(`${where}.valor debe ser una lista de códigos de miembros.`);
      if (!valor.length) throw new CaseError(`Seleccione al menos un miembro para el parámetro "${out.etiqueta}".`);
      if (!out.multiple && valor.length > 1) throw new CaseError(`El parámetro "${out.etiqueta}" admite un solo miembro.`);
      out.valor = [...new Set(valor)];
    }
    if (tipo === 'numero') {
      out.valor = Number(p.valor);
      if (p.valor === '' || p.valor === null || p.valor === undefined || !Number.isFinite(out.valor)) {
        throw new CaseError(`Indique un número para el parámetro "${out.etiqueta}".`);
      }
    }
    return out;
  });
}

// Reemplaza "$PARAMETRO" por los miembros elegidos en ese parámetro.
function applyParamRefs(obj, params, where, { single }) {
  if (!isObj(obj)) return obj;
  const out = {};
  for (const [dim, v] of Object.entries(obj)) {
    if (typeof v === 'string' && v.startsWith('$')) {
      const p = params.find((x) => x.id === v.slice(1));
      if (!p || p.tipo !== 'miembro') throw new CaseError(`${where}.${dim}: "${v}" no es un parámetro de tipo miembro.`);
      if (p.dimension !== dim) throw new CaseError(`${where}.${dim}: el parámetro ${p.id} es de la dimensión ${p.dimension}.`);
      if (single && p.valor.length !== 1) throw new CaseError(`${where}.${dim}: el parámetro ${p.id} tiene ${p.valor.length} miembros; aquí se necesita uno solo (use "variar").`);
      out[dim] = single ? p.valor[0] : [...p.valor];
    } else out[dim] = v;
  }
  return out;
}

// Valida la definición y devuelve una copia normalizada.
function normalizeCase(raw) {
  if (!isObj(raw)) throw new CaseError('El caso de prueba debe ser un objeto JSON.');
  const c = {
    id: String(raw.id || '').trim(),
    nombre: String(raw.nombre || raw.id || '').trim(),
    descripcion: String(raw.descripcion || ''),
    modelo: typeof raw.modelo === 'string' ? raw.modelo.trim() : String(raw.modelo?.id || '').trim(),
    multiAction: String(raw.multiAction || '').trim(),
    version: String(raw.version || '').trim(),
    medida: raw.medida ? String(raw.medida) : null,
    esperaMaxSeg: Number(raw.esperaMaxSeg) > 0 ? Math.min(Number(raw.esperaMaxSeg), 3600) : 600,
    tolerancia: raw.tolerancia === undefined ? 0.01 : Number(raw.tolerancia),
  };
  if (!ID_RE.test(c.id)) throw new CaseError('"id" es obligatorio (letras, números, _ . -).');
  if (!c.modelo) throw new CaseError('"modelo" es obligatorio (ID del modelo, p. ej. Couh7ojg5e54rh2d4udijq6o83k).');
  if (!MA_RE.test(c.multiAction)) throw new CaseError('"multiAction" debe tener el formato <paquete>:<ID>, p. ej. t.TEST:CEEFOKMRUKJBY5BN47F1NS2L8G.');
  if (!/^public\.\S+$/.test(c.version)) throw new CaseError('"version" debe ser una versión pública de pruebas, p. ej. public.PRUEBAS.');
  if (!Number.isFinite(c.tolerancia) || c.tolerancia < 0) throw new CaseError('"tolerancia" debe ser un número mayor o igual a 0.');
  c.periodos = expandPeriods(raw.periodos);
  c.parametros = normalizeParams(raw.parametros);
  c.comun = checkMembers(applyParamRefs(raw.comun, c.parametros, 'comun', { single: true }), 'comun');
  c.limpieza = Array.isArray(raw.limpieza?.alcance) ? raw.limpieza.alcance.map(String) : null;

  const names = new Set();
  const group = (g, i, kind) => {
    const where = `${kind}[${i}]`;
    if (!isObj(g)) throw new CaseError(`${where} debe ser un objeto.`);
    const nombre = String(g.nombre || '').trim();
    if (!/^[A-Za-z_][A-Za-z0-9_]{0,40}$/.test(nombre)) throw new CaseError(`${where}.nombre es obligatorio (letras, números y _; sin espacios).`);
    if (names.has(nombre)) throw new CaseError(`El nombre "${nombre}" está repetido.`);
    names.add(nombre);
    return {
      nombre,
      fijo: checkMembers(applyParamRefs(g.fijo, c.parametros, `${where}.fijo`, { single: true }), `${where}.fijo`),
      variar: checkVariar(applyParamRefs(g.variar, c.parametros, `${where}.variar`, { single: false }), `${where}.variar`),
    };
  };
  if (!Array.isArray(raw.entradas) || !raw.entradas.length) throw new CaseError('"entradas" debe tener al menos un grupo de datos de entrada.');
  c.entradas = raw.entradas.map((g, i) => {
    const out = group(g, i, 'entradas');
    out.min = Number(g.min ?? 1);
    out.max = Number(g.max ?? 1000);
    out.decimales = Number.isInteger(g.decimales) ? Math.min(Math.max(g.decimales, 0), 7) : 2;
    if (!Number.isFinite(out.min) || !Number.isFinite(out.max) || out.min > out.max) throw new CaseError(`entradas[${i}]: "min" y "max" deben ser números con min ≤ max.`);
    return out;
  });
  if (!Array.isArray(raw.esperado) || !raw.esperado.length) throw new CaseError('"esperado" debe tener al menos un resultado a verificar.');
  c.esperado = raw.esperado.map((g, i) => {
    const out = group(g, i, 'esperado');
    out.formula = String(g.formula || '');
    out.script = compileFormula(out.formula, `esperado[${i}]`);
    out.tolerancia = g.tolerancia === undefined ? c.tolerancia : Number(g.tolerancia);
    return out;
  });
  const inputNames = new Set(c.entradas.map((e) => e.nombre));
  for (const g of [...c.entradas, ...c.esperado]) {
    for (const [dim, spec] of Object.entries(g.variar)) {
      if (typeof spec === 'string' && !inputNames.has(spec.slice(1))) throw new CaseError(`${g.nombre}.variar.${dim}: "${spec}" no es una entrada.`);
      if (Object.hasOwn(g.fijo, dim) || Object.hasOwn(c.comun, dim)) throw new CaseError(`${g.nombre}: la dimensión ${dim} está en "variar" y también fija.`);
    }
  }
  return c;
}

// Resuelve los miembros de "variar" (aleatorios y referencias @ENTRADA).
// pickMembers(dim, filtro) -> Promise<string[]> con los miembros candidatos del maestro.
async function resolveMembers(c, { seed, pickMembers }) {
  const rand = rng(seed ^ 0x9E3779B9);
  const resolved = new Map(); // nombre -> { dim: [miembros] }
  const pick = async (spec, dim, who) => {
    if (Array.isArray(spec)) return spec;
    const pool = (await pickMembers(dim, spec.filtro)).filter((m) => m !== '#');
    if (!pool.length) throw new CaseError(`${who}: no hay miembros de ${dim} que cumplan el filtro ${JSON.stringify(spec.filtro)}.`);
    const copy = [...pool];
    for (let i = copy.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [copy[i], copy[j]] = [copy[j], copy[i]]; }
    return copy.slice(0, Math.min(spec.aleatorio, copy.length)).sort();
  };
  for (const g of c.entradas) {
    const r = {};
    for (const [dim, spec] of Object.entries(g.variar)) if (typeof spec !== 'string') r[dim] = await pick(spec, dim, g.nombre);
    resolved.set(g.nombre, r);
  }
  for (const g of [...c.entradas, ...c.esperado]) {
    const r = resolved.get(g.nombre) || {};
    for (const [dim, spec] of Object.entries(g.variar)) {
      if (typeof spec === 'string') {
        const src = resolved.get(spec.slice(1))?.[dim];
        if (!src) throw new CaseError(`${g.nombre}.variar.${dim}: la entrada ${spec.slice(1)} no varía la dimensión ${dim}.`);
        r[dim] = src;
      } else if (!r[dim]) r[dim] = await pick(spec, dim, g.nombre);
    }
    resolved.set(g.nombre, r);
  }
  return resolved;
}

// Producto cartesiano de las listas de "variar"
function combos(variar) {
  let out = [{}];
  for (const [dim, list] of Object.entries(variar)) {
    const next = [];
    for (const o of out) for (const m of list) next.push({ ...o, [dim]: m });
    out = next;
  }
  return out;
}

function cellsOf(c, g, resolved) {
  const list = [];
  for (const date of c.periodos) {
    for (const combo of combos(resolved.get(g.nombre))) {
      list.push({ nombre: g.nombre, date, coords: { ...c.comun, ...g.fijo, ...combo } });
      if (list.length > MAX_CELLS) throw new CaseError(`${g.nombre} genera más de ${MAX_CELLS} celdas; reduzca periodos o miembros.`);
    }
  }
  return list;
}

function generateInputs(c, resolved, seed) {
  const rand = rng(seed);
  const out = [];
  for (const g of c.entradas) {
    const f = 10 ** g.decimales;
    for (const cell of cellsOf(c, g, resolved)) {
      const value = Math.round((g.min + rand() * (g.max - g.min)) * f) / f;
      out.push({ ...cell, value });
    }
  }
  return out;
}

const keyOf = (date, coords, dims) => [date, ...dims.map((d) => coords[d] ?? '')].join('\u0001');

// Calcula los valores esperados. En la fórmula:
//   v('ENTRADA')                valor de la entrada en la misma celda (mismo periodo y mismos
//                               miembros en las dimensiones que esa entrada varía)
//   sum('ENTRADA', {Dim: 'x'})  suma de la entrada en el mismo periodo (filtro opcional)
//   c.<Dimensión>, c.Date       miembros de la celda que se está calculando
//   round(x, dec), abs, min, max, pow, sqrt, Math
function computeExpected(c, resolved, inputs) {
  const byInput = new Map();
  for (const g of c.entradas) {
    const dims = Object.keys(g.variar);
    const index = new Map(); const byDate = new Map();
    for (const cell of inputs.filter((x) => x.nombre === g.nombre)) {
      index.set(keyOf(cell.date, cell.coords, dims), cell.value);
      if (!byDate.has(cell.date)) byDate.set(cell.date, []);
      byDate.get(cell.date).push(cell);
    }
    byInput.set(g.nombre, { dims, index, byDate });
  }
  const need = (name) => {
    const x = byInput.get(String(name));
    if (!x) throw new Error(`"${name}" no es una entrada del caso.`);
    return x;
  };
  const out = [];
  for (const g of c.esperado) {
    for (const cell of cellsOf(c, g, resolved)) {
      const cur = { ...cell.coords, Date: cell.date };
      const sandbox = {
        c: Object.freeze({ ...cur }),
        v: (name) => {
          const x = need(name);
          return x.index.get(keyOf(cell.date, cell.coords, x.dims)) ?? 0;
        },
        sum: (name, filtro = {}) => {
          const x = need(name);
          return (x.byDate.get(cell.date) || [])
            .filter((i) => Object.entries(filtro).every(([d, m]) => i.coords[d] === m))
            .reduce((a, i) => a + i.value, 0);
        },
        round: (x, d = 0) => Math.round(x * 10 ** d) / 10 ** d,
        abs: Math.abs, min: Math.min, max: Math.max, pow: Math.pow, sqrt: Math.sqrt, Math,
      };
      let expected = null; let error = null;
      try {
        expected = g.script.runInNewContext(sandbox, { timeout: 50 });
        if (typeof expected !== 'number' || !Number.isFinite(expected)) {
          error = `La fórmula devolvió ${expected === undefined ? 'un valor vacío' : JSON.stringify(expected)} (se esperaba un número).`;
          expected = null;
        }
      } catch (e) {
        error = `Error en la fórmula: ${e.message}`;
      }
      out.push({ ...cell, expected, error, tolerancia: g.tolerancia });
    }
  }
  return out;
}

// Registros para el Data Import API: todas las dimensiones del modelo, "#" si no se indicó.
function toImportRecords(cells, meta, version) {
  return cells.map((cell) => {
    const rec = {};
    for (const k of meta.keys) rec[k] = '#';
    for (const [d, m] of Object.entries(cell.coords)) {
      if (!meta.keys.includes(d)) throw new CaseError(`La dimensión "${d}" no existe en el modelo (dimensiones: ${meta.keys.join(', ')}).`);
      rec[d] = m;
    }
    rec[meta.versionColumn] = version;
    rec[meta.dateColumn] = cell.date;
    rec[meta.measure] = cell.value;
    return rec;
  });
}

const q = (v) => `'${String(v).replace(/'/g, "''")}'`;
const anyOf = (dim, list) => (list.length === 1 ? `${dim} eq ${q(list[0])}` : `(${list.map((m) => `${dim} eq ${q(m)}`).join(' or ')})`);

// Filtro OData ($filter) para leer de FactData sólo las celdas de un grupo esperado.
function factFilter(c, g, resolved, meta) {
  const parts = [`${meta.versionColumn} eq ${q(c.version)}`, anyOf(meta.dateColumn, c.periodos)];
  for (const [d, m] of Object.entries({ ...c.comun, ...g.fijo })) parts.push(`${d} eq ${q(m)}`);
  for (const [d, list] of Object.entries(resolved.get(g.nombre))) parts.push(anyOf(d, list));
  return parts.join(' and ');
}

function readValue(row, measure) {
  for (const k of [measure, 'SignedData', 'Value', 'AMOUNT', 'Amount']) {
    if (row[k] !== undefined && row[k] !== null && row[k] !== '') {
      const n = Number(row[k]);
      if (Number.isFinite(n)) return n;
    }
  }
  return null;
}

// Compara esperado vs. filas de FactData de ese grupo (se suman las filas que
// coinciden en las dimensiones del grupo; las demás dimensiones se agregan).
function compareGroup(expectedCells, rows, meta) {
  if (!expectedCells.length) return [];
  const dims = Object.keys(expectedCells[0].coords);
  const actual = new Map(); const seen = new Set();
  for (const row of rows) {
    const date = String(row[meta.dateColumn] ?? '').slice(0, 6);
    const coords = {};
    for (const d of dims) coords[d] = row[d] === undefined ? undefined : String(row[d]);
    const k = keyOf(date, coords, dims);
    const v = readValue(row, meta.measure);
    if (v === null) continue;
    actual.set(k, (actual.get(k) || 0) + v);
  }
  const out = expectedCells.map((e) => {
    const k = keyOf(e.date, e.coords, dims);
    seen.add(k);
    const real = actual.has(k) ? actual.get(k) : null;
    if (e.error) return { ...e, real, diff: null, ok: false };
    const diff = (real ?? 0) - e.expected;
    const tol = Math.max(e.tolerancia, Math.abs(e.expected) * 1e-9);
    return { ...e, real, diff, ok: Math.abs(diff) <= tol };
  });
  // Celdas con datos en SAC que no estaban en lo esperado (dentro del mismo alcance)
  const extra = [...actual.entries()].filter(([k, v]) => !seen.has(k) && Math.abs(v) > 0).length;
  return Object.assign(out, { extra });
}

function summarize(groups) {
  const cells = groups.flatMap((g) => g.cells);
  const failed = cells.filter((x) => !x.ok);
  const maxDiff = cells.reduce((m, x) => (x.diff === null ? m : Math.max(m, Math.abs(x.diff))), 0);
  return {
    ok: failed.length === 0 && cells.length > 0,
    cells: cells.length, passed: cells.length - failed.length, failed: failed.length,
    formulaErrors: cells.filter((x) => x.error).length,
    missing: cells.filter((x) => x.real === null && x.expected !== 0).length,
    extra: groups.reduce((a, g) => a + (g.extra || 0), 0),
    maxDiff,
  };
}

// parameterValues para la API de multi actions a partir de los parámetros del caso.
function parameterValues(c) {
  return c.parametros.map((p) => {
    switch (p.tipo) {
      case 'version': return { parameterId: p.id, value: { memberIds: [c.version], hierarchyId: p.jerarquia } };
      case 'periodos': return { parameterId: p.id, value: { memberIds: [...c.periodos], hierarchyId: p.jerarquia } };
      case 'miembro': return { parameterId: p.id, value: { memberIds: [...p.valor], hierarchyId: p.jerarquia } };
      case 'numero': return { parameterId: p.id, value: p.valor };
      default: return fillParameters([p.raw], c)[0];
    }
  });
}

// Reemplaza {{version}} y {{periodos}} en los parámetros con formato de la API de SAP.
function fillParameters(params, c) {
  const walk = (x) => {
    if (typeof x === 'string') {
      if (x === '{{periodos}}') return [...c.periodos];
      return x.replace(/\{\{version\}\}/g, c.version);
    }
    if (Array.isArray(x)) return x.flatMap((i) => (i === '{{periodos}}' ? [...c.periodos] : [walk(i)]));
    if (isObj(x)) return Object.fromEntries(Object.entries(x).map(([k, v]) => [k, walk(v)]));
    return x;
  };
  return walk(params);
}

module.exports = {
  CaseError, rng, expandPeriods, normalizeCase, resolveMembers, generateInputs, computeExpected,
  toImportRecords, factFilter, compareGroup, summarize, fillParameters, parameterValues, normalizeParams, cellsOf,
};
