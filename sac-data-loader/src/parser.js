'use strict';

const path = require('path');
const ExcelJS = require('exceljs');

// Lee un archivo (Excel o plano) y devuelve una grilla de celdas crudas:
//   { sheetName, rows: [ { n: <número de fila en el archivo>, cells: [...] } ], warnings: [] }
// Las celdas conservan su tipo (número, fecha, texto) para que el validador decida.

const TEXT_EXT = new Set(['.csv', '.txt']);
const EXCEL_EXT = new Set(['.xlsx', '.xlsm']);
const ALLOWED_EXT = new Set([...TEXT_EXT, ...EXCEL_EXT]);

class ParseError extends Error {
  constructor(code, message) { super(message); this.code = code; }
}

function extensionOf(filename) {
  return path.extname(String(filename || '')).toLowerCase();
}

function assertAllowed(filename, buffer) {
  const ext = extensionOf(filename);
  if (ext === '.xls') {
    throw new ParseError('ARCH_FORMATO', 'El formato .xls (Excel 97-2003) no está soportado. Guarde el archivo como .xlsx.');
  }
  if (!ALLOWED_EXT.has(ext)) {
    throw new ParseError('ARCH_FORMATO', `Extensión "${ext || 'sin extensión'}" no permitida. Use .xlsx, .xlsm, .csv o .txt.`);
  }
  if (!buffer || buffer.length === 0) throw new ParseError('ARCH_VACIO', 'El archivo está vacío.');
  const isZip = buffer[0] === 0x50 && buffer[1] === 0x4b; // "PK": contenedor OOXML
  if (EXCEL_EXT.has(ext) && !isZip) {
    throw new ParseError('ARCH_FORMATO', 'El archivo no es un Excel válido (el contenido no corresponde a .xlsx/.xlsm).');
  }
  if (TEXT_EXT.has(ext) && isZip) {
    throw new ParseError('ARCH_FORMATO', 'El archivo parece ser un Excel renombrado como texto. Súbalo con extensión .xlsx.');
  }
  return ext;
}

// ---------------------------------------------------------------- texto plano

function decodeText(buffer) {
  if (buffer[0] === 0xef && buffer[1] === 0xbb && buffer[2] === 0xbf) {
    return { text: buffer.subarray(3).toString('utf8'), encoding: 'UTF-8 (BOM)' };
  }
  if (buffer[0] === 0xff && buffer[1] === 0xfe) {
    return { text: buffer.subarray(2).toString('utf16le'), encoding: 'UTF-16LE' };
  }
  try {
    return { text: new TextDecoder('utf-8', { fatal: true }).decode(buffer), encoding: 'UTF-8' };
  } catch {
    // Excel en Windows (es-CO) exporta CSV en Windows-1252
    try {
      return { text: new TextDecoder('windows-1252').decode(buffer), encoding: 'Windows-1252' };
    } catch {
      return { text: buffer.toString('latin1'), encoding: 'Latin-1' };
    }
  }
}

function countOutsideQuotes(line, ch) {
  let n = 0; let q = false;
  for (const c of line) {
    if (c === '"') q = !q;
    else if (c === ch && !q) n++;
  }
  return n;
}

function detectDelimiter(text) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '').slice(0, 20);
  let best = { ch: ',', score: -1 };
  for (const ch of [';', ',', '\t', '|']) {
    const counts = lines.map((l) => countOutsideQuotes(l, ch));
    const max = Math.max(0, ...counts);
    if (max === 0) continue;
    const modal = mode(counts.filter((c) => c > 0));
    const consistent = counts.filter((c) => c === modal).length;
    const score = consistent * 1000 + modal;
    if (score > best.score) best = { ch, score };
  }
  return best.ch;
}

function mode(arr) {
  const f = new Map();
  for (const v of arr) f.set(v, (f.get(v) || 0) + 1);
  let best = 0; let bestN = -1;
  for (const [v, n] of f) if (n > bestN || (n === bestN && v > best)) { best = v; bestN = n; }
  return best;
}

// Parser RFC 4180: comillas, comillas escapadas ("") y saltos de línea dentro de comillas.
function parseDelimited(text, delimiter) {
  const rows = [];
  let row = []; let field = ''; let inQuotes = false; let line = 1; let rowStart = 1;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else inQuotes = false;
      } else {
        if (c === '\n') line++;
        field += c;
      }
      continue;
    }
    if (c === '"' && field === '') { inQuotes = true; continue; }
    if (c === delimiter) { row.push(field); field = ''; continue; }
    if (c === '\r') continue;
    if (c === '\n') {
      row.push(field); rows.push({ n: rowStart, cells: row });
      row = []; field = ''; line++; rowStart = line;
      continue;
    }
    field += c;
  }
  if (inQuotes) throw new ParseError('ARCH_COMILLAS', `Comilla sin cerrar a partir de la fila ${rowStart}.`);
  if (field !== '' || row.length) { row.push(field); rows.push({ n: rowStart, cells: row }); }
  return rows;
}

