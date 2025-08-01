#!/usr/bin/env python3
"""
Script para probar la funcionalidad de WebSocket.
"""

import asyncio
import websockets
import json
import sys
import os
from pathlib import Path

# Configurar el path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

async def test_websocket():
    """Prueba la funcionalidad de WebSocket."""
    try:
        # URL del WebSocket (ajusta según tu configuración)
        uri = "ws://localhost:8000/api/travels/test_travel_id/ws?token=test_token"
        
        print(f"🔌 Conectando a: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Conexión WebSocket establecida")
            
            # Enviar mensaje de prueba
            test_message = {
                "type": "message",
                "data": {
                    "message": "Design me a trip to Thailand",
                    "is_user": True
                }
            }
            
            print(f"📤 Enviando mensaje: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Recibir respuesta
            response = await websocket.recv()
            print(f"📥 Respuesta recibida: {response}")
            
            # Parsear respuesta
            response_data = json.loads(response)
            print(f"📋 Tipo de respuesta: {response_data.get('type')}")
            print(f"💬 Mensaje: {response_data.get('data', {}).get('message', 'Sin mensaje')}")
            
    except Exception as e:
        print(f"❌ Error en prueba WebSocket: {e}")

if __name__ == "__main__":
    print("🧪 Iniciando prueba de WebSocket...")
    asyncio.run(test_websocket()) 