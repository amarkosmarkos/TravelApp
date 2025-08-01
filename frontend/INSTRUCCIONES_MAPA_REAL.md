# 🗺️ Instrucciones para Implementar el Mapa Real

## 🚀 Paso 1: Instalar Dependencias

### Opción A: Usando el script automático (Recomendado)
```bash
# En PowerShell
.\install-leaflet.ps1

# O en CMD
install-leaflet.bat
```

### Opción B: Instalación manual
```bash
cd frontend
npm install leaflet react-leaflet
```

## 🔧 Paso 2: Activar el Mapa Real

1. **Abrir el archivo:** `frontend/src/components/MapViewReal.js`

2. **Descomentar las líneas de importación** (líneas 12-14):
```javascript
// Cambiar de:
// import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
// import L from 'leaflet';
// import 'leaflet/dist/leaflet.css';

// A:
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
```

3. **Descomentar el código del mapa** (líneas 180-220):
```javascript
// Cambiar de:
{/* 
TODO: Uncomment this after installing leaflet and react-leaflet

<MapContainer 
    center={mapCenter} 
    zoom={8} 
    style={{ height: '100%', width: '100%' }}
    ref={mapRef}
>
    <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    />
    
    {citiesWithCoordinates.map((city, index) => (
        <Marker 
            key={index} 
            position={[city.coordinates.latitude, city.coordinates.longitude]}
            eventHandlers={{
                click: () => onCitySelect && onCitySelect(city, index)
            }}
        >
            <Popup>
                <Box sx={{ p: 1 }}>
                    <Typography variant="h6" gutterBottom>
                        {city.name}
                    </Typography>
                    <Chip 
                        label={`Día ${index + 1}`}
                        size="small"
                        color="primary"
                        sx={{ mb: 1 }}
                    />
                    {city.description && (
                        <Typography variant="body2" color="text.secondary">
                            {city.description}
                        </Typography>
                    )}
                </Box>
            </Popup>
        </Marker>
    ))}
</MapContainer>
*/}

// A:
<MapContainer 
    center={mapCenter} 
    zoom={8} 
    style={{ height: '100%', width: '100%' }}
    ref={mapRef}
>
    <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    />
    
    {citiesWithCoordinates.map((city, index) => (
        <Marker 
            key={index} 
            position={[city.coordinates.latitude, city.coordinates.longitude]}
            eventHandlers={{
                click: () => onCitySelect && onCitySelect(city, index)
            }}
        >
            <Popup>
                <Box sx={{ p: 1 }}>
                    <Typography variant="h6" gutterBottom>
                        {city.name}
                    </Typography>
                    <Chip 
                        label={`Día ${index + 1}`}
                        size="small"
                        color="primary"
                        sx={{ mb: 1 }}
                    />
                    {city.description && (
                        <Typography variant="body2" color="text.secondary">
                            {city.description}
                        </Typography>
                    )}
                </Box>
            </Popup>
        </Marker>
    ))}
</MapContainer>
```

4. **Comentar el placeholder** (líneas 222-350):
```javascript
// Comentar todo el bloque del placeholder:
{/*
<Box sx={{
    height: '100%',
    width: '100%',
    background: `...`,
    // ... resto del código del placeholder
}}>
    // ... contenido del placeholder
</Box>
*/}
```

## 🔄 Paso 3: Reiniciar el Servidor

```bash
# Detener el servidor actual (Ctrl+C)
# Luego reiniciar:
npm start
```

## ✅ Paso 4: Verificar la Implementación

1. **Navegar a la página del itinerario**
2. **Verificar que el mapa real se carga**
3. **Probar la interactividad:**
   - Hacer clic en marcadores
   - Hacer clic en ciudades de la lista
   - Verificar que se sincronizan

## 🎯 Características del Mapa Real

### ✅ Funcionalidades Implementadas:
- **Mapa interactivo** con OpenStreetMap
- **Marcadores personalizados** para cada ciudad
- **Popups informativos** con detalles de la ciudad
- **Sincronización** entre lista y mapa
- **Centrado automático** basado en las ciudades
- **Zoom y navegación** nativos de Leaflet

### 🎨 Personalización Disponible:
- **Diferentes proveedores de tiles:**
  - OpenStreetMap (actual)
  - CartoDB (más limpio)
  - Stamen (artístico)
- **Estilos de marcadores**
- **Colores y temas**

## 🐛 Solución de Problemas

### Error: "Module not found"
```bash
# Reinstalar dependencias
npm install leaflet react-leaflet
```

### Error: "Leaflet is not defined"
```javascript
// Asegúrate de que las importaciones estén descomentadas
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
```

### Mapa no se muestra
1. Verificar que el CSS de Leaflet esté importado
2. Verificar que el contenedor tenga altura definida
3. Revisar la consola del navegador para errores

## 🚀 Próximos Pasos (Opcionales)

1. **Agregar rutas entre ciudades:**
```javascript
import { Polyline } from 'react-leaflet';

// Dentro del MapContainer
<Polyline 
    positions={citiesWithCoordinates.map(city => [
        city.coordinates.latitude, 
        city.coordinates.longitude
    ])}
    color="blue"
    weight={3}
/>
```

2. **Agregar controles personalizados:**
```javascript
import { ZoomControl, ScaleControl } from 'react-leaflet';

<MapContainer>
    <ZoomControl position="topright" />
    <ScaleControl position="bottomleft" />
</MapContainer>
```

3. **Agregar búsqueda de ubicaciones:**
```javascript
// Integrar con servicios de geocoding
// Ej: Nominatim, Google Geocoding API
```

## 📞 Soporte

Si tienes problemas:
1. Verificar que todas las dependencias estén instaladas
2. Revisar la consola del navegador
3. Verificar que el código esté descomentado correctamente
4. Reiniciar el servidor de desarrollo

¡El mapa real estará funcionando perfectamente! 🎉 