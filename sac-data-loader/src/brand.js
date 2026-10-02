'use strict';

const fs = require('fs');
const path = require('path');

// Marca (empresa) de la aplicación: textos, logos, colores y catálogo de
// modelos. Cada marca vive en brands/<id>/ y se elige con BRAND en el .env.

const BRANDS_DIR = path.join(__dirname, '..', 'brands');
const DEFAULT_BRAND = 'ciudadlimpia';
const TEXT_KEYS = ['name', 'appName', 'utilLabel', 'kicker', 'heroTitle', 'heroText', 'footer'];

function listBrands() {
  return fs.readdirSync(BRANDS_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory() && fs.existsSync(path.join(BRANDS_DIR, d.name, 'brand.json')))
    .map((d) => d.name);
}

function loadBrand(id = DEFAULT_BRAND) {
  const brandId = String(id || DEFAULT_BRAND).trim().toLowerCase();
  if (!/^[a-z0-9-]+$/.test(brandId) || !fs.existsSync(path.join(BRANDS_DIR, brandId, 'brand.json'))) {
    throw new Error(`BRAND="${id}" no existe. Marcas disponibles: ${listBrands().join(', ')}.`);
  }
  const dir = path.join(BRANDS_DIR, brandId);
  const raw = JSON.parse(fs.readFileSync(path.join(dir, 'brand.json'), 'utf8'));
  for (const k of TEXT_KEYS) {
    if (typeof raw[k] !== 'string' || !raw[k]) throw new Error(`brands/${brandId}/brand.json: falta "${k}".`);
  }
  return {
    ...raw,
    id: brandId,
    dir,
    logoWidth: Number(raw.logoWidth) || 176,
    logoHeight: Number(raw.logoHeight) || 54,
    templatesFile: raw.templates ? path.resolve(dir, raw.templates) : null,
  };
}

const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// Reemplaza {{clave}} en index.html con los textos (escapados) de la marca.
function renderIndex(html, brand) {
  return html.replace(/\{\{(\w+)\}\}/g, (m, k) => (brand[k] === undefined ? m : escapeHtml(brand[k])));
}

module.exports = { loadBrand, listBrands, renderIndex, DEFAULT_BRAND };
