# Cargador de datos a SAP Analytics Cloud

Aplicación web (Node.js) para que los usuarios de planeación carguen archivos **Excel (.xlsx/.xlsm)** o **planos (.csv/.txt)** a los modelos de planeación de SAC.

- **Cada usuario inicia sesión con sus propias credenciales de SAC** (OAuth 2.0 Authorization Code + PKCE). La aplicación **nunca ve la contraseña**: el usuario se autentica en la página de login de SAC o de su IdP corporativo. Toda carga se hace con el token de ese usuario, así que SAC aplica sus roles y su Data Access Control.
- **Valida el archivo antes de escribir** en SAC: primero una validación local y luego una validación dentro de SAC. Sólo si ambas pasan se habilita la carga, y el usuario debe confirmarla.
- **Todo o nada**: si SAC rechaza una sola fila, se cancela el job completo y no se escribe nada.
- Deja una **bitácora de auditoría** con quién cargó qué, cuándo, a qué modelo y versión, y el resultado.

Usa el **Data Import API** de SAC (`/api/v1/dataimport`) para escribir y el **Data Export API** (`/api/v1/dataexport`) para leer los maestros de las dimensiones.

**Varias empresas, un mismo código.** La variable `BRAND` del `.env` elige la empresa: nombre, logo, colores y modelos de SAC.

| `BRAND` | Empresa | Identidad visual | Modelos |
|---|---|---|---|
| `ciudadlimpia` (por defecto) | Ciudad Limpia | ciudadlimpia.com: verdes, botones redondeados | `config/templates.json` |
| `fanalca` | Fanalca | fanalca.com: azul marino #071D49, azul #005EB8, franja azul–cian, títulos livianos | `brands/fanalca/templates.json` |

Cada marca vive en `brands/<marca>/`: `brand.json` (textos, carpeta y puerto del instalador), `theme.css` (colores), `img/` (logos y favicon), `icon.ico` (ícono de Windows) y el catálogo de modelos.

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
| 1. Archivo | Modelo (Gastos, Ingreso, EEFF u otro), versión (lista leída de SAC; `public.Actual` bloqueada), método de carga y archivo. La pantalla muestra las columnas que debe traer el archivo |
| 2. Validación local | Resumen, hallazgos (errores y advertencias con fila, columna y valor), totales por periodo, vista previa y reporte CSV descargable |
| 3. Validación en SAC | Resultado de SAC. Con *Borrar y reemplazar*, cuántos registros se borrarán; se exige confirmarlo |
| 4. Carga | Estado del job y número de registros escritos |

---

## 2. Validaciones

**Del archivo**
- Extensión permitida (.xlsx, .xlsm, .csv, .txt) y contenido real del archivo (un Excel renombrado se detecta). Tamaño y número de filas máximos.
- Codificación (UTF-8, UTF-8 con BOM, UTF-16, Windows-1252) y separador (`;` `,` tabulador `|`) detectados automáticamente. Comillas sin cerrar.
- En Excel se lee la primera hoja visible con datos.

**De la estructura**
- Fila de encabezados encontrada automáticamente (puede haber títulos o una fila `Versión:` arriba).
- Columnas obligatorias: todas las dimensiones del modelo deben venir en el archivo, salvo las que tienen valor por defecto.
- Columnas desconocidas (error), columnas ignoradas como *Total* u *Observaciones* (advertencia), encabezados duplicados, columnas con datos sin encabezado.
- Periodos: `Ene 2026`, `ene-26`, `Enero 2026`, `Jan 2026`, `202601`, `2026-01`, `01/2026` o fechas de Excel. Periodos inválidos, repetidos o fuera de rango.
- Las columnas se comparan con la metadata real del modelo en SAC.

**De la versión**
- Obligatoria (sin versión, SAC cargaría en `public.Actual`).
- Versiones bloqueadas (`BLOCKED_VERSIONS`).
- La versión del archivo, en el bloque de contexto o en una columna, debe coincidir con la seleccionada.
- Debe existir en el modelo.

**De cada fila**
- Dimensiones vacías, fechas en lugar de códigos, caracteres de control, espacios de más (se eliminan y se avisa), longitud máxima de la columna.
- Valores permitidos, si se configuran.
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
3. **Modelos**: `config/templates.json` ya trae los tres modelos de Ciudad Limpia con su ID y su nombre. Si se crea otro modelo, agréguelo ahí o use *Otro modelo*.

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

