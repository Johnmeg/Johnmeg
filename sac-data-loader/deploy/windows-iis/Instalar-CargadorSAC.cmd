@echo off
REM Ejecute este archivo con clic derecho > "Ejecutar como administrador".
REM Uso: Instalar-CargadorSAC.cmd -Dominio cargas-sac.ciudadlimpia.com [otros parametros]
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Instalar-CargadorSAC.ps1" %*
pause
