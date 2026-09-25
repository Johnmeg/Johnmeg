'use strict';

// Orquesta el job del Data Import API en dos etapas para que el usuario
// confirme antes de escribir:
//   prepare(): crea el job, envía los datos por bloques, valida en SAC.
//              Si SAC rechaza UNA sola fila, se cancela el job completo.
//   run():     ejecuta el job validado y consulta el estado hasta terminar.
//
// Detalle importante del API: al enviar datos (POST /jobs/{id}) SAC descarta
// en silencio las filas inválidas y sólo guarda las válidas. Por eso no basta
// con executeWithFailedRows=false: se revisa failedNumberRows en cada envío y
// además se compara el total del job contra los registros enviados.

async function safeDelete(client, jobId) {
  try { await client.deleteJob(jobId); } catch { /* el job expira solo a los 15 días */ }
}

function jobSettingsFor({ importMethod, template, meta }) {
  const settings = {
    importMethod,
    executeWithFailedRows: false,
    ignoreAdditionalColumns: false,
  };
  if (importMethod === 'CleanAndReplace') {
    settings.dimensionScope = template.cleanAndReplaceScope && template.cleanAndReplaceScope.length
      ? template.cleanAndReplaceScope
      : [meta.versionColumn, meta.dateColumn];
  }
  if (template.reverseSignByAccountType) settings.reverseSignByAccountType = true;
  return settings;
}

async function prepare(client, { modelId, importType, records, jobSettings, chunkSize = 10000, onProgress = () => {} }) {
  const jobId = await client.createJob(modelId, importType, { JobSettings: jobSettings });
  try {
    let sent = 0;
    for (let i = 0; i < records.length; i += chunkSize) {
      const chunk = records.slice(i, i + chunkSize);
      const res = await client.postData(jobId, chunk);
      sent += chunk.length;
      onProgress({ stage: 'envio', sent, total: records.length });
      if (Number(res?.failedNumberRows) > 0) {
        const rejected = (res.failedRows || []).map((f) => ({ ...(f.row || {}), _REJECTION_REASON: f.reason }));
        await safeDelete(client, jobId);
        return {
          ok: false, stage: 'ENVIO', rejected,
          message: `SAC rechazó ${res.failedNumberRows} fila(s) al recibir los datos. No se cargó nada.`,
        };
      }
    }

    onProgress({ stage: 'validacion' });
    const v = await client.validateJob(jobId);
    if (Number(v?.failedNumberRows) > 0) {
      const rejected = await client.invalidRows(jobId).catch(() => []);
      await safeDelete(client, jobId);
      return {
        ok: false, stage: 'VALIDACION', rejected,
        message: `La validación de SAC encontró ${v.failedNumberRows} fila(s) inválida(s). No se cargó nada.`,
      };
    }
    const inJob = Number(v?.totalNumberRowsInJob);
    if (Number.isFinite(inJob) && inJob !== records.length) {
      await safeDelete(client, jobId);
      return {
        ok: false, stage: 'CONTEO', rejected: [],
        message: `SAC recibió ${inJob} registros pero se enviaron ${records.length}. Se canceló la carga por seguridad.`,
      };
    }
    return {
      ok: true, jobId, totalRows: Number.isFinite(inJob) ? inJob : records.length,
      jobStatus: v?.jobStatus,
      cleanAndReplaceAffectedRows: v?.additionalInformation?.cleanAndReplaceAffectedRows || [],
    };
  } catch (e) {
    await safeDelete(client, jobId);
    throw e;
  }
}

const FINAL = new Set(['COMPLETED', 'FAILED']);

async function run(client, jobId, { pollMs = 2000, timeoutMs = 30 * 60 * 1000, onStatus = () => {} } = {}) {
  const started = Date.now();
  const r = await client.runJob(jobId);
  let status = { jobStatus: r?.jobStatus, failedNumberRows: Number(r?.failedNumberRows) || 0, totalNumberRowsInJob: r?.totalNumberRowsInJob };
  onStatus(status);
  while (!FINAL.has(status.jobStatus)) {
    if (Date.now() - started > timeoutMs) {
      return { ...status, jobStatus: 'TIMEOUT', message: 'El job sigue en proceso en SAC; consulte su estado más tarde.' };
    }
    await new Promise((res) => setTimeout(res, pollMs));
    const s = await client.jobStatus(jobId);
    status = {
      jobStatus: s?.jobStatus,
      description: s?.jobStatusDescription,
      failedNumberRows: Number(s?.additionalInformation?.failedNumberRows) || 0,
      totalNumberRowsInJob: s?.additionalInformation?.totalNumberRowsInJob,
    };
    onStatus(status);
  }
  if (status.jobStatus === 'FAILED') {
    status.rejected = await client.invalidRows(jobId).catch(() => []);
  }
  return status;
}

module.exports = { prepare, run, jobSettingsFor, safeDelete };
