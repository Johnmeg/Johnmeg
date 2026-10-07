'use strict';

// Interpreta un valor numérico venido de Excel o de un archivo plano.
// Soporta formato colombiano/español (1.234.567,89) e inglés (1,234,567.89),
// negativos con signo inicial o final y contables entre paréntesis: (1.500).
//
// Devuelve { value, blank, ambiguous, error }:
//   blank     -> celda vacía (no se carga, no es error)
//   ambiguous -> "1.234" / "1,234": se resolvió con el locale configurado (advertencia)
//   error     -> el texto no es un número válido

function result(value, extra = {}) {
  return { value, blank: false, ambiguous: false, error: null, ...extra };
}

function parseNumber(raw, locale = 'es') {
  if (raw === null || raw === undefined) return result(null, { blank: true });

  if (typeof raw === 'number') {
    return Number.isFinite(raw) ? result(raw) : result(null, { error: 'Número no finito' });
  }
  if (typeof raw === 'boolean' || raw instanceof Date) {
    return result(null, { error: 'Se esperaba un número' });
  }

  let s = String(raw).replace(/[  \s]/g, '');
  if (s === '') return result(null, { blank: true });

  let negative = false;
  if (/^\(.*\)$/.test(s)) { negative = true; s = s.slice(1, -1); }
  s = s.replace(/^\$|\$$/g, '');
  if (s.startsWith('-')) { negative = !negative; s = s.slice(1); }
  else if (s.startsWith('+')) { s = s.slice(1); }
  else if (s.endsWith('-')) { negative = !negative; s = s.slice(0, -1); }

  if (/^\d+(\.\d+)?[eE][+-]?\d+$/.test(s)) {
    const v = Number(s);
    return Number.isFinite(v) ? result(negative ? -v : v) : result(null, { error: 'Número fuera de rango' });
  }

  if (!/^[\d.,]+$/.test(s) || !/\d/.test(s)) {
    return result(null, { error: `"${raw}" no es un número válido` });
  }

  const dots = (s.match(/\./g) || []).length;
  const commas = (s.match(/,/g) || []).length;
  let ambiguous = false;
  let normalized;

  if (dots && commas) {
    // Ambos separadores: el último que aparece es el decimal.
    const dec = s.lastIndexOf('.') > s.lastIndexOf(',') ? '.' : ',';
    const thou = dec === '.' ? ',' : '.';
    if ((s.split(dec).length - 1) > 1) return result(null, { error: `"${raw}" tiene varios separadores decimales` });
    const [intPart, decPart] = s.split(dec);
    if (!validGrouping(intPart, thou)) return result(null, { error: `"${raw}" tiene separadores de miles mal ubicados` });
    normalized = intPart.split(thou).join('') + '.' + decPart;
  } else if (dots || commas) {
    const sep = dots ? '.' : ',';
    const count = dots || commas;
    const parts = s.split(sep);
    if (count > 1) {
      // Varias ocurrencias: sólo puede ser separador de miles (1.234.567).
      if (!validGrouping(s, sep)) return result(null, { error: `"${raw}" tiene separadores de miles mal ubicados` });
      normalized = parts.join('');
    } else if (parts[1].length !== 3 || parts[0] === '' || parts[0] === '0') {
      // Una sola ocurrencia sin grupo de 3 dígitos (o "0,500"): es decimal.
      normalized = parts[0] + '.' + parts[1];
    } else {
      // "1.234" o "1,234": ambiguo, se decide por el locale.
      ambiguous = true;
      const thousandsSep = locale === 'en' ? ',' : '.';
      normalized = sep === thousandsSep ? parts.join('') : parts[0] + '.' + parts[1];
    }
  } else {
    normalized = s;
  }

  const v = Number(normalized);
  if (!Number.isFinite(v)) return result(null, { error: `"${raw}" no es un número válido` });
  return result(negative ? -v : v, { ambiguous });
}

// 1.234.567 -> grupos después del primero deben tener exactamente 3 dígitos.
function validGrouping(intPart, sep) {
  const groups = intPart.split(sep);
  if (groups[0] === '' || groups[0].length > 3 && groups.length > 1) return false;
  return groups.slice(1).every((g) => /^\d{3}$/.test(g));
}

function countDecimals(value) {
  if (!Number.isFinite(value) || Number.isInteger(value)) return 0;
  const s = value.toString();
  if (s.includes('e-')) return Number(s.split('e-')[1]) + (s.split('e-')[0].split('.')[1] || '').length;
  return (s.split('.')[1] || '').length;
}

module.exports = { parseNumber, countDecimals };
