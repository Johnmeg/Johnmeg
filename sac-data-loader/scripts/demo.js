'use strict';

// Modo demostración: levanta un SAC simulado (OAuth + Data Import/Export API)
// y la aplicación apuntando a él. Sirve para probar el flujo completo sin
// tocar un tenant real. Usuarios: ana/demo (planificador), luis/demo (sin permiso).

const crypto = require('crypto');
const path = require('path');
const { createMockSac, CLIENT_ID, CLIENT_SECRET } = require('../test/mockSac');
const { loadTemplates } = require('../src/config');
const { createApp } = require('../src/app');
const { createAudit } = require('../src/audit');

const APP_PORT = Number(process.env.PORT || 3000);
const SAC_PORT = Number(process.env.MOCK_SAC_PORT || 4010);
const appUrl = `http://localhost:${APP_PORT}`;
const sacUrl = `http://localhost:${SAC_PORT}`;

const mock = createMockSac({ baseUrl: sacUrl, redirectUris: [`${appUrl}/auth/callback`] });
mock.app.listen(SAC_PORT, () => console.log(`SAC simulado en ${sacUrl}`));

const cfg = {
  port: APP_PORT,
  baseUrl: appUrl,
  sac: {
    tenantUrl: sacUrl,
    authorizeUrl: `${sacUrl}/oauth/authorize`,
    tokenUrl: `${sacUrl}/oauth/token`,
    clientId: CLIENT_ID,
    clientSecret: CLIENT_SECRET,
    scope: '',
    usePkce: true,
  },
  sessionSecret: crypto.randomBytes(32).toString('hex'),
  cookieSecure: false,
  sessionMinutes: 60,
  maxFileMb: 20,
  maxRows: 100000,
  chunkSize: 2,           // bloques pequeños para ver el envío por partes
  numberLocale: 'es',
  blockedVersions: ['public.Actual'],
  validateMembers: true,
  templates: loadTemplates(path.join(__dirname, '..', 'config', 'templates.json')),
};

const app = createApp(cfg, { audit: createAudit(path.join(__dirname, '..', 'logs', 'audit-demo.log')) });
app.listen(APP_PORT, () => {
  console.log(`Aplicación en ${appUrl}`);
  console.log('Usuarios de prueba: ana / demo (puede cargar), luis / demo (sin permiso de escritura)');
  console.log('Archivos de ejemplo en ./samples');
});
