'use strict';

const fs = require('fs');
const path = require('path');

// Bitácora de auditoría (una línea JSON por evento): quién cargó qué, cuándo,
// a qué modelo/versión y con qué resultado. No guarda valores financieros,
// sólo conteos y la huella SHA-256 del archivo para trazabilidad.

function createAudit(file) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  return function audit(event) {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...event });
    fs.appendFile(file, `${line}\n`, (err) => {
      if (err) console.error('[auditoria] no se pudo escribir:', err.message);
    });
  };
}

module.exports = { createAudit };
