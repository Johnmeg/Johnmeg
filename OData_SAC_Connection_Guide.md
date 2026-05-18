# Guía: Conexión OData Services en SAP Analytics Cloud (SAC) entre Diferentes Ambientes

## Índice

1. [Prerrequisitos](#1-prerrequisitos)
2. [Conceptos Clave](#2-conceptos-clave)
3. [Configuración en el Sistema Origen (SAP Backend)](#3-configuración-en-el-sistema-origen-sap-backend)
4. [Configuración del Agente de Datos (SAP Cloud Connector)](#4-configuración-del-agente-de-datos-sap-cloud-connector)
5. [Crear la Conexión OData en SAC](#5-crear-la-conexión-odata-en-sac)
6. [Conectar entre Diferentes Ambientes (DEV / QA / PRD)](#6-conectar-entre-diferentes-ambientes-dev--qa--prd)
7. [Crear un Modelo desde la Conexión OData](#7-crear-un-modelo-desde-la-conexión-odata)
8. [Transporte de Conexiones entre Ambientes SAC](#8-transporte-de-conexiones-entre-ambientes-sac)
9. [Verificación y Pruebas](#9-verificación-y-pruebas)
10. [Resolución de Problemas Comunes](#10-resolución-de-problemas-comunes)
11. [Buenas Prácticas](#11-buenas-prácticas)

---

## 1. Prerrequisitos

### En SAP Backend (S/4HANA, BW/4HANA, ECC)
- Usuario con rol `SAP_BC_DWB_WBDISPLAY` o equivalente con acceso a los servicios OData requeridos.
- Servicios OData activados en transacción `/IWFND/MAINT_SERVICE` o `/n/IWFND/MAINT_SERVICE`.
- Servicio expuesto y con estado **Active** en el Gateway.

### En SAP Analytics Cloud
- Usuario administrador con rol **BI Admin** o **System Owner**.
- Acceso a **System Administration > Connections**.
- Tenant SAC disponible y licenciado.

### Red / Conectividad
- Si el sistema origen es **On-Premise**: SAP Cloud Connector (SCC) instalado y operativo.
- Si el sistema origen es **Cloud**: URL pública del servicio OData accesible desde internet (HTTPS).
- Certificados SSL válidos (no auto-firmados en producción).

---

## 2. Conceptos Clave

| Término | Descripción |
|---|---|
| **OData** | Protocolo estándar REST para exponer y consumir datos (Open Data Protocol). |
| **SAC Live Connection** | Conexión en tiempo real; los datos NO se importan a SAC. |
| **SAC Import Connection** | Los datos se importan/replican en SAC para su análisis offline. |
| **Cloud Connector (SCC)** | Túnel seguro entre la red corporativa (on-premise) y SAP BTP/SAC. |
| **Ambiente** | Instancia separada del sistema: Desarrollo (DEV), Calidad (QA), Producción (PRD). |

---

## 3. Configuración en el Sistema Origen (SAP Backend)

### Paso 3.1 — Verificar el servicio OData activo

1. Ingresar a SAP GUI del sistema backend correspondiente al ambiente (DEV, QA o PRD).
2. Ejecutar la transacción:
   ```
   /n/IWFND/MAINT_SERVICE
   ```
3. Buscar el servicio por su **Technical Service Name** (ej. `ZVENTAS_SRV`).
4. Confirmar que el campo **Status** muestra el icono verde (activo).

### Paso 3.2 — Obtener la URL del servicio

1. En `/IWFND/MAINT_SERVICE`, seleccionar el servicio y hacer clic en **Call Browser**.
2. El navegador mostrará la URL base del servicio. Copiarla. Formato típico:
   ```
   https://<host>:<puerto>/sap/opu/odata/sap/<NOMBRE_SERVICIO>/
   ```
3. Verificar que al abrir la URL en un navegador se devuelva el XML del service document.

### Paso 3.3 — Asignar usuario técnico

1. Crear o utilizar un usuario técnico dedicado (tipo **System** o **Service**) en transacción `SU01`.
2. Asignar los roles mínimos necesarios para leer los EntitySets del servicio.
3. **No utilizar usuarios personales** para conexiones de sistema a sistema.

---

## 4. Configuración del Agente de Datos (SAP Cloud Connector)

> **Aplica solo si el sistema origen es On-Premise.** Si el origen es Cloud, pasar al paso 5.

### Paso 4.1 — Acceder a la administración del SCC

1. Abrir el navegador y acceder a la URL del Cloud Connector:
   ```
   https://<host-scc>:8443
   ```
2. Ingresar con credenciales de administrador del SCC.

### Paso 4.2 — Configurar el Sub-account de SAP BTP

1. Ir a **Connector > Cloud To On-Premise > Access Control**.
2. Verificar que el sub-account de SAP BTP (asociado a SAC) esté conectado:
   - Estado: **Connected** (ícono verde).

### Paso 4.3 — Agregar el sistema backend como recurso expuesto

1. En la sección **Mapping Virtual To Internal System**, hacer clic en **+** (Agregar).
2. Completar los campos:

   | Campo | Valor ejemplo |
   |---|---|
   | **Back-end Type** | `ABAP System` |
   | **Protocol** | `HTTPS` |
   | **Internal Host** | `sapdev.empresa.com` |
   | **Internal Port** | `44300` |
   | **Virtual Host** | `sapdev-virtual` |
   | **Virtual Port** | `44300` |
   | **Principal Type** | `None` (o `X.509` si usa certificados) |

3. Hacer clic en **Save**.

### Paso 4.4 — Exponer los recursos (paths OData)

1. Seleccionar el sistema recién creado y en **Resources**, hacer clic en **+**.
2. Agregar el path del servicio OData:

   | Campo | Valor |
   |---|---|
   | **URL Path** | `/sap/opu/odata/sap/ZVENTAS_SRV/` |
   | **Active** | Marcado |
   | **Access Policy** | `Path and all sub-paths` |

3. Guardar y verificar que el estado sea **Reachable**.

---

## 5. Crear la Conexión OData en SAC

### Paso 5.1 — Acceder a la sección de Conexiones

1. Ingresar a SAP Analytics Cloud con usuario administrador.
2. En el menú principal (barra lateral izquierda), navegar a:
   ```
   System > Administration > Connections
   ```
3. Hacer clic en el botón **+ Add Connection** (esquina superior derecha).

### Paso 5.2 — Seleccionar el tipo de conexión

1. En el buscador del diálogo, escribir **OData** o navegar hasta:
   ```
   Connect to Live Data > SAP OData Services
   ```
   o bien:
   ```
   Import Data > OData Services
   ```
   > **Nota:** Elegir **Live** para análisis en tiempo real sin importación, o **Import** para replicar datos en SAC.

2. Hacer clic en **Next**.

### Paso 5.3 — Configurar los parámetros de conexión

Completar el formulario con la siguiente información:

#### Para conexión On-Premise (a través de Cloud Connector):

| Campo | Valor |
|---|---|
| **Connection Name** | `CON_VENTAS_DEV` (nombre descriptivo, incluir ambiente) |
| **Description** | `Conexión OData servicio de ventas - Ambiente DEV` |
| **Connection Type** | `On-Premise` |
| **Host** | Virtual host configurado en SCC (ej. `sapdev-virtual`) |
| **Port** | `44300` |
| **Client** | Mandante SAP (ej. `100`) |
| **Language** | `ES` (o `EN`) |
| **Authentication Method** | `User Name and Password` |
| **User Name** | Usuario técnico (ej. `SAC_TECH_USER`) |
| **Password** | Contraseña del usuario técnico |

#### Para conexión Cloud / Internet:

| Campo | Valor |
|---|---|
| **Connection Name** | `CON_VENTAS_DEV` |
| **Connection Type** | `Internet` |
| **URL** | `https://sapdev.empresa.com:44300/sap/opu/odata/sap/ZVENTAS_SRV/` |
| **Authentication Method** | `Basic Authentication` o `OAuth 2.0` |
| **User Name** | Usuario técnico |
| **Password** | Contraseña |

### Paso 5.4 — Validar y guardar la conexión

1. Hacer clic en **Test Connection** para verificar la conectividad.
2. Si el test es exitoso (mensaje verde: *"Connection tested successfully"*), hacer clic en **Create**.
3. La conexión aparecerá en el listado de **Connections** con estado **OK**.

---

## 6. Conectar entre Diferentes Ambientes (DEV / QA / PRD)

La estrategia recomendada es crear **una conexión OData por cada ambiente**, con nomenclatura clara.

### Paso 6.1 — Estructura de nomenclatura recomendada

```
CON_<SISTEMA>_<AMBIENTE>
```

Ejemplos:
- `CON_S4H_VENTAS_DEV`
- `CON_S4H_VENTAS_QAS`
- `CON_S4H_VENTAS_PRD`

### Paso 6.2 — Crear conexión para cada ambiente

Repetir el proceso del **Paso 5** para cada ambiente, cambiando:

| Parámetro | DEV | QAS | PRD |
|---|---|---|---|
| **Connection Name** | `CON_S4H_DEV` | `CON_S4H_QAS` | `CON_S4H_PRD` |
| **Host (SCC Virtual)** | `s4h-dev-virtual` | `s4h-qas-virtual` | `s4h-prd-virtual` |
| **SAP Client** | `100` | `200` | `300` |
| **User** | `SAC_TECH_DEV` | `SAC_TECH_QAS` | `SAC_TECH_PRD` |

> **Recomendación de seguridad:** Usar usuarios técnicos diferentes por ambiente con solo los permisos necesarios (principio de mínimo privilegio).

### Paso 6.3 — Asociar conexiones a ambientes SAC (Tenant Strategy)

SAP recomienda tener un **tenant SAC por ambiente** para separación total:

```
SAC Tenant DEV  ──── OData ────► S/4HANA DEV
SAC Tenant QAS  ──── OData ────► S/4HANA QAS
SAC Tenant PRD  ──── OData ────► S/4HANA PRD
```

Si se usa **un único tenant SAC** con múltiples ambientes de backend:

```
SAC Tenant PRD ──── CON_S4H_DEV ────► S/4HANA DEV
               ──── CON_S4H_QAS ────► S/4HANA QAS
               ──── CON_S4H_PRD ────► S/4HANA PRD
```

---

## 7. Crear un Modelo desde la Conexión OData

### Paso 7.1 — Crear nuevo modelo de adquisición de datos

1. En SAC, ir a **Modeler > New Model**.
2. Seleccionar **Get data from a data source**.
3. En el buscador de fuentes, seleccionar la conexión OData creada (ej. `CON_S4H_VENTAS_DEV`).

### Paso 7.2 — Seleccionar el EntitySet

1. SAC mostrará los **EntitySets** disponibles del servicio OData.
2. Seleccionar el EntitySet deseado (ej. `VentasSet`, `PedidosSet`).
3. Previsualizar los datos y verificar que las columnas sean correctas.

### Paso 7.3 — Configurar el mapeo de campos

1. Identificar las dimensiones (campos descriptivos) y medidas (campos numéricos).
2. En SAC, marcar cada campo con su tipo:
   - **Dimension**: campos de texto, fecha, ID.
   - **Measure**: campos numéricos (importes, cantidades).
3. Configurar el campo de **Date** para análisis temporal.

### Paso 7.4 — Guardar el modelo

1. Asignar nombre descriptivo: `MDL_VENTAS_DEV`.
2. Seleccionar la carpeta de destino.
3. Hacer clic en **Create Model**.

---

## 8. Transporte de Conexiones entre Ambientes SAC

### Opción A — Exportar/Importar manualmente (tenant único)

1. En **System > Administration > Connections**, seleccionar la conexión.
2. Hacer clic en **Export** (ícono de descarga) → descarga un archivo `.json`.
3. En el ambiente destino, ir a **Connections > Import** y subir el `.json`.
4. Actualizar las credenciales y el host del nuevo ambiente.

### Opción B — SAC Transport (SAP Content Network)

Para tenants con **SAC Lifecycle Management** habilitado:

1. Ir a **System > Administration > Transport**.
2. Crear un paquete de transporte seleccionando las conexiones a mover.
3. Exportar hacia el tenant destino (QAS o PRD).
4. En el tenant destino, ir a **Transport > Import** y aceptar el paquete.
5. Actualizar credenciales sensibles manualmente (las contraseñas no se transportan por seguridad).

---

## 9. Verificación y Pruebas

### Paso 9.1 — Verificar la conexión

1. Ir a **System > Administration > Connections**.
2. Seleccionar la conexión y hacer clic en **Validate** o **Check Connection**.
3. Estado esperado: **Connection is working correctly** (ícono verde).

### Paso 9.2 — Verificar datos en el modelo

1. Abrir el modelo creado en el Modeler.
2. Ir a **Data Management > Refresh Data**.
3. Verificar que los registros se carguen sin errores.
4. Revisar el log en **Data Management > Job History**.

### Paso 9.3 — Prueba funcional en historia/dashboard

1. Crear una **Story** de prueba usando el modelo.
2. Agregar un gráfico básico (ej. tabla con totales de ventas).
3. Verificar que los datos correspondan a lo esperado del sistema origen.

---

## 10. Resolución de Problemas Comunes

| Error | Causa probable | Solución |
|---|---|---|
| `Connection failed: Host not reachable` | Cloud Connector no conectado o host virtual incorrecto | Verificar SCC: estado Connected, host virtual coincide con configuración en SAC |
| `401 Unauthorized` | Credenciales incorrectas o usuario bloqueado | Verificar usuario/contraseña en SAP; desbloquear usuario en `SU01` |
| `403 Forbidden` | Usuario sin autorización al servicio OData | Asignar roles necesarios en el sistema backend |
| `Service not found (404)` | Servicio OData no activo o path incorrecto | Verificar en `/IWFND/MAINT_SERVICE` que el servicio esté activo |
| `SSL Certificate error` | Certificado no confiable o expirado | Importar certificado en SAC (System > Trusted Certificates) |
| `Timeout` | Red lenta o SCC sobrecargado | Revisar métricas del SCC; aumentar timeout en configuración |
| `No data returned` | Filtros OData incorrectos o usuario sin datos | Verificar en el browser del backend que el servicio retorna datos |

---

## 11. Buenas Prácticas

1. **Nomenclatura consistente**: incluir siempre el ambiente en el nombre de la conexión (`_DEV`, `_QAS`, `_PRD`).
2. **Usuarios técnicos dedicados**: nunca usar cuentas personales; crear un usuario de servicio por ambiente y sistema.
3. **Principio de mínimo privilegio**: asignar solo los roles y EntitySets necesarios al usuario técnico.
4. **Rotación de contraseñas**: establecer política de rotación para los usuarios técnicos y actualizar las conexiones en SAC cuando cambien.
5. **Monitoreo**: revisar periódicamente el **Job History** en SAC para detectar fallos en la carga de datos.
6. **Documentar conexiones**: mantener un inventario de conexiones con nombre, sistema origen, ambiente, propietario y fecha de última validación.
7. **Separación de tenants**: en proyectos productivos, usar tenants SAC separados para DEV/QAS/PRD siempre que sea posible.
8. **Validar antes de transportar**: siempre probar la conexión en DEV antes de replicarla en QAS y PRD.
9. **Certificados SSL**: usar certificados firmados por una CA reconocida en ambientes productivos.
10. **Timeout y paginación OData**: para grandes volúmenes de datos, configurar correctamente el `$top` y `$skip` en el servicio OData o usar la paginación del modelo en SAC.

---

*Guía elaborada para SAP Analytics Cloud (SAC) versión 2024 y superior.*
*Válida para conexiones OData hacia SAP S/4HANA, SAP BW/4HANA y sistemas SAP con SAP Gateway habilitado.*