Levanta un **SAC simulado** (login OAuth, Data Import y Data Export API) y la aplicación en `http://localhost:3000`. Para ver la versión de Fanalca: `BRAND=fanalca npm run demo` (en Windows: `set BRAND=fanalca` y luego `npm run demo`).

- Usuarios de prueba: `ana` / `demo` (puede cargar) y `luis` / `demo` (sin permiso de escritura).
- Hay archivos de ejemplo en `samples/` (Ciudad Limpia) y `samples/fanalca/` (Fanalca) para Gastos, Ingresos y EEFF: válidos y con errores a propósito. Se regeneran con `node scripts/make-samples.js`. Los códigos de miembros son los del simulador; en SAC real use sus códigos.

### Pruebas

```bash
npm test
```

18 pruebas cubren:

- **Unitarias:** números, periodos, lectura de archivos y validador.
- **De extremo a extremo contra el SAC simulado:** login con PKCE, validación, validación en SAC, carga, *Borrar y reemplazar* con confirmación, cancelación, rechazo de filas en SAC, usuario sin permisos, renovación y revocación del token, protección anti-CSRF y aislamiento entre usuarios.

---

## 5. Modelos configurados (`config/templates.json`)

No se necesitan plantillas especiales: el archivo trae como **encabezados los nombres reales de las dimensiones** del modelo. Los periodos pueden venir de dos formas:
- **Meses como columnas**, por ejemplo `Ene 2026`, `Feb 2026` o `202601`.
- **Una columna `Date` y otra `Importe`**, con un registro por fila.

La versión se elige en pantalla. Si el archivo trae una columna `Version`, debe coincidir con la seleccionada.

| Carga a | Modelo en SAC | Columnas del archivo |
|---|---|---|
| Gastos Ciudad Limpia | Modelo Gastos Ciudad Limpia | `Sociedad_CL`, `Cecos_CL`, `Cebes_CL`, `Cuentas_Egresos_CL`, `Auditoria_CL`, `Moneda_CL` + periodos |
| Ingreso Ciudad Limpia | Modelo Ingreso Ciudad Limpia | `Sociedad_CL`, `Cebes_CL`, `Ratio_CL`, `Auditoria_CL`, `Moneda_CL` + periodos. `Cliente` y `Regional` son opcionales: si no vienen, se carga `#`. Permite *Borrar y reemplazar* |
| EEFF Ciudad Limpia | Modelo EEFF Ciudad Limpia | `Sociedad_CL`, `Cuentas_EF_CL`, `Cebes_CL`, `Cecos_CL`, `Auditoria_CL`, `Moneda_CL` + periodos |
| Otro modelo | Se elige de la lista de modelos del usuario | Las dimensiones de ese modelo + periodos |

**Fanalca** (`BRAND=fanalca`, `brands/fanalca/templates.json`):

| Carga a | Modelo en SAC (ID) | Columnas del archivo |
|---|---|---|
| Ingresos Fanalca | Modelo Ingresos FANALCA (`Couh7ojg5e54rh2d4udijq6o83k`) | `Sociedades`, `Cebes`, `Ratio`, `Auditoria`, `Moneda` + periodos. `Clientes` y `Referencias` son opcionales (si no vienen se carga `#`). Permite *Borrar y reemplazar* (alcance: Version, Date, Sociedades, Auditoria) |
| Gastos Fanalca | Modelo Gastos FANALCA (`Cunejii8r2d7vr4ldq2ousgfg7f`) | `Sociedades`, `Cecos`, `Cebes`, `Cuentas_Egresos`, `Auditoria`, `Moneda` + periodos |
| EEFF Fanalca | Modelo EEFF FANALCA (`C2kgen7fqc13vleoibl06hk4j7o`) | `Sociedades`, `Cuentas_EF`, `Cebes`, `Auditoria`, `Moneda` + periodos |
| Otro modelo | Se elige de la lista de modelos del usuario | Las dimensiones de ese modelo + periodos |

El modelo se busca por su **ID**, tomado de la URL del Modeler, y si ese ID no aparece, por su **nombre**. Las columnas `Total`, `Observaciones` y `Comentarios` se ignoran con una advertencia. Cualquier otra columna desconocida es un error, porque puede ser un mes o una dimensión mal escrita.

