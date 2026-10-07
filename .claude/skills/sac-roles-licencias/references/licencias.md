# Licencias de SAP Analytics Cloud

Verificado: 7 de octubre de 2026 (SAP Help Q3 2026 / 2026.15; BDC Service Description
Guide v9-2026; artículo de soporte "Managing Licenses with Roles and Teams").

## Contenido
1. Tipos de licencia
2. Jerarquía y cómo se decide la licencia de un usuario
3. Falta de licencias: traspaso a una superior y fallos
4. Licencias concurrentes
5. Quién no consume licencia
6. Tenants de prueba
7. Compra: SAC dentro de SAP Business Data Cloud (Capacity Units)
8. Cambios comerciales 2025-2026
9. Planificación embebida y otras ediciones

## 1. Tipos de licencia

Licencias disponibles en el tenant (dependen de lo comprado):

| Licencia | Nominal / concurrente | Comentario |
|---|---|---|
| Business Intelligence | Nominal | Historias, modelos analíticos, predictivo. Sin funciones de planificación. |
| Business Intelligence (Concurrent Session) | Concurrente | **Ya no se vende** para tenants nuevos; los clientes existentes la conservan. |
| Business Intelligence Embedded | — | Roles *BI Embedded …* para escenarios embebidos. |
| Planning Standard | Nominal | Planificación de usuario final + todo BI. |
| Planning Professional | Nominal | Todo Standard + modelado de planificación, data actions, asignaciones. |
| Analytics Hub (add-on) | Nominal | **Ya no se vende**. Se suma a la licencia principal. |

Nombres comerciales actuales en la documentación: *SAP Analytics Cloud for business
intelligence, predictive edition*, *… for planning, predictive standard edition* y
*… for planning, predictive professional edition*. En BDC aparecen como *public system
option*.

Las licencias de planificación **incluyen un usuario BI de uso completo**.

Se pueden crear roles para: Business Intelligence, Business Intelligence Embedded,
Planning Standard, Planning Professional y Analytics Hub.

## 2. Jerarquía y licencia del usuario

- Planning Professional incluye Planning Standard, que incluye Business Intelligence. Un
  usuario con Planning Standard **no** consume además una licencia BI.
- Todo usuario activo necesita licencia. Cada rol está asociado a **un** tipo de licencia,
  y el usuario consume la **más alta** de la unión de sus roles (directos o heredados de
  equipos). No aplica a Analytics Hub (add-on aparte) ni al carácter concurrente.
- Todos los roles del mismo tipo de licencia consumen lo mismo: *BI Admin* consume igual que
  *BI Content Viewer*. Un rol personalizado con todos los permisos no tiene nada especial
  frente a *Admin*.
- Un usuario sin roles (ni directos ni por equipo) recibe una licencia BI por defecto y la
  consume, aunque casi no pueda hacer nada.
- Al **crear** un usuario, SAC solo considera los roles asignados directamente para
  calcular la licencia, aunque el proceso lo agregue a un equipo.
- Roles por defecto (*Use as Default Role*): se asignan a usuarios nuevos sin rol. Puede
  haber varios; en ese caso el usuario nuevo recibe todos.

## 3. Falta de licencias

- Si no quedan licencias del tipo que corresponde, SAC usa una **superior** disponible
  (BI → Planning Standard → Planning Professional). Ese usuario consume una licencia más
  cara sin aviso visible.
- Si tampoco hay superiores, la operación **falla completa**: crear el usuario, agregar
  usuarios a un equipo o asignar el rol. Si se agregan 100 usuarios a un equipo y uno no
  tiene licencia, no se agrega ninguno. El error queda en el registro de actividades.
- Desde la versión de agosto de 2023 (Q3 2023) **no** se pueden asignar más licencias
  nominales que las contratadas.
- Para liberar: desactivar o eliminar usuarios, quitar roles (o equipos) o comprar más.
- Existe la nota KBA 2535356 ("number of available licenses have been exceeded") y la KBA
  3515540 ("user is assigned a different license than the role should give them").

## 4. Licencias concurrentes (solo BI)

- El carácter concurrente es una **propiedad del usuario** (*Asignar como: Licencia de
  sesión concurrente*), no del rol ni del equipo. Columna `IS_CONCURRENT` en la
  exportación de usuarios; `isConcurrent` en SCIM.
- Desde Q3 2023 la propiedad solo "solicita" una licencia concurrente **si** la licencia
  resultante es BI. Si el usuario tiene un rol de planificación, consume una licencia
  nominal de planificación aunque la propiedad diga concurrente.
- Asignar un rol de planificación o de Analytics Hub **directamente** a un usuario cambia su
  BI a nominal sin avisar. Por equipo no lo cambia.
- Se consumen al iniciar sesión. Si se agotan, el usuario ve "No Sessions Available".
- Se pueden marcar como concurrentes los usuarios nuevos con un rol por defecto
  configurado como concurrente. El mapeo SAML no define el tipo de licencia.
