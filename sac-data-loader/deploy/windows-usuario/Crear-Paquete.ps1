<#
.SYNOPSIS
  Arma el paquete ZIP del instalador para repartir a los usuarios (una marca por paquete).

.DESCRIPTION
  Ejecutar desde la carpeta sac-data-loader (en su computador, no en el de cada usuario):

    powershell -ExecutionPolicy Bypass -File .\deploy\windows-usuario\Crear-Paquete.ps1 -Marca fanalca -ConfigEmpresa C:\ruta\.env

  -Marca: ciudadlimpia (por defecto) o fanalca. Define nombre, colores, modelos, carpeta,
  accesos directos y puerto del paquete.
  Para el instalador .exe (todo incluido, sin descargas) use build-exe.js (ver DESPLIEGUE.md).

  -ConfigEmpresa (opcional): un .env que ya funciona. Del archivo sólo se copian los datos de
  SAC al paquete como config-empresa.env; así los usuarios no tienen que escribirlos.
  ATENCIÓN: ese archivo lleva el Secret del cliente OAuth. Comparta el ZIP sólo con usuarios
  autorizados (por ejemplo, una carpeta de Teams/SharePoint con acceso restringido).
#>
[CmdletBinding()]
param(
    [ValidatePattern('^[a-z0-9-]+$')]
    [string]$Marca = 'ciudadlimpia',
    [string]$Salida,
    [string]$ConfigEmpresa
)
$ErrorActionPreference = 'Stop'
$raiz = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$jsonMarca = Join-Path $raiz "brands\$Marca\brand.json"
if (-not (Test-Path $jsonMarca)) { throw "La marca '$Marca' no existe (carpeta brands)." }
$infoMarca = [IO.File]::ReadAllText($jsonMarca, [Text.Encoding]::UTF8) | ConvertFrom-Json
if (-not $Salida) {
    $nombre = if ($Marca -eq 'ciudadlimpia') { 'CargadorSAC-Instalador.zip' } else { "CargadorSAC-$($infoMarca.name)-Instalador.zip" }
    $Salida = Join-Path (Get-Location) $nombre
}
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('paquete-' + [guid]::NewGuid().ToString('N'))
$pkg = Join-Path $tmp 'CargadorSAC-Instalador'
$app = Join-Path $pkg 'app'
$ins = Join-Path $pkg 'instalador'
New-Item -ItemType Directory -Force -Path $app, $ins | Out-Null

foreach ($i in @('server.js', 'package.json', 'package-lock.json', 'README.md', '.env.example')) { Copy-Item (Join-Path $raiz $i) $app }
foreach ($d in @('src', 'public', 'config', 'brands', 'samples')) { Copy-Item (Join-Path $raiz $d) $app -Recurse }
foreach ($f in @('Instalar-CargadorSAC-Usuario.ps1', 'Abrir-CargadorSAC.cmd', 'Detener-CargadorSAC.cmd', 'Desinstalar-CargadorSAC.cmd')) {
    Copy-Item (Join-Path $PSScriptRoot $f) $ins
}
[IO.File]::WriteAllText((Join-Path $ins 'marca.txt'), $Marca, [Text.Encoding]::ASCII)
Copy-Item (Join-Path $PSScriptRoot 'Instalar.cmd') $pkg
$leame = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'LEAME.txt'), [Text.Encoding]::UTF8)
$leame = $leame.Replace('{{MARCA}}', $infoMarca.name.ToUpper()).Replace('{{CARPETA}}', $infoMarca.installer.folder)
$leame = $leame.Replace('{{ACCESO}}', $infoMarca.installer.shortcut).Replace('{{PUERTO}}', "$($infoMarca.installer.port)")
[IO.File]::WriteAllText((Join-Path $pkg 'LEAME.txt'), $leame, (New-Object Text.UTF8Encoding($true)))

if ($ConfigEmpresa) {
    $permitidas = @('SAC_TENANT_URL', 'SAC_AUTHORIZE_URL', 'SAC_TOKEN_URL', 'SAC_CLIENT_ID', 'SAC_CLIENT_SECRET', 'SAC_OAUTH_SCOPE',
        'SAC_OAUTH_PKCE', 'MAX_FILE_MB', 'MAX_ROWS', 'CHUNK_SIZE', 'NUMBER_LOCALE', 'BLOCKED_VERSIONS', 'VALIDATE_MEMBERS')
    $valores = [ordered]@{}
    foreach ($linea in [IO.File]::ReadAllLines((Resolve-Path $ConfigEmpresa).Path)) {
        if ($linea.TrimStart([char]0xFEFF) -match '^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$' -and $permitidas -contains $Matches[1]) { $valores[$Matches[1]] = $Matches[2] }
    }
    foreach ($k in @('SAC_TENANT_URL', 'SAC_AUTHORIZE_URL', 'SAC_TOKEN_URL', 'SAC_CLIENT_ID', 'SAC_CLIENT_SECRET')) {
        if (-not $valores[$k] -or $valores[$k] -match '[<>]') { throw "El archivo $ConfigEmpresa no tiene un valor válido para $k." }
    }
    $lineas = @('# Datos de SAC para el Cargador de datos a SAC. CONFIDENCIAL: contiene el Secret del cliente OAuth.')
    foreach ($k in $valores.Keys) { $lineas += "$k=$($valores[$k])" }
    [IO.File]::WriteAllText((Join-Path $pkg 'config-empresa.env'), (($lineas -join "`r`n") + "`r`n"), (New-Object Text.UTF8Encoding($false)))
    Write-Host 'Se incluyó config-empresa.env: comparta el ZIP sólo con usuarios autorizados.' -ForegroundColor Yellow
}

if (Test-Path $Salida) { Remove-Item $Salida -Force }
Compress-Archive -Path $pkg -DestinationPath $Salida
Remove-Item $tmp -Recurse -Force
Write-Host "Paquete listo: $Salida" -ForegroundColor Green
