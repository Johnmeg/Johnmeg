# Guía de roles SAC: usuarios Planning Standard que cargan archivos

Esta guía explica cómo dar a los usuarios con licencia **SAP Analytics Cloud for Planning, Standard Edition** el acceso que necesitan para cargar archivos a los modelos de planeación con el **Cargador de datos a SAC**, sin asignarles una licencia Professional.

Aplica a los modelos de Fanalca (Ingresos, Gastos y EEFF FANALCA) y a los de Ciudad Limpia. Los pasos los debe ejecutar un administrador de SAC (rol con permiso de crear y asignar roles).

## Resumen

| Qué | Valor |
|---|---|
| Rol base a copiar | **Planner Reporter** (`PROFILE:sap.epm:Planner_Reporter`) |
| Nombre sugerido de la copia | **Planificador - Carga de datos** |
| Licencia del rol | Planning Standard (no cambiarla) |
| Permiso clave | **Planning Model: Leer + Mantener (Maintain)** |
| Además | Compartir cada modelo con el equipo con *Leer + Mantener* |

## Por qué Planner Reporter

- **Planner Reporter** es el rol estándar de SAC que consume la licencia **Planning Standard**. Los roles Admin, BI Admin y Planner Modeler consumen **Planning Professional**.
- La API de importación de datos de SAC (la que usa el Cargador) acepta usuarios Planning Standard.
- Cuando el usuario se conecta con su propia cuenta (OAuth de usuario de negocio), SAC exige el permiso **Mantener (Maintain)** sobre el objeto **Planning Model**, incluso si el modelo es analítico.
- **Mantener** permite agregar o reemplazar datos en un modelo **sin cambiar su estructura**. Crear, Actualizar y Eliminar modelos son permisos de Professional.

> Nunca modifique el rol estándar Planner Reporter: SAP lo puede restablecer en una actualización. Trabaje siempre sobre una copia.

## Paso 1. Copiar el rol

1. En SAC abra el menú **☰ → Seguridad → Roles**.
2. Abra el rol **Planner Reporter**.
3. Use **Guardar como** y nombre la copia **Planificador - Carga de datos**.
4. Verifique en la parte superior del rol que la licencia siga siendo **Planning Standard**.

## Paso 2. Revisar los permisos de la copia

En la matriz de permisos de la copia confirme estas casillas. Primero revise si **Mantener** ya está marcado en *Planning Model*; según la versión del tenant puede venir activo.

| Objeto | Leer | Mantener | Ejecutar | Para qué |
|---|---|---|---|---|
| Planning Model | Sí | **Sí** | Sí | Cargar archivos con el Cargador (obligatorio) |
| Data Action | Sí | — | Sí | Ejecutar los data actions después de la carga |
| Multi Action | Sí | — | Sí | Solo si el usuario usa el Probador de data actions |

> **No marque** Crear, Actualizar ni Eliminar en *Planning Model*. Esas casillas exigen licencia Professional y SAC cambiaría la licencia del rol.

Guarde el rol.

## Paso 3. Asignar el rol

1. Abra **☰ → Seguridad → Usuarios** (o, desde el rol, la sección **Usuarios y equipos**).
2. Asigne el rol **Planificador - Carga de datos**. Es mejor asignarlo a un **equipo** (por ejemplo *Carga de datos Fanalca*) que a cada usuario.
3. Confirme que los usuarios tengan la licencia **Planning Standard** asignada.

## Paso 4. Compartir cada modelo

El rol da el permiso general; además cada modelo debe estar compartido con el equipo.

1. Abra **☰ → Archivos** y ubique el modelo.
2. Seleccione el modelo y use **Compartir**.
3. Agregue el equipo y elija el acceso **Personalizado** con al menos **Leer** y **Mantener**.
4. Repita para cada modelo que el equipo carga: **Ingresos**, **Gastos** y **EEFF FANALCA** (y los modelos de Ciudad Limpia cuando aplique).

## Paso 5. Otras restricciones que pueden bloquear la carga

- **Data Access Control (DAC):** si las dimensiones *Sociedades* o *Cebes* tienen control de acceso, el usuario necesita permiso de **escritura** sobre los miembros que carga.
- **Bloqueo de datos (Data Locking):** las celdas bloqueadas o restringidas no se pueden sobrescribir.
- **Versión:** la versión destino debe ser pública y estar habilitada para escritura. El Cargador bloquea `public.Actual` por defecto (variable `BLOCKED_VERSIONS`).
- **Gestión de datos del Modelador:** los usuarios Planning Standard cargan con el Cargador, no desde *Modelador → Gestión de datos*, que exige el permiso Crear (Professional).

## Prueba

1. Con un usuario Planning Standard, cargue un archivo pequeño en una versión de pruebas.
2. Si la carga termina bien, el acceso está completo.
3. Si aparece el mensaje *"Su usuario no tiene permisos en SAC para esta operación o modelo"* (error 403):
   1. Revise primero el **Paso 4** (el modelo compartido con *Mantener*).
   2. Luego el **Paso 2** (casilla *Mantener* en Planning Model).
   3. Por último el **Data Access Control** del Paso 5.

## Fuentes

- SAP Help: [Permisos de los roles estándar](https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/14cac91febef464dbb1efce20e3f1613/fe6efb8aba9444c6a3ce21eef02bba62.html)
- SAP Help: [Licencias de planificación y roles](https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/00f68c2e08b941f081002fd3691d86a7/e61ce06c6bb2428eb649fb6ccba73c79.html)
- SAP Help: [Permisos de la API de importación de datos](https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/00f68c2e08b941f081002fd3691d86a7/93fec5646f144e109745ce74fd492c3f.html)
- SAP Help: [Compartir modelos](https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/00f68c2e08b941f081002fd3691d86a7/44b47657d843475581824fb328156e7d.html)
- SAP KBA [3380048](https://userapps.support.sap.com/sap/support/knowledge/en/3380048)
- SAP KBA [2604397](https://userapps.support.sap.com/sap/support/knowledge/en/2604397)
