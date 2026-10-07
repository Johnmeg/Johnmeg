#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Quita el Cargador de datos a SAC: servicio, sitio de IIS y regla de firewall.
  Con -BorrarArchivos también elimina la carpeta de la aplicación (se guarda una copia del .env y de logs).
#>
[CmdletBinding()]
param(
    [string]$RutaApp = 'C:\apps\sac-data-loader',
    [string]$RutaSitio = 'C:\inetpub\sac-data-loader',
    [switch]$BorrarArchivos
)
$ErrorActionPreference = 'Stop'
$NombreServicio = 'SacDataLoader'
$NombreSitio = 'CargadorSAC'

$svc = Get-Service -Name $NombreServicio -ErrorAction SilentlyContinue
if ($svc) {
    if ($svc.Status -ne 'Stopped') { Stop-Service -Name $NombreServicio -Force }
    & sc.exe delete $NombreServicio | Out-Null
    Write-Host "Servicio $NombreServicio eliminado."
}

if (Get-Module -ListAvailable -Name WebAdministration) {
    Import-Module WebAdministration
    if (Get-Website -Name $NombreSitio) { Remove-Website -Name $NombreSitio; Write-Host "Sitio IIS $NombreSitio eliminado." }
    if (Test-Path "IIS:\AppPools\$NombreSitio") { Remove-WebAppPool -Name $NombreSitio }
}
if (Test-Path $RutaSitio) { Remove-Item $RutaSitio -Recurse -Force }

Get-NetFirewallRule -DisplayName 'Cargador SAC - HTTP/HTTPS' -ErrorAction SilentlyContinue | Remove-NetFirewallRule

if ($BorrarArchivos -and (Test-Path $RutaApp)) {
    $respaldo = Join-Path $env:USERPROFILE ('respaldo-cargador-sac-{0:yyyyMMdd-HHmmss}' -f (Get-Date))
    New-Item -ItemType Directory -Force -Path $respaldo | Out-Null
    foreach ($item in @('.env', 'logs')) {
        $p = Join-Path $RutaApp $item
        if (Test-Path $p) { Copy-Item $p $respaldo -Recurse -Force }
    }
    Remove-Item $RutaApp -Recurse -Force
    Write-Host "Carpeta $RutaApp eliminada. Copia de .env y logs en $respaldo"
}
Write-Host 'Listo. (IIS, URL Rewrite, ARR, Node.js y el certificado no se desinstalan.)'
