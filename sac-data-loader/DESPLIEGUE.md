# Guía de despliegue en un servidor

Esta guía explica cómo publicar el **Cargador de datos a SAC** en un servidor, para que el equipo de planeación de Ciudad Limpia lo use desde el navegador con una dirección fija, por ejemplo `https://cargas-sac.ciudadlimpia.com`. Así nadie tiene que instalar Node.js en su computador.

Cada usuario sigue entrando con **sus propias credenciales de SAP Analytics Cloud**. El servidor nunca ve contraseñas y cada carga se hace con los permisos de quien la ejecuta.

---

## 1. Cómo queda montado

```
 Usuarios (navegador)
        │  HTTPS 443
        ▼
 ┌─────────────────────────────┐      HTTPS 443       ┌──────────────────────────────┐
 │ Proxy inverso con certificado│ ───────────────────▶ │ SAP Analytics Cloud          │
 │ (IIS, nginx o SAP BTP)       │                      │  · <tenant>.analytics.cloud.sap
 │        │ HTTP 127.0.0.1:3000 │                      │  · <tenant>.authentication…  │
 │        ▼                     │                      └──────────────────────────────┘
 │ Aplicación Node.js (servicio)│
 └─────────────────────────────┘
```

- La **aplicación** escucha en el puerto 3000, solo dentro del servidor.
- El **proxy inverso** pone el certificado HTTPS y reenvía el tráfico a la aplicación.
- La aplicación llama a SAC **desde el servidor**. Por eso el servidor necesita salida a internet hacia el tenant de SAC.

**Elija una opción:**

| Opción | Cuándo usarla |
|---|---|
| **A. Windows Server + IIS** | Es el caso más común en redes corporativas Windows |
| **B. Linux + nginx** | Si TI prefiere servidores Linux |
| **C. SAP BTP (Cloud Foundry)** | Si Fanalca tiene subcuenta BTP. No requiere servidor propio y trae HTTPS incluido |
| **D. Docker** | Si TI ya opera contenedores |

---

## 2. Antes de empezar

