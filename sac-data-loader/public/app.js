'use strict';

// Interfaz del cargador. Todo el texto que viene del archivo o de SAC se pinta
// con textContent (nunca innerHTML) para evitar inyección de HTML.

(() => {
  const $ = (id) => document.getElementById(id);
  const fmt = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 6 });
  const METHOD_INFO = {
    Update: {
      label: 'Reemplazar valores (Update)',
      help: 'Escribe cada combinación del archivo reemplazando el valor que exista. No borra datos que no vengan en el archivo.',
    },
    CleanAndReplace: {
      label: 'Borrar y reemplazar (CleanAndReplace)',
      help: 'Primero borra en SAC todos los datos del alcance indicado y luego escribe el archivo. Úselo para recargar un escenario completo.',
    },
    Append: {
      label: 'Sumar a lo existente (Append)',
      help: 'Suma el valor del archivo al valor que ya exista en SAC.',
    },
  };

  const state = { me: null, templates: [], template: null, versions: null, file: null, result: null, polling: null };

  // ---------------------------------------------------------------- utilidades
  async function api(url, { method = 'GET', body, form } = {}) {
    const opts = { method, credentials: 'same-origin', headers: { Accept: 'application/json' } };
    if (method !== 'GET') opts.headers['X-Requested-With'] = 'sac-loader';
    if (form) opts.body = form;
    else if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
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

  function setBanner(node, kind, parts) {
    node.className = `alert ${kind}`;
    node.replaceChildren(...parts.map((p) => (typeof p === 'string' ? document.createTextNode(p) : p)));
    node.hidden = false;
  }

  function setStep(n) {
    document.querySelectorAll('.stepper li').forEach((li) => {
      const s = Number(li.dataset.step);
      li.classList.toggle('active', s === n);
      li.classList.toggle('done', s < n);
    });
  }

  function busy(btn, on, label) {
    if (on) { btn.dataset.label = btn.textContent; btn.textContent = label; btn.disabled = true; }
    else { btn.textContent = btn.dataset.label || btn.textContent; btn.disabled = false; }
  }

  // ---------------------------------------------------------------- sesión
  function showLogin(error) {
    $('appView').hidden = true; $('userBox').hidden = true; $('loginView').hidden = false;
    if (error) { $('loginError').textContent = error; $('loginError').hidden = false; }
  }

  async function init() {
    const params = new URLSearchParams(location.search);
    const err = params.get('error');
    if (err) history.replaceState(null, '', '/');
    try {
      state.me = await api('/api/me');
    } catch {
      state.me = null;
    }
    if (!state.me?.authenticated) {
      showLogin(err);
      return;
    }
    const u = state.me.user;
    $('userName').textContent = u.name;
    $('userTenant').textContent = u.email || state.me.tenant;
    $('userInitials').textContent = u.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
    $('userBox').hidden = false; $('loginView').hidden = true; $('appView').hidden = false;
    const lim = state.me.limits;
    $('dropLimits').textContent = `Formatos: ${lim.extensions.join(', ')} · máximo ${lim.maxFileMb} MB y ${fmt.format(lim.maxRows)} filas`;

    const { templates } = await api('/api/templates');
    state.templates = templates;
    const sel = $('templateSel');
    sel.replaceChildren(el('option', 'Seleccione…'));
    sel.firstChild.value = '';
    for (const t of templates) {
      const o = el('option', t.name); o.value = t.id; sel.append(o);
    }
  }

  $('logoutBtn').addEventListener('click', async () => {
    try { await api('/auth/logout', { method: 'POST' }); } catch { /* igual se cierra */ }
    location.href = '/';
  });

  // ---------------------------------------------------------------- paso 1
  $('templateSel').addEventListener('change', async () => {
    const t = state.templates.find((x) => x.id === $('templateSel').value) || null;
    state.template = t;
    $('templateDesc').textContent = t ? [t.description, t.sheet ? `Hoja esperada: ${t.sheet}.` : ''].filter(Boolean).join(' ') : '';
    $('modelField').hidden = !t?.selectableModel;
    $('modelName').textContent = t ? (t.model || 'Seleccione el modelo') : '—';
    renderMethods(t);
    resetVersions();
    if (!t) return;
    if (t.selectableModel) {
      const ms = $('modelSel');
      ms.replaceChildren(el('option', 'Cargando modelos…'));
      try {
        const { models } = await api('/api/models');
        ms.replaceChildren(el('option', 'Seleccione…'));
        ms.firstChild.value = '';
        for (const m of models) { const o = el('option', m.name); o.value = m.id; o.title = m.id; ms.append(o); }
      } catch (e) { ms.replaceChildren(el('option', 'No se pudieron leer los modelos')); toast(e.message); }
    } else {
      loadVersions();
    }
  });

  $('modelSel').addEventListener('change', () => {
    const opt = $('modelSel').selectedOptions[0];
    $('modelName').textContent = opt?.value ? `${opt.textContent} (${opt.value})` : 'Seleccione el modelo';
    resetVersions();
    if (opt?.value) loadVersions();
  });

  function renderMethods(t) {
    const box = $('methodOptions');
    box.replaceChildren();
    const methods = t?.importMethods || ['Update'];
    methods.forEach((m, i) => {
      const lab = el('label');
      const r = document.createElement('input');
      r.type = 'radio'; r.name = 'importMethod'; r.value = m; r.checked = i === 0;
      r.addEventListener('change', () => { $('methodHint').textContent = methodHelp(m, t); });
      lab.append(r, el('span', METHOD_INFO[m]?.label || m));
      box.append(lab);
    });
    $('methodHint').textContent = methodHelp(methods[0], t);
  }

  function methodHelp(m, t) {
    let s = METHOD_INFO[m]?.help || '';
    if (m === 'CleanAndReplace' && t?.cleanAndReplaceScope) s += ` Alcance del borrado: ${t.cleanAndReplaceScope.join(', ')}.`;
    return s;
  }

  function resetVersions() {
    state.versions = null;
    $('versionSel').hidden = false; $('versionInput').hidden = true;
    $('versionSel').replaceChildren(el('option', state.template ? 'Cargando versiones…' : '—'));
    $('versionHint').textContent = '';
    $('columnsHint').textContent = '';
  }

  async function loadVersions() {
    const t = state.template;
    const q = new URLSearchParams({ template: t.id });
    if (t.selectableModel) q.set('modelId', $('modelSel').value);
    try {
      const data = await api(`/api/versions?${q}`);
      if (!t.selectableModel) $('modelName').textContent = `${data.model.name} (${data.model.id})`;
      const cols = (data.expectedColumns || []).map((c) => (c.optional ? `${c.name} (opcional)` : c.name));
      $('columnsHint').textContent = cols.length
        ? `El archivo debe traer las columnas ${cols.join(', ')} y los meses (p. ej. Ene 2026) o las columnas ${data.dateColumn} e ${data.measure}.`
        : '';
      state.versions = data.versions;
      if (!data.versions) {
        // SAC no expone el maestro de versiones: se escribe a mano (SAC lo valida)
        $('versionSel').hidden = true; $('versionInput').hidden = false;
        $('versionHint').textContent = 'Escriba el ID de la versión, p. ej. public.Plan. SAC la validará.';
        return;
      }
      const vs = $('versionSel');
      vs.replaceChildren(el('option', 'Seleccione…'));
      vs.firstChild.value = '';
      for (const v of data.versions) {
        const o = el('option', v.blocked ? `${v.id} (bloqueada)` : v.id);
        o.value = v.id; o.disabled = v.blocked; vs.append(o);
      }
      if (data.versions.some((v) => v.blocked)) $('versionHint').textContent = 'Las versiones bloqueadas se alimentan desde S/4HANA y no admiten carga manual.';
    } catch (e) {
      $('versionSel').replaceChildren(el('option', 'No disponible'));
      toast(e.message, 7000);
    }
  }

  function selectedVersion() {
    return ($('versionInput').hidden ? $('versionSel').value : $('versionInput').value).trim();
  }

  // Arrastrar y soltar
  const drop = $('dropZone');
  ['dragenter', 'dragover'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', (e) => { if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); });
  $('fileInput').addEventListener('change', () => setFile($('fileInput').files[0]));

  function setFile(f) {
    state.file = f || null;
    drop.classList.toggle('has-file', Boolean(f));
    $('dropText').textContent = f ? `${f.name} · ${(f.size / 1024).toFixed(1)} KB` : 'Arrastre aquí el archivo o haga clic para buscarlo';
  }

  $('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const t = state.template;
    if (!t) return toast('Seleccione el modelo al que va a cargar.');
    if (t.selectableModel && !$('modelSel').value) return toast('Seleccione el modelo de destino.');
    const version = selectedVersion();
    if (!version) return toast('Seleccione la versión de destino.');
    if (!state.file) return toast('Seleccione el archivo a cargar.');
    const maxBytes = state.me.limits.maxFileMb * 1024 * 1024;
    if (state.file.size > maxBytes) return toast(`El archivo supera ${state.me.limits.maxFileMb} MB.`);

    const form = new FormData();
    form.append('template', t.id);
    if (t.selectableModel) form.append('modelId', $('modelSel').value);
    form.append('version', version);
    form.append('importMethod', document.querySelector('input[name="importMethod"]:checked')?.value || 'Update');
    form.append('file', state.file, state.file.name);

    const btn = $('validateBtn');
    busy(btn, true, 'Validando…');
    try {
      const r = await api('/api/validate', { method: 'POST', form });
      state.result = r;
      renderResult(r);
    } catch (err) {
      toast(err.message, 8000);
    } finally {
      busy(btn, false);
    }
    return undefined;
  });

  // ---------------------------------------------------------------- paso 2
  function renderResult(r) {
    $('step2').hidden = false; $('step3').hidden = true; $('step4').hidden = true;
    setStep(2);
    const s = r.summary;
    const warnings = s.warnings ?? r.issues.filter((i) => i.severity !== 'error').length;
    if (r.ok) {
      setBanner($('resultBanner'), warnings ? 'warn' : 'ok', [
        el('b', '✔ El archivo es válido. '),
        `${fmt.format(s.records)} registros listos para ${r.model.name} / ${r.version}.`,
        warnings ? ` Revise ${warnings} advertencia(s) antes de continuar.` : '',
      ]);
    } else {
      setBanner($('resultBanner'), 'error', [
        el('b', `✖ ${fmt.format(s.errors)} error(es). `),
        'Corrija el archivo y vuelva a validarlo. No se enviará nada a SAC mientras existan errores.',
      ]);
    }

    const facts = [
      ['Archivo', s.fileName],
      ['Hoja / formato', s.sheet || [s.fileInfo?.encoding, s.fileInfo?.delimiter && `separador ${s.fileInfo.delimiter}`].filter(Boolean).join(' · ') || '—'],
      ['Fila de encabezados', s.headerRow ?? '—'],
      ['Diseño', s.layout === 'wide' ? 'Periodos en columnas' : s.layout === 'long' ? 'Periodo en una columna' : '—'],
      ['Filas leídas', fmt.format(s.rowsRead)],
      ['Registros a cargar', fmt.format(s.records)],
      ['Celdas vacías omitidas', fmt.format(s.skippedBlank)],
      ['Total general', fmt.format(s.grandTotal)],
      ['Método', METHOD_INFO[r.importMethod]?.label || r.importMethod],
      ['Tipo de importación', r.importType],
    ];
    $('facts').replaceChildren(...facts.map(([k, v]) => { const d = el('div'); d.append(el('dt', k), el('dd', v)); return d; }));

    $('nErrors').textContent = fmt.format(s.errors ?? 0);
    $('nWarnings').textContent = fmt.format(warnings);
    $('issuesCount').textContent = String(r.issues.length);
    renderIssues();

    const tb = $('totalsTable').tBodies[0];
    tb.replaceChildren(...s.periods.map((p) => {
      const tr = el('tr'); tr.append(el('td', periodLabel(p)), el('td', fmt.format(s.totalsByPeriod[p]), 'num')); return tr;
    }));
    const tf = $('totalsTable').tFoot;
    const ftr = el('tr'); ftr.append(el('td', 'Total'), el('td', fmt.format(s.grandTotal), 'num'));
    tf.replaceChildren(ftr);

    const cols = r.columns;
    const hr = el('tr'); cols.forEach((c) => hr.append(el('th', c)));
    $('previewTable').tHead.replaceChildren(hr);
    $('previewTable').tBodies[0].replaceChildren(...r.preview.map((rec) => {
      const tr = el('tr');
      cols.forEach((c, i) => tr.append(el('td', i === cols.length - 1 ? fmt.format(rec[c]) : rec[c], i === cols.length - 1 ? 'num' : '')));
      return tr;
    }));

    $('reportBtn').href = `/api/report/${encodeURIComponent(r.uploadId)}`;
    $('prepareBtn').disabled = !r.ok;
    selectTab('issues');
    $('step2').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function periodLabel(p) {
    const M = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    if (/^\d{6}$/.test(p)) return `${M[Number(p.slice(4, 6)) - 1]} ${p.slice(0, 4)} (${p})`;
    return p;
  }

  function renderIssues() {
    const r = state.result;
    if (!r) return;
    const showE = $('fErrors').checked; const showW = $('fWarnings').checked;
    const list = r.issues.filter((i) => (i.severity === 'error' ? showE : showW));
    $('issuesTable').tBodies[0].replaceChildren(...list.map((i) => {
      const tr = el('tr', null, `sev-${i.severity}`);
      tr.append(
        el('td', `${i.severity === 'error' ? 'Error' : 'Advertencia'} · ${i.title}`),
        el('td', i.row ?? ''), el('td', i.column ?? ''), el('td', i.value ?? '', 'value'), el('td', i.message),
      );
      return tr;
    }));
    $('issuesEmpty').hidden = r.issues.length > 0;
    $('issuesTable').parentElement.hidden = r.issues.length === 0;
  }
  $('fErrors').addEventListener('change', renderIssues);
  $('fWarnings').addEventListener('change', renderIssues);

  function selectTab(name) {
    document.querySelectorAll('.tab').forEach((b) => b.classList.toggle('active', b.dataset.tab === name));
    ['issues', 'totals', 'preview'].forEach((n) => { $(`tab-${n}`).hidden = n !== name; });
  }
  document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => selectTab(b.dataset.tab)));

  function restart() {
    stopPolling();
    state.result = null;
    $('step2').hidden = true; $('step3').hidden = true; $('step4').hidden = true;
    $('fileInput').value = ''; setFile(null);
    setStep(1);
    $('step1').scrollIntoView({ behavior: 'smooth' });
  }
  $('restartBtn').addEventListener('click', restart);
  $('againBtn').addEventListener('click', restart);

  // ---------------------------------------------------------------- paso 3
  $('prepareBtn').addEventListener('click', async () => {
    const r = state.result;
    if (!r?.ok) return;
    $('step3').hidden = false; setStep(3);
    $('prepareProgress').hidden = false; $('prepareResult').replaceChildren();
    $('rejectedWrap').hidden = true; $('carConfirm').hidden = true; $('step3Actions').hidden = true;
    $('prepareBtn').disabled = true; $('restartBtn').disabled = true;
    $('step3').scrollIntoView({ behavior: 'smooth', block: 'start' });
    try {
      const p = await api('/api/sac/prepare', { method: 'POST', body: { uploadId: r.uploadId } });
      $('prepareProgress').hidden = true;
      const box = el('div');
      if (!p.ok) {
        setBanner(box, 'error', [el('b', '✖ SAC rechazó los datos. '), p.message, ' Descargue el reporte para ver el detalle.']);
        $('prepareResult').replaceChildren(box);
        renderRejected(p.rejected);
        $('prepareBtn').disabled = true;
        return;
      }
      setBanner(box, 'ok', [el('b', '✔ SAC validó los datos. '), `${fmt.format(p.totalRows)} registros listos para escribir. Aún no se ha cargado nada.`]);
      $('prepareResult').replaceChildren(box);
      $('step3Actions').hidden = false;
      if (r.importMethod === 'CleanAndReplace') {
        const n = (p.cleanAndReplaceAffectedRows || []).reduce((a, x) => a + (Number(x.numberOfRowsToBeDeleted) || 0), 0);
        const scope = p.jobSettings?.dimensionScope?.join(', ') || '';
        $('carText').textContent = `Entiendo que SAC borrará ${fmt.format(n)} registro(s) existente(s) en el alcance (${scope}) de los datos del archivo antes de escribir los nuevos.`;
        $('carConfirm').hidden = false; $('carCheck').checked = false;
        $('runBtn').disabled = true;
      } else {
        $('runBtn').disabled = false;
      }
    } catch (e) {
      $('prepareProgress').hidden = true;
      const box = el('div');
      setBanner(box, 'error', [el('b', '✖ '), e.message]);
      $('prepareResult').replaceChildren(box);
      $('prepareBtn').disabled = false;
    } finally {
      $('restartBtn').disabled = false;
    }
  });

  $('carCheck').addEventListener('change', () => { $('runBtn').disabled = !$('carCheck').checked; });

  function renderRejected(rows) {
    if (!rows?.length) return;
    const cols = [...new Set(rows.flatMap((x) => Object.keys(x)))];
    const reasonFirst = ['_REJECTION_REASON', ...cols.filter((c) => c !== '_REJECTION_REASON')];
    const hr = el('tr'); reasonFirst.forEach((c) => hr.append(el('th', c === '_REJECTION_REASON' ? 'Motivo del rechazo' : c)));
    $('rejectedTable').tHead.replaceChildren(hr);
    $('rejectedTable').tBodies[0].replaceChildren(...rows.map((row) => {
      const tr = el('tr'); reasonFirst.forEach((c) => tr.append(el('td', row[c] ?? ''))); return tr;
    }));
    $('rejectedWrap').hidden = false;
  }

  $('cancelBtn').addEventListener('click', async () => {
    try {
      await api('/api/sac/cancel', { method: 'POST', body: { uploadId: state.result.uploadId } });
      toast('Carga cancelada. No se escribió nada en SAC.');
      restart();
    } catch (e) { toast(e.message); }
  });

  // ---------------------------------------------------------------- paso 4
  $('runBtn').addEventListener('click', async () => {
    const r = state.result;
    const body = { uploadId: r.uploadId };
    if (r.importMethod === 'CleanAndReplace') body.confirmCleanAndReplace = $('carCheck').checked;
    busy($('runBtn'), true, 'Iniciando…');
    try {
      await api('/api/sac/run', { method: 'POST', body });
    } catch (e) {
      busy($('runBtn'), false); toast(e.message, 8000); return;
    }
    $('step3Actions').hidden = true; $('carConfirm').hidden = true;
    $('step4').hidden = false; $('runProgress').hidden = false; $('runResult').replaceChildren(); $('againBtn').hidden = true;
    setStep(4);
    $('step4').scrollIntoView({ behavior: 'smooth', block: 'start' });
    poll();
  });

  function stopPolling() { clearTimeout(state.polling); state.polling = null; }

  async function poll() {
    const r = state.result;
    let s;
    try {
      s = await api(`/api/sac/status/${encodeURIComponent(r.uploadId)}`);
    } catch (e) {
      $('runText').textContent = `No se pudo consultar el estado (${e.message}). Reintentando…`;
      state.polling = setTimeout(poll, 4000);
      return;
    }
    if (s.state === 'RUNNING') {
      $('runText').textContent = `Estado en SAC: ${s.status?.jobStatus || 'iniciando'}…`;
      state.polling = setTimeout(poll, 2000);
      return;
    }
    $('runProgress').hidden = true; $('againBtn').hidden = false;
    const box = el('div');
    if (s.state === 'COMPLETED') {
      const n = s.status?.totalNumberRowsInJob ?? s.totalRows;
      setBanner(box, 'ok', [el('b', '✔ Carga completada. '), `${fmt.format(n)} registros escritos en ${r.model.name} / ${r.version}.`]);
      document.querySelectorAll('.stepper li').forEach((li) => li.classList.add('done'));
    } else if (s.state === 'TIMEOUT') {
      setBanner(box, 'warn', [el('b', 'La carga sigue en proceso en SAC. '), s.status?.message || 'Consulte su estado más tarde.']);
    } else {
      setBanner(box, 'error', [el('b', '✖ La carga no se completó. '), s.message || s.status?.description || `Estado: ${s.state}.`]);
      if (s.rejected?.length) renderRejectedInto(box, s.rejected);
    }
    $('runResult').replaceChildren(box);
  }

  function renderRejectedInto(container, rows) {
    const p = el('p', `SAC rechazó ${rows.length} fila(s). Descargue el reporte del paso 2 para el detalle completo.`);
    container.append(p);
  }

  init().catch((e) => toast(e.message, 8000));
})();