Campos disponibles por modelo:

| Campo | Uso |
|---|---|
| `model` | `{ "id": "...", "name": "..." }`; `{ "selectable": true }` permite elegir el modelo |
| `columns` | `"byName"` (encabezado = dimensión) o un mapeo `{ "Encabezado del archivo": "Dimensión" }` |
| `defaultValues` | Valor que se usa si la columna no viene en el archivo, p. ej. `"Cliente": "#"` |
| `fixedValues` | Valor que se aplica siempre |
| `importMethods` | `Update` (reemplaza el valor de la celda), `CleanAndReplace` (borra primero el alcance) o `Append` (suma) |
| `cleanAndReplaceScope` | Dimensiones que definen qué se borra con `CleanAndReplace` |
| `allowedValues` | Lista de valores permitidos por columna |
| `rules` | `allowNegative`, `skipZeroValues`, `maxDecimals` |
| `periodRange` | `{ "from": "202601", "to": "202612" }` |
| `layout` | `auto` (por defecto), `wide` o `long` |

## 6. Seguridad

- **OAuth Authorization Code + PKCE + `state`**. La sesión se regenera al iniciar sesión.
- Los tokens de SAC y el client secret **se quedan en el servidor**. El navegador sólo tiene una cookie de sesión `HttpOnly`, `SameSite=Lax` y `Secure` en HTTPS.
- Protección CSRF con la cabecera `X-Requested-With` obligatoria en todo POST. No se habilita CORS.
- Cabeceras de seguridad: CSP estricta sin scripts ni estilos en línea, `X-Frame-Options: DENY`, `nosniff` y `no-referrer`.
- Límite de tamaño, de extensión y de filas. Un usuario no puede consultar ni ejecutar el archivo validado de otro.
- El reporte CSV neutraliza fórmulas (`=`, `+`, `-`, `@`) para evitar inyección en Excel.
- La auditoría (`logs/audit.log`, JSON por línea) **no guarda valores financieros**: sólo conteos y la huella SHA-256 del archivo.

**Despliegue** (guía completa paso a paso en [`DESPLIEGUE.md`](DESPLIEGUE.md): Windows/IIS, Linux/nginx, SAP BTP, Docker e instalación en el computador de cada usuario)
- Publique detrás de HTTPS (`APP_BASE_URL=https://…`, `TRUST_PROXY=true` si hay proxy inverso).
- Las sesiones y los archivos validados se guardan en memoria. Use **una sola instancia**, o cambie el store de `express-session` por Redis si necesita varias.
- También puede desplegarse en SAP BTP (Cloud Foundry) como aplicación Node.js.

---

## 7. Limitaciones conocidas

- `.xls` (Excel 97-2003) no se soporta: guarde el archivo como `.xlsx`.
- Se carga **una medida** por modelo (`Importe`).
- `privateFactData` (versiones privadas) sólo aplica a usuarios de negocio. Se usa automáticamente cuando la versión empieza por `private.`.
- Si SAC no expone el maestro de una dimensión por el Data Export API, se avisa y esos códigos los valida SAC en el paso 3.
- La dimensión **Version** de Gastos y EEFF tiene un solo miembro. Si es `public.Actual`, que está bloqueada por defecto, cree una versión de plan o forecast en SAC o ajuste `BLOCKED_VERSIONS`.
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
src/brand.js            marca (BRAND): textos, logos, colores y modelos
src/tester/             probador de data actions (motor y ejecución contra SAC)
public/                 interfaz (HTML/CSS/JS sin dependencias): cargador (index) y probador (pruebas)
brands/                 una carpeta por empresa (ciudadlimpia, fanalca)
config/templates.json   modelos de Ciudad Limpia (Gastos, Ingreso, EEFF) y otro modelo
deploy/windows-usuario/ instalador para el computador del usuario (ZIP y .exe)
test/                   pruebas y SAC simulado
samples/                archivos de ejemplo
```

## 9. Probador de data actions (aplicación separada)

Es una **aplicación independiente del cargador**: el mismo código arrancado con `APP_MODE=probador`. Tiene su propio puerto, su `.env`, su carpeta, su acceso directo e instalador (`Instalar-ProbadorDA-<Marca>.exe`) y su Redirect URI. Para Fanalca es `http://localhost:3011/auth/callback`; para Ciudad Limpia, `http://localhost:3010/auth/callback`. El cargador no muestra ni publica nada del probador, y viceversa.

