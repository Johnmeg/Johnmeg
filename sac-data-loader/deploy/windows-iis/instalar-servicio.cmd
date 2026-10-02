@echo off
REM Instala la aplicación como servicio de Windows con NSSM (https://nssm.cc).
REM Ejecutar como administrador. Ajuste las rutas si instaló en otra carpeta.
set APP=C:\apps\sac-data-loader
set NODE=C:\Program Files\nodejs\node.exe

nssm install SacDataLoader "%NODE%" "%APP%\server.js"
nssm set SacDataLoader AppDirectory "%APP%"
nssm set SacDataLoader DisplayName "Cargador de datos a SAC - Ciudad Limpia"
nssm set SacDataLoader Start SERVICE_AUTO_START
nssm set SacDataLoader AppStdout "%APP%\logs\servicio.log"
nssm set SacDataLoader AppStderr "%APP%\logs\servicio.log"
nssm set SacDataLoader AppRotateFiles 1
nssm set SacDataLoader AppRotateOnline 1
nssm set SacDataLoader AppRotateBytes 10485760
nssm set SacDataLoader AppEnvironmentExtra NODE_ENV=production
nssm start SacDataLoader
