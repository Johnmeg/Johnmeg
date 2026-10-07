# Roles estándar de SAP Analytics Cloud

Fuente: SAP Help, *Standard Application Roles*, Q3 2026 (2026.15). Los IDs se usan al
importar asignaciones desde CSV o al asignar roles con la API REST/SCIM.

Los roles que aparecen dependen de las licencias del tenant. SAP actualiza los roles
estándar cuando agrega derechos nuevos, por eso se recomienda **copiarlos** (Guardar como)
y no editarlos.

## Roles principales

| Rol | ID | Licencia que consume | Para quién |
|---|---|---|---|
| System Owner | `PROFILE:sap.epm:System_Owner` | Ninguna (gratis) | Uno solo por tenant; todos los privilegios. No se asigna a equipos. |
| Admin | `PROFILE:sap.epm:Admin` | **Planning Professional** | Administrador del sistema: usuarios, roles, transportes, todo. |
| Modeler | `PROFILE:sap.epm:Modeler` | **Planning Professional** | Crea y cambia modelos y dimensiones (incluida planificación). |
| Planner Reporter | `PROFILE:sap.epm:Planner_Reporter` | **Planning Standard** | Planifica y presupuesta; actualiza tablas de moneda; crea historias. |
| Viewer | `PROFILE:sap.epm:Viewer` | **Planning Standard** | Solo lectura, pero consume Planning Standard. No comparte ni mueve contenido. |
| BI Admin | `PROFILE:sap.epm:BI_Admin` | Business Intelligence | Administrador BI: todo menos tareas de planificación. |
| BI Content Creator | `PROFILE:sap.epm:BI_Content_Creator` | Business Intelligence | Crea modelos analíticos, dimensiones e historias. |
| BI Content Viewer | `PROFILE:sap.epm:BI_Content_Viewer` | Business Intelligence | Solo lectura de datos no planificados. Sin archivos privados ni compartir. |
| Predictive Content Creator | `PROFILE:sap.epm:Predictive_Content_Creator` | Business Intelligence | Escenarios predictivos (necesita Create y Read). |
| Predictive Admin | `PROFILE:sap.epm:Predictive_Admin` | Business Intelligence | Predictivo + repositorios de datos. |
| Translator | `PROFILE:sap.epm:Translator` | — | Traducciones (XLIFF). |
| BTP Content Creator | `PROFILE:sap.epm:HCP_Content_Creator` | — | Modelos no planificados (nombre heredado de SCP). |
| BTP Content Viewer | `PROFILE:sap.epm:BI_Content_Viewer` | — | Lectura de datos no planificados. |

Notas clave:
- **Viewer ≠ BI Content Viewer.** Para un usuario que solo mira historias, *BI Content
  Viewer* consume BI; *Viewer* consume Planning Standard. Es un error caro y frecuente.
- Planner Reporter, Viewer, Admin y Modeler traen Create/Read/Update/Delete/Share en el
  privilegio *Story*. BI Content Viewer solo trae Read en Story.
- Todos los roles anteriores incluyen el uso del *data analyzer* y ver custom widgets.

## Roles BI Embedded

| Rol | ID | Qué permite |
|---|---|---|
| BI Embedded Content Viewer | `PROFILE:sap.epm:Embedded_BI_Content_Viewer` | Lectura de datos no planificados. |
| BI Embedded Content Editor | `PROFILE:sap.epm:Embedded_BI_Content_Editor` | Leer y actualizar historias (no modelos); CRUD de artefactos componibles. |
| BI Embedded User | `PROFILE:sap.epm:Embedded_BI_User` | Leer/actualizar historias; crear, actualizar y eliminar modelos. |
| BI Embedded Administrator | `PROFILE:sap.epm:Embedded_BI_Admin` | Lo anterior + gestionar equipos. |
| BI Embedded Content Administrator | `PROFILE:sap.epm:Embedded_BI_Content_Admin` | Lo anterior + CRUD de componibles + exportar/importar por ACN. |
| BI Embedded Scheduling User | `PROFILE:sap.epm:Embedded_BI_Schedule_Creator` | Crear y gestionar sus programaciones. |
| BI Embedded Scheduling Admin | `PROFILE:sap.epm:Embedded_BI_Schedule_Admin` | Gestionar programaciones de todos. |
| BI Embedded Shared Viewer | `PROFILE:sap.epm:Embedded_BI_Shared_Viewer` | Lectura sin comentarios ni archivos privados. |

## Roles de Analytics Hub (add-on, ya no se vende)

| Rol | ID |
|---|---|
| Analytics Hub Admin | `PROFILE:sap.epm:Analytics_Hub_Admin` |
| Analytics Hub Content Creator | `PROFILE:sap.epm:HCP_Content_Creator` |
| Analytics Hub Viewer | `PROFILE:sap.epm:Analytics_Hub_Content_Viewer` |

## Crear un rol personalizado (resumen)

1. `☰ → Seguridad → Roles → Crear rol`.
2. Nombre: solo **mayúsculas, números y guion bajo**, máximo **20 caracteres** (por
   ejemplo `PLAN_CARGA_DATOS`). La descripción es libre.
3. Elegir el **tipo de licencia**: se asigna a todos los usuarios con el rol.
4. Elegir una plantilla (roles estándar de esa licencia) o en blanco.
5. Ajustar la matriz de permisos, por tipo de objeto o por objeto individual.
6. *Configuración del rol*: **Usar como rol por defecto** (con licencia de usuario o de
   sesión concurrente), **Acceso completo a los datos** (ignora el control de acceso a
   datos del rol) y **Habilitar autoservicio** (los usuarios pueden solicitarlo; aprueba el
   gerente u otro usuario).
7. Asignar a usuarios o equipos y **Guardar**.

Permisos para crear roles: Read + Create/Update/Delete/Manage en el privilegio *Role*.
Para asignarlos: Read + Create y Update en *User* y *Team*, y Create, Update, Delete y
Manage en *Role*.
