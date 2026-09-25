'use strict';

// Conversión de encabezados/valores de periodo al formato de la dimensión Date de SAC.
// La granularidad sale de la metadata del modelo (maxLength de la columna Date):
//   4 -> YYYY, 6 -> YYYYMM (mensual, el caso normal), 8 -> YYYYMMDD

const MONTHS = {
  ene: 1, enero: 1, jan: 1, january: 1,
  feb: 2, febrero: 2, february: 2,
  mar: 3, marzo: 3, march: 3,
  abr: 4, abril: 4, apr: 4, april: 4,
  may: 5, mayo: 5,
  jun: 6, junio: 6, june: 6,
  jul: 7, julio: 7, july: 7,
  ago: 8, agosto: 8, aug: 8, august: 8,
  sep: 9, sept: 9, set: 9, septiembre: 9, setiembre: 9, september: 9,
  oct: 10, octubre: 10, october: 10,
  nov: 11, noviembre: 11, november: 11,
  dic: 12, diciembre: 12, dec: 12, december: 12,
};

const pad = (n, len = 2) => String(n).padStart(len, '0');
const validYear = (y) => y >= 1990 && y <= 2100;
const validMonth = (m) => m >= 1 && m <= 12;

function stripAccents(s) {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function fromDate(d) {
  if (Number.isNaN(d.getTime())) return null;
  // exceljs entrega las fechas en UTC
  return { y: d.getUTCFullYear(), m: d.getUTCMonth() + 1, d: d.getUTCDate() };
}

// Número de serie de fecha de Excel (sistema 1900).
function fromExcelSerial(n) {
  if (!Number.isInteger(n) || n < 30000 || n > 80000) return null;
  return fromDate(new Date(Date.UTC(1899, 11, 30) + n * 86400000));
}

function yearOf(txt) {
  const n = Number(txt);
  if (txt.length === 2) return 2000 + n;
  return txt.length === 4 ? n : NaN;
}

// Devuelve {y, m, d?} o null
function parseParts(input) {
  if (input === null || input === undefined || input === '') return null;
  if (input instanceof Date) return fromDate(input);
  if (typeof input === 'number') {
    if (Number.isInteger(input)) {
      const s = String(input);
      if (/^\d{6}$/.test(s)) return parseParts(s);
      if (/^\d{8}$/.test(s)) return parseParts(s);
      if (/^\d{4}$/.test(s)) return parseParts(s);
      return fromExcelSerial(input);
    }
    return null;
  }

  const s = stripAccents(String(input)).toLowerCase().trim()
    .replace(/[\s\-/._]+/g, ' ').trim();
  let m;

  if ((m = s.match(/^(\d{4})(\d{2})(\d{2})$/))) return { y: +m[1], m: +m[2], d: +m[3] };
  if ((m = s.match(/^(\d{4})(\d{2})$/))) return { y: +m[1], m: +m[2] };
  if ((m = s.match(/^(\d{4})$/))) return { y: +m[1] };
  if ((m = s.match(/^(\d{4}) (\d{1,2})$/))) return { y: +m[1], m: +m[2] };
  if ((m = s.match(/^(\d{1,2}) (\d{4})$/))) return { y: +m[2], m: +m[1] };
  if ((m = s.match(/^(\d{4}) (\d{1,2}) (\d{1,2})$/))) return { y: +m[1], m: +m[2], d: +m[3] };
  if ((m = s.match(/^(\d{1,2}) (\d{1,2}) (\d{4})$/))) return { y: +m[3], m: +m[2], d: +m[1] }; // dd/mm/yyyy
  if ((m = s.match(/^([a-z]+) (\d{2}|\d{4})$/)) && MONTHS[m[1]]) return { y: yearOf(m[2]), m: MONTHS[m[1]] };
  if ((m = s.match(/^(\d{4}) ([a-z]+)$/)) && MONTHS[m[2]]) return { y: +m[1], m: MONTHS[m[2]] };
  if ((m = s.match(/^([a-z]+)(\d{2}|\d{4})$/)) && MONTHS[m[1]]) return { y: yearOf(m[2]), m: MONTHS[m[1]] }; // ene2026
  return null;
}

// Convierte a clave de periodo según la longitud de la columna Date del modelo.
// Devuelve el string (p. ej. "202601") o null si no es un periodo válido.
function toPeriod(input, dateLength = 6) {
  const p = parseParts(input);
  if (!p || !validYear(p.y)) return null;
  if (dateLength === 4) return String(p.y);
  if (p.m === undefined || !validMonth(p.m)) return null;
  if (dateLength === 8) {
    if (p.d === undefined) return null;
    const probe = new Date(Date.UTC(p.y, p.m - 1, p.d));
    if (probe.getUTCMonth() !== p.m - 1) return null;
    return `${p.y}${pad(p.m)}${pad(p.d)}`;
  }
  return `${p.y}${pad(p.m)}`;
}

module.exports = { toPeriod, stripAccents };