function parseText(buffer) {
  const { text, encoding } = decodeText(buffer);
  if (text.includes('\u0000')) throw new ParseError('ARCH_FORMATO', 'El archivo contiene datos binarios; no es un archivo plano válido.');
  const delimiter = detectDelimiter(text);
  const rows = parseDelimited(text, delimiter);
  const names = { ',': 'coma', ';': 'punto y coma', '\t': 'tabulador', '|': 'barra vertical' };
  return { sheetName: null, rows, info: { encoding, delimiter: names[delimiter] } };
}

// ---------------------------------------------------------------- Excel

function cellValue(v) {
  if (v === null || v === undefined) return null;
  if (v instanceof Date) return v;
  if (typeof v !== 'object') return v;
  if ('result' in v) return cellValue(v.result);            // fórmula -> resultado calculado
  if ('formula' in v || 'sharedFormula' in v) return null;   // fórmula sin valor calculado
  if (Array.isArray(v.richText)) return v.richText.map((t) => t.text).join('');
  if ('text' in v) return v.text;                            // hipervínculo
  if ('error' in v) return { excelError: v.error };          // #N/A, #REF!, #DIV/0!...
  return String(v);
}

async function parseExcel(buffer, preferredSheet, maxRows) {
  const wb = new ExcelJS.Workbook();
  try {
    await wb.xlsx.load(buffer);
  } catch (e) {
    throw new ParseError('ARCH_FORMATO', `No se pudo leer el Excel: ${e.message}`);
  }
  const sheets = wb.worksheets.filter((ws) => ws.state !== 'hidden' && ws.state !== 'veryHidden');
  if (!sheets.length) throw new ParseError('ARCH_VACIO', 'El libro no tiene hojas visibles.');

  let ws;
  let warning = null;
  if (preferredSheet) {
    ws = wb.worksheets.find((s) => s.name.trim().toLowerCase() === String(preferredSheet).trim().toLowerCase());
    if (!ws) {
      const withData = sheets.filter((s) => s.actualRowCount > 0);
      if (withData.length !== 1) {
        throw new ParseError('ARCH_HOJA', `No se encontró la hoja "${preferredSheet}". Hojas del libro: ${wb.worksheets.map((s) => s.name).join(', ')}.`);
      }
      // Libro con una sola hoja con datos (p. ej. la hoja se renombró): se usa esa hoja.
      [ws] = withData;
      warning = `No existe la hoja "${preferredSheet}"; se leyó la única hoja con datos: "${ws.name}".`;
    }
  } else {
    ws = sheets.find((s) => s.actualRowCount > 0) || sheets[0];
  }

  if (ws.rowCount > maxRows + 200) {
    throw new ParseError('FILAS_MAX', `La hoja "${ws.name}" tiene ${ws.rowCount} filas; el máximo permitido es ${maxRows}.`);
  }

  const rows = [];
  ws.eachRow({ includeEmpty: false }, (row, n) => {
    const cells = [];
    for (let c = 1; c <= row.cellCount; c++) cells.push(cellValue(row.getCell(c).value));
    rows.push({ n, cells });
  });
  return { sheetName: ws.name, rows, info: { sheet: ws.name, warning } };
}

async function parseFile({ filename, buffer, preferredSheet, maxRows = 100000 }) {
  const ext = assertAllowed(filename, buffer);
  const parsed = EXCEL_EXT.has(ext) ? await parseExcel(buffer, preferredSheet, maxRows) : parseText(buffer);
  // Quitar filas totalmente vacías al final/inicio no altera la numeración (n se conserva).
  parsed.rows = parsed.rows.filter((r) => r.cells.some((c) => c !== null && c !== undefined && String(c).trim() !== ''));
  if (!parsed.rows.length) throw new ParseError('ARCH_VACIO', 'El archivo no contiene datos.');
  return { ...parsed, type: EXCEL_EXT.has(ext) ? 'excel' : 'texto' };
}

module.exports = { parseFile, ParseError, detectDelimiter, parseDelimited, ALLOWED_EXT };
