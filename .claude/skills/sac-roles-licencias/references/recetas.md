# Recetas y diagnóstico

Casos prácticos frecuentes. Cada receta indica el rol base, la licencia y los permisos.
Rutas de menú en la interfaz en español de SAC.

## Contenido
1. Usuario Planning Standard que carga archivos (Data Import API o un cargador)
2. Planificador que ingresa datos y ejecuta data actions
3. Lector de historias de planificación
4. Diseñador de data actions y modelos
5. Administrador delegado de usuarios
6. Propietario de bloqueos de datos
7. Diagnóstico: "no tiene permisos" / 403 / no puede ejecutar
8. Buenas prácticas de asignación
9. Auditoría y reducción de costo de licencias

## 1. Planning Standard que carga archivos

- Rol base: **Planner Reporter** → *Guardar como* (por ejemplo `PLAN_CARGA_DATOS`).
  Licencia Planning Standard.
- Permisos: Planning Model **Leer + Mantener + Ejecutar**; Data Action Leer + Ejecutar;
  Multi Action Leer + Ejecutar (si corre multi actions). No marcar Crear, Actualizar ni
  Eliminar en Planning Model (Professional). Si el modelo es analítico: Analytic Model
  Leer + Mantener.
- Compartir **cada modelo** con el equipo: Personalizado con Leer + Mantener.
- La Data Import API acepta Planning Standard. Con OAuth 3-legged (usuario de negocio) se
  respetan rol, compartir y control de acceso a datos.
- La carga desde *Modelador → Gestión de datos* crea o cambia trabajos de importación del
  modelo y suele exigir permisos de modelado; para usuarios Standard es más seguro un
  cargador vía API.

## 2. Planificador

- Rol base: Planner Reporter (Planning Standard).
- Permisos: Planning Model Leer + Mantener + Ejecutar; Data Action Leer + Ejecutar; Multi
  Action Leer + Ejecutar; Data Locking Leer + Mantener si es propietario de bloqueos;
  Calendar Template Leer + Ejecutar si instancia procesos.
- Además: modelo compartido, escritura en Data Access Control sobre sus miembros, versión
  pública con permiso de escritura y celdas sin bloquear.

## 3. Lector de historias de planificación

- Si solo mira: **BI Content Viewer** (licencia BI). Puede ver modelos de planificación y
  trabajar en versiones privadas, pero no publicar.
- No uses el rol estándar **Viewer** si no hace falta: consume Planning Standard.

## 4. Diseñador de data actions y modelos

- Rol base: **Modeler** (Planning Professional).
- Planning Model C/R/U/D/E/M; Data Action C/R/U/D/E; Multi Action C/R/U/D/E; Validation Rule
  si define combinaciones válidas; Dimension C/R/U/D/M.
- Asigna Professional solo a quienes diseñan; cuesta unas 11 veces más que Standard en CU.

## 5. Administrador delegado de usuarios (sin planificar)

- Rol base: **BI Admin** (licencia BI) o rol personalizado BI con:
  User Leer + Crear + Actualizar + Gestionar; Team Leer + Crear + Actualizar + Gestionar;
  Role Leer (+ Crear/Actualizar/Eliminar si crea roles).
- Para asignar roles necesita, según SAP: Read + Create + Update en User y Team, y Create,
  Update, Delete y Manage en Role.

## 6. Propietario de bloqueos de datos

- Configurar dimensiones de bloqueo y propietarios: Data Locking C/R/U/D.
- Cambiar el estado de un bloqueo como propietario: Data Locking **Leer + Mantener**.
- Mantener bloqueos requiere licencia de planificación (Standard o Professional).

## 7. Diagnóstico: "no tiene permisos", 403 o no puede ejecutar

Revisa en este orden y detente en la primera falla:

1. **Licencia que consume el usuario** (`Seguridad → Usuarios`, columna de licencia). ¿Es
   la esperada? Si consume BI y debía planificar, revisa sus roles y equipos. Si la
   asignación falló, puede faltar licencia (ver `licencias.md` §3).
2. **Permiso en el rol**: la casilla exacta (Mantener en Planning Model para cargar, Ejecutar
   en Data Action para correr, Leer **y** Ejecutar en Multi Action).
3. **Acceso al objeto**: el modelo, data action o multi action compartido con el usuario o su
   equipo (Archivos → Compartir).
4. **Data Access Control** de las dimensiones: permiso de escritura sobre los miembros.
   La opción *Acceso completo a los datos* del rol lo omite.
5. **Bloqueo de datos** o celdas restringidas.
6. **Versión**: pública y editable; las versiones externas (Datasphere en vivo) no aceptan
   importación.
7. **Data action**: los pasos de un data action pueden escribir en otros modelos (copia
   entre modelos) que el usuario también debe poder escribir.
8. **Usuario de API**: con OAuth Client Credentials el acceso es técnico (administrador);
   con Authorization Code se aplican todos los puntos anteriores al usuario.

Para multi actions con usuarios BI: pueden ejecutarlas, pero los pasos de planificación
(data actions, publicar versión) fallan por licencia.

## 8. Buenas prácticas de asignación (SAP)

- Copia los roles estándar como plantilla; no los edites.
- Asigna roles a **equipos**, no a usuarios (excepto System Owner, que no admite equipos).
- Con SAML: activa la creación dinámica de usuarios, mapea por USERID y mapea atributos a
  **equipos** (no a roles). Una asignación SAML a rol se revoca al iniciar sesión si el
  usuario deja de cumplir la condición.
- Roles de autoservicio (*Habilitar autoservicio*) con aprobación del gerente para roles de
  alto costo.
- Importación masiva de usuarios por CSV: actualiza ~1.000 usuarios por archivo (creación
  ~10.000).
- APIs: SCIM 2.0 para usuarios y equipos; los IDs de roles estándar están en
  `roles-estandar.md`.

## 9. Auditoría y reducción de costo

- Quién tiene qué: *Administration Cockpit*, contenido *SAC Usage Content* (Content
  Network) o la API SCIM. La exportación CSV de usuarios **no** trae la columna de licencia;
  la licencia consumida se ve en la interfaz.
- Uso real: `Seguridad → Actividades`, filtro *Inicio de sesión* por periodo.
- Ahorro típico: pasar lectores de *Viewer* a *BI Content Viewer*; desactivar usuarios
  inactivos (no consumen); revisar quién tiene *Admin*/*Modeler* (Professional) sin diseñar
  modelos; detectar usuarios que consumen una licencia superior por traspaso.
