'use strict';

// Probador de data actions (aplicación independiente del cargador).
// El caso de prueba (objeto JSON) es la fuente de verdad: los formularios de los
// pasos 1 y 2 y el editor JSON del paso 3 se mantienen sincronizados.
// Todo texto que viene de SAC o del caso se pinta con textContent (nunca innerHTML).

(() => {
  const $ = (id) => document.getElementById(id);
  const fmt = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 6 });
  const fmt2 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 });
  const STORE_KEY = 'probador-da:caso';
  const TIPOS = {
    version: 'Versión (la versión de pruebas)',
    periodos: 'Periodos (los periodos elegidos)',
    miembro: 'Miembro(s) de una dimensión',
    numero: 'Número',
  };
  const state = {
    case: null, catalog: [], plantilla: null, models: [], model: null, members: new Map(),
    runId: null, timer: null, lastReport: null, me: null,
  };

  const DEFAULT_TEMPLATE = {
    id: 'MI_PRUEBA',
    nombre: 'Mi prueba de data action',
    modelo: '',
    multiAction: '',
    version: 'public.PRUEBAS',
    periodos: { desde: '202601', hasta: '202603' },
    comun: {},
    parametros: [{ id: 'TargetVersion', tipo: 'version' }],
    entradas: [
      { nombre: 'PRECIO', fijo: { '<Dimensión cuenta>': '<cuenta precio>' }, min: 1000, max: 50000, decimales: 0 },
      { nombre: 'CANTIDAD', fijo: { '<Dimensión cuenta>': '<cuenta cantidad>' }, min: 1, max: 500, decimales: 2 },
    ],
    esperado: [
      { nombre: 'INGRESO', fijo: { '<Dimensión cuenta>': '<cuenta resultado>' }, formula: "v('PRECIO') * v('CANTIDAD')" },
    ],
    tolerancia: 0.01,
  };

  // ---------------------------------------------------------------- utilidades
  async function api(url, { method = 'GET', body } = {}) {
    const opts = { method, credentials: 'same-origin', headers: { Accept: 'application/json' } };
    if (method !== 'GET') opts.headers['X-Requested-With'] = 'sac-loader';
    if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    const res = await fetch(url, opts);
    let data = {};
    try { data = await res.json(); } catch { /* sin cuerpo */ }
    if (res.status === 401) { showLogin('Su sesión expiró. Inicie sesión nuevamente.'); throw new Error(data.error || 'Sesión expirada'); }
    if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
    return data;
  }
  function el(tag, text, cls) {
    const e = document.createElement(tag);
    if (text !== undefined && text !== null) e.textContent = String(text);
    if (cls) e.className = cls;
    return e;
  }
  function option(value, label, { disabled = false } = {}) {
    const o = el('option', label); o.value = value; o.disabled = disabled; return o;
  }
  function toast(msg, ms = 4000) {
    const t = $('toast');
    t.textContent = msg; t.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => { t.hidden = true; }, ms);
  }
  function busy(btn, on, label) {
    if (on) { btn.dataset.label = btn.textContent; btn.textContent = label; btn.disabled = true; }
    else { btn.textContent = btn.dataset.label || btn.textContent; btn.disabled = false; }
  }
  const secs = (ms) => (ms === null || ms === undefined ? '' : `${fmt2.format(ms / 1000)} s`);
  const num = (n) => (typeof n === 'number' ? fmt.format(n) : '—');
  const randomSeed = () => Math.floor(Math.random() * 999999) + 1;
  const toMonth = (p) => (/^\d{6}$/.test(String(p || '')) ? `${String(p).slice(0, 4)}-${String(p).slice(4)}` : '');
  const fromMonth = (m) => String(m || '').replace('-', '');

  function showLogin(error) {
    $('appView').hidden = true; $('userBox').hidden = true; $('loginView').hidden = false;
    if (error) { $('loginError').textContent = error; $('loginError').hidden = false; }
  }
  function showError(msg) {
    const e = $('caseError');
    e.textContent = msg; e.hidden = !msg;
    if (msg) e.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // ---------------------------------------------------------------- caso <-> JSON
  function writeJson() {
    $('caseJson').value = JSON.stringify(state.case, null, 2);
    $('jsonState').textContent = 'JSON válido.'; $('jsonState').className = 'hint ok-text';
    persist();
  }
  function persist() {
    try { localStorage.setItem(STORE_KEY, $('caseJson').value); } catch { /* sin almacenamiento */ }
  }
  function setCase(obj) {
    state.case = structuredClone(obj);
    if (!Array.isArray(state.case.parametros)) state.case.parametros = [];
    writeJson();
    renderForm();
  }
  function update(fn) {
    fn(state.case);
    writeJson();
    updateConfirm();
  }

  $('caseJson').addEventListener('input', () => {
    try {
      const c = JSON.parse($('caseJson').value);
      if (!c || typeof c !== 'object' || Array.isArray(c)) throw new Error('debe ser un objeto { ... }');
      state.case = c;
      if (!Array.isArray(state.case.parametros)) state.case.parametros = [];
      $('jsonState').textContent = 'JSON válido.'; $('jsonState').className = 'hint ok-text';
      clearTimeout(state.jsonTimer);
      state.jsonTimer = setTimeout(renderForm, 400);
    } catch (e) {
      $('jsonState').textContent = `JSON no válido: ${e.message}`; $('jsonState').className = 'hint err-text';
    }
    persist();
  });
  $('caseJson').addEventListener('keydown', (ev) => {
    if (ev.key === 'Tab') { // tabulación de 2 espacios dentro del editor
      ev.preventDefault();
      const t = ev.target; const { selectionStart: a, selectionEnd: b } = t;
      t.value = `${t.value.slice(0, a)}  ${t.value.slice(b)}`;
      t.selectionStart = t.selectionEnd = a + 2;
      t.dispatchEvent(new Event('input'));
    }
  });

  // ---------------------------------------------------------------- paso 1: formulario
  function renderForm() {
    const c = state.case;
    $('fNombre').value = c.nombre || '';
    $('fMultiAction').value = c.multiAction || '';
    $('fTolerancia').value = c.tolerancia ?? 0.01;
    renderPeriods();
    renderModelSelect();
    loadModel(c.modelo).then(() => { renderVersionSelect(); renderParams(); });
    renderParams();
    updateConfirm();
  }

  function renderPeriods() {
    const p = state.case.periodos;
    let desde = ''; let hasta = '';
    if (Array.isArray(p) && p.length) { const s = [...p].map(String).sort(); desde = s[0]; hasta = s[s.length - 1]; }
    else if (p && typeof p === 'object') { desde = p.desde; hasta = p.hasta; }
    $('fDesde').value = toMonth(desde); $('fHasta').value = toMonth(hasta);
    $('periodHint').textContent = Array.isArray(p) ? `El caso usa los periodos ${p.join(', ')}; al cambiar las fechas se usará el rango completo.` : '';
  }

  function renderModelSelect() {
    const sel = $('fModelo');
    const cur = state.case.modelo || '';
    const opts = [option('', state.models.length ? 'Seleccione el modelo…' : 'Cargando modelos…')];
    let found = false;
    for (const m of state.models) { opts.push(option(m.id, `${m.name} (${m.id})`)); if (m.id === cur) found = true; }
    if (cur && !found) opts.push(option(cur, `${cur} (no aparece en su lista de modelos)`));
    sel.replaceChildren(...opts);
    sel.value = cur;
  }

  async function loadModel(id) {
    if (!id) { state.model = null; $('modelHint').textContent = ''; return; }
    if (state.model?.id === id) return;
    $('modelHint').textContent = 'Leyendo la estructura del modelo…';
    try {
      const info = await api(`/api/tests/model?modelo=${encodeURIComponent(id)}`);
      state.model = { id, ...info };
      $('modelHint').textContent = `Dimensiones: ${info.dimensions.join(', ')}`;
    } catch (e) {
      state.model = { id, dimensions: [], versions: null };
      $('modelHint').textContent = `No se pudo leer el modelo: ${e.message}`;
    }
  }

  function renderVersionSelect() {
    const sel = $('fVersion');
    const cur = state.case.version || '';
    const list = state.model?.versions;
    const opts = [];
    let found = false;
    if (list) {
      for (const v of list) {
        opts.push(option(v.id, v.blocked ? `${v.id} (bloqueada)` : v.id, { disabled: v.blocked }));
        if (v.id === cur) found = true;
      }
    }
    if (cur && !found) opts.unshift(option(cur, list ? `${cur} (no existe en el modelo)` : cur));
    if (!opts.length) opts.push(option('', state.case.modelo ? 'Sin versiones' : 'Seleccione primero el modelo'));
    sel.replaceChildren(...opts);
    sel.value = cur;
  }

  $('fNombre').addEventListener('input', () => update((c) => { c.nombre = $('fNombre').value; }));
  $('fMultiAction').addEventListener('input', () => update((c) => { c.multiAction = $('fMultiAction').value.trim(); }));
  $('fTolerancia').addEventListener('input', () => update((c) => { const v = Number($('fTolerancia').value); if (Number.isFinite(v)) c.tolerancia = v; }));
  $('fVersion').addEventListener('change', () => update((c) => { c.version = $('fVersion').value; }));
  for (const id of ['fDesde', 'fHasta']) {
    $(id).addEventListener('change', () => update((c) => {
      const d = fromMonth($('fDesde').value); const h = fromMonth($('fHasta').value);
      if (d && h) { c.periodos = { desde: d, hasta: h }; $('periodHint').textContent = ''; }
    }));
  }
  $('fModelo').addEventListener('change', async () => {
    const id = $('fModelo').value;
    update((c) => { c.modelo = id; });
    state.model = null;
    await loadModel(id);
    renderVersionSelect();
    renderParams();
  });

  // ---------------------------------------------------------------- paso 2: parámetros
  async function membersOf(dim) {
    const key = `${state.case.modelo}|${dim}`;
    if (!state.members.has(key)) {
      state.members.set(key, api(`/api/tests/members?modelo=${encodeURIComponent(state.case.modelo)}&dim=${encodeURIComponent(dim)}`)
        .then((r) => r.members).catch((e) => { state.members.delete(key); throw e; }));
    }
    return state.members.get(key);
  }

  function renderParams() {
    const list = $('paramsList');
    const params = state.case.parametros || [];
    if (!params.length) {
      list.replaceChildren(el('p', 'Este data action no tiene parámetros configurados.', 'hint'));
      return;
    }
    list.replaceChildren(...params.map((p, i) => paramRow(p, i)));
  }

  function paramRow(p, i) {
    const row = el('div', null, 'param');
    if (p.parameterId !== undefined) { // formato de la API de SAP: sólo lectura aquí
      row.append(el('div', `${p.parameterId}`, 'param-id'), el('code', JSON.stringify(p.value)), el('small', 'Formato de la API de SAP: edítelo en el JSON del paso 3.', 'hint'));
      return row;
    }
    const head = el('div', null, 'param-head');
    const idIn = el('input'); idIn.type = 'text'; idIn.value = p.id || ''; idIn.placeholder = 'ID del parámetro'; idIn.setAttribute('aria-label', 'ID del parámetro');
    idIn.addEventListener('input', () => update((c) => { c.parametros[i].id = idIn.value.trim(); }));
    const tipo = el('select'); tipo.setAttribute('aria-label', 'Tipo');
    for (const [k, label] of Object.entries(TIPOS)) tipo.append(option(k, label));
    tipo.value = TIPOS[p.tipo] ? p.tipo : 'miembro';
    tipo.addEventListener('change', () => {
      update((c) => {
        const q = { id: c.parametros[i].id, tipo: tipo.value };
        if (tipo.value === 'miembro') { q.dimension = state.model?.dimensions?.[0] || ''; q.valor = []; }
        if (tipo.value === 'numero') q.valor = 0;
        c.parametros[i] = q;
      });
      renderParams();
    });
    const del = el('button', '✕', 'btn ghost small'); del.type = 'button'; del.title = 'Quitar parámetro';
    del.addEventListener('click', () => { update((c) => { c.parametros.splice(i, 1); }); renderParams(); });
    head.append(idIn, tipo, del);
    row.append(head);

    const body = el('div', null, 'param-body');
    if (p.tipo === 'version') body.append(el('span', `Se envía la versión de pruebas: ${state.case.version || '—'}`, 'hint'));
    else if (p.tipo === 'periodos') body.append(el('span', 'Se envían los periodos elegidos en el paso 1.', 'hint'));
    else if (p.tipo === 'numero') {
      const n = el('input'); n.type = 'number'; n.step = 'any'; n.value = p.valor ?? ''; n.setAttribute('aria-label', 'Valor');
      n.addEventListener('input', () => update((c) => { c.parametros[i].valor = n.value === '' ? '' : Number(n.value); }));
      body.append(n);
    } else memberPicker(body, p, i);
    row.append(body);
    return row;
  }

  function memberPicker(body, p, i) {
    const dims = state.model?.dimensions || [];
    const dimSel = el('select'); dimSel.setAttribute('aria-label', 'Dimensión');
    dimSel.append(option('', 'Dimensión…'));
    for (const d of dims) dimSel.append(option(d, d));
    if (p.dimension && !dims.includes(p.dimension)) dimSel.append(option(p.dimension, `${p.dimension} (no existe)`));
    dimSel.value = p.dimension || '';
    dimSel.addEventListener('change', () => { update((c) => { c.parametros[i].dimension = dimSel.value; c.parametros[i].valor = []; }); renderParams(); });

    const multi = el('label', null, 'check');
    const mcb = el('input'); mcb.type = 'checkbox'; mcb.checked = p.multiple !== false;
    mcb.addEventListener('change', () => update((c) => { c.parametros[i].multiple = mcb.checked; }));
    multi.append(mcb, document.createTextNode(' Varios miembros'));

    const chosen = el('div', null, 'chips');
    const valor = Array.isArray(p.valor) ? p.valor : (p.valor ? [p.valor] : []);
    const drawChips = () => {
      const cur = state.case.parametros[i].valor || [];
      chosen.replaceChildren(...(cur.length ? cur.map((m) => {
        const chip = el('span', null, 'chip');
        chip.append(el('span', m));
        const x = el('button', '×'); x.type = 'button'; x.title = `Quitar ${m}`;
        x.addEventListener('click', () => { update((c) => { c.parametros[i].valor = (c.parametros[i].valor || []).filter((v) => v !== m); }); drawChips(); });
        chip.append(x);
        return chip;
      }) : [el('span', 'Sin miembros elegidos', 'hint err-text')]));
    };
    if (!Array.isArray(state.case.parametros[i].valor)) state.case.parametros[i].valor = valor;
    drawChips();

    const filter = el('input'); filter.type = 'search'; filter.placeholder = 'Buscar miembro por código o descripción…';
    const list = el('select'); list.multiple = true; list.size = 6; list.setAttribute('aria-label', 'Miembros');
    const add = el('button', 'Agregar seleccionados', 'btn ghost small'); add.type = 'button';
    const note = el('small', '', 'hint');
    let all = [];
    const draw = () => {
      const q = filter.value.trim().toLowerCase();
      const shown = (q ? all.filter((m) => m.id.toLowerCase().includes(q) || m.description.toLowerCase().includes(q)) : all).slice(0, 500);
      list.replaceChildren(...shown.map((m) => option(m.id, m.description && m.description !== m.id ? `${m.id} · ${m.description}` : m.id)));
      note.textContent = `${shown.length} de ${all.length} miembro(s)${shown.length === 500 ? ' (refine la búsqueda)' : ''}`;
    };
    filter.addEventListener('input', draw);
    const addSelected = () => {
      const picked = [...list.selectedOptions].map((o) => o.value);
      if (!picked.length) return;
      update((c) => {
        const q = c.parametros[i];
        const cur = Array.isArray(q.valor) ? q.valor : [];
        q.valor = q.multiple === false ? [picked[0]] : [...new Set([...cur, ...picked])];
      });
      drawChips();
    };
    add.addEventListener('click', addSelected);
    list.addEventListener('dblclick', addSelected);

    const top = el('div', null, 'param-line');
    top.append(dimSel, multi);
    body.append(top, chosen);
    if (p.dimension && state.case.modelo) {
      const box = el('div', null, 'picker');
      box.append(filter, list, el('div', null, 'param-line'));
      box.lastChild.append(add, note);
      body.append(box);
      note.textContent = 'Cargando miembros…';
      membersOf(p.dimension).then((m) => { all = m; draw(); }).catch((e) => { note.textContent = e.message; note.className = 'hint err-text'; });
    } else body.append(el('small', 'Elija el modelo y la dimensión para ver sus miembros.', 'hint'));
  }

  $('addParamBtn').addEventListener('click', () => {
    update((c) => { c.parametros.push({ id: `Parametro${c.parametros.length + 1}`, tipo: 'miembro', dimension: state.model?.dimensions?.[0] || '', valor: [] }); });
    renderParams();
  });

  // ---------------------------------------------------------------- catálogo y archivos
  $('catalogSel').addEventListener('change', () => {
    const c = state.catalog.find((x) => x.id === $('catalogSel').value);
    $('catalogDesc').textContent = c?.descripcion || '';
    if (c) setCase(c);
  });
  $('newBtn').addEventListener('click', () => {
    const base = structuredClone(state.plantilla || DEFAULT_TEMPLATE);
    if (!base.modelo && state.case?.modelo) base.modelo = state.case.modelo;
    setCase(base);
    $('catalogSel').value = ''; $('catalogDesc').textContent = '';
  });
  $('openFile').addEventListener('change', async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    try {
      const obj = JSON.parse(await f.text());
      setCase(obj); toast(`Caso "${obj.nombre || obj.id || f.name}" abierto.`);
    } catch (e) { showError(`El archivo no es un JSON válido: ${e.message}`); }
    ev.target.value = '';
  });
  $('saveBtn').addEventListener('click', () => {
    const blob = new Blob([`${JSON.stringify(state.case, null, 2)}\n`], { type: 'application/json' });
    const a = el('a'); a.href = URL.createObjectURL(blob); a.download = `${state.case.id || 'caso'}.json`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
  $('seedBtn').addEventListener('click', () => { $('seed').value = randomSeed(); });

  function updateConfirm() {
    const v = state.case?.version || 'elegida';
    $('confirmText').textContent = `Confirmo que la versión ${v} es de pruebas: antes de cargar se borrarán sus datos en los periodos elegidos.`;
    $('confirmVersion').checked = false;
  }

  // ---------------------------------------------------------------- ejecución
  const ICON = { pending: '○', running: '◐', ok: '✔', error: '✖', skipped: '–' };
  function renderSteps(report, info) {
    $('runCard').hidden = false;
    $('runInfo').textContent = info || '';
    $('stepsList').replaceChildren(...report.steps.map((s) => {
      const li = el('li', null, `step ${s.status}`);
      li.append(el('span', ICON[s.status] || '○', 'step-icon'), el('span', s.label, 'step-label'));
      li.append(el('span', s.ms !== null ? secs(s.ms) : '', 'step-time'));
      if (s.detail) li.append(el('small', s.detail, 'step-detail'));
      return li;
    }));
  }

  function renderResult(report, all = [report]) {
    state.lastReport = report;
    $('resultCard').hidden = false;
    const b = $('resultBanner');
    const s = report.summary;
    if (report.state === 'PREVIEW') {
      b.className = 'alert ok';
      b.textContent = `Vista previa: ${report.inputs?.count ?? 0} celda(s) de entrada y ${report.expectedCount ?? 0} celda(s) esperada(s). No se escribió nada en SAC.`;
    } else if (report.state === 'PASSED') {
      b.className = 'alert ok';
      b.textContent = `✔ La prueba pasó: ${s.passed} de ${s.cells} celda(s) coinciden con lo esperado.`;
    } else if (report.state === 'FAILED') {
      b.className = 'alert error';
      b.textContent = `✖ La prueba falló: ${s.failed} de ${s.cells} celda(s) no coinciden (diferencia máxima ${num(s.maxDiff)}).`;
    } else {
      b.className = 'alert error';
      b.textContent = `✖ No se pudo completar la prueba: ${report.error || 'error desconocido'}`;
    }

    const facts = [
      ['Prueba', report.case?.nombre || report.case?.id || '—'],
      ['Versión', report.case?.version || '—'],
      ['Periodos', report.case?.periodos ? `${report.case.periodos[0]} – ${report.case.periodos[report.case.periodos.length - 1]}` : '—'],
      ['Semilla', report.seed],
      ['Tiempo total', secs(report.ms)],
      ['Celdas de entrada', report.inputs?.count ?? '—'],
    ];
    if (s) facts.push(['Celdas verificadas', s.cells], ['Con diferencia', s.failed], ['Diferencia máxima', num(s.maxDiff)], ['Sin dato en SAC', s.missing], ['Celdas adicionales', s.extra]);
    if (report.multiAction) facts.push(['Multi action', report.multiAction.status || '—']);
    $('facts').replaceChildren(...facts.map(([k, v]) => { const d = el('div'); d.append(el('dt', k), el('dd', v)); return d; }));

    const reps = all.filter(Boolean);
    $('repsWrap').hidden = reps.length < 2;
    $('repsTable').tBodies[0].replaceChildren(...reps.map((r, i) => {
      const tr = el('tr', null, r.state === 'PASSED' ? '' : 'sev-error');
      tr.append(el('td', i + 1), el('td', r.seed), el('td', { PASSED: 'Pasó', FAILED: 'Falló', ERROR: 'Error', RUNNING: 'En curso' }[r.state] || r.state),
        el('td', r.summary?.cells ?? '—', 'num'), el('td', r.summary?.failed ?? '—', 'num'), el('td', secs(r.ms), 'num'));
      return tr;
    }));

    $('paramsSent').hidden = !report.parameterValues;
    $('paramsSentPre').textContent = report.parameterValues ? JSON.stringify({ parameterValues: report.parameterValues }, null, 2) : '';

    const msgs = report.multiAction?.messages || [];
    const box = $('maMessages');
    box.replaceChildren();
    if (msgs.length) {
      const div = el('div', null, 'alert warn');
      div.append(el('b', 'Mensajes de SAC (multi action):'));
      const ul = el('ul');
      for (const m of msgs) {
        ul.append(el('li', `[${m.severity || ''}] ${m.message || ''}`));
        for (const d of m.details || []) for (const l of d.logs || []) ul.append(el('li', `  ${d.stepName || ''}: ${l.message}`));
      }
      div.append(ul); box.append(div);
    }

    renderGroups();
    renderInputs(report);
    if (state.runId && report.state !== 'PREVIEW') {
      $('csvBtn').href = `/api/tests/report/${encodeURIComponent(state.runId)}`;
      $('csvBtn').hidden = false;
    } else $('csvBtn').hidden = true;
    document.querySelectorAll('.stepper li').forEach((li, i) => { li.classList.toggle('active', i === 3); li.classList.toggle('done', i < 3); });
  }

  function renderGroups() {
    const report = state.lastReport;
    const only = $('onlyDiff').checked;
    const wrap = $('groups');
    wrap.replaceChildren();
    for (const g of report.groups || []) {
      const cells = only ? g.cells.filter((x) => x.ok === false) : g.cells;
      const h = el('h3', `${g.nombre}`, 'group-title');
      h.append(el('code', ` = ${g.formula}`));
      wrap.append(h);
      if (g.extra) wrap.append(el('p', `Hay ${g.extra} celda(s) con datos en SAC dentro de este alcance que no estaban en lo esperado.`, 'hint err-text'));
      if (!cells.length) { wrap.append(el('p', only ? 'Sin diferencias. ✔' : 'Sin celdas.', 'empty')); continue; }
      const dims = Object.keys(cells[0].coords);
      const preview = cells[0].real === undefined;
      const tw = el('div', null, 'table-wrap');
      const t = el('table');
      const hr = el('tr');
      for (const c of ['Periodo', ...dims, 'Esperado', ...(preview ? [] : ['Real', 'Diferencia', 'Estado'])]) {
        hr.append(el('th', c, ['Esperado', 'Real', 'Diferencia'].includes(c) ? 'num' : ''));
      }
      const thead = el('thead'); thead.append(hr);
      const tb = el('tbody');
      for (const x of cells.slice(0, 1000)) {
        const tr = el('tr', null, x.ok === false ? 'sev-error' : '');
        tr.append(el('td', x.date));
        for (const d of dims) tr.append(el('td', x.coords[d]));
        tr.append(el('td', x.error ? x.error : num(x.expected), 'num'));
        if (!preview) {
          tr.append(el('td', x.real === null ? 'sin dato' : num(x.real), 'num'), el('td', x.diff === null ? '—' : num(x.diff), 'num'), el('td', x.ok ? 'OK' : 'Diferencia'));
        }
        tb.append(tr);
      }
      t.append(thead, tb); tw.append(t); wrap.append(tw);
      if (cells.length > 1000) wrap.append(el('p', `Se muestran 1.000 de ${cells.length} celdas; descargue el CSV para verlas todas.`, 'hint'));
    }
  }
  $('onlyDiff').addEventListener('change', () => state.lastReport && renderGroups());

  function renderInputs(report) {
    const rows = report.inputs?.sample || [];
    $('inputsBox').hidden = !rows.length;
    if (!rows.length) return;
    const dims = [...new Set(rows.flatMap((r) => Object.keys(r.coords)))];
    const hr = el('tr');
    for (const c of ['Entrada', 'Periodo', ...dims, 'Valor']) hr.append(el('th', c, c === 'Valor' ? 'num' : ''));
    $('inputsTable').tHead.replaceChildren(hr);
    $('inputsTable').tBodies[0].replaceChildren(...rows.map((r) => {
      const tr = el('tr');
      tr.append(el('td', r.nombre), el('td', r.date), ...dims.map((d) => el('td', r.coords[d] ?? '')), el('td', num(r.value), 'num'));
      return tr;
    }));
  }

  function common() {
    showError('');
    if (!state.case) throw new Error('Defina el caso de prueba.');
    try { JSON.parse($('caseJson').value); } catch (e) { throw new Error(`El JSON del paso 3 no es válido: ${e.message}`); }
    let seed = Number.parseInt($('seed').value, 10);
    if (!(seed > 0)) { seed = randomSeed(); $('seed').value = seed; }
    return { c: state.case, seed };
  }

  $('previewBtn').addEventListener('click', async () => {
    let req;
    try { req = common(); } catch (e) { showError(e.message); return; }
    busy($('previewBtn'), true, 'Generando…');
    try {
      state.runId = null;
      const report = await api('/api/tests/preview', { method: 'POST', body: { case: req.c, seed: req.seed } });
      renderSteps(report, 'Vista previa: valida la definición, los parámetros y los miembros contra el modelo y genera los datos, sin escribir en SAC.');
      renderResult(report);
      $('resultCard').scrollIntoView({ behavior: 'smooth' });
    } catch (e) { showError(e.message); } finally { busy($('previewBtn'), false); }
  });

  $('runBtn').addEventListener('click', async () => {
    let req;
    try { req = common(); } catch (e) { showError(e.message); return; }
    if (!$('confirmVersion').checked) { showError('Marque la confirmación de que la versión es de pruebas.'); return; }
    busy($('runBtn'), true, 'Ejecutando…');
    $('previewBtn').disabled = true;
    try {
      const reps = Math.min(Math.max(Number.parseInt($('reps').value, 10) || 1, 1), 20);
      const r = await api('/api/tests/run', {
        method: 'POST',
        body: { case: req.c, seed: req.seed, repeticiones: reps, confirmVersion: true, detenerEnFallo: $('stopOnFail').checked },
      });
      state.runId = r.runId;
      $('resultCard').hidden = true;
      $('runCard').scrollIntoView({ behavior: 'smooth' });
      poll();
    } catch (e) {
      showError(e.message);
      busy($('runBtn'), false); $('previewBtn').disabled = false;
    }
  });

  async function poll() {
    clearTimeout(state.timer);
    let st;
    try { st = await api(`/api/tests/status/${encodeURIComponent(state.runId)}`); } catch (e) {
      showError(e.message); busy($('runBtn'), false); $('previewBtn').disabled = false; return;
    }
    const done = st.reports.length;
    const cur = st.current || st.reports[done - 1];
    if (cur) renderSteps(cur, `Repetición ${st.current ? done + 1 : done} de ${st.reps} · semilla ${cur.seed}`);
    if (st.state === 'DONE') {
      busy($('runBtn'), false); $('previewBtn').disabled = false;
      const last = st.reports[st.reports.length - 1];
      if (last) {
        renderResult(last, st.reports);
        $('resultCard').scrollIntoView({ behavior: 'smooth' });
        toast(st.reports.every((r) => r.state === 'PASSED') ? `Prueba terminada: ${st.reports.length} repetición(es) correctas.` : 'Prueba terminada con diferencias o errores.');
      } else if (st.error) showError(st.error);
      return;
    }
    state.timer = setTimeout(poll, 1500);
  }

  // ---------------------------------------------------------------- inicio
  $('logoutBtn').addEventListener('click', async () => {
    try { await api('/auth/logout', { method: 'POST' }); } catch { /* igual se cierra */ }
    location.href = '/';
  });

  async function init() {
    const params = new URLSearchParams(location.search);
    const err = params.get('error');
    if (err) history.replaceState(null, '', '/');
    let me = null;
    try { me = await api('/api/me'); } catch { me = null; }
    if (!me?.authenticated) { showLogin(err); return; }
    const u = me.user;
    $('userName').textContent = u.name;
    $('userTenant').textContent = u.email || me.tenant;
    $('userInitials').textContent = u.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
    $('userBox').hidden = false; $('loginView').hidden = true; $('appView').hidden = false;
    $('seed').value = randomSeed();

    const [cat, models] = await Promise.all([api('/api/tests/catalog'), api('/api/models').catch(() => ({ models: [] }))]);
    state.catalog = cat.casos || [];
    state.plantilla = cat.plantilla || null;
    state.models = models.models || [];
    const sel = $('catalogSel');
    sel.replaceChildren(option('', state.catalog.length ? 'Seleccione un caso…' : 'No hay casos guardados'));
    for (const c of state.catalog) sel.append(option(c.id, c.nombre || c.id));

    let saved = null;
    try { saved = JSON.parse(localStorage.getItem(STORE_KEY) || 'null'); } catch { saved = null; }
    setCase(saved && typeof saved === 'object' ? saved : (state.plantilla || DEFAULT_TEMPLATE));
  }

  init().catch((e) => showError(e.message));
})();
