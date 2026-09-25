# Cargador de datos a SAP Analytics Cloud

Aplicación web (Node.js) para que los usuarios de planeación carguen archivos **Excel (.xlsx/.xlsm)** o **planos (.csv/.txt)** a los modelos de planeación de SAC.

- **Cada usuario inicia sesión con sus propias credenciales de SAC** (OAuth 2.0 Authorization Code + PKCE). La aplicación **nunca ve la contraseña**: el usuario se autentica en la página de login de SAC o de su IdP corporativo. Toda carga se hace con el token de ese usuario, así que SAC aplica sus roles y su Data Access Control.
- **Valida el archivo antes de escribir** en SAC: primero una validación local y luego una validación dentro de SAC. Sólo si ambas pasan se habilita la carga, y el usuario debe confirmarla.
- **Todo o nada**: si SAC rechaza una sola fila, se cancela el job completo y no se escribe nada.
- Deja una **bitácora de auditoría** con quién cargó qué, cuándo, a qué modelo y versión, y el resultado.

Usa el **Data Import API** de SAC (`/api/v1/dataimport`) para escribir y el **Data Export API** (`/api/v1/dataexport`) para leer los maestros de las dimensiones.

---

## 1. Flujo

```
Navegador ──► App (Node.js) ──► SAC Data Import / Export API
   │               │
   │  1. Login ────┼──► Página de login de SAC (OAuth) ──► token del usuario (queda en el servidor)
   │  2. Archivo ──┤  Validación local (estructura, códigos, números, periodos, duplicados…)
   │  3. Validar en SAC: crea el job, envía los datos, POST /validate  (no escribe nada)
   │  4. Confirmar ──► POST /run  ──► consulta el estado hasta COMPLETED / FAILED
```

| Paso | Qué ve el usuario |
|---|---|
| 1. Archivo | Plantilla (PL-01…PL-08 o Genérico), modelo, versión (lista leída de SAC; `public.Actual` bloqueada), método de carga y archivo |
| 2. Validación local | Resumen, hallazgos (errores y advertencias con fila, columna y valor), totales por periodo, vista previa y reporte CSV descargable |
| 3. Validación en SAC | Resultado de SAC. Con *Borrar y reemplazar*, cuántos registros se borrarán; se exige confirmarlo |
| 4. Carga | Estado del job y número de registros escritos |

---

## 2. Validaciones

**Del archivo**
- Extensión permitida (.xlsx, .xlsm, .csv, .txt) y contenido real del archivo (un Excel renombrado se detecta). Tamaño y número de filas máximos.
- Codificación (UTF-8, UTF-8 con BOM, UTF-16, Windows-1252) y separador (`;` `,` tabulador `|`) detectados automáticamente. Comillas sin cerrar.
- Hoja esperada de la plantilla. Si el libro tiene una sola hoja con datos, se usa esa hoja y se muestra una advertencia.

**De la estructura**
- Fila de encabezados encontrada automáticamente (el bloque de contexto de la plantilla puede ir arriba).
- Columnas obligatorias: todas las dimensiones clave del modelo deben venir en el archivo, en el bloque de contexto o como valor fijo de la plantilla.
- Columnas desconocidas (error), columnas ignoradas como *Total* u *Observaciones* (advertencia), encabezados duplicados, columnas con datos sin encabezado.
- Periodos: `Ene 2026`, `ene-26`, `Enero 2026`, `Jan 2026`, `202601`, `2026-01`, `01/2026` o fechas de Excel. Periodos inválidos, repetidos o fuera de rango.
- La plantilla apunta a columnas que existen en el modelo (se lee la metadata real del modelo en SAC).

**De la versión**
- Obligatoria (sin versión, SAC cargaría en `public.Actual`).
- Versiones bloqueadas (`BLOCKED_VERSIONS`).
- La versión del archivo, en el bloque de contexto o en una columna, debe coincidir con la seleccionada.
- Debe existir en el modelo.

