'use strict';

const { parseNumber, countDecimals } = require('./numbers');
const { toPeriod, stripAccents } = require('./periods');

// Motor de validación local. Recibe la grilla leída del archivo, la plantilla,
// la metadata real del modelo en SAC y (si están disponibles) los miembros de
// cada dimensión. Devuelve los registros listos para el Data Import API y la
// lista de hallazgos. Un solo error (severity "error") bloquea la carga.

const CATALOG = {
  ENC_NO_ENCONTRADO: 'No se encontró la fila de encabezados de la plantilla',
  ENC_DUPLICADO: 'Columna duplicada en el encabezado',
  ENC_VACIO: 'Columna con datos pero sin encabezado',
  COL_FALTANTE: 'Falta una columna/dimensión obligatoria',
  COL_DESCONOCIDA: 'Columna que no pertenece a la plantilla ni al modelo',
  COL_IGNORADA: 'Columna ignorada',
  COL_NO_EXISTE_EN_MODELO: 'La plantilla apunta a una columna que no existe en el modelo',
  PER_SIN_COLUMNAS: 'No hay columnas de periodo',
  PER_INVALIDO: 'Periodo inválido',
  PER_DUPLICADO: 'Periodo repetido',
  PER_FUERA_RANGO: 'Periodo fuera del rango permitido',
  VERSION_REQUERIDA: 'Versión no seleccionada',
  VERSION_BLOQUEADA: 'Versión bloqueada para carga',
  VERSION_DIFERENTE: 'La versión del archivo no coincide con la seleccionada',
  VERSION_INEXISTENTE: 'La versión no existe en el modelo',
  VAL_OBLIGATORIO: 'Valor obligatorio vacío',
  VAL_TIPO: 'Tipo de dato inválido',
  VAL_LONGITUD: 'Valor excede la longitud máxima',
  VAL_CARACTERES: 'Caracteres no permitidos',
  VAL_ESPACIOS: 'Espacios al inicio/fin (se eliminaron)',
  VAL_NO_PERMITIDO: 'Valor no permitido para la columna',
  MIEMBRO_INEXISTENTE: 'El miembro no existe en la dimensión del modelo',
  NUM_INVALIDO: 'Valor numérico inválido',
  NUM_AMBIGUO: 'Formato numérico ambiguo',
  NUM_NEGATIVO: 'Valor negativo no permitido',
  NUM_DECIMALES: 'Demasiados decimales',
  NUM_EXCESIVO: 'Valor inusualmente grande',
  CLAVE_DUPLICADA: 'Combinación de dimensiones repetida',
  FILAS_MAX: 'Se superó el máximo de filas',
  SIN_REGISTROS: 'No hay valores para cargar',
};

class Issues {
  constructor({ maxPerKey = 50, maxTotal = 5000 } = {}) {
    this.items = []; this.perKey = new Map(); this.suppressed = new Map();
    this.errors = 0; this.warnings = 0; this.maxPerKey = maxPerKey; this.maxTotal = maxTotal;
  }

  add(severity, code, message, { row = null, column = null, value = null } = {}) {
    if (severity === 'error') this.errors++; else this.warnings++;
    const key = `${code}|${column || ''}`;
    const n = (this.perKey.get(key) || 0) + 1;
    this.perKey.set(key, n);
    if (n > this.maxPerKey || this.items.length >= this.maxTotal) {
      this.suppressed.set(key, { severity, code, column, count: (this.suppressed.get(key)?.count || 0) + 1 });
      return;
    }
    this.items.push({ severity, code, title: CATALOG[code] || code, message, row, column, value: display(value) });
  }

  error(code, message, where) { this.add('error', code, message, where); }
  warn(code, message, where) { this.add('warning', code, message, where); }