Prueba un data action con datos aleatorios en pocos segundos, sin construir historias ni cargar archivos a mano. En pantalla se eligen:
- **Modelo**, **multi action** (ID), **versión de pruebas** (lista del modelo; las bloqueadas no se pueden elegir), **periodos** (desde/hasta) y **tolerancia**.
- **Parámetros del data action**, los mismos de la multi action:
  - **Versión**: envía la versión de pruebas.
  - **Periodos**: envía los periodos elegidos.
  - **Miembro(s)**: se elige la dimensión y se buscan los miembros directamente en SAC.
  - **Número**.

  Un parámetro de tipo miembro también se puede usar en los datos de prueba con `"$ID"`. Por ejemplo, `"comun": { "Sociedades": "$Sociedad" }` o `"variar": { "Cebes": "$Cebes" }`, para que los datos aleatorios queden dentro del alcance del parámetro.
- **Datos de prueba y resultado esperado** en el JSON del caso. Se sincroniza con los formularios.

Por cada prueba:

1. **Valida la definición** del caso y **lee la estructura del modelo**.
2. **Resuelve los miembros**: listas fijas, miembros **al azar** del maestro (también filtrados por propiedad, por ejemplo `EMISOR = Y`) o los mismos de otra entrada (`@ENTRADA`). Verifica que todos existan.
3. **Genera datos aleatorios** reproducibles (con la misma **semilla**, los mismos datos) y calcula los **valores esperados** con la fórmula del caso.
4. **Limpia y carga** las entradas en la **versión de pruebas** con *CleanAndReplace* (alcance `Version + Date` por defecto). Usa el Data Import API, como el cargador.
5. **Ejecuta la multi action** que contiene el data action, con la API pública de SAC (`POST /api/v1/multiActions/<paquete>:<ID>/executions`), y espera a que termine (`GET …/executions/<id>`).
6. **Lee los resultados** con el Data Export API (`FactData` filtrado por versión, periodos y miembros).
7. **Compara** celda por celda con una tolerancia. Muestra las diferencias, los mensajes de SAC y descarga un CSV.

Con **Repeticiones** corre el mismo caso varias veces con semillas distintas. **Vista previa** hace los pasos 1 a 3 sin escribir nada en SAC.

### Preparación en SAC (una vez)
- **Cliente OAuth propio del probador** (*Interactive Usage*) con la Redirect URI de su puerto (tabla de la Opción E en `DESPLIEGUE.md`).
- **Versión de pruebas** pública en cada modelo, por ejemplo `public.PRUEBAS`. La prueba **borra sus datos** en los periodos del caso antes de cargar. Las versiones de `BLOCKED_VERSIONS` (`public.Actual`) se rechazan.
- **Multi action por data action**: SAC no tiene API pública para ejecutar un data action directamente. Cree una multi action con un paso *Data Action* y exponga el parámetro de versión, por ejemplo `TargetVersion`. Su ID tiene la forma `<paquete>:<ID>` (ejemplo de SAP: `t.TEST:CEEFOKMRUKJBY5BN47F1NS2L8G`); el ID del objeto aparece en la URL del navegador al abrir la multi action.
- La API de multi actions se usa con un **usuario de negocio** (*Interactive Usage*); SAP indica que no admite *client credentials*.
- **Permisos** del usuario: escribir en el modelo y ejecutar la multi action.

### Definición del caso (JSON)
```json
{
  "id": "FN_PXQ_VENTAS", "nombre": "P×Q ventas",
  "modelo": "Couh7ojg5e54rh2d4udijq6o83k",
  "multiAction": "t.XXXX:CXXXXXXXXXXXXXXXXXXXXXXXX",
  "version": "public.PRUEBAS",
  "periodos": { "desde": "202601", "hasta": "202603" },
  "parametros": [
    { "id": "TargetVersion", "tipo": "version" },
    { "id": "Sociedad", "tipo": "miembro", "dimension": "Sociedades", "valor": ["FN_MOTOS"], "multiple": false }
  ],
  "comun": { "Auditoria": "PRESUPUESTO_EXCEL", "Moneda": "COP", "Sociedades": "$Sociedad" },
  "entradas": [
    { "nombre": "PRECIO", "fijo": { "Ratio": "PRECIO" }, "variar": { "Sociedades": { "aleatorio": 1 }, "Cebes": { "aleatorio": 2 } }, "min": 5000000, "max": 15000000, "decimales": 0 },
    { "nombre": "UNIDADES", "fijo": { "Ratio": "UNIDADES" }, "variar": { "Sociedades": "@PRECIO", "Cebes": "@PRECIO" }, "min": 10, "max": 2000, "decimales": 0 }
  ],
  "esperado": [
    { "nombre": "VENTAS", "fijo": { "Ratio": "ING_VENTAS_NAL" }, "variar": { "Sociedades": "@PRECIO", "Cebes": "@PRECIO" }, "formula": "v('PRECIO') * v('UNIDADES')" }
  ],
  "tolerancia": 0.01
}
```