**De cada fila**
- Dimensiones vacías, fechas en lugar de códigos, caracteres de control, espacios de más (se eliminan y se avisa), longitud máxima de la columna.
- Valores permitidos por plantilla (p. ej. `Auditoria_CL`).
- **Miembros existentes** en el maestro de cada dimensión. SAC distingue mayúsculas, y se sugiere el código correcto (`"cl_bog"`: ¿Quiso decir `"CL_BOG"`?). El miembro `#` (sin asignar) siempre se acepta.
- Números en formato colombiano (`1.234.567,89`) o inglés, negativos contables `(1.500)` o `1500-`, errores de Excel (`#N/A`, `#REF!`), texto en lugar de número, formato ambiguo (`1.234`), negativos no permitidos, decimales y valores inusualmente grandes.
- **Combinaciones repetidas**: SAC se quedaría sólo con el último valor.
- Archivo sin valores para cargar.

**En SAC**, antes de escribir
- Cada envío se revisa. SAC descarta en silencio las filas inválidas al recibirlas, así que si hay alguna **se cancela el job**.
- `POST /jobs/{id}/validate` aplica las reglas del modelo: miembros, jerarquías, permisos, Data Access Control y bloqueos de datos.
- Se compara el número de registros recibidos por SAC con los enviados.
- El job se crea con `executeWithFailedRows: false` e `ignoreAdditionalColumns: false`.

---

## 3. Configuración en SAP Analytics Cloud

1. **Crear el cliente OAuth**: *Sistema → Administración → App Integration → OAuth Clients → Add a New OAuth Client*
   - **Purpose:** `Interactive Usage`. Esto hace que el token lleve el contexto del usuario (3-legged).
   - **Redirect URI:** `<APP_BASE_URL>/auth/callback`, p. ej. `https://cargas.fanalca.com/auth/callback`
   - Copie **Client ID** y **Secret**. En la misma pantalla copie **Authorization URL** y **Token URL**.
2. **Permisos de los usuarios**: el usuario necesita en SAC permisos de planificación sobre el modelo (leer y mantener/importar datos), además de acceso de escritura a la versión y a los miembros según el Data Access Control. La aplicación no amplía ningún permiso: si SAC niega la operación, se informa al usuario.
3. **Nombres de modelos y columnas**: en `config/templates.json` cada plantilla indica el modelo por nombre (`model.name`) o, mejor, por ID (`model.id`). También indica el mapeo de encabezados a dimensiones. Revíselos contra los modelos reales. La app valida la metadata al cargar y avisa si una columna no existe.

---

## 4. Instalación y ejecución

Requiere **Node.js 20 o superior**.

```bash
cd sac-data-loader
npm install
cp .env.example .env      # complete las variables de SAC y SESSION_SECRET
npm start                 # http://localhost:3000
```

### Modo demostración (sin SAC real)

```bash
npm run demo
```

Levanta un **SAC simulado** (login OAuth, Data Import y Data Export API) y la aplicación en `http://localhost:3000`.

- Usuarios de prueba: `ana` / `demo` (puede cargar) y `luis` / `demo` (sin permiso de escritura).
- Hay archivos de ejemplo en `samples/`: válidos y con errores a propósito. Se regeneran con `node scripts/make-samples.js`.

### Pruebas

```bash
npm test
```

18 pruebas cubren:

- **Unitarias:** números, periodos, lectura de archivos y validador.
- **De extremo a extremo contra el SAC simulado:** login con PKCE, validación, validación en SAC, carga, *Borrar y reemplazar* con confirmación, cancelación, rechazo de filas en SAC, usuario sin permisos, renovación y revocación del token, protección anti-CSRF y aislamiento entre usuarios.

---

## 5. Plantillas (`config/templates.json`)