  list() {
    const extra = [...this.suppressed.values()].map((s) => ({
      severity: s.severity, code: s.code, title: CATALOG[s.code] || s.code, row: null, column: s.column, value: null,
      message: `… y ${s.count} hallazgo(s) más del mismo tipo${s.column ? ` en la columna ${s.column}` : ''}.`,
    }));
    return [...this.items, ...extra];
  }
}

function display(v) {
  if (v === null || v === undefined) return null;
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  if (typeof v === 'object' && v.excelError) return v.excelError;
  const s = String(v);
  return s.length > 80 ? `${s.slice(0, 77)}...` : s;
}

// "Cebes_CL (componente)" -> "cebes_cl" ; "Auditoría:" -> "auditoria"
function norm(x) {
  if (x === null || x === undefined) return '';
  return stripAccents(String(x)).toLowerCase()
    .replace(/\(.*?\)/g, '').replace(/:\s*$/, '').replace(/\s+/g, ' ').trim();
}

const isBlank = (v) => v === null || v === undefined || (typeof v === 'string' && v.trim() === '');
const bareVersion = (v) => norm(v).replace(/^(public|private)\./, '');

// Convierte una celda de dimensión a texto (los códigos numéricos de Excel llegan como número).
function dimText(raw) {
  if (typeof raw === 'number') return Number.isInteger(raw) ? String(raw) : String(raw);
  if (raw instanceof Date || (raw && typeof raw === 'object')) return null;
  return String(raw);
}

function findHeaderRow(rows, expected, dateLength) {
  let best = null;
  for (const r of rows.slice(0, 40)) {
    let score = 0;
    for (const c of r.cells) {
      if (isBlank(c)) continue;
      if (expected.has(norm(c))) score += 2;
      else if (toPeriod(c, dateLength)) score += 1;
    }
    if (score > 0 && (!best || score > best.score)) best = { row: r, score };
  }
  return best && best.score >= 2 ? best.row : null;
}

function readContext(rows, headerN, contextFields) {
  const ctx = {};
  if (!contextFields) return ctx;
  const labels = new Map(Object.entries(contextFields).map(([k, v]) => [norm(k), v]));
  for (const r of rows) {
    if (r.n >= headerN) break;
    r.cells.forEach((c, i) => {
      const target = labels.get(norm(c));
      if (!target) return;
      const value = r.cells.slice(i + 1).find((x) => !isBlank(x));
      if (value !== undefined && !/^<.*>$/.test(String(value).trim())) {
        ctx[target] = { value: String(value).trim(), row: r.n };
      }
    });
  }
  return ctx;
}

