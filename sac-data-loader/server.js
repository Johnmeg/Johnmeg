'use strict';

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
app.listen(cfg.port, cfg.host, () => {
  console.log(`Cargador SAC escuchando en ${cfg.baseUrl} (puerto ${cfg.port}${cfg.host ? `, interfaz ${cfg.host}` : ''})`);
  console.log(`Tenant SAC: ${cfg.sac.tenantUrl}`);
  console.log(`Plantillas: ${cfg.templates.map((t) => t.id).join(', ')}`);
});
