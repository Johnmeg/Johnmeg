# Privilegios y permisos de SAP Analytics Cloud

Fuente: SAP Help, *Privileges and Permissions* y *Understand Licenses, Roles, and
Permissions*, Q3 2026 (2026.15).

## Contenido
1. Significado de cada permiso
2. Matriz por privilegio (objetos de planificación y modelado)
3. Matriz por privilegio (administración y seguridad)
4. Matriz por privilegio (contenido, colaboración e IA)
5. Permisos por objeto individual y por compartir
6. Qué exige Planning Professional

Leyenda de la matriz (8 posiciones): `C` Crear, `R` Leer, `U` Actualizar, `D` Eliminar,
`E` Ejecutar, `M` Mantener, `S` Compartir, `M` Gestionar (Manage, última posición).
Un guion significa que el permiso no existe para ese privilegio.

## 1. Significado de cada permiso

| Permiso | Qué permite |
|---|---|
| Crear (Create) | Crear objetos de ese tipo, o subir datos a un objeto. Siempre acompáñelo de Leer. |
| Leer (Read) | Abrir y ver el objeto y su contenido. |
| Actualizar (Update) | Editar el objeto, **incluida la estructura** de modelos y dimensiones. |
| Eliminar (Delete) | Borrar el objeto. |
| Ejecutar (Execute) | Ejecutar un proceso (data action, multi action, funciones de planificación, publicar en el catálogo…). |
| Mantener (Maintain) | Mantener **valores** sin cambiar la estructura: en Planning Model y Analytic Model, actualizar datos (fact data); en Dimension, actualizar miembros; en Lifecycle, importar paquetes; en Connection, ver Conexiones y Estado de programación. |
| Compartir (Share) | Compartir (y mover) ese tipo de objeto. |
| Gestionar (Manage) | En User/Team: asignar roles y aprobar solicitudes. En archivos públicos/privados: control total. En Deleted Files: restaurar lo de otros. En Catalog Administration: activar el catálogo. |

## 2. Planificación y modelado

| Privilegio | Matriz | Notas |
|---|---|---|
| Planning Model | `CRUDEM--` | **Mantener** = agregar o cambiar datos sin tocar la estructura. **Actualizar** = cambiar la estructura (miembros, rango de fechas). **Ejecutar** = habilita las funciones de planificación. |
| Analytic Model | `CRUD-M--` | Igual que arriba, sin Ejecutar. |
| Dimension | `CRUD-M--` | Mantener = agregar miembros sin cambiar la definición; Actualizar = cambiar la definición. |
| Currency | `CRUD----` | Tablas de conversión de moneda. |
| Data Action | `CRUDE---` | C/U/D = diseñar data actions (Professional). **Ejecutar** = correrlos (por ejemplo desde una historia). |
| Multi Action | `CRUDE---` | **Leer** es necesario para abrir el inicio de multi actions, agregarla a un starter **y ejecutarla**; **Ejecutar** la corre. |
| Data Locking | `CRUD-M--` | C/R/U/D para configurar dimensiones de bloqueo y propietarios. **Leer + Mantener** para que un propietario cambie el estado de un bloqueo. |
| Validation Rule | `CRUD----` | Reglas de combinaciones válidas. **Exige Planning Professional.** |
| Calendar Template | `CRUDE---` | Plantillas de procesos de calendario; Ejecutar para instanciarlas. |
| Calendar Admin | `-------M` | Ver y editar todos los eventos del calendario (excepto publicaciones). |
| Job Monitor | `-R-----M` | Con Leer o Gestionar ve **todos** los jobs de data actions y multi actions; sin él, solo los propios, los de versiones que posee y los de tareas compartidas. |
| Compass Simulation | `CRUD-M--` | Leer = escenarios privados; Mantener = publicar escenarios públicos. |
| Data Change Log | `-R-D----` | Auditoría de cambios de datos al publicar versiones. |
| Dataset | `CR------` | Leer contenido; Crear = crear, editar y borrar datasets. |
| Live Connections to HANA | `----E---` | Crear modelos sobre fuentes HANA en vivo. |
| Other Data Sources | `----E---` | Ver el menú Conexiones y conexiones de importación. Va junto con *Connection*. |
| Connection | `CRUD-M-M` | Conexiones individuales. Mantener muestra *Conexiones* y *Estado de programación*. Gestionar solo para administradores. |
| Personal Data Acquisition | `----E---` | Subir datos a una historia. |
| Standard Unit | `-RU-----` | Tablas de unidades de medida. |

## 3. Administración y seguridad

