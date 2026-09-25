'use strict';

const crypto = require('crypto');

// OAuth 2.0 Authorization Code Grant (3-legged) contra el servidor de
// autorización de SAC. Cada usuario inicia sesión en la página de login de SAC
// (o del IdP corporativo) con SUS credenciales; esta aplicación nunca ve la
// contraseña. El token resultante lleva el contexto del usuario, por lo que SAC
// aplica sus roles y su Data Access Control en cada carga.
//
// En SAC: Sistema > Administración > App Integration > Add a New OAuth Client
//   Purpose: Interactive Usage  |  Redirect URI: <APP_BASE_URL>/auth/callback

const b64url = (buf) => buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

function randomToken(bytes = 32) { return b64url(crypto.randomBytes(bytes)); }

function pkcePair() {
  const verifier = randomToken(48);
  const challenge = b64url(crypto.createHash('sha256').update(verifier).digest());
  return { verifier, challenge };
}

function redirectUri(cfg) { return `${cfg.baseUrl}/auth/callback`; }

function buildAuthorizeUrl(cfg, { state, codeChallenge }) {
  const u = new URL(cfg.sac.authorizeUrl);
  u.searchParams.set('response_type', 'code');
  u.searchParams.set('client_id', cfg.sac.clientId);
  u.searchParams.set('redirect_uri', redirectUri(cfg));
  u.searchParams.set('state', state);
  if (cfg.sac.scope) u.searchParams.set('scope', cfg.sac.scope);
  if (codeChallenge) {
    u.searchParams.set('code_challenge', codeChallenge);
    u.searchParams.set('code_challenge_method', 'S256');
  }
  return u.toString();
}

async function tokenRequest(cfg, params) {
  const body = new URLSearchParams({ client_id: cfg.sac.clientId, ...params });
  const basic = Buffer.from(`${cfg.sac.clientId}:${cfg.sac.clientSecret}`).toString('base64');
  const res = await fetch(cfg.sac.tokenUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json', Authorization: `Basic ${basic}` },
    body,
    signal: AbortSignal.timeout(30000),
  });
  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch { /* respuesta no JSON */ }
  if (!res.ok || !data.access_token) {
    const detail = data.error_description || data.error || text.slice(0, 200);
    const err = new Error(`El servidor de autorización de SAC rechazó la solicitud de token (${res.status}): ${detail}`);
    err.status = res.status;
    throw err;
  }
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token || null,
    expiresAt: Date.now() + (Number(data.expires_in) || 3600) * 1000,
    idToken: data.id_token || null,
  };
}

function exchangeCode(cfg, { code, codeVerifier }) {
  const params = { grant_type: 'authorization_code', code, redirect_uri: redirectUri(cfg) };
  if (codeVerifier) params.code_verifier = codeVerifier;
  return tokenRequest(cfg, params);
}

function refresh(cfg, refreshToken) {
  return tokenRequest(cfg, { grant_type: 'refresh_token', refresh_token: refreshToken });
}

// Lee (sin verificar firma) las claims del JWT sólo para mostrar quién está
// conectado y registrar la auditoría. La autorización real la hace SAC al
// validar el token en cada llamada.
function decodeJwt(token) {
  try {
    const part = String(token).split('.')[1];
    return JSON.parse(Buffer.from(part.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8'));
  } catch {
    return null;
  }
}

function userFromTokens(tokens) {
  const c = decodeJwt(tokens.idToken) || decodeJwt(tokens.accessToken) || {};
  const id = c.user_name || c.email || c.sub || c.user_id || 'usuario-sac';
  const name = [c.given_name, c.family_name].filter(Boolean).join(' ') || c.name || id;
  return { id: String(id), name: String(name), email: c.email || null };
}

module.exports = { pkcePair, randomToken, buildAuthorizeUrl, exchangeCode, refresh, userFromTokens, redirectUri };
