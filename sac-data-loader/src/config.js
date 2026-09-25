'use strict';

const fs = require('fs');
const path = require('path');

// Carga la configuración desde variables de entorno (.env) y el catálogo de
// plantillas (config/templates.json). Falla al iniciar si falta algo esencial.

function loadDotEnv(file = path.join(__dirname, '..', '.env')) {
  if (!fs.existsSync(file)) return;
  // Si una variable aparece repetida en el archivo, gana la última línea.
  // Las variables ya definidas en el sistema no se sobrescriben.
  const values = {};
  for (const line of fs.readFileSync(file, 'utf8').replace(/^﻿/, '').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (m) values[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
  for (const [k, v] of Object.entries(values)) {
    if (process.env[k] === undefined) process.env[k] = v;
  }
}

function loadTemplates(file) {
  const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  const defaults = raw.defaults || {};
  const ids = new Set();
  const templates = (raw.templates || []).map((t) => {
    if (!t.id || !t.name) throw new Error(`Plantilla sin "id" o "name" en ${file}`);
    if (ids.has(t.id)) throw new Error(`Plantilla duplicada "${t.id}" en ${file}`);
    ids.add(t.id);
    return {
      importType: 'factData',
      layout: 'auto',
      ...defaults,
      ...t,
      rules: { ...(defaults.rules || {}), ...(t.rules || {}) },
      ignoreColumns: [...(defaults.ignoreColumns || []), ...(t.ignoreColumns || [])],
      contextFields: { ...(defaults.contextFields || {}), ...(t.contextFields || {}) },
      model: t.model || {},
    };
  });
  return templates;
}

function loadConfig(env = process.env) {
  if (env === process.env) loadDotEnv();
  const port = Number(env.PORT || 3000);
  const baseUrl = String(env.APP_BASE_URL || `http://localhost:${port}`).replace(/\/+$/, '');
  const cfg = {
    port,
    baseUrl,
    sac: {
      tenantUrl: String(env.SAC_TENANT_URL || '').replace(/\/+$/, ''),
      authorizeUrl: env.SAC_AUTHORIZE_URL || '',
      tokenUrl: env.SAC_TOKEN_URL || '',
      clientId: env.SAC_CLIENT_ID || '',
      clientSecret: env.SAC_CLIENT_SECRET || '',
      scope: env.SAC_OAUTH_SCOPE || '',
      usePkce: env.SAC_OAUTH_PKCE !== 'false',
    },
    sessionSecret: env.SESSION_SECRET || '',
    cookieSecure: env.COOKIE_SECURE ? env.COOKIE_SECURE === 'true' : baseUrl.startsWith('https://'),
    sessionMinutes: Number(env.SESSION_MINUTES || 60),
    maxFileMb: Number(env.MAX_FILE_MB || 20),
    maxRows: Number(env.MAX_ROWS || 100000),
    chunkSize: Number(env.CHUNK_SIZE || 10000),
    numberLocale: env.NUMBER_LOCALE === 'en' ? 'en' : 'es',
    blockedVersions: String(env.BLOCKED_VERSIONS ?? 'public.Actual').split(',').map((s) => s.trim()).filter(Boolean),
    validateMembers: env.VALIDATE_MEMBERS !== 'false',
    trustProxy: env.TRUST_PROXY === 'true',
    auditFile: env.AUDIT_FILE || path.join(__dirname, '..', 'logs', 'audit.log'),
    templatesFile: env.TEMPLATES_FILE || path.join(__dirname, '..', 'config', 'templates.json'),
  };

  const missing = [];
  for (const [k, v] of Object.entries({
    SAC_TENANT_URL: cfg.sac.tenantUrl, SAC_AUTHORIZE_URL: cfg.sac.authorizeUrl, SAC_TOKEN_URL: cfg.sac.tokenUrl,
    SAC_CLIENT_ID: cfg.sac.clientId, SAC_CLIENT_SECRET: cfg.sac.clientSecret, SESSION_SECRET: cfg.sessionSecret,
  })) if (!v || /[<>]/.test(v)) missing.push(k); // "<...>" = texto de ejemplo sin reemplazar
  if (missing.length) {
    throw new Error(`Faltan variables de configuración (vacías o con el texto de ejemplo <...>): ${missing.join(', ')}. Complételas en el archivo .env y guárdelo.`);
  }
  if (cfg.sessionSecret.length < 32) throw new Error('SESSION_SECRET debe tener al menos 32 caracteres aleatorios.');

  cfg.templates = loadTemplates(cfg.templatesFile);
  return cfg;
}

module.exports = { loadConfig, loadTemplates, loadDotEnv };
