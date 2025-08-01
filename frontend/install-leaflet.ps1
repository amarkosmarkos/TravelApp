Write-Host "========================================" -ForegroundColor Green
Write-Host "Instalando Leaflet para el mapa real" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Set-Location $PSScriptRoot
Write-Host "Instalando leaflet y react-leaflet..." -ForegroundColor Yellow
npm install leaflet react-leaflet

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Instalacion completada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora puedes:" -ForegroundColor Cyan
Write-Host "1. Descomentar el codigo del mapa en MapViewReal.js" -ForegroundColor White
Write-Host "2. Reiniciar el servidor de desarrollo" -ForegroundColor White
Write-Host ""
Read-Host "Presiona Enter para continuar" 