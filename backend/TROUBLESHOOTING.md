# 🔧 Guía de Solución de Problemas

## Problemas Identificados y Soluciones

### 1. Error de Serialización JSON: `MessageType is not JSON serializable`

**Problema:**
```
ERROR:app.routers.travel:Error in WebSocket endpoint: Object of type MessageType is not JSON serializable
```

**Causa:**
El enum `MessageType` no se puede serializar directamente a JSON.

**Solución:**
✅ **SOLUCIONADO** - Se modificó `backend/app/agents/message_router.py` para convertir el enum a string antes de devolver la respuesta.

### 2. Error de Importación: `No module named 'app'`

**Problema:**
```
ModuleNotFoundError: No module named 'app'
```

**Causa:**
Python no puede encontrar el módulo `app` debido a problemas con el PYTHONPATH.

**Solución:**
✅ **SOLUCIONADO** - Se crearon scripts de inicio que configuran correctamente el PYTHONPATH:
- `start_server.py` - Script principal para ejecutar el servidor
- `run.py` - Script alternativo
- `uvicorn_config.py` - Configuración para uvicorn

### 3. Problema de Coordenadas en Itinerarios

**Problema:**
Las coordenadas no se muestran correctamente en los itinerarios.

**Causa:**
Formato incorrecto de coordenadas al guardar en la base de datos.

**Solución:**
✅ **SOLUCIONADO** - Se modificó `backend/app/services/ai_matching_service.py` para:
- Guardar coordenadas en formato correcto (latitude/longitude como float)
- Manejar casos donde las coordenadas no existen
- Validar que las coordenadas sean números válidos

### 4. Problema de WebSocket y Mensajes en Tiempo Real

**Problema:**
Los mensajes no se reciben correctamente en tiempo real.

**Causa:**
Formato incorrecto de respuesta en el endpoint WebSocket.

**Solución:**
✅ **SOLUCIONADO** - Se modificó `backend/app/routers/travel.py` para:
- Formatear correctamente las respuestas de WebSocket
- Incluir información de clasificación en las respuestas
- Manejar errores de mensajes vacíos

### 5. Relación 1:1 entre Travel e Itinerary

**Problema:**
No se fuerza la relación 1:1 entre un viaje y su itinerario.

**Causa:**
Falta de restricciones en la base de datos.

**Solución:**
✅ **SOLUCIONADO** - Se modificó `backend/app/crud/travel.py` para:
- Crear índice único en `travel_id`
- Forzar actualización en lugar de crear duplicados
- Asegurar que solo exista un itinerario por viaje

### 6. Cómo Ejecutar el Servidor Correctamente

#### Opción 1: Usar el script de inicio (Recomendado)
```bash
cd backend
python start_server.py
```

#### Opción 2: Usar uvicorn directamente
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Opción 3: Usar el script run.py
```bash
cd backend
python run.py
```

### 7. Scripts de Verificación

#### Verificar coordenadas en itinerarios:
```bash
cd backend
python verify_coordinates.py
```

#### Probar WebSocket:
```bash
cd backend
python test_websocket.py
```

### 8. Configuración del Entorno

#### Paso 1: Instalar dependencias
```bash
cd backend
pip install -r requirements.txt
```

#### Paso 2: Configurar variables de entorno
```bash
cd backend
python setup.py
```

#### Paso 3: Editar el archivo .env
Asegúrate de configurar las siguientes variables:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `JWT_SECRET_KEY`
- `MONGODB_URL`

### 9. Verificación del Sistema

#### Verificar que MongoDB esté ejecutándose
```bash
# En Windows
net start MongoDB

# En Linux/Mac
sudo systemctl start mongod
```

#### Verificar la conexión a la base de datos
```bash
cd backend
python -c "from app.database import connect_to_mongodb; import asyncio; asyncio.run(connect_to_mongodb())"
```

### 10. Logs y Debugging

#### Habilitar logs detallados
En el archivo `.env`:
```
LOG_LEVEL=DEBUG
DEBUG=True
```

#### Verificar logs en tiempo real
```bash
# En Windows PowerShell
Get-Content backend/logs/app.log -Wait

# En Linux/Mac
tail -f backend/logs/app.log
```

### 11. Problemas Comunes

#### Error: "Connection refused"
- Verificar que MongoDB esté ejecutándose
- Verificar que el puerto 27017 esté disponible

#### Error: "Invalid API key"
- Verificar que las credenciales de Azure OpenAI estén correctas
- Verificar que el endpoint y deployment name sean correctos

#### Error: "WebSocket connection failed"
- Verificar que el frontend esté ejecutándose en el puerto 3000
- Verificar la configuración de CORS

#### Error: "Coordinates not showing"
- Ejecutar `python verify_coordinates.py` para verificar el estado
- Verificar que los sitios en la BD tengan coordenadas válidas

### 12. Estructura de Archivos Importante

```
backend/
├── app/
│   ├── main.py              # Punto de entrada principal
│   ├── agents/              # Agentes de IA
│   ├── routers/             # Endpoints de la API
│   ├── services/            # Servicios de negocio
│   └── models/              # Modelos de datos
├── start_server.py          # Script de inicio principal
├── setup.py                 # Script de configuración
├── verify_coordinates.py    # Script de verificación de coordenadas
├── test_websocket.py        # Script de prueba de WebSocket
├── requirements.txt         # Dependencias
└── .env                     # Variables de entorno
```

### 13. Comandos Útiles

#### Reiniciar el servidor
```bash
# Detener el servidor (Ctrl+C)
# Luego ejecutar:
python start_server.py
```

#### Limpiar caché de Python
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
```

#### Verificar sintaxis de Python
```bash
python -m py_compile app/main.py
```

#### Verificar coordenadas
```bash
python verify_coordinates.py
```

### 14. Contacto y Soporte

Si sigues teniendo problemas:
1. Verifica los logs en `backend/logs/`
2. Asegúrate de que todas las dependencias estén instaladas
3. Verifica que las variables de entorno estén configuradas correctamente
4. Revisa que MongoDB esté ejecutándose
5. Ejecuta los scripts de verificación

---

**Última actualización:** 2025-08-01
**Versión:** 2.0.0 