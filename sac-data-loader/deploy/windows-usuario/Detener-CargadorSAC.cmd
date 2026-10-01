@echo off
rem Cierra el Cargador de datos a SAC que corre en segundo plano.
setlocal EnableExtensions
set "TITULO=Cargador de datos a SAC"
if exist "%~dp0config.cmd" call "%~dp0config.cmd"
set "PIDF=%~dp0app\logs\app.pid"
if not exist "%PIDF%" goto noactivo
set /p PID=<"%PIDF%"
tasklist /FI "PID eq %PID%" /FI "IMAGENAME eq node.exe" 2>nul | find /I "node.exe" >nul || goto noactivo
taskkill /PID %PID% /T /F >nul 2>&1
del "%PIDF%" >nul 2>&1
echo %TITULO%: detenido.
timeout /t 3 >nul
exit /b 0

:noactivo
del "%PIDF%" >nul 2>&1
echo %TITULO%: no estaba abierto.
timeout /t 3 >nul
exit /b 0
