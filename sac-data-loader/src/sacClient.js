'use strict';

// Cliente del Data Import API (y de la lectura de miembros vía Data Export API)
// de SAP Analytics Cloud. Siempre actúa con el token del usuario que inició
// sesión, de modo que SAC aplica sus roles y su Data Access Control.
//
// Referencia: https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/14cac91febef464dbb1efce20e3f1613/fe6efb8aba9444c6a3ce21eef02bba62.html

class SacError extends Error {
  constructor(status, message, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

const FRIENDLY = {
  401: 'La sesión con SAP Analytics Cloud expiró. Inicie sesión nuevamente.',
  403: 'Su usuario no tiene permisos en SAC para esta operación o modelo (rol de planificación o Data Access Control).',
  404: 'SAC no encontró el recurso (modelo o job). Verifique la configuración del modelo en config/templates.json.',
};

class SacClient {
  // state: objeto persistido en la sesión del usuario { csrf, cookies }
  constructor({ tenantUrl, getToken, state, timeoutMs = 120000 }) {
    this.tenant = tenantUrl.replace(/\/+$/, '');
    this.getToken = getToken;
    this.state = state;
    if (!this.state.cookies) this.state.cookies = {};
    this.timeoutMs = timeoutMs;
  }

  importUrl(p) { return `${this.tenant}/api/v1/dataimport${p}`; }
  exportUrl(p) { return `${this.tenant}/api/v1/dataexport${p}`; }

  cookieHeader() {
    const pairs = Object.entries(this.state.cookies).map(([k, v]) => `${k}=${v}`);
    return pairs.length ? pairs.join('; ') : undefined;
  }

  storeCookies(res) {
    const list = typeof res.headers.getSetCookie === 'function' ? res.headers.getSetCookie() : [];
    for (const c of list) {
      const [pair] = c.split(';');
      const i = pair.indexOf('=');
      if (i > 0) this.state.cookies[pair.slice(0, i).trim()] = pair.slice(i + 1).trim();
    }
  }

  async fetchCsrf() {
    const res = await this.raw('GET', this.importUrl('/models'), { headers: { 'x-csrf-token': 'fetch' } });
    const token = res.headers.get('x-csrf-token');
    if (!res.ok || !token) {
      throw new SacError(res.status || 500, 'No fue posible obtener el token CSRF de SAC.');
    }
    this.state.csrf = token;
    return token;
  }

  async raw(method, url, { headers = {}, body } = {}) {
    const token = await this.getToken();
    const h = { Authorization: `Bearer ${token}`, Accept: 'application/json', ...headers };
    const cookie = this.cookieHeader();
    if (cookie) h.Cookie = cookie;
    const res = await fetch(url, {
      method, headers: h, body, redirect: 'manual', signal: AbortSignal.timeout(this.timeoutMs),
    });
    this.storeCookies(res);
    return res;
  }

  // Llamada JSON con manejo de CSRF (un reintento si SAC lo pide nuevamente).
  async call(method, url, { json, csrf = false, allow404 = false } = {}) {
    for (let attempt = 0; attempt < 2; attempt++) {
      const headers = {};
      if (csrf) headers['x-csrf-token'] = this.state.csrf || await this.fetchCsrf();
      let body;
      if (json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json); }

      const res = await this.raw(method, url, { headers, body });
      if (res.status >= 300 && res.status < 400) {
        // SAC redirige al login cuando el token ya no es válido
        throw new SacError(401, FRIENDLY[401]);
      }
      if (csrf && res.status === 403 && /required/i.test(res.headers.get('x-csrf-token') || '') && attempt === 0) {
        this.state.csrf = null;
        continue;
      }
      const text = await res.text();
      let data = null;
      if (text) { try { data = JSON.parse(text); } catch { data = { raw: text }; } }
      if (res.status === 404 && allow404) return null;
      if (!res.ok) {
        const sacMsg = data?.error?.message || data?.message || (typeof data?.raw === 'string' ? data.raw.slice(0, 300) : '');
        const base = FRIENDLY[res.status] || `SAC respondió con error ${res.status}.`;
        throw new SacError(res.status, sacMsg ? `${base} Detalle de SAC: ${sacMsg}` : base, data);
      }
      return data;
    }
    throw new SacError(403, 'SAC rechazó el token CSRF.');
  }

  // ------------------------------------------------------------ modelos
  async listModels() {
    const data = await this.call('GET', this.importUrl('/models'));
    return (data?.models || []).map((m) => ({ id: m.modelID, name: m.modelName, description: m.description || '' }));
  }

  async getMetadata(modelId) {
    return this.call('GET', this.importUrl(`/models/${encodeURIComponent(modelId)}/metadata`));
  }

  // ------------------------------------------------------------ jobs
  async createJob(modelId, importType, body) {
    const data = await this.call('POST', this.importUrl(`/models/${encodeURIComponent(modelId)}/${importType}`), { json: body, csrf: true });
    if (!data?.JobID) throw new SacError(500, 'SAC no devolvió el identificador del job de importación.', data);
    return data.JobID;
  }

  async postData(jobId, rows) {
    return this.call('POST', this.importUrl(`/jobs/${encodeURIComponent(jobId)}`), { json: { Data: rows }, csrf: true });
  }

  async validateJob(jobId) {
    return this.call('POST', this.importUrl(`/jobs/${encodeURIComponent(jobId)}/validate`), { json: {}, csrf: true });
  }

  async invalidRows(jobId) {
    const data = await this.call('GET', this.importUrl(`/jobs/${encodeURIComponent(jobId)}/invalidRows`));
    return data?.failedRows || [];
  }

  async runJob(jobId) {
    return this.call('POST', this.importUrl(`/jobs/${encodeURIComponent(jobId)}/run`), { json: {}, csrf: true });
  }

  async jobStatus(jobId) {
    return this.call('GET', this.importUrl(`/jobs/${encodeURIComponent(jobId)}/status`));
  }

  async deleteJob(jobId) {
    return this.call('DELETE', this.importUrl(`/jobs/${encodeURIComponent(jobId)}`), { csrf: true, allow404: true });
  }

  // ------------------------------------------------------------ miembros (Data Export API)
  // Devuelve un Set con los IDs de la dimensión, o null si SAC no expone ese maestro.
  async getMembers(modelId, dimension, { maxMembers = 500000 } = {}) {
    const base = this.exportUrl(`/providers/sac/${encodeURIComponent(modelId)}/${encodeURIComponent(`${dimension}Master`)}`);
    let url = `${base}?$select=ID`;
    let data = await this.call('GET', url, { allow404: true }).catch((e) => {
      if (e.status === 400) return undefined; // $select no soportado: reintentar sin él
      throw e;
    });
    if (data === undefined) { url = base; data = await this.call('GET', url, { allow404: true }); }
    if (data === null) return null;

    const ids = new Set();
    while (data) {
      for (const row of data.value || []) {
        const id = row.ID ?? row.id ?? row[`${dimension}___ID`];
        if (id !== undefined && id !== null) ids.add(String(id));
      }
      if (ids.size > maxMembers) break;
      const next = data['@odata.nextLink'];
      if (!next) break;
      url = new URL(next, base).toString(); // nextLink puede ser absoluto o relativo al proveedor
      data = await this.call('GET', url);
    }
    return ids;
  }
}

module.exports = { SacClient, SacError };
