'use strict';

// Probador de data actions. Todo texto que viene de SAC o del caso se pinta con
// textContent (nunca innerHTML).

(() => {
  const $ = (id) => document.getElementById(id);
  const fmt = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 6 });
  const fmt2 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 });
  const STORE_KEY = 'probador-da:caso';
  const state = { catalog: [], plantilla: null, runId: null, timer: null, lastReport: null };

  const DEFAULT_TEMPLATE = {
    id: 'MI_PRUEBA',
    nombre: 'Mi prueba de data action',
    descripcion: 'Reemplace modelo, multi action, miembros y fórmula por los de su data action.',
    modelo: '<ID del modelo>',
    multiAction: '<paquete>:<ID de la multi action>',
    version: 'public.PRUEBAS',
    periodos: { desde: '202601', hasta: '202603' },
    comun: {},
    parametros: [{ parameterId: 'TargetVersion', value: { memberIds: ['{{version}}'], hierarchyId: null } }],
    entradas: [
      { nombre: 'PRECIO', fijo: { Ratio: '<cuenta precio>' }, min: 1000, max: 50000, decimales: 0 },
      { nombre: 'CANTIDAD', fijo: { Ratio: '<cuenta cantidad>' }, min: 1, max: 500, decimales: 2 },
    ],
    esperado: [
      { nombre: 'INGRESO', fijo: { Ratio: '<cuenta resultado>' }, formula: "v('PRECIO') * v('CANTIDAD')" },
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

  function showLogin(error) {
    $('appView').hidden = true; $('userBox').hidden = true; $('loginView').hidden = false;
    if (error) { $('loginError').textContent = error; $('loginError').hidden = false; }
  }
  function showError(msg) {
    const e = $('caseError');
    e.textContent = msg; e.hidden = !msg;
    if (msg) e.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // ---------------------------------------------------------------- editor
  function setEditor(obj) {
    $('caseJson').value = JSON.stringify(obj, null, 2);
    onEditorChange();
  }
  function readCase() {
    try {
      const c = JSON.parse($('caseJson').value);
      if (!c || typeof c !== 'object' || Array.isArray(c)) throw new Error('debe ser un objeto { ... }');
      return c;
    } catch (e) {
      throw new Error(`El JSON del caso no es válido: ${e.message}`);
    }
  }
  function onEditorChange() {
    let c = null;
    try { c = readCase(); $('jsonState').textContent = 'JSON válido.'; $('jsonState').className = 'hint ok-text'; } catch (e) {
      $('jsonState').textContent = e.message; $('jsonState').className = 'hint err-text';
    }
    try { localStorage.setItem(STORE_KEY, $('caseJson').value); } catch { /* sin almacenamiento */ }
    const v = c?.version ? String(c.version) : 'del caso';
    $('confirmText').textContent = `Confirmo que la versión ${v} es de pruebas: antes de cargar se borrarán sus datos en los periodos del caso.`;
    $('confirmVersion').checked = false;
  }
  $('caseJson').addEventListener('input', onEditorChange);
  $('caseJson').addEventListener('keydown', (ev) => {
    if (ev.key === 'Tab') { // tabulación de 2 espacios dentro del editor
      ev.preventDefault();
      const t = ev.target; const { selectionStart: a, selectionEnd: b } = t;
      t.value = `${t.value.slice(0, a)}  ${t.value.slice(b)}`;
      t.selectionStart = t.selectionEnd = a + 2;
      onEditorChange();
    }
  });

  $('catalogSel').addEventListener('change', () => {
    const c = state.catalog.find((x) => x.id === $('catalogSel').value);
    $('catalogDesc').textContent = c?.descripcion || '';
    if (c) setEditor(c);
  });
  $('newBtn').addEventListener('click', () => {
    setEditor(state.plantilla || DEFAULT_TEMPLATE);
    $('catalogSel').value = '';
  });
  $('openFile').addEventListener('change', async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    try {
      const obj = JSON.parse(await f.text());
      setEditor(obj); toast(`Caso "${obj.nombre || obj.id || f.name}" abierto.`);
    } catch (e) { showError(`El archivo no es un JSON válido: ${e.message}`); }
    ev.target.value = '';
  });
  $('saveBtn').addEventListener('click', () => {
    let c;
    try { c = readCase(); } catch (e) { showError(e.message); return; }
    const blob = new Blob([`${JSON.stringify(c, null, 2)}\n`], { type: 'application/json' });
    const a = el('a'); a.href = URL.createObjectURL(blob); a.download = `${c.id || 'caso'}.json`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
  $('seedBtn').addEventListener('click', () => { $('seed').value = randomSeed(); });

  // ---------------------------------------------------------------- pasos
  const ICON = { pending: '○', running: '◐', ok: '✔', error: '✖', skipped: '–' };
  function renderSteps(report, info) {
    $('runCard').hidden = false;
    $('runInfo').textContent = info || '';
    const list = $('stepsList');
    list.replaceChildren(...report.steps.map((s) => {
      const li = el('li', null, `step ${s.status}`);
      li.append(el('span', ICON[s.status] || '○', 'step-icon'), el('span', s.label, 'step-label'));
      li.append(el('span', s.ms !== null ? secs(s.ms) : '', 'step-time'));
      if (s.detail) li.append(el('small', s.detail, 'step-detail'));
      return li;
    }));
  }

  // ---------------------------------------------------------------- resultado
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
      ['Caso', report.case?.nombre || report.case?.id || '—'],
      ['Versión', report.case?.version || '—'],
      ['Semilla', report.seed],
      ['Tiempo total', secs(report.ms)],
      ['Celdas de entrada', report.inputs?.count ?? '—'],
    ];
    if (s) facts.push(['Celdas verificadas', s.cells], ['Con diferencia', s.failed], ['Diferencia máxima', num(s.maxDiff)], ['Sin dato en SAC', s.missing], ['Celdas adicionales', s.extra]);
    if (report.multiAction) facts.push(['Multi action', report.multiAction.status || '—']);
    $('facts').replaceChildren(...facts.map(([k, v]) => { const d = el('div'); d.append(el('dt', k), el('dd', v)); return d; }));

    // Repeticiones
    const reps = all.filter(Boolean);
    $('repsWrap').hidden = reps.length < 2;
    $('repsTable').tBodies[0].replaceChildren(...reps.map((r, i) => {
      const tr = el('tr', null, r.state === 'PASSED' ? '' : 'sev-error');
      tr.append(el('td', i + 1), el('td', r.seed), el('td', { PASSED: 'Pasó', FAILED: 'Falló', ERROR: 'Error', RUNNING: 'En curso' }[r.state] || r.state),
        el('td', r.summary?.cells ?? '—', 'num'), el('td', r.summary?.failed ?? '—', 'num'), el('td', secs(r.ms), 'num'));
      return tr;
    }));

    // Mensajes de la multi action
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

  // ---------------------------------------------------------------- acciones
  function common() {
    showError('');
    const c = readCase();
    let seed = Number.parseInt($('seed').value, 10);
    if (!(seed > 0)) { seed = randomSeed(); $('seed').value = seed; }
    return { c, seed };
  }

  $('previewBtn').addEventListener('click', async () => {
    let req;
    try { req = common(); } catch (e) { showError(e.message); return; }
    busy($('previewBtn'), true, 'Generando…');
    try {
      state.runId = null;
      const report = await api('/api/tests/preview', { method: 'POST', body: { case: req.c, seed: req.seed } });
      renderSteps(report, 'Vista previa: valida la definición y los miembros contra el modelo y genera los datos, sin escribir en SAC.');
      renderResult(report);
      $('resultCard').scrollIntoView({ behavior: 'smooth' });
    } catch (e) { showError(e.message); } finally { busy($('previewBtn'), false); }
  });

  $('runBtn').addEventListener('click', async () => {
    let req;
    try { req = common(); } catch (e) { showError(e.message); return; }
    if (!$('confirmVersion').checked) { showError('Marque la confirmación de que la versión del caso es de pruebas.'); return; }
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
    if (cur) {
      const n = st.current ? done + 1 : done;
      renderSteps(cur, `Repetición ${n} de ${st.reps} · semilla ${cur.seed}`);
    }
    if (st.state === 'DONE') {
      busy($('runBtn'), false); $('previewBtn').disabled = false;
      const last = st.reports[st.reports.length - 1];
      if (last) {
        renderResult(last, st.reports);
        $('resultCard').scrollIntoView({ behavior: 'smooth' });
        const okAll = st.reports.every((r) => r.state === 'PASSED');
        toast(okAll ? `Prueba terminada: ${st.reports.length} repetición(es) correctas.` : 'Prueba terminada con diferencias o errores.');
      } else if (st.error) showError(st.error);
      return;
    }
    state.timer = setTimeout(poll, 1500);
  }

  // ---------------------------------------------------------------- inicio
  $('logoutBtn').addEventListener('click', async () => {
    try { await api('/auth/logout', { method: 'POST' }); } catch { /* igual se cierra */ }
    location.href = '/pruebas';
  });

  async function init() {
    let me = null;
    try { me = await api('/api/me'); } catch { me = null; }
    if (!me?.authenticated) { showLogin(); return; }
    const u = me.user;
    $('userName').textContent = u.name;
    $('userTenant').textContent = u.email || me.tenant;
    $('userInitials').textContent = u.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
    $('userBox').hidden = false; $('loginView').hidden = true; $('appView').hidden = false;
    $('seed').value = randomSeed();

    const cat = await api('/api/tests/catalog');
    state.catalog = cat.casos || [];
    state.plantilla = cat.plantilla || null;
    const sel = $('catalogSel');
    sel.replaceChildren(el('option', state.catalog.length ? 'Seleccione un caso…' : 'No hay casos guardados'));
    sel.firstChild.value = '';
    for (const c of state.catalog) { const o = el('option', c.nombre || c.id); o.value = c.id; sel.append(o); }

    let saved = null;
    try { saved = localStorage.getItem(STORE_KEY); } catch { /* sin almacenamiento */ }
    if (saved) { $('caseJson').value = saved; onEditorChange(); } else setEditor(state.plantilla || DEFAULT_TEMPLATE);
  }

  init().catch((e) => showError(e.message));
})();
