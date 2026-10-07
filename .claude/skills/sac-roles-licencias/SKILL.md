---
name: sac-roles-licencias
description: Experto en roles, permisos y licenciamiento de SAP Analytics Cloud (SAC). Úsala siempre que el usuario pregunte qué licencia o rol necesita alguien en SAC (Business Intelligence, Planning Standard, Planning Professional, concurrente, Analytics Hub, embedded), cómo copiar o diseñar un rol personalizado, qué casillas marcar en la matriz de permisos (Leer, Mantener, Ejecutar, Planning Model, Data Action, Multi Action, Data Locking…), por qué un usuario consume una licencia distinta o recibe "sin permisos"/403, cuántas licencias o Capacity Units (CU) de Business Data Cloud comprar, o cómo asignar roles con equipos, SAML o SCIM. También aplica a preguntas de costo de licencias, cumplimiento, auditoría de licencias y a guías para administradores de SAC, aunque no digan "licencia" o "rol" explícitamente (por ejemplo "este usuario no puede ejecutar el data action", "quiero que carguen archivos sin ser modeladores").
---

# Roles y licenciamiento de SAP Analytics Cloud

Esta skill responde preguntas de seguridad y licencias de SAC con información verificada
en la documentación oficial de SAP. La base de conocimiento está en `references/` y fue
verificada el **7 de octubre de 2026** contra SAP Help **Q3 2026 (2026.15)** y la
*SAP Business Data Cloud Service Description Guide v9-2026*.

## Cómo trabajar

1. **Identifica el tipo de pregunta** y lee solo la referencia que corresponde:

   | Si preguntan por… | Lee |
   |---|---|
   | Tipos de licencia, cuál consume un usuario, concurrentes, usuarios desactivados, tenants de prueba, compra en BDC / Capacity Units, cambios comerciales 2026 | `references/licencias.md` |
   | Roles estándar, sus IDs (`PROFILE:sap.epm:…`) y la licencia que consume cada uno | `references/roles-estandar.md` |
   | Qué casilla marcar, qué significa Mantener vs Actualizar, permisos por objeto | `references/permisos.md` |
   | Qué puede hacer cada licencia (planificación, modelos analíticos, APIs) | `references/funciones-por-licencia.md` |
   | Un caso práctico: diseñar un rol, error 403, "no puede ejecutar", buenas prácticas | `references/recetas.md` |
   | Citar fuentes | `references/fuentes.md` |

2. **Razona con las reglas centrales** (abajo) antes de recomendar un rol. La mayoría de
   errores de licenciamiento vienen de olvidar una de ellas.

3. **Responde en el idioma del usuario** (normalmente español), con rutas de menú de SAC
   (`☰ → Seguridad → Roles`), una tabla de permisos cuando haya casillas que marcar y los
   pasos numerados. Termina con las fuentes que usaste.

4. **Verifica si la pregunta es sensible al tiempo.** Precios, Capacity Units, nombres
   comerciales, funciones nuevas (Joule, IA, Enterprise Planning) y reglas de compra
   cambian cada trimestre. Si la pregunta depende de eso, o la fecha actual está a más de
   seis meses de la fecha de verificación, consulta la fuente oficial antes de afirmar.
   `help.sap.com` puede estar bloqueado para WebFetch; en ese caso usa Firecrawl
   (`firecrawl_scrape`) o la búsqueda web. Di explícitamente qué verificaste y qué no.

## Reglas centrales

Estas reglas explican el 90 % de los casos. Están detalladas, con su fuente, en las
referencias.

- **Licencia → rol → permiso.** La licencia define qué funciones existen para el usuario;
  el rol elige un subconjunto de esas funciones; el permiso habilita una acción sobre un
  tipo de objeto. Compartir un archivo o modelo da acceso a ese objeto concreto, pero no
  reemplaza el permiso del rol.
- **Jerarquía:** Planning Professional ⊃ Planning Standard ⊃ Business Intelligence. Un
  usuario consume **una sola** de estas (más add-ons como Analytics Hub).
- **La licencia la decide el rol.** Cada rol (estándar o personalizado) está asociado a un
  solo tipo de licencia. Si un usuario tiene varios roles, consume la **más alta** de la
  unión de todos sus roles, sea por asignación directa o heredada por equipo.
- **Cuidado con los nombres:** el rol estándar **Viewer** consume **Planning Standard**, no
  BI; **Admin** y **Modeler** consumen **Planning Professional**; **BI Admin**, **BI Content
  Creator** y **BI Content Viewer** consumen BI. Para un lector puro usa *BI Content Viewer*.
- **Mantener ≠ Actualizar.** *Mantener* (Maintain) en Planning Model / Analytic Model
  permite escribir datos sin cambiar la estructura; *Actualizar* (Update) cambia la
  estructura. Crear, actualizar o eliminar modelos de planificación y crear o editar data
  actions o validation rules es **Planning Professional**.
- **Planning Standard** puede: ingresar datos (incluso no reservados), crear versiones
  públicas, ejecutar data actions, multi actions y asignaciones, mantener bloqueos de
  datos y usar la **Data Import API**. Una licencia BI no puede usar la Data Import API ni
  publicar versiones de planificación.
- **Sin licencia disponible, se usa una superior;** si tampoco hay, la operación entera
  falla (crear el usuario, agregarlo a un equipo, asignar el rol). Desde agosto de 2023 SAC
  hace cumplir el número de licencias nominales.
- **Los usuarios desactivados no consumen licencia.** El *System Owner* y los usuarios de
  soporte de SAP tampoco.
- **Concurrentes:** solo existen para BI y ya no se venden para tenants nuevos. Que un
  usuario sea concurrente es una propiedad del usuario, no del rol ni del equipo. Un rol de
  planificación siempre fuerza licencia nominal.
- **Tenants de prueba:** todas las licencias son Planning Professional.
- **Buena práctica de SAP:** copia un rol estándar como plantilla (no lo edites; SAP lo
  actualiza), asigna roles a **equipos** y no a usuarios, y mapea equipos (no roles) desde
  SAML.

## Diagnóstico rápido: "¿qué licencia y rol necesita?"

Pregunta qué tiene que **hacer** la persona y sigue el primer caso que aplique:

1. Crea o cambia modelos de planificación, data actions, asignaciones o validation rules →
   **Planning Professional** (copia de *Modeler* o *Admin*).
2. Ingresa o carga datos en modelos de planificación, publica versiones, ejecuta data
   actions o multi actions, mantiene bloqueos → **Planning Standard** (copia de *Planner
   Reporter*).
3. Solo crea historias y modelos analíticos, o lee → **Business Intelligence** (copia de *BI
   Content Creator* o *BI Content Viewer*).
4. Administra usuarios y roles sin planificar → *BI Admin* (BI). Si además administra
   contenido de planificación → *Admin* (Professional).

Luego confirma los permisos puntuales en `references/permisos.md` y los bloqueos ajenos al
rol (compartir el modelo, Data Access Control, bloqueo de datos, versión) en
`references/recetas.md`.

## Qué no hacer

- No afirmes precios en moneda: SAP publica Capacity Units por usuario, no precios. Si
  preguntan por costo, da las CU de la tabla de BDC, explica que el valor monetario de la
  CU depende del contrato y sugiere el *Capacity Unit Estimator*.
- No inventes nombres de permisos ni IDs de rol: usa los de las referencias o verifica.
- No recomiendes asignar Planning Professional "por si acaso": cuesta muchas veces más que
  Standard (820,43 CU frente a 72,85 CU por usuario al mes en el tramo de entrada).
