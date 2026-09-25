@echo off
rem Abre el Cargador de datos a SAC: lo inicia en segundo plano si no esta
rem corriendo y abre el navegador en http://localhost:<puerto>
setlocal EnableExtensions
set "BASE=%~dp0"
call "%BASE%config.cmd"
set "SALUD=http://127.0.0.1:%PUERTO%/healthz"
set "LOG_FILE=%BASE%app\logs\app.log"
set "PID_FILE=%BASE%app\logs\app.pid"
where curl.exe >nul 2>&1 || set "SIN_CURL=1"

call :salud && goto abrir

echo Iniciando el Cargador de datos a SAC...
if not exist "%BASE%app\logs" mkdir "%BASE%app\logs"
powershell.exe -NoProfile -Command "Start-Process -FilePath $env:NODE_EXE -ArgumentList 'server.js' -WorkingDirectory (Join-Path $env:BASE 'app') -WindowStyle Hidden"

set /a INTENTOS=0
:esperar
timeout /t 1 /nobreak >nul
call :salud && goto abrir
set /a INTENTOS+=1
if %INTENTOS% LSS 40 goto esperar

powershell.exe -NoProfile -Command "$t = ''; if (Test-Path $env:LOG_FILE) { $t = (Get-Content $env:LOG_FILE -Tail 8) -join [Environment]::NewLine }; (New-Object -ComObject WScript.Shell).Popup('No fue posible iniciar el Cargador de datos a SAC.' + [Environment]::NewLine + [Environment]::NewLine + $t + [Environment]::NewLine + [Environment]::NewLine + 'Registro: ' + $env:LOG_FILE, 0, 'Cargador de datos a SAC', 16) | Out-Null"
exit /b 1

:abrir
start "" "http://localhost:%PUERTO%/"
exit /b 0

:salud
if defined SIN_CURL (
  powershell.exe -NoProfile -Command "try { $null = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri $env:SALUD; exit 0 } catch { exit 1 }" >nul 2>&1
) else (
  curl.exe --noproxy "*" -s -f -m 2 "%SALUD%" >nul 2>&1
)
exit /b %errorlevel%
