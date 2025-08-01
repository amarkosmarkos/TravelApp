@echo off
echo ========================================
echo Instalando Leaflet para el mapa real
echo ========================================
echo.

cd /d "%~dp0"
echo Instalando leaflet y react-leaflet...
npm install leaflet react-leaflet

echo.
echo ========================================
echo Instalacion completada!
echo ========================================
echo.
echo Ahora puedes:
echo 1. Descomentar el codigo del mapa en MapViewReal.js
echo 2. Reiniciar el servidor de desarrollo
echo.
pause 