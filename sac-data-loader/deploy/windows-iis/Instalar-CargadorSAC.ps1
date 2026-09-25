#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Instala o actualiza el Cargador de datos a SAC (Ciudad Limpia) en Windows Server con IIS.

.DESCRIPTION
  Ejecutar en el servidor, como administrador, desde la carpeta sac-data-loader extraída del ZIP:

    powershell -ExecutionPolicy Bypass -File .\deploy\windows-iis\Instalar-CargadorSAC.ps1 -Dominio cargas-sac.ciudadlimpia.com

  Hace, en orden:
    1. Verifica (o instala con -InstalarNode) Node.js LTS.
    2. Copia la aplicación a -RutaApp e instala sus dependencias (npm ci).
    3. Crea el archivo .env pidiendo los datos del cliente OAuth de SAC (el Secret no se muestra).
    4. Protege el .env y crea el servicio de Windows "SacDataLoader" con NSSM.
    5. Instala IIS, URL Rewrite y ARR si faltan, y crea el sitio HTTPS que reenvía a la aplicación.
    6. Abre los puertos 80 y 443 en el firewall y verifica que todo responda.

  Se puede ejecutar de nuevo para ACTUALIZAR la aplicación: conserva el .env y los registros.

.PARAMETER Dominio
  Nombre DNS con el que los usuarios abrirán la aplicación, p. ej. cargas-sac.ciudadlimpia.com

.PARAMETER Certificado
  Huella (thumbprint) del certificado HTTPS ya instalado en "Equipo local > Personal".
  Si se omite, se busca uno vigente para el dominio.

.PARAMETER ArchivoPfx
  Alternativa a -Certificado: ruta a un .pfx que se importará (pide la contraseña).

.PARAMETER CuentaServicio
  LocalService (recomendado, pocos privilegios) o LocalSystem.

.PARAMETER Proxy
  Proxy corporativo para la salida a internet (npm y SAC), p. ej. http://proxy.fanalca.local:8080

.PARAMETER CertificadoRaizCA
  Certificado raíz (.pem) si el proxy inspecciona TLS. Se pasa a Node como NODE_EXTRA_CA_CERTS.

.PARAMETER Reconfigurar
  Vuelve a pedir los datos de SAC y reescribe el .env aunque ya exista.

.PARAMETER SinIIS
  Sólo instala la aplicación y el servicio (útil si el proxy HTTPS es otro equipo).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9.-]+$')]
    [string]$Dominio,

    [string]$RutaApp = 'C:\apps\sac-data-loader',
    [string]$RutaSitio = 'C:\inetpub\sac-data-loader',
    [ValidateRange(1024, 65535)]
    [int]$Puerto = 3000,
    [string]$Certificado,
    [string]$ArchivoPfx,
    [ValidateSet('LocalService', 'LocalSystem')]
    [string]$CuentaServicio = 'LocalService',
    [string]$Proxy,
    [string]$CertificadoRaizCA,
    [string]$RutaNssm,
    [switch]$InstalarNode,
    [switch]$Reconfigurar,
    [switch]$SinIIS
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$NombreServicio = 'SacDataLoader'
$NombreSitio = 'CargadorSAC'
$Origen = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$script:paso = 0

# ------------------------------------------------------------------ utilidades
function Paso([string]$texto) {
    $script:paso++
    Write-Host ''
    Write-Host ("[{0}] {1}" -f $script:paso, $texto) -ForegroundColor Green
}
function Ok([string]$texto) { Write-Host "    OK  $texto" -ForegroundColor DarkGreen }
function Aviso([string]$texto) { Write-Host "    !!  $texto" -ForegroundColor Yellow }
function Falla([string]$texto) { throw $texto }

function Descargar([string]$url, [string]$destino) {
    $params = @{ Uri = $url; OutFile = $destino; UseBasicParsing = $true }
    if ($Proxy) { $params.Proxy = $Proxy; $params.ProxyUseDefaultCredentials = $true }
    Invoke-WebRequest @params
}

function Instalar-Msi([string]$archivo) {
    $p = Start-Process msiexec.exe -ArgumentList '/i', ('"{0}"' -f $archivo), '/qn', '/norestart' -Wait -PassThru
    if ($p.ExitCode -ne 0 -and $p.ExitCode -ne 3010) { Falla "La instalación de $archivo terminó con código $($p.ExitCode)." }
}