| # | Qué | Quién |
|---|---|---|
| 1 | **Nombre DNS** de la aplicación, p. ej. `cargas-sac.ciudadlimpia.com`, apuntando al servidor | TI / redes |
| 2 | **Certificado HTTPS** para ese nombre (corporativo o Let's Encrypt). En BTP no hace falta | TI |
| 3 | **Servidor**: 1 vCPU, 2 GB de RAM y 2 GB de disco. Windows Server 2019+ o Linux (Ubuntu 22.04+ / RHEL 8+) | TI |
| 4 | **Node.js 22 o 24 LTS** de 64 bits (https://nodejs.org) | TI |
| 5 | **Salida HTTPS (443)** desde el servidor hacia el tenant de SAC y su servidor de autenticación: los hosts de `SAC_TENANT_URL` y `SAC_TOKEN_URL`, p. ej. `fanalca-clpriv-sac.us21.analytics.cloud.sap` y `fanalca-clpriv-sac.authentication.us21.hana.ondemand.com` | TI / seguridad |
| 6 | **Cliente OAuth de producción** en SAC (paso 3) | Administrador SAC |
| 7 | **Acceso de red de los usuarios**: por lo general solo red interna o VPN | TI / seguridad |

> **Una sola instancia.** Las sesiones se guardan en la memoria del proceso. No ponga dos copias de la aplicación detrás de un balanceador. Si el servicio se reinicia, los usuarios deben iniciar sesión de nuevo.

---

## 3. Cliente OAuth de producción en SAC

Cree un cliente **nuevo** para el servidor. No reutilice el de pruebas en `localhost`: así cada entorno tiene su propio secreto.

1. En SAC vaya a **Sistema → Administración → App Integration → OAuth Clients → Add a New OAuth Client**.
2. Llene:
   - **Name:** `Cargador de datos - Producción`
   - **Purpose:** `Interactive Usage`
   - **Authorization Grant:** Authorization Code
   - **Redirect URI:** `https://cargas-sac.ciudadlimpia.com/auth/callback`. Es la URL final más `/auth/callback`, exactamente igual, sin barra al final.
3. Guarde y copie el **Client ID** y el **Secret**. Entréguelos a TI por un canal seguro, nunca por correo ni chat.
4. Cuando el servidor funcione, **borre o regenere el Secret** del cliente de pruebas.

---

## 4. Configuración de producción (`.env`)

La aplicación lee su configuración del archivo `.env` en la carpeta `sac-data-loader`, o de variables de entorno del sistema; las del sistema tienen prioridad. Parta de `.env.example`.

| Variable | Valor en el servidor |
|---|---|
| `APP_BASE_URL` | `https://cargas-sac.ciudadlimpia.com`, la URL exacta que usarán los usuarios |
| `HOST` | `127.0.0.1` en opciones A y B, para que el puerto 3000 no quede expuesto. **No la ponga** en BTP ni Docker |
| `PORT` | `3000` (en BTP la asigna la plataforma) |
| `TRUST_PROXY` | `true`. Obligatorio detrás de IIS, nginx o BTP |
| `SESSION_SECRET` | Clave **nueva**: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` |
| `SAC_TENANT_URL` | URL del tenant **productivo** |
| `SAC_AUTHORIZE_URL` / `SAC_TOKEN_URL` | Las de *App Integration* del tenant productivo |
| `SAC_CLIENT_ID` / `SAC_CLIENT_SECRET` | Las del cliente del paso 3 |
| `BLOCKED_VERSIONS` | `public.Actual` |
| `SAC_DEBUG` | `false` |
| `AUDIT_FILE` | Déjelo vacío en A y B (queda en `logs/audit.log`); use `stdout` en C y D |

**Proteja el `.env`:** solo el administrador y la cuenta del servicio deben poder leerlo, porque contiene el Secret de SAC.

---

## Opción A: Windows Server + IIS

### A1. Instalar la aplicación
1. Instale **Node.js LTS (x64)** desde https://nodejs.org con las opciones por defecto.
2. Copie la carpeta `sac-data-loader` del ZIP a `C:\apps\sac-data-loader`, **sin** la carpeta `node_modules`.
3. Abra `cmd` **como administrador**:
   ```
   cd C:\apps\sac-data-loader
   npm ci --omit=dev
   ```
4. Cree `C:\apps\sac-data-loader\.env` con los valores de la sección 4. Recuerde `HOST=127.0.0.1` y `TRUST_PROXY=true`.
5. Limite los permisos del archivo: clic derecho en `.env` → **Propiedades → Seguridad**. Deje solo a *Administradores* y a la cuenta del servicio.
6. Prueba rápida:
   ```
   node server.js
   ```
   Debe decir `Cargador SAC escuchando en https://cargas-sac… (puerto 3000, interfaz 127.0.0.1)`. Detenga la prueba con `Ctrl + C`.

### A2. Dejarla como servicio de Windows
1. Descargue **NSSM** (https://nssm.cc), copie `nssm.exe` (versión win64) a `C:\Windows\System32`.
2. Revise las rutas en `deploy\windows-iis\instalar-servicio.cmd` y ejecútelo **como administrador**.
3. En **Servicios** (`services.msc`) debe aparecer *Cargador de datos a SAC - Ciudad Limpia* en estado **En ejecución** e **inicio automático**.
4. **Recomendado:** ejecute el servicio con una cuenta de servicio dedicada, sin privilegios de administrador. Se configura en Servicios → Propiedades → Iniciar sesión, o con `nssm set SacDataLoader ObjectName`. Esa cuenta debe poder leer la carpeta y escribir en `logs\`.

### A3. Configurar IIS como proxy HTTPS
1. Instale el rol **IIS** (Administrador del servidor → Agregar roles → *Servidor web (IIS)*).
2. Instale los módulos de Microsoft **URL Rewrite** y **Application Request Routing (ARR)**:
   - https://www.iis.net/downloads/microsoft/url-rewrite
   - https://www.iis.net/downloads/microsoft/application-request-routing
3. En el Administrador de IIS, en el **nodo del servidor**:
   1. Abra **Application Request Routing Cache → Server Proxy Settings…**.
   2. Marque **Enable proxy**.
   3. Ponga **Time-out (seconds) = 300**.
   4. Pulse **Aplicar**.
4. Todavía en el nodo del servidor:
   1. Abra **URL Rewrite → View Server Variables… → Add…**.
   2. Agregue `HTTP_X_FORWARDED_PROTO`.
5. Cree un **sitio** nuevo, por ejemplo con carpeta física `C:\inetpub\sac-data-loader`:
   - **Enlace HTTPS**, puerto 443, host `cargas-sac.ciudadlimpia.com`, con el certificado instalado.
   - **Enlace HTTP**, puerto 80, mismo host. Sirve para redirigir a HTTPS.
6. Copie `deploy\windows-iis\web.config` a `C:\inetpub\sac-data-loader\`.
7. En el **Firewall de Windows**, permita la entrada solo por **443** y **80**. El puerto 3000 no debe abrirse.

Continúe en la **sección 5 (verificación)**.

---

## Opción B: Linux + nginx + systemd

```bash
# 1. Node.js LTS (ejemplo Ubuntu, con el repositorio oficial de NodeSource)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs nginx

# 2. Usuario de servicio y carpeta
sudo useradd --system --home /opt/sac-data-loader --shell /usr/sbin/nologin sacloader
sudo mkdir -p /opt/sac-data-loader
sudo cp -r sac-data-loader/. /opt/sac-data-loader/     # el "/." copia también .env.example
cd /opt/sac-data-loader
sudo rm -rf node_modules .env                          # no llevar dependencias ni .env de pruebas
sudo npm ci --omit=dev
sudo mkdir -p logs

# 3. Configuración (valores de la sección 4, con HOST=127.0.0.1 y TRUST_PROXY=true)
sudo cp .env.example .env && sudo nano .env
sudo chown -R sacloader:sacloader /opt/sac-data-loader
sudo chmod 600 .env

# 4. Servicio
sudo cp deploy/linux/sac-data-loader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sac-data-loader
sudo systemctl status sac-data-loader        # debe decir "active (running)"

# 5. nginx con HTTPS (ajuste el nombre y las rutas del certificado en el archivo)
sudo cp deploy/linux/nginx-sac-data-loader.conf /etc/nginx/conf.d/sac-data-loader.conf
sudo nginx -t && sudo systemctl reload nginx
```

En el firewall abra solo 80 y 443. Luego continúe en la **sección 5**.

---

## Opción C: SAP BTP, Cloud Foundry

**Requisitos:**
- Subcuenta BTP con **Cloud Foundry** habilitado y un espacio (*space*) con cuota de al menos 256 MB.
- **CF CLI v8** instalado.

1. Inicie sesión con el **API Endpoint** que muestra la subcuenta en el cockpit de BTP (Overview):
   ```
   cf login -a https://api.cf.<región>.hana.ondemand.com
   ```
2. Desde la carpeta `sac-data-loader`, suba la aplicación **sin arrancarla**. Cambie `host` por un nombre libre y use el dominio de su región:
   ```
   cf push -f deploy/btp/manifest.yml --var host=cargas-sac-cl --var domain=cfapps.us21.hana.ondemand.com --no-start
   ```
   La URL quedará como `https://cargas-sac-cl.cfapps.us21.hana.ondemand.com`. Esa es la base de la **Redirect URI** del paso 3: `https://cargas-sac-cl.cfapps.us21.hana.ondemand.com/auth/callback`.
3. Cargue los secretos. No van en el manifiesto ni en el código:
   ```
   cf set-env sac-data-loader SAC_TENANT_URL "https://<tenant>.analytics.cloud.sap"
   cf set-env sac-data-loader SAC_AUTHORIZE_URL "https://<subdominio>.authentication.<región>.hana.ondemand.com/oauth/authorize"
   cf set-env sac-data-loader SAC_TOKEN_URL "https://<subdominio>.authentication.<región>.hana.ondemand.com/oauth/token"
   cf set-env sac-data-loader SAC_CLIENT_ID "<client id>"
   cf set-env sac-data-loader SAC_CLIENT_SECRET "<secret>"
   cf set-env sac-data-loader SESSION_SECRET "<clave de 64 caracteres>"
   ```
4. Arranque y revise:
   ```
   cf start sac-data-loader
   cf logs sac-data-loader --recent
   ```

**Notas:**
- BTP ya entrega HTTPS y el manifiesto deja `TRUST_PROXY=true`. No configure IIS ni nginx.
- La auditoría sale por la salida estándar (`cf logs`). Para conservarla más de unos días, conecte el servicio **SAP Cloud Logging** o exporte los registros.
- Mantenga `instances: 1`.

---

## Opción D: Docker

```bash
cd sac-data-loader
docker build -t sac-data-loader .
docker run -d --name sac-data-loader --restart unless-stopped \
  --env-file /ruta/segura/produccion.env \
  -p 127.0.0.1:3000:3000 sac-data-loader
```

- En `produccion.env` **no** ponga `HOST=127.0.0.1`. El contenedor debe escuchar en todas sus interfaces; el `-p 127.0.0.1:…` ya limita el acceso.
- Delante del contenedor va un proxy HTTPS (nginx o IIS) como en las opciones A o B, o el balanceador de su plataforma.
- La auditoría sale por `docker logs sac-data-loader`.

---

## 5. Verificación después del despliegue

| # | Prueba | Resultado esperado |
|---|---|---|
| 1 | Abrir `https://cargas-sac…/healthz` | Muestra `ok` |
| 2 | Abrir `http://cargas-sac…` (sin la *s*) | Redirige a `https://` |
| 3 | Abrir la URL | Pantalla de inicio con el logo de Ciudad Limpia |
| 4 | **Iniciar sesión con SAP Analytics Cloud** | Pasa por el login de SAC y vuelve con **su nombre** arriba a la derecha |
| 5 | Cargar un archivo pequeño a una versión de prueba | Validación local ✔ → Validación en SAC ✔ → Carga completada |
| 6 | Revisar la auditoría: `logs\audit.log` (A/B), `cf logs` (C) o `docker logs` (D) | Aparecen las líneas `LOGIN`, `VALIDACION`, `PREPARACION` y `CARGA` con su usuario |
| 7 | Desde otro equipo, abrir `http://<servidor>:3000` | **No debe responder**, porque el puerto está cerrado |
| 8 | Probar con un usuario sin permiso de escritura en el modelo | La validación en SAC muestra que no tiene permisos y no se carga nada |

---

## 6. Actualizar a una versión nueva

1. **Avise a los usuarios.** Al reiniciar, las sesiones se cierran y las validaciones en curso se pierden.
2. Respalde `.env` y la carpeta `logs`.
3. Detenga el servicio:
   - Windows: `nssm stop SacDataLoader`
   - Linux: `sudo systemctl stop sac-data-loader`
4. Reemplace los archivos de la aplicación. **Conserve `.env` y `logs\`**.
5. Instale las dependencias con `npm ci --omit=dev` y arranque de nuevo:
   - Windows: `nssm start SacDataLoader`
   - Linux: `sudo systemctl start sac-data-loader`
6. En BTP basta con `cf push -f deploy/btp/manifest.yml --var host=… --var domain=…`. Las variables de `cf set-env` se conservan.
7. Repita las pruebas 1, 3 y 4 de la sección 5.

---

## 7. Operación y seguridad

- **Registros:**
  - `logs\servicio.log` en Windows (lo rota NSSM a los 10 MB) o `journalctl -u sac-data-loader` en Linux.
  - La auditoría en `logs\audit.log` no guarda valores financieros; conviene respaldarla con la política de TI.
- **Aviso esperado al arrancar:** `MemoryStore is not designed for a production environment`. Es normal con una sola instancia, y la aplicación limpia las sesiones vencidas cada minuto.
- **Secretos:**
  - Rote el Secret de SAC y `SESSION_SECRET` al menos una vez al año y cuando alguien que los conocía deje el equipo.
  - Para rotar el Secret: genere uno nuevo en *App Integration*, actualice `.env` (o `cf set-env`) y reinicie.
- **Certificado HTTPS:** renuévelo antes de su vencimiento (en BTP es automático).
- **Actualizaciones de Node.js:** aplique las versiones de parche LTS cada mes y ejecute `npm audit --omit=dev` al actualizar la aplicación.
- **Acceso:** publique la aplicación solo en la red interna o VPN, salvo que seguridad apruebe exponerla a internet.
- **Versiones bloqueadas:** mantenga `BLOCKED_VERSIONS=public.Actual` para que nadie sobrescriba datos que vienen de S/4HANA.
- **Diagnóstico:** `SAC_DEBUG=true` solo mientras se investiga un error; luego vuelva a `false` y reinicie.

---

## 8. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| Después del login de SAC vuelve a la pantalla de inicio con *"La solicitud de inicio de sesión no es válida o expiró"* | La cookie segura no llega: el proxy no envía `X-Forwarded-Proto: https`, falta `TRUST_PROXY=true`, o el usuario entró por una URL distinta a `APP_BASE_URL` | Revise `TRUST_PROXY=true`. En IIS, confirme que la variable `HTTP_X_FORWARDED_PROTO` está permitida (A3, paso 4). En nginx, confirme `proxy_set_header X-Forwarded-Proto $scheme`. Entre siempre por la URL exacta de `APP_BASE_URL` |
| SAC muestra un error de `redirect_uri` | La Redirect URI del cliente OAuth no coincide con `APP_BASE_URL` + `/auth/callback` | Corríjala en *App Integration*. Debe ser idéntica, con `https` y sin barra final |
| "SAC no aceptó el inicio de sesión…" | Client ID, Secret o Token URL incorrectos | Revise `.env` o `cf set-env` y reinicie |
| "No fue posible conectarse con SAP Analytics Cloud…" | El servidor no tiene salida a SAC (firewall o proxy corporativo) | Abra la salida 443 a los hosts de SAC. Si hay proxy corporativo, con Node 24 defina `NODE_USE_ENV_PROXY=1` y `HTTPS_PROXY=http://<proxy>:<puerto>`. Si el proxy inspecciona TLS, agregue `NODE_EXTRA_CA_CERTS=<ruta al certificado raíz corporativo .pem>` |
| Error 413 al subir el archivo | Límite de tamaño del proxy | IIS: `maxAllowedContentLength` en `web.config`. nginx: `client_max_body_size` |
| Error 502 o 503 | El servicio de la aplicación está detenido | Revise el servicio y `logs\servicio.log` o `journalctl`. Si ve `[configuración] Faltan variables…`, complete el `.env` |
| Error 504 al validar archivos grandes | El proxy cortó por tiempo | Suba el *timeout* del proxy a 300 s (ARR Server Proxy Settings / `proxy_read_timeout`) |
| Todos los usuarios deben volver a iniciar sesión | El servicio se reinició | Es normal: las sesiones viven en memoria. Programe los reinicios fuera del horario de cargas |