| Campo | Uso |
|---|---|
| `model` | `{ "id": "..." }` o `{ "name": "..." }`; `{ "selectable": true }` permite elegir el modelo (plantilla GENERICO) |
| `sheet` | Hoja del libro Excel |
| `layout` | `wide` (un periodo por columna), `long` (columnas `Date` e `Importe`) o `auto` |
| `columns` | Encabezado del archivo → columna del modelo. El texto entre paréntesis del encabezado se ignora: `Cebes_CL (componente)`. `"byName"` = los encabezados se llaman igual que las columnas del modelo |
| `fixedValues` | Valor para todas las filas, p. ej. `"Cliente": "#"` |
| `contextFields` | Etiquetas del bloque superior (`Versión:`, `Moneda:`, `Auditoría:`) → columna del modelo |
| `allowedValues` | Lista de valores permitidos por columna |
| `ignoreColumns` | Columnas que se leen pero no se cargan (advertencia) |
| `importMethods` | `Update` (reemplaza el valor de la celda), `CleanAndReplace` (borra primero el alcance) o `Append` (suma) |
| `cleanAndReplaceScope` | Dimensiones que definen qué se borra con `CleanAndReplace` |
| `rules` | `allowNegative`, `skipZeroValues`, `maxDecimals` |
| `periodRange` | `{ "from": "202601", "to": "202612" }` |
| `measure`, `versionColumn`, `dateColumn` | Sólo si no se pueden deducir de la metadata del modelo |
| `reverseSignByAccountType` | Invierte el signo según el tipo de cuenta (opción del Data Import API) |

---

## 6. Seguridad

- **OAuth Authorization Code + PKCE + `state`**. La sesión se regenera al iniciar sesión.
- Los tokens de SAC y el client secret **se quedan en el servidor**. El navegador sólo tiene una cookie de sesión `HttpOnly`, `SameSite=Lax` y `Secure` en HTTPS.
- Protección CSRF con la cabecera `X-Requested-With` obligatoria en todo POST. No se habilita CORS.
- Cabeceras de seguridad: CSP estricta sin scripts ni estilos en línea, `X-Frame-Options: DENY`, `nosniff` y `no-referrer`.
- Límite de tamaño, de extensión y de filas. Un usuario no puede consultar ni ejecutar el archivo validado de otro.
- El reporte CSV neutraliza fórmulas (`=`, `+`, `-`, `@`) para evitar inyección en Excel.
- La auditoría (`logs/audit.log`, JSON por línea) **no guarda valores financieros**: sólo conteos y la huella SHA-256 del archivo.

**Despliegue**
- Publique detrás de HTTPS (`APP_BASE_URL=https://…`, `TRUST_PROXY=true` si hay proxy inverso).
- Las sesiones y los archivos validados se guardan en memoria. Use **una sola instancia**, o cambie el store de `express-session` por Redis si necesita varias.
- También puede desplegarse en SAP BTP (Cloud Foundry) como aplicación Node.js.

---

## 7. Limitaciones conocidas

- `.xls` (Excel 97-2003) no se soporta: guarde el archivo como `.xlsx`.
- Se carga **una medida** por plantilla (`Importe`).
- `privateFactData` (versiones privadas) sólo aplica a usuarios de negocio. Se usa automáticamente cuando la versión empieza por `private.`.
- Si SAC no expone el maestro de una dimensión por el Data Export API, se avisa y esos códigos los valida SAC en el paso 3.
- **PL-02:** el modelo de ingresos no tiene la dimensión de tipo de residuo, así que la columna `Tipo_Residuo` se ignora con advertencia. Agregue la dimensión al modelo si se requiere.
- SAC guarda los jobs 15 días y permite hasta 100 jobs activos por usuario y modelo. La app elimina los jobs cancelados o rechazados.

---

## 8. Estructura

```
server.js               arranque
src/app.js              rutas, sesión, OAuth, orquestación
src/oauth.js            Authorization Code + PKCE, refresh
src/sacClient.js        cliente Data Import / Export API (CSRF, cookies, errores)
src/loader.js           job en dos etapas: prepare (envío + validate) y run
src/parser.js           lectura de Excel / CSV
src/validator.js        motor de validación
src/numbers.js          números es-CO / en
src/periods.js          periodos → YYYYMM
src/meta.js             metadata del modelo
src/config.js, audit.js configuración y auditoría
public/                 interfaz (HTML/CSS/JS sin dependencias)
config/templates.json   catálogo de plantillas PL-01…PL-08 y GENERICO
test/                   pruebas y SAC simulado
samples/                archivos de ejemplo
```

## Referencias

- SAP Help: *Data Import Service API*: <https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/14cac91febef464dbb1efce20e3f1613/fe6efb8aba9444c6a3ce21eef02bba62.html>
- SAP Community: *Getting authenticated with Data Export and Data Import APIs*: <https://community.sap.com/t5/technology-blog-posts-by-sap/getting-authenticated-with-data-export-and-data-import-api-s/ba-p/14060183>