- No tiene sentido desactivar usuarios concurrentes para ahorrar licencias.
- Si SAP retira las licencias concurrentes del contrato, los usuarios pasan a nominal.

## 5. Quién no consume licencia

- Usuarios **desactivados** (`☰ → Seguridad → Usuarios → Desactivar`). Se pueden crear
  desactivados con la importación de usuarios (`IS_USER_DEACTIVATED = TRUE`). No hay API
  soportada para activar o desactivar; se hace en la interfaz.
- El usuario con el rol **System Owner** (uno solo por tenant; no se puede asignar a un
  equipo; es el único que edita la configuración SAML).
- Usuarios de soporte de SAP.

## 6. Tenants de prueba

- Los tenants *Test* y *Test Preview* solo tienen licencias **Planning Professional**: todo
  usuario consume Professional, sin importar sus roles.
- En BDC: *SAP Analytics Cloud, test tenant, public system option*, mínimo 20 usuarios.

## 7. Compra dentro de SAP Business Data Cloud (BDC)

SAC se contrata hoy dentro de SAP Business Data Cloud, que se mide en **Capacity Units
(CU)**. Para SAC, la CU se calcula por **usuario y mes** según el tipo de licencia y el
tramo. Los usuarios se cuentan por separado en cada instancia (no se suman entre tenants).

Tabla 1 de la *BDC Service Description Guide v9-2026* (CU por usuario por mes):

| Servicio | Tramo de usuarios | CU por usuario/mes |
|---|---|---|
| SAC for business intelligence, public system option | 25 – 200 | 25,60 |
| | 201 – 500 | 21,60 |
| | 501 – 1.000 | 17,38 |
| | 1.001 – 3.000 | 15,95 |
| | 3.001 – 5.000 | 12,64 |
| | 5.001+ | 10,54 |
| SAC for planning, standard edition, public system option | 10 – 200 | 72,85 |
| | 201 – 500 | 57,98 |
| | 501 – 1.000 | 46,70 |
| | 1.001+ | 41,57 |
| SAC for planning, professional edition, public system option | 1+ | 820,43 |
| SAC, test tenant, public system option | 20+ | 47,05 |

Mínimos para aprovisionar (blog de SAP sobre el *BDC Capacity Unit Estimator*,
actualizado en marzo de 2026):

| Tenant | Mínimo de licencias | Mínimo de CU/mes |
|---|---|---|
| Prueba / QA | 20 usuarios de prueba (funciones de Planning Professional) | 941 |
| Producción solo BI | 25 BI | 640 |
| Producción con planificación | 10 Planning Standard + 1 Planning Professional | 1.548,93 |

No se puede aprovisionar producción solo con Planning Standard: hace falta al menos un
Planning Professional.

**Condición nueva en la guía v9-2026:** el uso de las licencias de planificación de SAC
(Standard y Professional) en BDC está sujeto a que el cliente contrate por separado el
servicio **SAP Enterprise Planning**, y el número total de usuarios de planificación no
puede superar los usuarios contratados en SAP Enterprise Planning. Confirma esto con el
contrato o con SAP antes de cotizar, porque cambia cómo se compra la planificación.

El valor monetario de una CU depende del contrato; SAP no publica un precio por CU en la
guía. Para estimar use el *SAP Business Data Cloud Capacity Unit Estimator*.

## 8. Cambios comerciales 2025-2026

- **1 de enero de 2026:** SAC y SAP Datasphere salieron de la lista de servicios elegibles
  para **nuevas** suscripciones BTPEA, CPEA y PAYG (créditos de BTP). Siguen disponibles
  hasta el fin del contrato vigente; los créditos comprados antes del 1 de enero de 2026 se
  pueden seguir usando. Para renovar, el camino es SAP Business Data Cloud.
- Los tenants existentes de SAC se conservan bajo BDC **sin migración técnica**.
- **SAP Enterprise Planning** (presentado en SAP Sapphire, mayo de 2026) usa SAC for planning
  como motor y agrega contenido de dominio, productos de datos de BDC y agentes de Joule.
- Las funciones de IA (Joule, funciones generativas) se controlan con los permisos
  *Generative AI* y *Joule* del rol; su consumo comercial (AI Units) se rige por los
  contratos de SAP Business AI, no por la licencia de SAC. Verifica la condición vigente.

## 9. Planificación embebida y otras ediciones

- **BI Embedded**: roles *BI Embedded Content Viewer/Editor/User/Administrator…* para
  escenarios embebidos (por ejemplo S/4HANA). No incluyen planificación.
- **Private option** (*SAP Analytics Cloud, predictive enterprise edition, private
  option*): tenant privado con usuarios aprovisionados como Planning Professional, mínimo
  10.000 usuarios, 2 TB de memoria en todos los tramos.
- Si se retiran las licencias de planificación de un tenant, el contenido de planificación
  queda restringido incluso para administradores BI; solo el *System Owner* puede moverlo o
  eliminarlo.