function validate({ grid, template, meta, members = new Map(), options = {} }) {
  const issues = new Issues();
  const {
    version, numberLocale = 'es', maxRows = 100000, blockedVersions = [],
  } = options;
  const rules = { allowNegative: true, skipZeroValues: false, maxDecimals: 7, ...(template.rules || {}) };
  const { versionColumn, dateColumn, measure, dateLength } = meta;
  const records = [];
  const summary = {
    sheet: grid.sheetName, fileInfo: grid.info || {}, headerRow: null, layout: null,
    rowsRead: 0, records: 0, skippedBlank: 0, periods: [], totalsByPeriod: {}, grandTotal: 0,
  };
  const finish = () => {
    summary.records = records.length;
    summary.periods = Object.keys(summary.totalsByPeriod).sort();
    summary.grandTotal = round(Object.values(summary.totalsByPeriod).reduce((a, b) => a + b, 0));
    for (const p of summary.periods) summary.totalsByPeriod[p] = round(summary.totalsByPeriod[p]);
    summary.errors = issues.errors; summary.warnings = issues.warnings;
    return { ok: issues.errors === 0 && records.length > 0, issues: issues.list(), records, summary };
  };

  // ---------------------------------------------------------------- mapeo de columnas
  const modelCols = meta.columns; // Map nombre -> {type, maxLength, isKey}
  const colMap = new Map(); // norm(encabezado archivo) -> columna del modelo
  if (template.columns === 'byName' || !template.columns) {
    for (const name of modelCols.keys()) colMap.set(norm(name), name);
  } else {
    for (const [fileHeader, modelCol] of Object.entries(template.columns)) {
      if (!modelCols.has(modelCol)) {
        issues.error('COL_NO_EXISTE_EN_MODELO',
          `La plantilla "${template.id}" mapea "${fileHeader}" a "${modelCol}", pero el modelo no tiene esa columna. Columnas del modelo: ${[...modelCols.keys()].join(', ')}.`,
          { column: modelCol });
        continue;
      }
      colMap.set(norm(fileHeader), modelCol);
    }
  }
  const ignoreSet = new Map((template.ignoreColumns || []).map((c) => [norm(typeof c === 'string' ? c : c.name), c]));
  const expected = new Set([...colMap.keys(), ...ignoreSet.keys(), norm(dateColumn), norm(measure)]);

  const header = findHeaderRow(grid.rows, expected, dateLength);
  if (!header) {
    issues.error('ENC_NO_ENCONTRADO',
      `No se encontró la fila de encabezados. Se esperaban columnas como: ${[...colMap.keys()].slice(0, 8).join(', ')}.`);
    return finish();
  }
  summary.headerRow = header.n;
  const context = readContext(grid.rows, header.n, template.contextFields);

  const dimCols = []; const periodCols = []; let dateIdx = -1; let measureIdx = -1; let versionIdx = -1;
  const seenModel = new Map(); const seenPeriod = new Map();
  header.cells.forEach((cell, idx) => {
    if (isBlank(cell)) return;
    const h = norm(cell);
    const label = String(cell).trim();
    const where = { row: header.n, column: label, value: label };
    if (colMap.get(h) === versionColumn) { versionIdx = idx; return; }
    if (colMap.has(h) && colMap.get(h) !== measure && colMap.get(h) !== dateColumn) {
      const modelCol = colMap.get(h);
      if (seenModel.has(modelCol)) { issues.error('ENC_DUPLICADO', `"${label}" aparece más de una vez en el encabezado.`, where); return; }
      seenModel.set(modelCol, idx); dimCols.push({ idx, modelCol, label });
      return;
    }
    if (h === norm(dateColumn)) { dateIdx = idx; return; }
    if (h === norm(measure)) { measureIdx = idx; return; }
    const p = toPeriod(cell, dateLength);
    if (p) {
      if (seenPeriod.has(p)) { issues.error('PER_DUPLICADO', `El periodo ${p} está en dos columnas ("${seenPeriod.get(p)}" y "${label}").`, where); return; }
      seenPeriod.set(p, label); periodCols.push({ idx, period: p, label });
      return;
    }
    if (ignoreSet.has(h)) {
      const def = ignoreSet.get(h);
      const note = typeof def === 'object' && def.note ? ` ${def.note}` : '';
      issues.warn('COL_IGNORADA', `La columna "${label}" no se carga.${note}`, where);
      return;
    }
    const msg = `La columna "${label}" no pertenece a la plantilla "${template.name}". Revise el nombre o elimínela.`;
    if (template.ignoreUnknownColumns) issues.warn('COL_DESCONOCIDA', msg, where);
    else issues.error('COL_DESCONOCIDA', msg, where);
  });

  // Columnas con datos pero sin encabezado
  let width = header.cells.length;
  for (const r of grid.rows) if (r.n > header.n && r.cells.length > width) width = r.cells.length;
  for (let idx = 0; idx < width; idx++) {
    if (!isBlank(header.cells[idx])) continue;
    const hit = grid.rows.find((r) => r.n > header.n && !isBlank(r.cells[idx]));
    if (hit) issues.error('ENC_VACIO', `La columna ${colLetter(idx)} tiene datos (fila ${hit.n}) pero no tiene encabezado.`, { row: header.n, column: colLetter(idx) });
  }

  // ---------------------------------------------------------------- layout
  let layout = template.layout || 'auto';
  if (layout === 'auto') layout = periodCols.length && dateIdx < 0 ? 'wide' : 'long';
  summary.layout = layout;
  if (layout === 'wide' && !periodCols.length) {
    issues.error('PER_SIN_COLUMNAS', 'No se encontraron columnas de periodo (p. ej. "Ene 2026" o "202601") en el encabezado.', { row: header.n });
  }
  if (layout === 'long') {
    if (dateIdx < 0) issues.error('COL_FALTANTE', `Falta la columna de periodo "${dateColumn}".`, { row: header.n, column: dateColumn });
    if (measureIdx < 0) issues.error('COL_FALTANTE', `Falta la columna de valor "${measure}".`, { row: header.n, column: measure });
  }

  // ---------------------------------------------------------------- valores fijos / contexto / versión
  const constants = {}; // columna del modelo -> valor aplicado a todas las filas
  for (const [col, value] of Object.entries(template.fixedValues || {})) {
    if (!modelCols.has(col)) {
      issues.error('COL_NO_EXISTE_EN_MODELO', `El valor fijo "${col}" de la plantilla no existe en el modelo.`, { column: col });
      continue;
    }
    constants[col] = { value: String(value), source: 'plantilla' };
  }
  for (const [col, { value, row }] of Object.entries(context)) {
    if (col === versionColumn) continue;
    if (!modelCols.has(col)) continue;
    constants[col] = { value, source: `archivo (fila ${row})`, row };
  }

  if (!version) {
    issues.error('VERSION_REQUERIDA', 'Seleccione la versión de destino. Sin versión, SAC cargaría por defecto en public.Actual.');
  } else {
    if (blockedVersions.some((b) => norm(b) === norm(version))) {
      issues.error('VERSION_BLOQUEADA', `La versión "${version}" está bloqueada para cargas desde archivo (se alimenta de S/4HANA).`, { column: versionColumn, value: version });
    }
    const vctx = context[versionColumn];
    if (vctx && bareVersion(vctx.value) !== bareVersion(version)) {
      issues.error('VERSION_DIFERENTE',
        `El archivo indica la versión "${vctx.value}" (fila ${vctx.row}) pero se seleccionó "${version}". Corrija la selección o el archivo.`,
        { row: vctx.row, column: versionColumn, value: vctx.value });
    }
    const vm = members.get(versionColumn);
    if (vm && !vm.has(version)) {
      issues.error('VERSION_INEXISTENTE', `La versión "${version}" no existe en el modelo. Disponibles: ${[...vm].slice(0, 10).join(', ')}.`, { column: versionColumn, value: version });
    }
  }

  for (const [col, c] of Object.entries(constants)) {
    checkDimValue(c.value, col, { row: c.row || null, column: col, value: c.value }, `(valor de ${c.source})`);
  }

  // Columnas clave obligatorias
  const provided = new Set([versionColumn, dateColumn, ...Object.keys(constants), ...dimCols.map((d) => d.modelCol)]);
  for (const key of meta.keys) {
    if (!provided.has(key)) {
      issues.error('COL_FALTANTE', `El modelo exige la dimensión "${key}" y no viene en el archivo ni como valor fijo de la plantilla.`, { row: header.n, column: key });
    }
  }
  if (issues.errors) return finish(); // no seguir fila a fila con una estructura inválida

  // ---------------------------------------------------------------- filas de datos
  const periodRange = template.periodRange || {};
  const seenKeys = new Map();
  const ambiguous = { count: 0, first: null, confirmed: false }; // confirmed: otro valor del archivo usa el formato sin ambigüedad
  const dataRows = grid.rows.filter((r) => r.n > header.n);
  if (dataRows.length > maxRows) {
    issues.error('FILAS_MAX', `El archivo tiene ${dataRows.length} filas de datos; el máximo es ${maxRows}. Divida el archivo.`);
    return finish();
  }

  for (const r of dataRows) {
    const cells = r.cells;
    if (dimCols.every((d) => isBlank(cells[d.idx]))
      && (layout === 'wide' ? periodCols.every((p) => isBlank(cells[p.idx])) : isBlank(cells[measureIdx]))) continue;
    summary.rowsRead++;

    const base = {};
    for (const [col, c] of Object.entries(constants)) base[col] = c.value;
    if (version) base[versionColumn] = version;

    let rowOk = true;
    if (versionIdx >= 0 && !isBlank(cells[versionIdx]) && version && bareVersion(cells[versionIdx]) !== bareVersion(version)) {
      issues.error('VERSION_DIFERENTE', `La fila trae la versión "${cells[versionIdx]}" pero se seleccionó "${version}".`,
        { row: r.n, column: versionColumn, value: cells[versionIdx] });
      rowOk = false;
    }
    for (const d of dimCols) {
      const where = { row: r.n, column: d.label, value: cells[d.idx] };
      const raw = cells[d.idx];
      if (isBlank(raw)) { issues.error('VAL_OBLIGATORIO', `"${d.label}" está vacío.`, where); rowOk = false; continue; }
      const txt = dimText(raw);
      if (txt === null) { issues.error('VAL_TIPO', `"${d.label}" debe ser un código, no una fecha u objeto.`, where); rowOk = false; continue; }
      const clean = txt.trim();
      if (clean !== txt) issues.warn('VAL_ESPACIOS', `Se quitaron espacios en "${d.label}".`, where);
      if (!checkDimValue(clean, d.modelCol, where)) rowOk = false;
      base[d.modelCol] = clean;
    }

    const values = []; // [{period, value, where}]
    if (layout === 'wide') {
      for (const p of periodCols) values.push({ period: p.period, raw: cells[p.idx], where: { row: r.n, column: p.label, value: cells[p.idx] } });
    } else {
      const rawDate = cells[dateIdx];
      const where = { row: r.n, column: dateColumn, value: rawDate };
      const period = toPeriod(rawDate, dateLength);
      if (!period) {
        const fmt = { 4: 'AAAA', 6: 'AAAAMM', 8: 'AAAAMMDD' }[dateLength] || 'AAAAMM';
        issues.error('PER_INVALIDO', `"${display(rawDate)}" no es un periodo válido (formato esperado ${fmt}).`, where);
        rowOk = false;
      } else values.push({ period, raw: cells[measureIdx], where: { row: r.n, column: measure, value: cells[measureIdx] } });
    }

    const dupPeriods = []; let dupOf = null;
    for (const v of values) {
      if (periodRange.from && v.period < periodRange.from || periodRange.to && v.period > periodRange.to) {
        issues.error('PER_FUERA_RANGO', `El periodo ${v.period} está fuera del rango permitido ${periodRange.from || '…'}–${periodRange.to || '…'}.`, v.where);
        rowOk = false; continue;
      }
      if (v.raw && typeof v.raw === 'object' && v.raw.excelError) {
        issues.error('NUM_INVALIDO', `La celda contiene el error de Excel ${v.raw.excelError}.`, v.where); rowOk = false; continue;
      }
      const num = parseNumber(v.raw, numberLocale);
      if (num.blank) { summary.skippedBlank++; continue; }
      if (num.error) { issues.error('NUM_INVALIDO', num.error, v.where); rowOk = false; continue; }
      if (num.ambiguous) { ambiguous.count++; if (!ambiguous.first) ambiguous.first = { ...v.where, parsed: num.value }; }
      else if (typeof v.raw === 'string' && (numberLocale === 'en' ? /\.\d|,.*,/ : /,\d|\..*\./).test(v.raw)) ambiguous.confirmed = true;
      if (num.value < 0 && !rules.allowNegative) { issues.error('NUM_NEGATIVO', `Esta plantilla no admite valores negativos (${num.value}).`, v.where); rowOk = false; continue; }
      if (countDecimals(num.value) > rules.maxDecimals) issues.warn('NUM_DECIMALES', `${num.value} tiene más de ${rules.maxDecimals} decimales.`, v.where);
      if (Math.abs(num.value) >= 1e13) issues.warn('NUM_EXCESIVO', `${num.value} es inusualmente grande; verifique unidades (¿miles vs pesos?).`, v.where);
      if (num.value === 0 && rules.skipZeroValues) { summary.skippedBlank++; continue; }

      if (!rowOk) continue;
      const rec = { ...base, [dateColumn]: v.period, [measure]: num.value };
      const key = meta.keys.map((k) => rec[k]).join('\u0001');
      const first = seenKeys.get(key);
      if (first) { dupPeriods.push(v.period); dupOf = dupOf || first; continue; }
      seenKeys.set(key, r.n);
      records.push(rec);
      summary.totalsByPeriod[v.period] = (summary.totalsByPeriod[v.period] || 0) + num.value;
    }
    if (dupPeriods.length) {
      const which = dupPeriods.length === 1 ? `el periodo ${dupPeriods[0]}` : `${dupPeriods.length} periodos (${dupPeriods[0]}…${dupPeriods[dupPeriods.length - 1]})`;
      issues.error('CLAVE_DUPLICADA',
        `La fila ${r.n} repite la combinación de dimensiones de la fila ${dupOf} en ${which}. Consolide los valores en una sola fila.`,
        { row: r.n, column: dimCols.map((d) => d.label).join(' + ') || null });
    }
  }

  if (ambiguous.count && !ambiguous.confirmed) {
    const f = ambiguous.first;
    const sep = numberLocale === 'en' ? 'coma = miles, punto = decimales' : 'punto = miles, coma = decimales';
    issues.warn('NUM_AMBIGUO',
      `${ambiguous.count} valor(es) como "${f.value}" (fila ${f.row}) se interpretaron con el formato ${numberLocale === 'en' ? 'inglés' : 'es-CO'} (${sep}): "${f.value}" = ${f.parsed}. Verifique que ese sea el formato de su archivo.`,
      { row: f.row, column: f.column, value: f.value });
  }
  if (!records.length && !issues.errors) {
    issues.error('SIN_REGISTROS', 'El archivo no tiene valores numéricos para cargar (todas las celdas de valor están vacías).');
  }
  return finish();

  // -------------------------------------------------------------- helpers con acceso a issues
  function checkDimValue(value, col, where, suffix = '') {
    const def = modelCols.get(col) || {};
    let ok = true;
    if (/[\u0000-\u001F\u007F]/.test(value)) { issues.error('VAL_CARACTERES', `"${col}" contiene caracteres de control (saltos de línea, tabuladores).`, where); ok = false; }
    if (def.maxLength && value.length > def.maxLength) {
      issues.error('VAL_LONGITUD', `"${value}" tiene ${value.length} caracteres; el máximo para ${col} es ${def.maxLength}. ${suffix}`.trim(), where); ok = false;
    }
    const allowed = (template.allowedValues || {})[col];
    if (allowed && !allowed.includes(value)) {
      issues.error('VAL_NO_PERMITIDO', `"${value}" no está permitido en ${col}. Permitidos: ${allowed.join(', ')}. ${suffix}`.trim(), where); ok = false;
    }
    const set = members.get(col);
    if (ok && set && value !== '#' && !set.has(value)) {
      const hint = [...set].find((m) => m.toLowerCase() === value.toLowerCase());
      issues.error('MIEMBRO_INEXISTENTE',
        `"${value}" no existe en la dimensión ${col}.${hint ? ` ¿Quiso decir "${hint}"? (SAC distingue mayúsculas)` : ''} ${suffix}`.trim(), where);
      ok = false;
    }
    return ok;
  }
}

function colLetter(idx) {
  let s = ''; let n = idx + 1;
  while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); }
  return s;
}

function round(v) { return Math.round(v * 1e6) / 1e6; }

module.exports = { validate, norm, CATALOG };
