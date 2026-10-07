'use strict';

const fs = require('fs');
const path = require('path');

// Bitácora de auditoría (una línea JSON por evento): quién cargó qué, cuándo,
// a qué modelo/versión y con qué resultado. No guarda valores financieros,
// sólo conteos y la huella SHA-256 del archivo para trazabilidad.

// AUDIT_FILE=stdout escribe en la salida estándar (Cloud Foundry, Docker),
// donde la plataforma recoge los registros.
function createAudit(file) {
  if (file === 'stdout') {
    return (event) => console.log(`[auditoria] ${JSON.stringify({ ts: new Date().toISOString(), ...event })}`);
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  return function audit(event) {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...event });
    fs.appendFile(file, `${line}\n`, (err) => {
      if (err) console.error('[auditoria] no se pudo escribir:', err.message);
    });
  };
}

module.exports = { createAudit };
