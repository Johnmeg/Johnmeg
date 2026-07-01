# Configuración de tenant SAP Analytics Cloud para el Add-in de Excel

## Tenant a registrar

- URL original: `https://fanalca-clpriv-sac.us21.analytics.cloud.sap/`
- URL normalizada (sin `/` final, tal como exige el instructivo): `https://fanalca-clpriv-sac.us21.analytics.cloud.sap`
- Dominio: `analytics.cloud.sap` → **no estándar**, requiere configuración manual por el administrador de Microsoft 365 (el dominio estándar `hcs.cloud.sap` no necesita esto).

## Prerrequisitos

1. El add-in debe estar desplegado de forma centralizada y publicado vía el Microsoft 365 admin center (paso 8 del despliegue: elegir **Just me** y **Deploy**).
2. Acceso a una máquina Windows con permisos de administrador de Microsoft 365.
3. Módulo de PowerShell `O365CentralizedAddInDeployment` instalado:

   ```powershell
   Install-Module -Name O365CentralizedAddInDeployment
   ```

## Pasos

1. Abrir PowerShell y conectarse al tenant de Office 365:

   ```powershell
   Connect-OrganizationAddInService
   ```

   Se abrirá un diálogo de login: usar el usuario administrador de Microsoft 365.

2. Registrar el tenant SAC (incluyendo siempre `https://hcs.cloud.sap`, que es obligatorio en el comando aunque no se use):

   ```powershell
   Set-OrganizationAddInOverrides -ProductId 8a512e2b-c04e-4c06-9235-11b6cd59f584 -AppDomains "https://hcs.cloud.sap", "https://fanalca-clpriv-sac.us21.analytics.cloud.sap"
   ```

   Verificar que el resultado del comando muestre la configuración con el dominio agregado.

   > Si hay más tenants SAC no estándar en la organización, se agregan como elementos adicionales separados por coma en la misma lista de `-AppDomains`.

3. (Opcional) Rollback a la configuración por defecto:

   ```powershell
   Set-OrganizationAddInOverrides -ProductId 8a512e2b-c04e-4c06-9235-11b6cd59f584 -AppDomains "https://hcs.cloud.sap"
   ```

4. Desplegar el add-in a los usuarios/grupos desde el Microsoft 365 admin center.

5. **Limpiar la caché del add-in** en cada cliente que ya lo haya cargado antes de esta configuración:
   - **Excel Online**: F12 → pestaña Application → Local Storage → clic derecho sobre `https://***-excel.officeapps.live.com` → Clear → refrescar.
   - **Excel para Mac**: cerrar Excel, ir a `/Users/<user>/Library/Containers/com.microsoft.Excel/Data/Library/Application Support/Microsoft/Office/16.0/Wef`, buscar `8a512e2b-c04e-4c06-9235-11b6cd59f584` y borrar los resultados.
   - **Excel para Windows**: cerrar todas las apps de M365 → Excel → File → Options → Trust Center → Trust Center Settings → Trusted Add-in Catalogs → marcar "Next time Office starts, clear all previously-started web add-in cache" → cerrar y reabrir Excel.

## Notas

- La conexión de PowerShell (`Connect-OrganizationAddInService`) puede perderse; si el comando falla, reconectar y reintentar.
- No agregar caracteres extra (como `/`) al final de las URLs registradas, o el tenant no quedará registrado correctamente.