function Leer([string]$pregunta, [string]$patron = '.+', [string]$ejemplo = '') {
    while ($true) {
        if ($ejemplo) { Write-Host "    Ejemplo: $ejemplo" -ForegroundColor DarkGray }
        $valor = (Read-Host "    $pregunta").Trim()
        if ($valor -match $patron -and $valor -notmatch '[<>\r\n]') { return $valor }
        Aviso 'Valor no válido, intente de nuevo.'
    }
}

function Leer-Secreto([string]$pregunta) {
    while ($true) {
        $seguro = Read-Host "    $pregunta" -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro)
        try { $valor = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim() }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
        if ($valor -and $valor -notmatch '[\r\n]') { return $valor }
        Aviso 'El valor no puede estar vacío.'
    }
}

function Nueva-Clave {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    return (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Escribir-Utf8([string]$ruta, [string]$contenido) {
    [IO.File]::WriteAllText($ruta, $contenido, (New-Object Text.UTF8Encoding($false)))
}

function Probar-Salud([string]$url, [int]$intentos = 15) {
    for ($i = 0; $i -lt $intentos; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 4
            if ($r.StatusCode -eq 200 -and $r.Content -match 'ok') { return $true }
        } catch { Start-Sleep -Seconds 2 }
    }
    return $false
}

function Nssm { & $script:Nssm @args; if ($LASTEXITCODE -ne 0) { Falla "nssm $($args -join ' ') falló (código $LASTEXITCODE)." } }

# ------------------------------------------------------------------ inicio
New-Item -ItemType Directory -Force -Path (Join-Path $RutaApp 'logs') | Out-Null
$transcript = Join-Path $RutaApp ('logs\instalacion-{0:yyyyMMdd-HHmmss}.log' -f (Get-Date))
Start-Transcript -Path $transcript | Out-Null

try {
    Write-Host ''
    Write-Host '  Cargador de datos a SAC - Ciudad Limpia' -ForegroundColor Green
    Write-Host "  Instalación en Windows Server + IIS   ->   https://$Dominio" -ForegroundColor Green

    if (-not (Test-Path (Join-Path $Origen 'package.json')) -or -not (Test-Path (Join-Path $Origen 'server.js'))) {
        Falla "No se encontró la aplicación en $Origen. Ejecute el script desde la carpeta sac-data-loader extraída del ZIP."
    }

    # -------------------------------------------------------------- 1. Node.js
    Paso 'Node.js'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    $nodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue
    $nodeVersion = $null
    if ($nodeCmd) { $nodeVersion = [version]((& $nodeCmd.Source -v).Trim().TrimStart('v')) }
    if (-not $nodeVersion -or $nodeVersion.Major -lt 20) {
        if (-not $InstalarNode) {
            Falla 'Node.js 20 o superior no está instalado. Instálelo desde https://nodejs.org (LTS, x64) o ejecute el script con -InstalarNode.'
        }
        $indice = Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json' -UseBasicParsing
        $lts = $indice | Where-Object { $_.version -like 'v22.*' -and $_.lts } | Select-Object -First 1
        if (-not $lts) { Falla 'No se pudo determinar la versión LTS de Node.js.' }
        $msi = Join-Path $env:TEMP ("node-{0}-x64.msi" -f $lts.version)
        Write-Host "    Descargando Node.js $($lts.version)..."
        Descargar ("https://nodejs.org/dist/{0}/node-{0}-x64.msi" -f $lts.version) $msi
        Instalar-Msi $msi
        $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
        $nodeCmd = Get-Command node.exe
        $nodeVersion = [version]((& $nodeCmd.Source -v).Trim().TrimStart('v'))
    }
    $NodeExe = $nodeCmd.Source
    $Npm = Join-Path (Split-Path $NodeExe) 'npm.cmd'
    Ok "Node.js $nodeVersion en $NodeExe"

    # -------------------------------------------------------------- 2. copiar aplicación
    Paso "Copiando la aplicación a $RutaApp"
    $servicio = Get-Service -Name $NombreServicio -ErrorAction SilentlyContinue
    if ($servicio -and $servicio.Status -ne 'Stopped') {
        Stop-Service -Name $NombreServicio -Force
        Ok 'Servicio detenido para actualizar'
    }
    if ((Resolve-Path $Origen).Path.TrimEnd('\') -ne $RutaApp.TrimEnd('\')) {
        & robocopy.exe $Origen $RutaApp /E /NFL /NDL /NJH /NJS /NP /R:2 /W:2 /XD node_modules logs test samples .git /XF .env | Out-Null
        if ($LASTEXITCODE -ge 8) { Falla "robocopy falló (código $LASTEXITCODE)." }
    }
    Ok 'Archivos copiados (se conservan .env y logs)'

    # -------------------------------------------------------------- 3. dependencias
    Paso 'Instalando dependencias (npm ci)'
    if ($Proxy) { $env:HTTPS_PROXY = $Proxy; $env:HTTP_PROXY = $Proxy }
    if ($CertificadoRaizCA) { $env:NODE_EXTRA_CA_CERTS = $CertificadoRaizCA }
    Push-Location $RutaApp
    try {
        & $Npm ci --omit=dev --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { Falla 'npm ci falló. Revise la salida a internet (registry.npmjs.org) o use -Proxy.' }
    } finally { Pop-Location }
    Ok 'Dependencias instaladas'

    # -------------------------------------------------------------- 4. configuración .env
    Paso 'Configuración (.env)'
    $envPath = Join-Path $RutaApp '.env'
    if ((Test-Path $envPath) -and -not $Reconfigurar) {
        Ok 'Se conserva el .env existente (use -Reconfigurar para reescribirlo)'
    } else {
        Write-Host '    Datos del cliente OAuth de SAC (Sistema > Administración > App Integration).'
        Write-Host "    La Redirect URI del cliente debe ser: https://$Dominio/auth/callback" -ForegroundColor Cyan
        $tenant = (Leer 'URL del tenant de SAC' '^https://[^/]+' 'https://fanalca.us21.analytics.cloud.sap').TrimEnd('/')
        $authUrl = Leer 'Authorization URL' '^https://.+/oauth/authorize$' 'https://<subdominio>.authentication.us21.hana.ondemand.com/oauth/authorize'
        $tokenUrl = Leer 'Token URL' '^https://.+/oauth/token$' 'https://<subdominio>.authentication.us21.hana.ondemand.com/oauth/token'
        $clientId = Leer 'OAuth Client ID'
        $secret = Leer-Secreto 'Secret (no se muestra al escribir)'
        $lineas = @(
            "# Generado por Instalar-CargadorSAC.ps1 el $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
            "PORT=$Puerto",
            'HOST=127.0.0.1',
            "APP_BASE_URL=https://$Dominio",
            'TRUST_PROXY=true',
            "SESSION_SECRET=$(Nueva-Clave)",
            'SESSION_MINUTES=60',
            "SAC_TENANT_URL=$tenant",
            "SAC_AUTHORIZE_URL=$authUrl",
            "SAC_TOKEN_URL=$tokenUrl",
            "SAC_CLIENT_ID=$clientId",
            "SAC_CLIENT_SECRET=$secret",
            'SAC_OAUTH_PKCE=true',
            'MAX_FILE_MB=20',
            'MAX_ROWS=100000',
            'CHUNK_SIZE=10000',
            'NUMBER_LOCALE=es',
            'BLOCKED_VERSIONS=public.Actual',
            'VALIDATE_MEMBERS=true',
            'SAC_DEBUG=false'
        )
        Escribir-Utf8 $envPath (($lineas -join "`r`n") + "`r`n")
        $secret = $null
        Ok ".env creado en $envPath"
    }

    Push-Location $RutaApp
    try {
        $salida = & $NodeExe -e "require('./src/config').loadConfig(); console.log('config-ok')" 2>&1
    } finally { Pop-Location }
    if (($salida -join "`n") -notmatch 'config-ok') { Falla "La configuración no es válida: $($salida -join ' ')" }
    Ok 'Configuración válida'

    # -------------------------------------------------------------- 5. permisos
    Paso "Permisos de archivos (cuenta del servicio: $CuentaServicio)"
    $sid = if ($CuentaServicio -eq 'LocalService') { 'S-1-5-19' } else { 'S-1-5-18' }
    & icacls.exe $RutaApp /grant "*${sid}:(OI)(CI)RX" /Q | Out-Null
    & icacls.exe (Join-Path $RutaApp 'logs') /grant "*${sid}:(OI)(CI)M" /Q | Out-Null
    # .env: sólo Administradores, SYSTEM y la cuenta del servicio
    & icacls.exe $envPath /inheritance:r /grant:r '*S-1-5-32-544:F' '*S-1-5-18:F' "*${sid}:R" /Q | Out-Null
    if ($LASTEXITCODE -ne 0) { Falla 'No se pudieron ajustar los permisos del .env.' }
    Ok '.env visible sólo para Administradores, SYSTEM y la cuenta del servicio'

    # -------------------------------------------------------------- 6. servicio de Windows
    Paso "Servicio de Windows '$NombreServicio'"
    if ($RutaNssm) { $script:Nssm = $RutaNssm }
    elseif (Get-Command nssm.exe -ErrorAction SilentlyContinue) { $script:Nssm = (Get-Command nssm.exe).Source }
    elseif (Test-Path (Join-Path $RutaApp 'tools\nssm.exe')) { $script:Nssm = Join-Path $RutaApp 'tools\nssm.exe' }
    else {
        Write-Host '    Descargando NSSM...'
        $zip = Join-Path $env:TEMP 'nssm-2.24.zip'
        try { Descargar 'https://nssm.cc/release/nssm-2.24.zip' $zip }
        catch { Falla 'No se pudo descargar NSSM. Descárguelo de https://nssm.cc y ejecute el script con -RutaNssm C:\ruta\nssm.exe' }
        $tmp = Join-Path $env:TEMP 'nssm-2.24'
        Expand-Archive -Path $zip -DestinationPath $env:TEMP -Force
        New-Item -ItemType Directory -Force -Path (Join-Path $RutaApp 'tools') | Out-Null
        Copy-Item (Join-Path $tmp 'win64\nssm.exe') (Join-Path $RutaApp 'tools\nssm.exe') -Force
        $script:Nssm = Join-Path $RutaApp 'tools\nssm.exe'
    }
    Ok "NSSM: $script:Nssm"

    if (-not (Get-Service -Name $NombreServicio -ErrorAction SilentlyContinue)) {
        Nssm install $NombreServicio $NodeExe server.js
    }
    $log = Join-Path $RutaApp 'logs\servicio.log'
    Nssm set $NombreServicio Application $NodeExe
    Nssm set $NombreServicio AppParameters server.js
    Nssm set $NombreServicio AppDirectory $RutaApp
    Nssm set $NombreServicio DisplayName 'Cargador de datos a SAC - Ciudad Limpia'
    Nssm set $NombreServicio Description 'Carga validada de archivos a los modelos de planeación de SAP Analytics Cloud.'
    Nssm set $NombreServicio Start SERVICE_AUTO_START
    Nssm set $NombreServicio AppStdout $log
    Nssm set $NombreServicio AppStderr $log
    Nssm set $NombreServicio AppRotateFiles 1
    Nssm set $NombreServicio AppRotateOnline 1
    Nssm set $NombreServicio AppRotateBytes 10485760
    Nssm set $NombreServicio AppRestartDelay 5000
    $entorno = @('NODE_ENV=production')
    if ($Proxy) { $entorno += @('NODE_USE_ENV_PROXY=1', "HTTPS_PROXY=$Proxy", "HTTP_PROXY=$Proxy", 'NO_PROXY=127.0.0.1,localhost') }
    if ($CertificadoRaizCA) { $entorno += "NODE_EXTRA_CA_CERTS=$CertificadoRaizCA" }
    Nssm set $NombreServicio AppEnvironmentExtra $entorno

    $cuenta = if ($CuentaServicio -eq 'LocalService') { 'NT AUTHORITY\LocalService' } else { 'LocalSystem' }
    $svcCim = Get-CimInstance -ClassName Win32_Service -Filter "Name='$NombreServicio'"
    $r = Invoke-CimMethod -InputObject $svcCim -MethodName Change -Arguments @{ StartName = $cuenta; StartPassword = '' }
    if ($r.ReturnValue -ne 0) { Falla "No se pudo asignar la cuenta $cuenta al servicio (código $($r.ReturnValue))." }

    Start-Service -Name $NombreServicio
    if (-not (Probar-Salud "http://127.0.0.1:$Puerto/healthz")) {
        Aviso 'La aplicación no respondió. Últimas líneas de logs\servicio.log:'
        if (Test-Path $log) { Get-Content $log -Tail 25 | ForEach-Object { Write-Host "      $_" } }
        Falla "El servicio no arrancó. Si el registro muestra errores de permisos, pruebe con -CuentaServicio LocalSystem."
    }
    Ok "Servicio en ejecución y respondiendo en http://127.0.0.1:$Puerto"

    if (-not $SinIIS) {
        # ---------------------------------------------------------- 7. IIS
        Paso 'IIS, URL Rewrite y Application Request Routing'
        if (-not (Get-Command Get-WindowsFeature -ErrorAction SilentlyContinue)) {
            Falla 'Este instalador requiere Windows Server (Get-WindowsFeature no existe en este equipo). Use -SinIIS o instale IIS manualmente.'
        }
        Import-Module ServerManager
        $faltan = @('Web-Server', 'Web-Mgmt-Console') | Where-Object { -not (Get-WindowsFeature -Name $_).Installed }
        if ($faltan) {
            Write-Host "    Instalando $($faltan -join ', ')..."
            Install-WindowsFeature -Name $faltan | Out-Null
        }
        Ok 'Rol IIS instalado'

        if (-not (Test-Path "$env:SystemRoot\System32\inetsrv\rewrite.dll")) {
            Write-Host '    Descargando URL Rewrite 2.1...'
            $f = Join-Path $env:TEMP 'rewrite_amd64_en-US.msi'
            Descargar 'https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi' $f
            Instalar-Msi $f
        }
        Ok 'URL Rewrite instalado'

        if (-not (Test-Path "$env:ProgramFiles\IIS\Application Request Routing\requestRouter.dll")) {
            Write-Host '    Descargando Application Request Routing 3.0...'
            $f = Join-Path $env:TEMP 'requestRouter_amd64.msi'
            Descargar 'https://download.microsoft.com/download/E/9/8/E9849D6A-020E-47E4-9FD0-A023E99B54EB/requestRouter_amd64.msi' $f
            Instalar-Msi $f
        }
        Ok 'Application Request Routing instalado'

        $appcmd = "$env:SystemRoot\System32\inetsrv\appcmd.exe"
        & $appcmd set config -section:system.webServer/proxy /enabled:true /timeout:00:05:00 /commit:apphost | Out-Null
        if ($LASTEXITCODE -ne 0) { Falla 'No se pudo habilitar el proxy de ARR.' }
        $vars = & $appcmd list config -section:system.webServer/rewrite/allowedServerVariables
        if (-not ($vars -match 'HTTP_X_FORWARDED_PROTO')) {
            & $appcmd set config -section:system.webServer/rewrite/allowedServerVariables '/+[name=''HTTP_X_FORWARDED_PROTO'']' /commit:apphost | Out-Null
            if ($LASTEXITCODE -ne 0) { Falla 'No se pudo permitir la variable HTTP_X_FORWARDED_PROTO.' }
        }
        Ok 'Proxy de ARR habilitado (timeout 300 s) y variable HTTP_X_FORWARDED_PROTO permitida'

        # ---------------------------------------------------------- 8. certificado
        Paso "Certificado HTTPS para $Dominio"
        if ($ArchivoPfx) {
            $clavePfx = Read-Host '    Contraseña del archivo PFX' -AsSecureString
            $cert = Import-PfxCertificate -FilePath $ArchivoPfx -CertStoreLocation Cert:\LocalMachine\My -Password $clavePfx
            $Certificado = $cert.Thumbprint
        }
        if (-not $Certificado) {
            $candidatos = Get-ChildItem Cert:\LocalMachine\My | Where-Object {
                $c = $_
                $c.HasPrivateKey -and $c.NotAfter -gt (Get-Date) -and
                (@($c.DnsNameList | ForEach-Object { $_.Unicode }) | Where-Object { $Dominio -like $_ })
            } | Sort-Object NotAfter -Descending
            if (-not $candidatos) {
                Falla ("No hay un certificado vigente para $Dominio en 'Equipo local > Personal'. " +
                    'Instálelo o use -ArchivoPfx C:\ruta\certificado.pfx o -Certificado <huella>.')
            }
            $Certificado = @($candidatos)[0].Thumbprint
        }
        $Certificado = ($Certificado -replace '\s', '').ToUpper()
        $certObj = Get-Item "Cert:\LocalMachine\My\$Certificado" -ErrorAction SilentlyContinue
        if (-not $certObj) { Falla "No se encontró el certificado con huella $Certificado." }
        Ok ("{0} (vence {1:yyyy-MM-dd})" -f $certObj.Subject, $certObj.NotAfter)

        # ---------------------------------------------------------- 9. sitio
        Paso "Sitio IIS '$NombreSitio'"
        Import-Module WebAdministration
        New-Item -ItemType Directory -Force -Path $RutaSitio | Out-Null
        $webConfig = Get-Content (Join-Path $Origen 'deploy\windows-iis\web.config') -Raw
        $webConfig = $webConfig -replace '127\.0\.0\.1:3000', "127.0.0.1:$Puerto"
        Escribir-Utf8 (Join-Path $RutaSitio 'web.config') $webConfig

        if (-not (Test-Path "IIS:\AppPools\$NombreSitio")) { New-WebAppPool -Name $NombreSitio | Out-Null }
        Set-ItemProperty "IIS:\AppPools\$NombreSitio" -Name managedRuntimeVersion -Value ''

        if (-not (Get-Website -Name $NombreSitio)) {
            New-Website -Name $NombreSitio -PhysicalPath $RutaSitio -ApplicationPool $NombreSitio -HostHeader $Dominio -Port 80 | Out-Null
        } else {
            Set-ItemProperty "IIS:\Sites\$NombreSitio" -Name physicalPath -Value $RutaSitio
        }
        if (-not (Get-WebBinding -Name $NombreSitio -Protocol https)) {
            New-WebBinding -Name $NombreSitio -Protocol https -Port 443 -HostHeader $Dominio -SslFlags 1
        }
        $sslPath = "IIS:\SslBindings\!443!$Dominio"
        if (Test-Path $sslPath) { Remove-Item $sslPath -Force }
        (Get-WebBinding -Name $NombreSitio -Protocol https).AddSslCertificate($Certificado, 'My')
        Start-Website -Name $NombreSitio
        Ok "https://$Dominio -> http://127.0.0.1:$Puerto"

        # ---------------------------------------------------------- 10. firewall
        Paso 'Firewall de Windows'
        $regla = 'Cargador SAC - HTTP/HTTPS'
        if (-not (Get-NetFirewallRule -DisplayName $regla -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName $regla -Direction Inbound -Protocol TCP -LocalPort 80, 443 -Action Allow | Out-Null
        }
        Ok "Entrada permitida por 80 y 443 (el puerto $Puerto queda sólo para el propio servidor)"
    }

    # -------------------------------------------------------------- verificación final
    Paso 'Verificación'
    if (-not $SinIIS) {
        if (Probar-Salud "https://$Dominio/healthz" 3) { Ok "https://$Dominio/healthz responde" }
        else { Aviso "No se pudo abrir https://$Dominio/healthz desde este servidor (¿el DNS ya apunta aquí?). Pruébelo desde un equipo de usuario." }
    }

    Write-Host ''
    Write-Host '  Instalación terminada.' -ForegroundColor Green
    Write-Host '  Pendiente:'
    Write-Host "   1. En SAC, el cliente OAuth (Interactive Usage) debe tener la Redirect URI: https://$Dominio/auth/callback"
    Write-Host "   2. El DNS de $Dominio debe apuntar a este servidor."
    Write-Host "   3. Abra https://$Dominio, inicie sesión y cargue un archivo pequeño a una versión de prueba."
    Write-Host "  Registro de esta instalación: $transcript"
}
catch {
    Write-Host ''
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Registro de la instalación: $transcript" -ForegroundColor Red
    Stop-Transcript | Out-Null
    exit 1
}
Stop-Transcript | Out-Null
