'use strict';

// Normaliza la respuesta de GET /models/{id}/metadata:
//   { factData: { keys: [...], columns: [ {columnName, columnDataType, maxLength, isKey} ] } }
// y resuelve cuáles son las columnas de versión, fecha y medida.

class ConfigError extends Error {}

const NUMERIC = /decimal|double|integer|int|number|float/i;

function buildMeta(raw, template = {}) {
  const block = raw?.factData || raw?.privateFactData || raw?.masterFactData;
  if (!block || !Array.isArray(block.columns)) {
    throw new ConfigError('SAC no devolvió la metadata de datos (factData) del modelo.');
  }
  const columns = new Map();
  for (const c of block.columns) {
    columns.set(c.columnName, {
      type: c.columnDataType, maxLength: Number(c.maxLength) || null, isKey: Boolean(c.isKey),
    });
  }
  const keys = Array.isArray(block.keys) && block.keys.length
    ? block.keys.filter((k) => columns.has(k))
    : [...columns].filter(([, v]) => v.isKey).map(([k]) => k);

  const pick = (explicit, candidates, label) => {
    if (explicit) {
      if (!columns.has(explicit)) throw new ConfigError(`La plantilla indica ${label} "${explicit}", pero el modelo no tiene esa columna.`);
      return explicit;
    }
    const found = candidates();
    if (!found) throw new ConfigError(`No se pudo identificar la columna de ${label} del modelo; indíquela en la plantilla.`);
    return found;
  };

  const versionColumn = pick(template.versionColumn,
    () => keys.find((k) => /^version$/i.test(k)) || keys.find((k) => /version/i.test(k)), 'versión');
  const dateColumn = pick(template.dateColumn,
    () => keys.find((k) => /^date$/i.test(k)) || keys.find((k) => /date|fecha|tiempo|time|periodo/i.test(k)), 'fecha');
  const measure = pick(template.measure, () => {
    const nums = [...columns].filter(([, v]) => !v.isKey && NUMERIC.test(v.type || '')).map(([k]) => k);
    if (nums.length > 1) {
      throw new ConfigError(`El modelo tiene varias medidas (${nums.join(', ')}); indique en la plantilla cuál cargar ("measure").`);
    }
    return nums[0];
  }, 'medida');

  const dateLength = columns.get(dateColumn).maxLength || 6;
  return { columns, keys, versionColumn, dateColumn, measure, dateLength };
}

module.exports = { buildMeta, ConfigError };
