@echo off
rem Instalador del Cargador de datos a SAC para el computador del usuario.
rem Doble clic. No requiere permisos de administrador.
setlocal
set "PS1=%~dp0instalador\Instalar-CargadorSAC-Usuario.ps1"
if not exist "%PS1%" set "PS1=%~dp0Instalar-CargadorSAC-Usuario.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
echo.
pause