| Privilegio | Matriz | Notas |
|---|---|---|
| Role | `CRUD----` | Acceso a `Seguridad → Roles`. |
| User | `CRUD---M` | Leer = ver usuarios en diálogos. Para ver `Seguridad → Usuarios` se necesita Leer + Crear, Actualizar o Eliminar. Gestionar = asignar roles y aprobar solicitudes. |
| Team | `CRUD---M` | Leer = ver `Seguridad → Equipos`; Gestionar = asignar equipos a roles. |
| Activity Log | `-R-D----` | Registro de actividades. |
| Lifecycle | `-R---MS-` | Leer = Transporte (Exportar/Importar); Mantener = importar desde Content Network; Compartir = exportar. |
| System Information | `-RU-----` | Leer = *Acerca de*; Actualizar = Monitor, Administración, Sinónimos. |
| Ownership of Content | `----E---` | Transferir la propiedad del contenido. |
| Deleted Files | `-------M` | Restaurar archivos borrados de todos. |
| Public Files | `CR-D--SM` | Crear/editar en carpetas públicas; Gestionar = control total de Public y Samples. |
| Private Files | `CR-D--SM` | Carpetas privadas; Gestionar = acceder al contenido privado de otros (por ejemplo cuando alguien se va). |
| Uploaded Files | `C-------` | Subir archivos locales al tenant (adjuntos y repositorio). Revísalo en roles copiados. |
| Workspace | `-R-----M` | Ver espacios de trabajo; Gestionar = crearlos y asignar miembros. |
| Tenant Link | `-R------` | Ver el registro de vinculación de tenants. |
| Smart Data Access Agent Administration | `----E---` | Activar el agente para conexiones SQL en vivo. |
| Support Tool | `C-------` | Grabar errores de BW en vivo para soporte. |

## 4. Contenido, colaboración e IA

| Privilegio | Matriz | Notas |
|---|---|---|
| Story | `CRUD--S-` | Historias. Compartir también permite mover. |
| Data Analyzer | `CR--E---` | Usar el data analyzer. |
| Global Bookmark / Private Bookmark (Personal) | `CRUD--S-` | Marcadores. |
| Private Bookmark (Others) | `C-------` | Copiar marcadores privados de otros. |
| Comment | `CR-D----` | Comentarios en celdas e historias. |
| Discussion | `CR------` | Discusiones. |
| Theme / Custom Widget / Widget Add-On | `CRUD----` | Temas, widgets personalizados y complementos. |
| Composite | `CRUD--S-` | Composites para historias. |
| Analysis Workbook / Add-in Workbook | `CRUD----` | Libros de Analysis for Office / Add-in en el repositorio. |
| Schedule Publication | `C------M` | Programar publicaciones; Gestionar = administrar las de todos. |
| Publish Content | `----E---` | Publicar en el Catálogo. |
| Catalog Administration | `-------M` | Activar el Catálogo. |
| Content Link | `CRUD----` | Enlaces a contenido externo. |
| Translation | `CR-D----` | Panel de traducción (XLIFF). |
| Predictive Scenario | `CRUD----` | Smart Predict. |
| Remote Dataset | `C-------` | Datasets en vivo desde HANA on-premise. |
| Metrics List | `CRUD--S-` | Listas de *My Metrics*. |
| Metrics Alert and Report | `C-------` | Suscribirse a reportes de métricas. |
| Video Data Story | `CRUD--S-` | Historias en video. |
| Private Insight | `C-------` | Guardar insights privados sin poder crear archivos. |
| Runtime Notification | `C-------` | Enviar notificaciones desde historias. |
| Just Ask | `----EM-M` | Ejecutar = usarlo; Mantener = consultar modelos no publicados en Just Ask; Gestionar = administrar modelos, sinónimos y reglas. |
| Generative AI | `----E---` | Funciones asistidas por IA. |
| Joule | `-R--E---` | Leer = insights analíticos en Joule; Ejecutar reservado. |
| Analytics Hub Assets | `CRUDE---` | Ejecutar = validar o rechazar activos. |
| Analytics Hub Structures | `CRUD----` | Estructuras del Hub. |
| Digital Boardroom | `CRUD--S-` | **Obsoleto.** |
| Automated Discoveries | `----E---` | **Obsoleto**, sin efecto. |

## 5. Permisos por objeto y por compartir

- La mayoría de los permisos aplican a **todos** los objetos de un tipo. Algunos (por
  ejemplo Data Change Log, modelos, dimensiones) se pueden dar **por objeto** expandiendo
  la fila en la matriz del rol.
- Hay permisos que solo aplican a objetos **propios** (por ejemplo, Eliminar dimensiones que
  el usuario creó).
- **Compartir** un archivo o carpeta (Archivos → Compartir) da acceso a ese objeto a
  usuarios o equipos, con niveles Ver, Editar, Completo o Personalizado (Leer, Mantener,
  Actualizar…). SAP recomienda usar compartir solo para archivos y carpetas puntuales; los
  permisos generales van en el rol.
- Para cargar o escribir datos en un modelo se necesitan **las dos cosas**: el permiso en el
  rol (Mantener en Planning Model) y acceso al modelo (compartido con Leer + Mantener).

## 6. Qué exige Planning Professional

Según la documentación, requieren licencia Planning Professional:
- Crear, actualizar y eliminar **modelos de planificación**.
- Crear o editar **data actions**, incluidos los pasos de asignación.
- **Validation Rule** (todas sus casillas).
- Crear y eliminar **plantillas de calendario** con contenido de planificación.
- Establecer la conexión de SAC a **BPC**.

Si en un rol Planning Standard no se puede marcar una casilla de esta lista, la causa es la
licencia del rol. Confirma siempre la licencia que termina consumiendo el usuario en
`Seguridad → Usuarios`.
