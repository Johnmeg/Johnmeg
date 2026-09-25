'use strict';

// Genera archivos de ejemplo (válidos y con errores) en ./samples para probar
// la aplicación con el simulador de SAC (npm run demo). Los encabezados son
// los nombres reales de las dimensiones de los modelos de Ciudad Limpia; los
// códigos de miembros son ficticios (los del simulador).

const fs = require('fs');
const path = require('path');
const ExcelJS = require('exceljs');

const OUT = path.join(__dirname, '..', 'samples');
const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'].map((m) => `${m} 2026`);
const doce = (v) => Array(12).fill(v);

async function excel(file, header, rows) {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet('Datos');
  ws.addRow(header).eachCell((c) => {
    c.font = { bold: true, color: { argb: 'FFFFFFFF' } };
    c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF0A6ED1' } };
  });
  rows.forEach((r) => ws.addRow(r));
  ws.columns.forEach((c, i) => { c.width = i < header.length - 12 ? 22 : 12; });
  await wb.xlsx.writeFile(path.join(OUT, file));
}

function csv(file, lines) {
  // UTF-8 con BOM, como lo guarda Excel en "CSV UTF-8 (delimitado por comas)"
  fs.writeFileSync(path.join(OUT, file), `﻿${lines.map((l) => l.join(';')).join('\r\n')}\r\n`);
}

(async () => {
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  // ------------------------------------------------------------ Gastos
  const GASTOS = ['Sociedad_CL', 'Cecos_CL', 'Cebes_CL', 'Cuentas_Egresos_CL', 'Auditoria_CL', 'Moneda_CL'];
  await excel('Gastos_CL_valido.xlsx', [...GASTOS, ...MESES], [
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5205_SERV_PUBLICOS', 'PRESUPUESTO_EXCEL', 'COP', ...doce(300000)],
    ['CL_BOG', 'CECO_OPER', 'RECOLECCION', '5105_SALARIOS', 'PRESUPUESTO_EXCEL', 'COP', ...doce(8000000)],
    ['CL_NEI', 'VEH_ABC123', 'RECOLECCION', '5210_COMBUSTIBLE', 'PRESUPUESTO_EXCEL', 'COP', ...doce(1500250.75)],
    ['CL_NEI', 'CECO_ADMIN', 'CORPORATIVO', '5260_DEPRECIACION', 'PRESUPUESTO_EXCEL', 'COP', ...doce(420000)],
  ]);
  csv('Gastos_CL_con_errores.csv', [
    [...GASTOS, ...MESES],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5205_SERV_PUBLICOS', 'PRESUPUESTO_EXCEL', 'COP', ...doce('300.000,00')],
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '9999_NO_EXISTE', 'PRESUPUESTO_EXCEL', 'COP', ...doce('10')],     // cuenta inexistente
    ['CL_BOG', 'CECO_OPER', 'BARRIDO', '5105_SALARIOS', 'PRESUPUESTO_EXCEL', 'COP', '1,2,3', ...doce('5').slice(1)], // número inválido
    ['CL_BOG', 'ceco_admin', 'RECOLECCION', '5105_SALARIOS', 'PRESUPUESTO_EXCEL', 'COP', ...doce('100')],     // minúsculas
    ['CL_BOG', 'CECO_ADMIN', 'RECOLECCION', '5205_SERV_PUBLICOS', 'PRESUPUESTO_EXCEL', 'COP', ...doce('50')], // fila repetida
    ['CL_NEI', 'CECO_ADMIN', 'RECOLECCION', '5105_SALARIOS', '', 'COP', ...doce('7')],                      // Auditoría vacía
  ]);
  csv('Gastos_CL_formato_largo.csv', [
    [...GASTOS, 'Date', 'Importe'],
    ['CL_MED', 'CECO_ADMIN', 'CORPORATIVO', '5205_SERV_PUBLICOS', 'MANUAL', 'COP', '202601', '1500000'],
    ['CL_MED', 'CECO_ADMIN', 'CORPORATIVO', '5205_SERV_PUBLICOS', 'MANUAL', 'COP', '2026-02', '1.600.000'],
    ['CL_MED', 'CECO_ADMIN', 'CORPORATIVO', '5205_SERV_PUBLICOS', 'MANUAL', 'COP', 'Mar 2026', '1.700.000,50'],
  ]);

  // ------------------------------------------------------------ Ingreso
  const INGRESO = ['Sociedad_CL', 'Cebes_CL', 'Ratio_CL', 'Auditoria_CL', 'Moneda_CL'];
  await excel('Ingreso_CL_valido.xlsx', [...INGRESO, ...MESES], [
    ['CL_BOG', 'RECOLECCION', 'ING_RECOLECCION', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(1250000.5)],
    ['CL_BOG', 'BARRIDO', 'ING_BARRIDO', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(830000)],
    ['CL_NEI', 'RECOLECCION', 'ING_RECOLECCION', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(415000)],
    ['CL_NEI', 'DISPOSICION', 'ING_DISPOSICION', 'PRESUPUESTO_TARIFAS', 'COP', 120000, 120000, 125000, 125000, 125000, 130000, 130000, 130000, 135000, 135000, 135000, 140000],
  ]);
  await excel('Ingreso_CL_con_errores.xlsx', [...INGRESO, ...MESES], [
    ['CL_BOG', 'RECOLECCION', 'ING_RECOLECCION', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(1000)],
    ['cl_bog', 'BARRIDO', 'ING_BARRIDO', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(1000)],             // minúsculas
    ['CL_CALI', 'RECOLECCION', 'ING_RECOLECCION', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(1000)],    // sociedad inexistente
    ['CL_NEI', '', 'ING_RECOLECCION', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(1000)],                // Cebes vacío
    ['CL_NEI', 'BARRIDO', 'ING_BARRIDO', 'PRESUPUESTO_TARIFAS', 'COP', 500, 'quinientos', ...Array(10).fill(500)],
    ['CL_BOG', 'RECOLECCION', 'ING_RECOLECCION', 'PRESUPUESTO_TARIFAS', 'COP', ...doce(2000)],     // fila repetida
  ]);
  csv('Ingreso_CL_con_cliente.csv', [
    ['Sociedad_CL', 'Cebes_CL', 'Cliente', 'Regional', 'Ratio_CL', 'Auditoria_CL', 'Moneda_CL', 'Ene 2026', 'Feb 2026', 'Mar 2026'],
    ['CL_BOG', 'RECOLECCION', 'CLI_001', 'REG_CENTRO', 'TARIFA', 'PXQ', 'COP', '45500', '45500', '46000'],
    ['CL_BOG', 'RECOLECCION', 'CLI_001', 'REG_CENTRO', 'CANTIDAD', 'PXQ', 'COP', '1200', '1180', '1250'],
  ]);

  // ------------------------------------------------------------ EEFF
  const EEFF = ['Sociedad_CL', 'Cuentas_EF_CL', 'Cebes_CL', 'Cecos_CL', 'Auditoria_CL', 'Moneda_CL'];
  await excel('EEFF_CL_valido.xlsx', [...EEFF, ...MESES], [
    ['CL_BOG', '1105_CAJA', 'CORPORATIVO', '#', 'MANUAL', 'COP', ...doce(50000000)],
    ['CL_BOG', '1305_CLIENTES', 'CORPORATIVO', '#', 'MANUAL', 'COP', ...doce(120000000)],
    ['CL_BOG', 'FC_CAPEX', 'RECOLECCION', 'CECO_OPER', 'MANUAL', 'COP', ...doce(-35000000)],
  ]);

  console.log(`Ejemplos generados en ${OUT}`);
})();