| Campo | Uso |
|---|---|
| `comun` / `fijo` | Miembros fijos (para todas las celdas / para un grupo). Las dimensiones que no se indiquen se cargan con `#` |
| `variar` | Lista de miembros, `{ "aleatorio": n, "filtro": { "PROPIEDAD": "valor" } }` o `"@ENTRADA"` |
| `parametros` | Parámetros de la multi action: `{ "id", "tipo": "version" \| "periodos" \| "miembro" \| "numero", "dimension", "valor", "multiple", "jerarquia" }`. También se acepta el formato de la API de SAP `{ "parameterId", "value" }`, que se envía tal cual, con `{{version}}` y `"{{periodos}}"` reemplazados |
| `limpieza.alcance` | Dimensiones del *CleanAndReplace* (por defecto `["Version", "Date"]`) |
| `esperaMaxSeg` | Tiempo máximo de espera de la multi action (por defecto 600) |

**Funciones de las fórmulas** (se calculan por celda esperada):

| Función | Valor |
|---|---|
| `v('ENTRADA')` | Valor de la entrada en el mismo periodo y con los mismos miembros en las dimensiones que esa entrada varía |
| `sum('ENTRADA', { Dim: 'x' })` | Suma de la entrada en el mismo periodo (filtro opcional, por ejemplo `{ Cuentas_Egresos_CL: c.Cuentas_Egresos_CL }`) |
| `c.<Dimensión>`, `c.Date` | Miembros de la celda que se calcula |
| `round(x, dec)`, `abs`, `min`, `max`, `pow`, `sqrt`, `Math` | Funciones numéricas |

Ejemplos incluidos, en `brands/<marca>/pruebas.json`: **P×Q de residuos** y **distribución de gastos por km** (Ciudad Limpia; emisores y receptores al azar por las propiedades `EMISOR` y `RECEPTOR`), **P×Q de ventas** y un **data action con un error a propósito** (Fanalca). Los modelos usan sus IDs reales. Reemplace `multiAction` por el de su multi action y los códigos de miembros por los suyos: los IDs `t.DEMO:…` solo existen en el modo demostración.

**Limitaciones:** la versión de pruebas debe ser pública; la lectura agrega las dimensiones que el resultado no indica; si el parámetro de fecha de la multi action usa jerarquía, los `memberIds` deben ser rutas (vea el ejemplo de SAP).

Fuentes: [API de multi actions (SAP Help)](https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/14cac91febef464dbb1efce20e3f1613/e5ade1ed7c274d929a18bcc859102c40.html), [iniciar una ejecución](https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/14cac91febef464dbb1efce20e3f1613/80680a8a1ca4460caad7f54675abc091.html), [estado de la ejecución](https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/14cac91febef464dbb1efce20e3f1613/ff7815c62f284af890ef4d21f06ff460.html), [Introduction of SAC Multi Actions Public API (SAP Community)](https://community.sap.com/t5/technology-blog-posts-by-sap/introduction-of-sac-multi-actions-public-api/ba-p/13577173), [Data Export API (SAP Community)](https://community.sap.com/t5/technology-blog-posts-by-sap/data-export-api-a-tour-of-the-api/ba-p/13567104).

## Referencias

- SAP Help: *Data Import Service API*: <https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/14cac91febef464dbb1efce20e3f1613/fe6efb8aba9444c6a3ce21eef02bba62.html>
- SAP Community: *Getting authenticated with Data Export and Data Import APIs*: <https://community.sap.com/t5/technology-blog-posts-by-sap/getting-authenticated-with-data-export-and-data-import-api-s/ba-p/14060183>
