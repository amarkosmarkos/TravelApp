#!/usr/bin/env python3
"""
Script para probar el WebSocket en tiempo real.
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
    """Prueba la conexión WebSocket."""
    try:
        print("🔌 Probando conexión WebSocket...")
        
        # URL del WebSocket
        uri = "ws://localhost:8000/api/travels/test_travel_123/ws?token=test_token"
        
        print(f"📡 Conectando a: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket conectado exitosamente")
            
            # Enviar mensaje de prueba
            test_message = {
                "type": "message",
                "data": {
                    "message": "Quiero ir a Tailandia por 7 días",
                    "is_user": True,
                    "travel_id": "test_travel_123"
                }
            }
            
            print(f"📤 Enviando mensaje: {json.dumps(test_message, indent=2)}")
            await websocket.send(json.dumps(test_message))
            
            # Esperar respuesta
            print("⏳ Esperando respuesta...")
            response = await websocket.recv()
            
            print(f"📥 Respuesta recibida: {response}")
            
            # Parsear respuesta
            try:
                response_data = json.loads(response)
                print(f"✅ Respuesta parseada: {json.dumps(response_data, indent=2)}")
                
                if response_data.get("type") == "message":
                    message = response_data.get("data", {})
                    print(f"📝 Mensaje del asistente: {message.get('message', '')[:100]}...")
                    print(f"🎯 Intención: {message.get('intention', 'unknown')}")
                else:
                    print(f"⚠️ Tipo de respuesta inesperado: {response_data.get('type')}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parseando respuesta: {e}")
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Conexión cerrada: {e}")
    except Exception as e:
        print(f"❌ Error en WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 