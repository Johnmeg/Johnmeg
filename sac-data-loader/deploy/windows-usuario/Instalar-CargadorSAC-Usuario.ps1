<#
.SYNOPSIS
  Instala el Cargador de datos a SAC o el Probador de data actions (Ciudad Limpia, Fanalca)
  en el computador del usuario. Son aplicaciones separadas: cada una con su carpeta, su
  acceso directo, su puerto y su configuración.

.DESCRIPTION
  No requiere permisos de administrador. Se instala en %LOCALAPPDATA%\<carpeta de la marca>
  (CargadorSAC para Ciudad Limpia, CargadorSAC-Fanalca para Fanalca):
    - Node.js portátil (sin instalador de Windows) si hace falta. Si el paquete trae
      node-v*-win-x64.zip no descarga nada.
    - La aplicación y sus dependencias (incluidas en el instalador .exe).
    - La configuración (.env), protegida para que sólo el usuario la lea.
    - Accesos directos en el escritorio y el menú Inicio.

  Si junto al instalador hay un archivo config-empresa.env (preparado por el
  administrador), toma de ahí los datos de SAC y no los pregunta.

  Ejecutar con doble clic en Instalar.cmd. Se puede ejecutar de nuevo para
  actualizar: conserva la configuración y los registros.

.PARAMETER Marca
  ciudadlimpia o fanalca. Por defecto la del archivo marca.txt del paquete.

.PARAMETER Producto
  cargador o probador. Por defecto el del archivo producto.txt del paquete.

.PARAMETER Puerto
  Puerto local (por defecto el de la marca: 3000 Ciudad Limpia, 3001 Fanalca). Debe
  coincidir con la Redirect URI del cliente OAuth en SAC: http://localhost:<Puerto>/auth/callback

.PARAMETER Proxy
  Proxy corporativo, p. ej. http://proxy.empresa.local:8080

.PARAMETER NodeZip
  Ruta a un node-vXX-win-x64.zip ya descargado (equipos sin acceso a nodejs.org).
