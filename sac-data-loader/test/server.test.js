'use strict';

// Arranque en segundo plano: LOG_FILE, PID_FILE y /healthz (lo que usan los
// accesos directos del instalador para el computador del usuario).

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');

function freePort() {
  return new Promise((resolve) => {
    const s = net.createServer().listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => resolve(port)); });
  });
}

test('server.js en segundo plano escribe registro y PID, y responde /healthz', async (t) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cargador-'));
  const port = await freePort();
  const env = {
    PATH: process.env.PATH,
    PORT: String(port), HOST: '127.0.0.1', APP_BASE_URL: `http://localhost:${port}`,
    SESSION_SECRET: 'x'.repeat(40),
    SAC_TENANT_URL: 'https://t.example', SAC_AUTHORIZE_URL: 'https://a.example/oauth/authorize',
    SAC_TOKEN_URL: 'https://a.example/oauth/token', SAC_CLIENT_ID: 'id', SAC_CLIENT_SECRET: 'secret',
    AUDIT_FILE: path.join(dir, 'audit.log'),
    LOG_FILE: path.join(dir, 'logs', 'app.log'), PID_FILE: path.join(dir, 'logs', 'app.pid'),
  };
  // Se lanza desde otra carpeta: la app debe resolver sus rutas por sí misma
  const child = spawn(process.execPath, [path.join(__dirname, '..', 'server.js')], { cwd: dir, env, stdio: 'ignore' });
  t.after(() => { try { child.kill(); } catch { /* ya terminó */ } });

  let ok = false;
  for (let i = 0; i < 50 && !ok; i++) {
    await new Promise((r) => setTimeout(r, 100));
    try { ok = (await (await fetch(`http://127.0.0.1:${port}/healthz`)).text()) === 'ok'; } catch { /* aún no */ }
  }
  assert.ok(ok, 'responde /healthz');
  assert.equal(fs.readFileSync(env.PID_FILE, 'utf8'), String(child.pid));
  assert.match(fs.readFileSync(env.LOG_FILE, 'utf8'), /Cargador SAC escuchando en http:\/\/localhost:/);

  child.kill('SIGTERM');
  await new Promise((r) => child.on('exit', r));
  assert.equal(fs.existsSync(env.PID_FILE), false, 'borra el PID al terminar');
});
