# Funciones por tipo de licencia

Fuentes: SAP Help *Features by License Type for Planning Models*, *Features by License Type
for Analytic Models* y *api/v1/dataimport* (REST API), Q3 2026 (2026.15).

Columnas: **BI** = SAC for business intelligence; **Std** = SAC for planning, standard
edition; **Pro** = SAC for planning, professional edition. "X" = disponible, "—" = no.

## Modelos de planificación

| Función | BI | Std | Pro |
|---|---|---|---|
| Crear, actualizar y eliminar modelos de planificación | — | — | X |
| Ver modelos de planificación / acceso de lectura | X | X | X |
| Crear versiones privadas | X | X | X |
| Crear versiones públicas | — (solo privadas) | X | X |
| Ver versiones privadas y públicas | X | X | X |
| Ingreso de datos sobre valores reservados (booked) | X (edita versiones privadas y en edición pública, **no publica**) | X | X |
| Ingreso de datos sobre valores no reservados (unbooked) | — | X | X |
| Data Export API | X | X | X |
| **Data Import API** | — | X | X |
| Crear miembros de dimensión desde la tabla | — | X | X |
| Mantener bloqueos de datos | — | X | X |
| Jerarquías | X | X | X |
| Calendario | Tareas y procesos; contenido de planificación requiere licencia de planificación | X | X |
| Plantillas de calendario | Instancia plantillas sin contenido de planificación | Instancia todas | Crea, elimina e instancia todas |
| **Crear o editar data actions** (incluidas asignaciones) | — | — | X |
| **Ejecutar data actions** | — | X | X |
| Ejecutar multi actions | X (con restricciones según los pasos) | X | X |
| Ejecutar pasos y procesos de asignación | — | X | X |
| Distribuir valores con el panel de planificación | — | X | X |
| Colaborar en modelos de planificación | X (solo versión privada) | X | X |
| Simulación de value driver tree | X (solo privada) | X | X |
| Conversión de moneda (crear o editar tablas) | — (solo ver) | X | X |
| Simulación | X (solo privada) | X | X |
| Publicar simulación en SAC | — | X | X |
| Comentarios en celdas | X | X | X |
| Conexión SAC → BPC | — | — | X (al menos un usuario) |

Notas:
- Las licencias de planificación incluyen un usuario BI de uso completo.
- Si se retiran las licencias de planificación del tenant, los usuarios BI no ven ni pueden
  mover o borrar el contenido de planificación; solo el propietario de la cuenta puede.
- Para modelos con varias medidas, hacia BPC standard solo se exporta, no se importa.

## Modelos analíticos

| Función | BI | Std | Pro |
|---|---|---|---|
| Crear, editar o eliminar modelos analíticos | X | X | X |
| Editar, ingresar o subir datos operativos | X | X | X |
| Generar modelos automáticamente | X | X | X |
| Data Export API | X | X | X |
| **Data Import API** | — | X | X |
| Historias, gráficos, Explorer, vínculos, dimensiones calculadas, mapas Esri, umbrales | X | X | X |
| Value driver trees en historias | X | X | X |
| Just Ask, Smart Predict, Smart Insights, R, forecasting en gráficos | X | X | X |
| Time series forecasting en celdas de tabla | — | X | X |

Administración (la tabla de SAP marca BI y Pro, no Std): administrar usuarios, roles y
equipos, auditoría, logs de actividad y de datos, archivos públicos, información del
sistema y despliegue de contenido. En la práctica, para administradores use *BI Admin*
(BI) o *Admin* (Professional).

## Data Import API por licencia

Requisito general: usuario de SAC con licencia **Planning Standard o Professional**. Flujos
OAuth soportados: Client Credentials y SAML Bearer (2-legged, administrador) y
Authorization Code (3-legged, usuario de negocio, respeta roles y acceso a datos).

| Acción | BI | Std | Pro |
|---|---|---|---|
| Tokens 2-legged y 3-legged | X | X | X |
| `GET /models`, `/models/{id}`, `/metadata` | X | X | X |
| `POST /models/{id}` y `/models/{id}/{importType}` (crear job) | — | X | X |
| `POST /jobs/{id}` (enviar datos), `/validate`, `/run`, `DELETE`, `GET /invalidRows` | — | X | X |
| `GET /jobs/{id}/status`, `GET /jobs` | X | X | X |
| `POST /import/{modelID}` (un clic, CSV o JSON) | — | X | X |
| Dimensiones públicas, tablas de moneda (GET y POST) | X | X | X |
| Tablas de unidades: metadata e import | — | X | X |

Además del rol, con 3-legged el usuario necesita **Mantener** en Planning Model (o Analytic
Model) y acceso al modelo compartido. `privateFactData` solo funciona con usuarios de
negocio. Límites: 100 jobs activos por usuario y por modelo; POST ≤ 300 MB; los jobs se
borran a los 15 días; no importa a versiones externas (Datasphere, BigQuery).
