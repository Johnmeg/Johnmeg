@echo off
rem Quita el Cargador de datos a SAC de este computador (usuario actual).
setlocal EnableExtensions
set "BASE=%~dp0"
echo Se quitara el Cargador de datos a SAC de este computador,
echo incluida su configuracion y sus registros.
choice /M "Desea continuar"
if errorlevel 2 exit /b 0

set "PIDF=%BASE%app\logs\app.pid"
if exist "%PIDF%" (
  set /p PID=<"%PIDF%"
)
if defined PID (
  tasklist /FI "PID eq %PID%" /FI "IMAGENAME eq node.exe" 2>nul | find /I "node.exe" >nul && taskkill /PID %PID% /T /F >nul 2>&1
)

powershell.exe -NoProfile -Command "Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Cargador de datos a SAC.lnk') -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Programs')) 'Cargador de datos a SAC') -Recurse -Force -ErrorAction SilentlyContinue"

set "CARPETA=%BASE:~0,-1%"
echo Listo. Se eliminara la carpeta %CARPETA%
start "" /min cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q "%CARPETA%""
exit
