#!/usr/bin/env node
'use strict';

// Construye el instalador .exe (Windows x64) de una marca, con todo incluido:
// la aplicación y sus librerías, Node.js portátil y los scripts de instalación.
// El usuario no necesita internet para instalar (sólo para usar SAC).
//
//   node deploy/windows-usuario/build-exe.js fanalca
//   node deploy/windows-usuario/build-exe.js ciudadlimpia
//   node deploy/windows-usuario/build-exe.js fanalca --producto probador   (Probador de data actions)
//
// Requisitos (en el equipo que construye, Linux, macOS o Windows): Node.js 20+,
// npm, Go 1.22+ y acceso a nodejs.org, registry.npmjs.org y proxy.golang.org.
//
// Resultado en dist/:
//   Instalar-CargadorSAC-<Marca>.exe        instalador de un solo archivo
//   CargadorSAC-<Marca>-Instalador-completo.zip   el mismo contenido en ZIP
//
// Opcional: --liviano no incluye Node.js (unos 35 MB menos): el instalador lo
// descarga de nodejs.org o usa el Node.js 20+ que ya tenga el equipo. Resultado:
//   Instalar-CargadorSAC-<Marca>-liviano.exe
//
// Opcional: --config-empresa <ruta .env> incluye los datos del cliente OAuth de
// SAC para que el usuario no tenga que escribirlos. Lleva el Secret: comparta el
// resultado sólo con usuarios autorizados.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..', '..');
const EXE_DIR = path.join(__dirname, 'exe');
const DIST = path.join(ROOT, 'dist');
const CACHE = path.join(DIST, '.cache');
const NODE_MAJOR = process.env.NODE_MAJOR || '22';
const RSRC = 'github.com/akavel/rsrc@v0.10.2';
const PERMITIDAS = ['SAC_TENANT_URL', 'SAC_AUTHORIZE_URL', 'SAC_TOKEN_URL', 'SAC_CLIENT_ID', 'SAC_CLIENT_SECRET', 'SAC_OAUTH_SCOPE',
  'SAC_OAUTH_PKCE', 'MAX_FILE_MB', 'MAX_ROWS', 'CHUNK_SIZE', 'NUMBER_LOCALE', 'BLOCKED_VERSIONS', 'VALIDATE_MEMBERS'];

const args = process.argv.slice(2);
const marca = (args.find((a, i) => !a.startsWith('--') && args[i - 1] !== '--producto' && args[i - 1] !== '--config-empresa') || 'fanalca').toLowerCase();
const iCfg = args.indexOf('--config-empresa');
const configEmpresa = iCfg >= 0 ? args[iCfg + 1] : null;
const liviano = args.includes('--liviano');
const iProd = args.indexOf('--producto');
const producto = iProd >= 0 ? String(args[iProd + 1] || '').toLowerCase() : 'cargador';
const QUE_HACE = {
  cargador: 'Instala en su computador la aplicación para validar y cargar archivos de Excel o\r\nCSV a los modelos de planeación de SAP Analytics Cloud. Entra con SU usuario de\r\nSAC: cada carga se hace con sus propios permisos.',
  probador: 'Instala en su computador el Probador de data actions: genera datos aleatorios en\r\nuna versión de pruebas, ejecuta el data action (multi action) y compara el\r\nresultado de SAC con el valor esperado. Entra con SU usuario de SAC.',
};

const log = (m) => console.log(`» ${m}`);
const run = (cmd, a, opts = {}) => execFileSync(cmd, a, { stdio: 'inherit', ...opts });

async function download(url, file) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  fs.writeFileSync(file, Buffer.from(await res.arrayBuffer()));
}

async function nodeZip() {
  const index = await (await fetch('https://nodejs.org/dist/index.json')).json();
  const lts = index.find((v) => v.version.startsWith(`v${NODE_MAJOR}.`) && v.lts);
  if (!lts) throw new Error(`No hay versión LTS de Node.js ${NODE_MAJOR}.`);
  const name = `node-${lts.version}-win-x64.zip`;
  const file = path.join(CACHE, name);
  const sums = await (await fetch(`https://nodejs.org/dist/${lts.version}/SHASUMS256.txt`)).text();
  const expected = sums.split('\n').find((l) => l.trim().endsWith(` ${name}`))?.split(/\s+/)[0];
  if (!expected) throw new Error(`Sin SHA-256 para ${name}.`);
  const sha = (f) => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
  if (!fs.existsSync(file) || sha(file) !== expected) {
    log(`Descargando ${name}...`);
    await download(`https://nodejs.org/dist/${lts.version}/${name}`, file);
    if (sha(file) !== expected) throw new Error(`${name}: el SHA-256 no coincide.`);
  }
  log(`Node.js ${lts.version} verificado (SHA-256)`);
  return { file, name };
}

function copy(src, dst) {
  fs.cpSync(src, dst, { recursive: true, filter: (s) => !/[\\/](node_modules|logs|\.env)$/.test(s) });
}

async function zipDir(dir, out) {
  const JSZip = require(path.join(ROOT, 'node_modules', 'jszip'));
  const zip = new JSZip();
  const walk = (abs, rel) => {
    for (const e of fs.readdirSync(abs, { withFileTypes: true })) {
      const a = path.join(abs, e.name);
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) walk(a, r);
      else zip.file(r, fs.readFileSync(a), { compression: /\.zip$/i.test(e.name) ? 'STORE' : 'DEFLATE', compressionOptions: { level: 9 } });
    }
  };
  walk(dir, '');
  const buf = await zip.generateAsync({ type: 'nodebuffer', platform: 'DOS' });
  fs.writeFileSync(out, buf);
}

