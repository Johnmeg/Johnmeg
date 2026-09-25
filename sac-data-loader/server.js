'use strict';

const fs = require('fs');
const path = require('path');
const util = require('util');

// Modo "segundo plano" (instalación en el computador del usuario): sin ventana,
// la salida va a LOG_FILE y el identificador del proceso a PID_FILE, para que
// el acceso directo "Detener" pueda cerrarlo.
if (process.env.LOG_FILE) {
  const file = process.env.LOG_FILE;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  try {
    if (fs.statSync(file).size > 5 * 1024 * 1024) fs.renameSync(file, `${file}.1`);
  } catch { /* todavía no existe */ }
  const out = fs.createWriteStream(file, { flags: 'a' });
  const write = (...args) => out.write(`${new Date().toISOString()} ${util.format(...args)}\n`);
  console.log = write;
  console.info = write;
  console.warn = write;
  console.error = write;
  process.on('uncaughtException', (e) => { write('[error]', e); out.end(() => process.exit(1)); });
}
if (process.env.PID_FILE) {
  const pidFile = process.env.PID_FILE;
  fs.mkdirSync(path.dirname(pidFile), { recursive: true });
  fs.writeFileSync(pidFile, String(process.pid));
  const cleanup = () => { try { if (fs.readFileSync(pidFile, 'utf8') === String(process.pid)) fs.unlinkSync(pidFile); } catch { /* ya no existe */ } };
  process.on('exit', cleanup);
  for (const sig of ['SIGINT', 'SIGTERM', 'SIGBREAK']) process.on(sig, () => process.exit(0));
}

const { loadConfig } = require('./src/config');
const { createAudit } = require('./src/audit');
const { createApp } = require('./src/app');

let cfg;
try {
  cfg = loadConfig();
} catch (e) {
  console.error(`\n[configuración] ${e.message}\n`);
  process.exit(1);
}

const app = createApp(cfg, { audit: createAudit(cfg.auditFile) });
const server = app.listen(cfg.port, cfg.host, () => {
  console.log(`Cargador SAC escuchando en ${cfg.baseUrl} (puerto ${cfg.port}${cfg.host ? `, interfaz ${cfg.host}` : ''})`);
  console.log(`Tenant SAC: ${cfg.sac.tenantUrl}`);
  console.log(`Plantillas: ${cfg.templates.map((t) => t.id).join(', ')}`);
});
server.on('error', (e) => {
  if (e.code === 'EADDRINUSE') {
    console.error(`[inicio] El puerto ${cfg.port} ya está en uso por otro programa (¿otra copia del cargador abierta?).`);
  } else {
    console.error('[inicio]', e.message);
  }
  process.exit(1);
});