#>
[CmdletBinding()]
param(
    [ValidatePattern('^[a-z0-9-]*$')]
    [string]$Marca,
    [ValidatePattern('^[a-z]*$')]
    [string]$Producto,
    [string]$Destino,
    [ValidateRange(0, 65535)]
    [int]$Puerto = 0,
    [string]$Proxy,
    [string]$CertificadoRaizCA,
    [string]$NodeZip,
    [switch]$Reconfigurar,
    [switch]$NoAbrir
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$Aqui = $PSScriptRoot
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
    $p = @{ Uri = $url; OutFile = $destino; UseBasicParsing = $true }
    if ($Proxy) { $p.Proxy = $Proxy; $p.ProxyUseDefaultCredentials = $true }
    Invoke-WebRequest @p
}
function Obtener([string]$url) {
    $p = @{ Uri = $url; UseBasicParsing = $true }
    if ($Proxy) { $p.Proxy = $Proxy; $p.ProxyUseDefaultCredentials = $true }
    return (Invoke-WebRequest @p).Content
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
# Datos del cliente OAuth de SAC en una ventana de Windows (se puede pegar con
# Ctrl+V o clic derecho). Devuelve $false si no hay interfaz gráfica disponible.
$CamposSac = @(
    @{ K = 'SAC_TENANT_URL'; T = 'URL del tenant de SAC'; P = '^https://[^/\s]+/?$'; E = 'https://fanalca-clpriv-sac.us21.analytics.cloud.sap' },
    @{ K = 'SAC_AUTHORIZE_URL'; T = 'Authorization URL'; P = '^https://\S+/oauth/authorize$'; E = 'https://<subdominio>.authentication.us21.hana.ondemand.com/oauth/authorize' },
    @{ K = 'SAC_TOKEN_URL'; T = 'Token URL'; P = '^https://\S+/oauth/token$'; E = 'https://<subdominio>.authentication.us21.hana.ondemand.com/oauth/token' },
    @{ K = 'SAC_CLIENT_ID'; T = 'OAuth Client ID'; P = '^\S+$'; E = '' },
    @{ K = 'SAC_CLIENT_SECRET'; T = 'Secret'; P = '^\S+$'; E = ''; S = $true }
)
function Limpiar-Valor($v) { return ([string]$v).Trim().Trim('"', "'").Trim() }
function Pedir-DatosSac-Ventana($valores) {
    try {
        Add-Type -AssemblyName System.Windows.Forms, System.Drawing -ErrorAction Stop
        [Windows.Forms.Application]::EnableVisualStyles()
    } catch { return $false }

    $f = New-Object Windows.Forms.Form
    $f.Text = $Titulo
    $f.StartPosition = 'CenterScreen'
    $f.FormBorderStyle = 'FixedDialog'
    $f.MaximizeBox = $false
    $f.MinimizeBox = $false
    $f.TopMost = $true
    $f.Font = New-Object Drawing.Font('Segoe UI', 10)
    $f.ClientSize = New-Object Drawing.Size(640, 470)

    $intro = New-Object Windows.Forms.Label
    $intro.Text = "Pegue los datos del cliente OAuth de SAC (Ctrl+V o clic derecho > Pegar).`r`n" +
        "La Redirect URI del cliente debe ser: http://localhost:$Puerto/auth/callback"
    $intro.Location = New-Object Drawing.Point(16, 12)
    $intro.Size = New-Object Drawing.Size(608, 44)
    $f.Controls.Add($intro)

    $cajas = @{}
    $y = 64
    foreach ($c in $CamposSac) {
        $l = New-Object Windows.Forms.Label
        $l.Text = $c.T
        $l.Location = New-Object Drawing.Point(16, $y)
        $l.Size = New-Object Drawing.Size(608, 20)
        $f.Controls.Add($l)
        $t = New-Object Windows.Forms.TextBox
        $t.Location = New-Object Drawing.Point(16, ($y + 22))
        $t.Size = New-Object Drawing.Size(608, 26)
        if ($c.S) { $t.UseSystemPasswordChar = $true }
        $actual = $valores[$c.K]
        if (Valor-Util $actual) { $t.Text = $actual } elseif ($c.K -eq 'SAC_TENANT_URL') { $t.Text = $c.E }
        $f.Controls.Add($t)
        $cajas[$c.K] = $t
        if ($c.E -and $c.K -ne 'SAC_TENANT_URL') {
            $e = New-Object Windows.Forms.Label
            $e.Text = "Ejemplo: $($c.E)"
            $e.ForeColor = [Drawing.Color]::Gray
            $e.Font = New-Object Drawing.Font('Segoe UI', 8)
            $e.Location = New-Object Drawing.Point(16, ($y + 50))
            $e.Size = New-Object Drawing.Size(608, 16)
            $f.Controls.Add($e)
            $y += 18
        }
        $y += 60
    }

    $ok = New-Object Windows.Forms.Button
    $ok.Text = 'Aceptar'
    $ok.Size = New-Object Drawing.Size(110, 34)
    $ok.Location = New-Object Drawing.Point(398, ($y + 6))
    $cancel = New-Object Windows.Forms.Button
    $cancel.Text = 'Cancelar'
    $cancel.Size = New-Object Drawing.Size(110, 34)
    $cancel.Location = New-Object Drawing.Point(514, ($y + 6))
    $cancel.DialogResult = [Windows.Forms.DialogResult]::Cancel
    $f.Controls.Add($ok)
    $f.Controls.Add($cancel)
    $f.AcceptButton = $ok
    $f.CancelButton = $cancel
    $f.ClientSize = New-Object Drawing.Size(640, ($y + 52))

    $ok.Add_Click({
        foreach ($c in $CamposSac) {
            $v = Limpiar-Valor $cajas[$c.K].Text
            if ($v -notmatch $c.P -or $v -match '[<>]') {
                [Windows.Forms.MessageBox]::Show($f, "Revise el campo '$($c.T)'.", 'Dato no válido', 'OK', 'Warning') | Out-Null
                $cajas[$c.K].Focus() | Out-Null
                return
            }
        }
        $f.DialogResult = [Windows.Forms.DialogResult]::OK
        $f.Close()
    })
    $f.Add_Shown({ $f.Activate(); $cajas['SAC_AUTHORIZE_URL'].Focus() | Out-Null })

    $r = $f.ShowDialog()
    if ($r -ne [Windows.Forms.DialogResult]::OK) { $f.Dispose(); Falla 'Instalación cancelada: faltan los datos de SAC.' }
    foreach ($c in $CamposSac) { $valores[$c.K] = Limpiar-Valor $cajas[$c.K].Text }
    $valores['SAC_TENANT_URL'] = $valores['SAC_TENANT_URL'].TrimEnd('/')
    $f.Dispose()
    return $true
}

function Nueva-Clave {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes); $rng.Dispose()
    return (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
}
function Escribir-Utf8([string]$ruta, [string]$contenido) {
    [IO.File]::WriteAllText($ruta, $contenido, (New-Object Text.UTF8Encoding($false)))
}
function Escribir-Ascii([string]$ruta, [string[]]$lineas) {
    [IO.File]::WriteAllText($ruta, (($lineas -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)
}

# Lee un archivo KEY=VALUE (como .env). Si una clave se repite, gana la última.
function Leer-Env([string]$ruta) {
    $valores = [ordered]@{}
    foreach ($linea in [IO.File]::ReadAllLines($ruta)) {
        $l = $linea.TrimStart([char]0xFEFF)
        if ($l -match '^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$') {
            $v = $Matches[2]
            if ($v.Length -ge 2 -and (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'")))) { $v = $v.Substring(1, $v.Length - 2) }
            $valores[$Matches[1]] = $v
        }
    }
    return $valores
}
function Valor-Util($v) { return ($v -and $v -notmatch '[<>]') }

function Version-Node([string]$exe) {
    try { return [version]((& $exe -v).Trim().TrimStart('v')) } catch { return $null }
}
function Puerto-Ocupado([int]$p) {
    $c = New-Object Net.Sockets.TcpClient
    try { $c.Connect('127.0.0.1', $p); return $true } catch { return $false } finally { $c.Close() }
}
function Probar-Salud([int]$intentos) {
    for ($i = 0; $i -lt $intentos; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Puerto/healthz" -UseBasicParsing -TimeoutSec 3
            if ($r.Content -match 'ok') { return $true }
        } catch { }
        Start-Sleep -Seconds 1
    }
    return $false
}

# ------------------------------------------------------------------ origen del paquete
$Origen = $null
foreach ($c in @((Join-Path $Aqui '..\app'), (Join-Path $Aqui '..\..'))) {
    if (Test-Path (Join-Path $c 'server.js')) { $Origen = (Resolve-Path $c).Path; break }
}
$ConfigEmpresa = @((Join-Path $Aqui '..\config-empresa.env'), (Join-Path $Aqui 'config-empresa.env')) |
    Where-Object { Test-Path $_ } | Select-Object -First 1

# ------------------------------------------------------------------ marca (empresa)
if (-not $Origen) {
    Write-Host '  ERROR: No se encontró la aplicación junto al instalador. Extraiga todo el ZIP antes de ejecutar Instalar.cmd.' -ForegroundColor Red
    exit 1
}
if (-not $Marca) {
    $archivoMarca = @((Join-Path $Aqui 'marca.txt'), (Join-Path $Aqui '..\marca.txt')) | Where-Object { Test-Path $_ } | Select-Object -First 1
    $Marca = if ($archivoMarca) { (Get-Content $archivoMarca -Raw).Trim().ToLower() } else { 'ciudadlimpia' }
}
$jsonMarca = Join-Path $Origen "brands\$Marca\brand.json"
if ($Marca -notmatch '^[a-z0-9-]+$' -or -not (Test-Path $jsonMarca)) {
    Write-Host "  ERROR: la marca '$Marca' no existe en el paquete." -ForegroundColor Red
    exit 1
}
$infoMarca = [IO.File]::ReadAllText($jsonMarca, [Text.Encoding]::UTF8) | ConvertFrom-Json
$NombreMarca = $infoMarca.name
if (-not $Producto) {
    $archivoProducto = @((Join-Path $Aqui 'producto.txt'), (Join-Path $Aqui '..\producto.txt')) | Where-Object { Test-Path $_ } | Select-Object -First 1
    $Producto = if ($archivoProducto) { (Get-Content $archivoProducto -Raw).Trim().ToLower() } else { 'cargador' }
}
$infoProducto = $infoMarca.installer.$Producto
if ($Producto -notin @('cargador', 'probador') -or -not $infoProducto) {
    Write-Host "  ERROR: el producto '$Producto' no existe (use cargador o probador)." -ForegroundColor Red
    exit 1
}
$Titulo = $infoProducto.shortcut
if (-not $Destino) { $Destino = Join-Path $env:LOCALAPPDATA $infoProducto.folder }
if (-not $Puerto) { $Puerto = [int]$infoProducto.port }
if ($Puerto -lt 1024) { Write-Host '  ERROR: el puerto debe estar entre 1024 y 65535.' -ForegroundColor Red; exit 1 }

New-Item -ItemType Directory -Force -Path $Destino | Out-Null
$transcript = Join-Path $Destino 'instalacion.log'
Start-Transcript -Path $transcript | Out-Null

try {
    Write-Host ''
    Write-Host "  $Titulo" -ForegroundColor Green
    Write-Host "  Instalación para el usuario $env:USERNAME en $Destino" -ForegroundColor Green

    # -------------------------------------------------------------- 1. versión anterior abierta
    Paso 'Cerrando una versión anterior (si está abierta)'
    $pidFile = Join-Path $Destino 'app\logs\app.pid'
    if (Test-Path $pidFile) {
        $viejo = (Get-Content $pidFile -Raw).Trim()
        $proc = $null
        if ($viejo -match '^\d+$') { $proc = Get-Process -Id ([int]$viejo) -ErrorAction SilentlyContinue }
        if ($proc -and $proc.ProcessName -eq 'node') {
            try { Stop-Process -Id $viejo -Force -ErrorAction Stop }
            catch {
                Falla ('La versión anterior está abierta y no se pudo cerrar (probablemente se instaló "como administrador"). ' +
                    'Reinicie el computador, o ciérrela en el Administrador de tareas (proceso node.exe), y vuelva a ejecutar el instalador ' +
                    'SIN "Ejecutar como administrador".')
            }
            Start-Sleep -Seconds 1; Ok 'Versión anterior detenida'
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
    if (Puerto-Ocupado $Puerto) {
        Falla ("El puerto $Puerto está en uso por otro programa. Si tiene abierta una ventana negra con 'npm start' o 'npm run demo', " +
            'ciérrela (Ctrl + C) y vuelva a ejecutar el instalador.')
    }
    Ok "Puerto $Puerto disponible"

    # -------------------------------------------------------------- 2. Node.js portátil
    Paso 'Node.js'
    $NodeDir = Join-Path $Destino 'node'
    $NodeExe = Join-Path $NodeDir 'node.exe'
    $portatil = $true
    $v = $null
    if (Test-Path $NodeExe) { $v = Version-Node $NodeExe }
    if (-not $v -or $v.Major -lt 20) {
        $zip = $NodeZip
        if (-not $zip) {
            # Instalador .exe / paquete completo: Node.js portátil incluido junto al instalador
            $incluido = Get-ChildItem $Aqui -Filter 'node-v*-win-x64.zip' -File -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
            if ($incluido) { $zip = $incluido.FullName; Ok "Node.js incluido en el paquete ($($incluido.Name))" }
        }
        if (-not $zip) {
            try {
                Write-Host '    Buscando la versión LTS de Node.js...'
                $indice = (Obtener 'https://nodejs.org/dist/index.json') | ConvertFrom-Json
                $lts = $indice | Where-Object { $_.version -like 'v22.*' -and $_.lts } | Select-Object -First 1
                $nombre = "node-$($lts.version)-win-x64.zip"
                $zip = Join-Path $env:TEMP $nombre
                Write-Host "    Descargando $nombre (unos 30 MB)..."
                Descargar "https://nodejs.org/dist/$($lts.version)/$nombre" $zip
                $sumas = Obtener "https://nodejs.org/dist/$($lts.version)/SHASUMS256.txt"
                $linea = ($sumas -split "`n") | Where-Object { $_ -match ([regex]::Escape($nombre) + '\s*$') } | Select-Object -First 1
                $esperado = ($linea -split '\s+')[0]
                if ((Get-FileHash $zip -Algorithm SHA256).Hash -ne $esperado.ToUpper()) { Falla 'La descarga de Node.js está dañada (SHA-256 no coincide).' }
                Ok 'Descarga verificada (SHA-256)'
            } catch {
                $sistema = Get-Command node.exe -ErrorAction SilentlyContinue
                $vs = $null
                if ($sistema) { $vs = Version-Node $sistema.Source }
                if ($vs -and $vs.Major -ge 20) {
                    Aviso "No se pudo descargar Node.js ($($_.Exception.Message)). Se usará el Node.js instalado: $($sistema.Source)"
                    $NodeExe = $sistema.Source; $portatil = $false; $zip = $null
                } else {
                    Falla ("No se pudo descargar Node.js: $($_.Exception.Message). Pruebe con -Proxy http://<proxy>:<puerto> " +
                        'o descargue node-v22.x.x-win-x64.zip de https://nodejs.org y use -NodeZip <ruta>.')
                }
            }
        }
        if ($zip) {
            Write-Host '    Extrayendo...'
            $tmp = Join-Path $env:TEMP ('cargador-node-' + [guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Force -Path $tmp | Out-Null
            if (Get-Command tar.exe -ErrorAction SilentlyContinue) { & tar.exe -xf $zip -C $tmp; if ($LASTEXITCODE -ne 0) { Falla 'No se pudo extraer Node.js.' } }
            else { Expand-Archive -Path $zip -DestinationPath $tmp -Force }
            $interno = Get-ChildItem $tmp -Directory | Select-Object -First 1
            if (Test-Path $NodeDir) { Remove-Item $NodeDir -Recurse -Force }
            Move-Item $interno.FullName $NodeDir
            Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    $v = Version-Node $NodeExe
    if (-not $v) { Falla "No se pudo ejecutar Node.js en $NodeExe." }
    $NpmCli = Join-Path (Split-Path $NodeExe) 'node_modules\npm\bin\npm-cli.js'
    Ok "Node.js $v ($(if ($portatil) { 'portátil' } else { 'del sistema' }))"

    # -------------------------------------------------------------- 3. aplicación
    Paso 'Copiando la aplicación'
    $App = Join-Path $Destino 'app'
    & robocopy.exe $Origen $App /E /NFL /NDL /NJH /NJS /NP /R:2 /W:2 /XD node_modules logs test deploy docs .git /XF .env | Out-Null
    if ($LASTEXITCODE -ge 8) { Falla "No se pudieron copiar los archivos (robocopy $LASTEXITCODE)." }
    New-Item -ItemType Directory -Force -Path (Join-Path $App 'logs') | Out-Null
    Ok "Aplicación en $App (se conservan .env y logs)"

    if (Test-Path (Join-Path $Origen 'node_modules\express\package.json')) {
        Paso 'Copiando librerías (incluidas en el paquete)'
        & robocopy.exe (Join-Path $Origen 'node_modules') (Join-Path $App 'node_modules') /MIR /NFL /NDL /NJH /NJS /NP /R:2 /W:2 | Out-Null
        if ($LASTEXITCODE -ge 8) { Falla "No se pudieron copiar las librerías (robocopy $LASTEXITCODE)." }
        Ok 'Librerías copiadas (sin descargar nada)'
    } else {
        Paso 'Instalando librerías (npm ci)'
        if ($Proxy) { $env:HTTPS_PROXY = $Proxy; $env:HTTP_PROXY = $Proxy }
        if ($CertificadoRaizCA) { $env:NODE_EXTRA_CA_CERTS = $CertificadoRaizCA }
        Push-Location $App
        try {
            & $NodeExe $NpmCli ci --omit=dev --no-audit --no-fund --loglevel=error
            if ($LASTEXITCODE -ne 0) { Falla 'npm ci falló. Revise la conexión a internet (registry.npmjs.org) o use -Proxy.' }
        } finally { Pop-Location }
        Ok 'Librerías instaladas'
    }

    # -------------------------------------------------------------- 4. configuración
    Paso 'Configuración (.env)'
    $envPath = Join-Path $App '.env'
    $existe = (Test-Path $envPath) -and -not $Reconfigurar
    if ($existe) {
        $valores = Leer-Env $envPath
        Ok 'Se conserva la configuración existente'
    } elseif ($ConfigEmpresa) {
        $valores = Leer-Env $ConfigEmpresa
        $valores.Remove('SESSION_SECRET')   # cada usuario tiene su propia clave de sesión
        Ok "Datos de SAC tomados de $(Split-Path $ConfigEmpresa -Leaf)"
    } else {
        $valores = [ordered]@{}
    }

    $faltan = @('SAC_TENANT_URL', 'SAC_AUTHORIZE_URL', 'SAC_TOKEN_URL', 'SAC_CLIENT_ID', 'SAC_CLIENT_SECRET') | Where-Object { -not (Valor-Util $valores[$_]) }
    if ($faltan) {
        Write-Host '    Datos del cliente OAuth de SAC (pídalos al administrador de SAC):'
        Write-Host "    La Redirect URI del cliente debe incluir: http://localhost:$Puerto/auth/callback" -ForegroundColor Cyan
        Write-Host '    Se abre una ventana para pegar los datos (puede quedar detrás de esta).' -ForegroundColor Cyan
        if (Pedir-DatosSac-Ventana $valores) {
            Ok 'Datos de SAC ingresados'
            $faltan = @()
        } else {
            Aviso 'No se pudo abrir la ventana; escríbalos aquí.'
        }
    }
    if ($faltan) {
        if ($faltan -contains 'SAC_TENANT_URL') { $valores['SAC_TENANT_URL'] = (Leer 'URL del tenant de SAC' '^https://[^/]+' 'https://fanalca-clpriv-sac.us21.analytics.cloud.sap').TrimEnd('/') }
        if ($faltan -contains 'SAC_AUTHORIZE_URL') { $valores['SAC_AUTHORIZE_URL'] = Leer 'Authorization URL' '^https://.+/oauth/authorize$' 'https://<subdominio>.authentication.us21.hana.ondemand.com/oauth/authorize' }
        if ($faltan -contains 'SAC_TOKEN_URL') { $valores['SAC_TOKEN_URL'] = Leer 'Token URL' '^https://.+/oauth/token$' 'https://<subdominio>.authentication.us21.hana.ondemand.com/oauth/token' }
        if ($faltan -contains 'SAC_CLIENT_ID') { $valores['SAC_CLIENT_ID'] = Leer 'OAuth Client ID' }
        if ($faltan -contains 'SAC_CLIENT_SECRET') { $valores['SAC_CLIENT_SECRET'] = Leer-Secreto 'Secret (no se muestra al escribir)' }
    }

    # Ajustes fijos para uso local en este computador
    $valores['PORT'] = "$Puerto"
    $valores['HOST'] = '127.0.0.1'
    $valores['APP_BASE_URL'] = "http://localhost:$Puerto"
    $valores['TRUST_PROXY'] = 'false'
    $valores['BRAND'] = $Marca
    $valores['APP_MODE'] = $Producto
    if (-not (Valor-Util $valores['SESSION_SECRET']) -or $valores['SESSION_SECRET'].Length -lt 32) { $valores['SESSION_SECRET'] = Nueva-Clave }
    $porDefecto = [ordered]@{ SESSION_MINUTES = '60'; SAC_OAUTH_PKCE = 'true'; MAX_FILE_MB = '20'; MAX_ROWS = '100000'; CHUNK_SIZE = '10000';
        NUMBER_LOCALE = 'es'; BLOCKED_VERSIONS = 'public.Actual'; VALIDATE_MEMBERS = 'true'; SAC_DEBUG = 'false' }
    foreach ($k in $porDefecto.Keys) { if (-not $valores.Contains($k)) { $valores[$k] = $porDefecto[$k] } }
    foreach ($k in @('AUDIT_FILE', 'TEMPLATES_FILE', 'COOKIE_SECURE')) { if ($valores.Contains($k)) { $valores.Remove($k) } }

    $orden = @('BRAND', 'APP_MODE', 'PORT', 'HOST', 'APP_BASE_URL', 'TRUST_PROXY', 'SESSION_SECRET', 'SESSION_MINUTES', 'SAC_TENANT_URL', 'SAC_AUTHORIZE_URL',
        'SAC_TOKEN_URL', 'SAC_CLIENT_ID', 'SAC_CLIENT_SECRET', 'SAC_OAUTH_SCOPE', 'SAC_OAUTH_PKCE', 'MAX_FILE_MB', 'MAX_ROWS', 'CHUNK_SIZE',
        'NUMBER_LOCALE', 'BLOCKED_VERSIONS', 'VALIDATE_MEMBERS', 'SAC_DEBUG')
    $lineas = @("# $Titulo - configuración de $env:USERNAME ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))")
    foreach ($k in $orden) { if ($valores.Contains($k)) { $lineas += "$k=$($valores[$k])" } }
    foreach ($k in $valores.Keys) { if ($orden -notcontains $k) { $lineas += "$k=$($valores[$k])" } }
    Escribir-Utf8 $envPath (($lineas -join "`r`n") + "`r`n")

    # Sólo este usuario (y el sistema) puede leer el .env
    $miSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    & icacls.exe $envPath /inheritance:r /grant:r "*${miSid}:F" '*S-1-5-18:F' /Q | Out-Null
    if ($LASTEXITCODE -ne 0) { Aviso 'No se pudieron restringir los permisos del .env.' }

    Push-Location $App
    try { $salida = & $NodeExe -e "require('./src/config').loadConfig(); console.log('config-ok')" 2>&1 } finally { Pop-Location }
    if (($salida -join "`n") -notmatch 'config-ok') { Falla "La configuración no es válida: $($salida -join ' ')" }
    Ok 'Configuración válida y protegida'

    # -------------------------------------------------------------- 5. accesos directos
    Paso 'Accesos directos'
    foreach ($f in @('Abrir-CargadorSAC.cmd', 'Detener-CargadorSAC.cmd', 'Desinstalar-CargadorSAC.cmd')) {
        Copy-Item (Join-Path $Aqui $f) (Join-Path $Destino $f) -Force
    }
    Copy-Item (Join-Path $App "brands\$Marca\icon.ico") (Join-Path $Destino 'CargadorSAC.ico') -Force
    $cfg = @('@echo off', 'rem Generado por el instalador. No modificar.', "set ""TITULO=$Titulo""")
    if ($portatil) { $cfg += 'set "NODE_EXE=%~dp0node\node.exe"' } else { $cfg += "set ""NODE_EXE=$NodeExe""" }
    $cfg += "set ""PUERTO=$Puerto"""
    if ($Proxy) { $cfg += @('set "NODE_USE_ENV_PROXY=1"', "set ""HTTPS_PROXY=$Proxy""", "set ""HTTP_PROXY=$Proxy""", 'set "NO_PROXY=127.0.0.1,localhost"') }
    if ($CertificadoRaizCA) { $cfg += "set ""NODE_EXTRA_CA_CERTS=$CertificadoRaizCA""" }
    Escribir-Ascii (Join-Path $Destino 'config.cmd') $cfg
    Get-ChildItem $Destino -File | Unblock-File -ErrorAction SilentlyContinue

    $shell = New-Object -ComObject WScript.Shell
    function Crear-Acceso([string]$ruta, [string]$objetivo, [string]$descripcion, [int]$ventana) {
        $a = $shell.CreateShortcut($ruta)
        $a.TargetPath = $objetivo
        $a.WorkingDirectory = $Destino
        $a.IconLocation = (Join-Path $Destino 'CargadorSAC.ico') + ',0'
        $a.Description = $descripcion
        $a.WindowStyle = $ventana
        $a.Save()
    }
    $escritorio = [Environment]::GetFolderPath('Desktop')
    $menu = Join-Path ([Environment]::GetFolderPath('Programs')) $Titulo
    New-Item -ItemType Directory -Force -Path $menu | Out-Null
    $abrir = Join-Path $Destino 'Abrir-CargadorSAC.cmd'
    Crear-Acceso (Join-Path $escritorio "$Titulo.lnk") $abrir "Abre $Titulo" 7
    Crear-Acceso (Join-Path $menu "$Titulo.lnk") $abrir "Abre $Titulo" 7
    Crear-Acceso (Join-Path $menu "Detener $Titulo.lnk") (Join-Path $Destino 'Detener-CargadorSAC.cmd') "Cierra $Titulo" 1
    Crear-Acceso (Join-Path $menu "Desinstalar $Titulo.lnk") (Join-Path $Destino 'Desinstalar-CargadorSAC.cmd') "Quita $Titulo" 1
    Ok "Escritorio y menú Inicio: '$Titulo'"

    # -------------------------------------------------------------- 6. prueba
    if (-not $NoAbrir) {
        Paso 'Abriendo la aplicación'
        Start-Process -FilePath $abrir -WorkingDirectory $Destino -WindowStyle Minimized
        if (Probar-Salud 40) { Ok "La aplicación responde en http://localhost:$Puerto" }
        else { Aviso "La aplicación no respondió todavía. Revise $App\logs\app.log" }
    }

    Write-Host ''
    Write-Host '  Instalación terminada.' -ForegroundColor Green
    Write-Host "  - Para usarla: doble clic en '$Titulo' (escritorio o menú Inicio)."
    Write-Host "  - Para cerrarla: menú Inicio > $Titulo > Detener."
    Write-Host "  - El cliente OAuth de SAC debe tener la Redirect URI http://localhost:$Puerto/auth/callback"
}
catch {
    Write-Host ''
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Registro de la instalación: $transcript" -ForegroundColor Red
    Stop-Transcript | Out-Null
    exit 1
}
Stop-Transcript | Out-Null