(async () => {
  const brandFile = path.join(ROOT, 'brands', marca, 'brand.json');
  if (!/^[a-z0-9-]+$/.test(marca) || !fs.existsSync(brandFile)) throw new Error(`La marca "${marca}" no existe (carpeta brands).`);
  const brand = JSON.parse(fs.readFileSync(brandFile, 'utf8'));
  const prod = brand.installer?.[producto];
  if (!prod) throw new Error(`Producto "${producto}" no válido: use --producto cargador o --producto probador.`);
  const nombre = brand.name.replace(/[^A-Za-z0-9]+/g, '');
  fs.mkdirSync(CACHE, { recursive: true });

  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'cargador-exe-'));
  const pkg = path.join(tmp, 'CargadorSAC-Instalador');
  const app = path.join(pkg, 'app');
  const ins = path.join(pkg, 'instalador');
  fs.mkdirSync(app, { recursive: true });
  fs.mkdirSync(ins, { recursive: true });
  try {
    log(`Marca: ${brand.name} · producto: ${producto}`);
    for (const f of ['server.js', 'package.json', 'package-lock.json', 'README.md', '.env.example']) fs.copyFileSync(path.join(ROOT, f), path.join(app, f));
    for (const d of ['src', 'public', 'config', 'brands', 'samples']) copy(path.join(ROOT, d), path.join(app, d));

    log('Instalando librerías de la aplicación (npm ci --omit=dev)...');
    run(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['ci', '--omit=dev', '--ignore-scripts', '--no-audit', '--no-fund', '--loglevel=error'], { cwd: app, shell: process.platform === 'win32' });

    if (!liviano) {
      const node = await nodeZip();
      fs.copyFileSync(node.file, path.join(ins, node.name));
    }

    for (const f of ['Instalar-CargadorSAC-Usuario.ps1', 'Abrir-CargadorSAC.cmd', 'Detener-CargadorSAC.cmd', 'Desinstalar-CargadorSAC.cmd']) {
      fs.copyFileSync(path.join(__dirname, f), path.join(ins, f));
    }
    fs.writeFileSync(path.join(ins, 'marca.txt'), marca);
    fs.writeFileSync(path.join(ins, 'producto.txt'), producto);
    fs.copyFileSync(path.join(__dirname, 'Instalar.cmd'), path.join(pkg, 'Instalar.cmd'));
    const leame = fs.readFileSync(path.join(__dirname, 'LEAME.txt'), 'utf8')
      .replaceAll('{{TITULO}}', prod.shortcut.toUpperCase()).replaceAll('{{QUE_HACE}}', QUE_HACE[producto])
      .replaceAll('{{CARPETA}}', prod.folder).replaceAll('{{ACCESO}}', prod.shortcut).replaceAll('{{PUERTO}}', String(prod.port));
    fs.writeFileSync(path.join(pkg, 'LEAME.txt'), leame);

    if (configEmpresa) {
      const valores = {};
      for (const l of fs.readFileSync(configEmpresa, 'utf8').replace(/^﻿/, '').split(/\r?\n/)) {
        const m = l.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
        if (m && PERMITIDAS.includes(m[1])) valores[m[1]] = m[2];
      }
      for (const k of PERMITIDAS.slice(0, 5)) if (!valores[k] || /[<>]/.test(valores[k])) throw new Error(`${configEmpresa}: falta un valor válido para ${k}.`);
      const lineas = ['# Datos de SAC para el Cargador de datos a SAC. CONFIDENCIAL: contiene el Secret del cliente OAuth.',
        ...Object.entries(valores).map(([k, v]) => `${k}=${v}`)];
      fs.writeFileSync(path.join(pkg, 'config-empresa.env'), `${lineas.join('\r\n')}\r\n`);
      log('Se incluyó config-empresa.env: comparta el instalador sólo con usuarios autorizados.');
    }

    log('Comprimiendo el paquete...');
    const payload = path.join(EXE_DIR, 'payload.zip');
    await zipDir(tmp, payload);

    log('Ícono y manifiesto (sin permisos de administrador)...');
    const syso = path.join(EXE_DIR, 'rsrc_windows_amd64.syso');
    run('go', ['run', RSRC, '-manifest', 'instalador.manifest', '-ico', path.join(ROOT, 'brands', marca, 'icon.ico'), '-arch', 'amd64', '-o', syso], { cwd: EXE_DIR });

    log('Compilando el .exe...');
    fs.mkdirSync(DIST, { recursive: true });
    const sufijo = liviano ? '-liviano' : '';
    const base = producto === 'probador' ? 'ProbadorDA' : 'CargadorSAC';
    const exe = path.join(DIST, `Instalar-${base}-${nombre}${sufijo}.exe`);
    run('go', ['build', '-trimpath', '-ldflags', '-s -w', '-o', exe, '.'], {
      cwd: EXE_DIR, env: { ...process.env, GOOS: 'windows', GOARCH: 'amd64', CGO_ENABLED: '0' },
    });
    const zipOut = path.join(DIST, `${base}-${nombre}-Instalador${liviano ? '-liviano' : '-completo'}.zip`);
    fs.copyFileSync(payload, zipOut);
    fs.rmSync(payload);
    fs.rmSync(syso);

    const mb = (f) => `${(fs.statSync(f).size / 1048576).toFixed(1)} MB`;
    log(`Listo:\n   ${exe} (${mb(exe)})\n   ${zipOut} (${mb(zipOut)})`);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
})().catch((e) => { console.error(`ERROR: ${e.message}`); process.exit(1); });
