#!/usr/bin/env python3
"""
Test del ChatService.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import connect_to_mongodb
from app.services.chat_service import chat_service

async def test_chat_service():
    """Test del ChatService."""
    try:
        print("Iniciando test del ChatService...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("Conexión a MongoDB establecida")
        
        # Test 1: Procesar mensaje
        print("\nTest 1: Procesar mensaje")
        test_message = "Quiero crear un itinerario para Tailandia"
        response = await chat_service.process_message(
            message=test_message,
            user_id="test_user",
            travel_id="test_travel_123"
        )
        print(f"Respuesta: {response}")
        
        # Test 2: Obtener mensajes
        print("\nTest 2: Obtener mensajes")
        messages = await chat_service.get_chat_messages(
            travel_id="test_travel_123",
            user_id="test_user",
            db=None
        )
        print(f"Mensajes obtenidos: {len(messages)}")
        
        print("\nTodos los tests del ChatService pasaron!")
        
    except Exception as e:
        print(f"Error en test ChatService: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_service()) 