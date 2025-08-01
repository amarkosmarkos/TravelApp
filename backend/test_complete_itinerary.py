#!/usr/bin/env python3
"""
Test del sistema completo de generación de itinerarios.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongodb
from app.agents.message_router import message_router

async def test_complete_itinerary():
    """Test del sistema completo de itinerarios."""
    try:
        print("🗺️ Probando sistema completo de itinerarios...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("✅ Conexión a MongoDB establecida")
        
        # Test 1: Crear itinerario para Tailandia
        print("\n🇹🇭 Test 1: Crear itinerario para Tailandia")
        test_message = "Quiero crear un itinerario para Tailandia con Bangkok, Chiang Mai y Ayutthaya"
        
        response = await message_router.route_message(
            message=test_message,
            user_id="test_user",
            travel_id="test_travel_thailand",
            context={"test": True}
        )
        
        print(f"Respuesta del sistema:")
        print(response.get("message", "No se generó mensaje"))
        
        # Test 2: Crear itinerario para Japón
        print("\n🇯🇵 Test 2: Crear itinerario para Japón")
        test_message_japan = "Quiero crear un itinerario para Japón"
        
        response_japan = await message_router.route_message(
            message=test_message_japan,
            user_id="test_user",
            travel_id="test_travel_japan",
            context={"test": True}
        )
        
        print(f"Respuesta del sistema:")
        print(response_japan.get("message", "No se generó mensaje"))
        
        print("\n✅ Sistema completo de itinerarios probado!")
        
    except Exception as e:
        print(f"❌ Error en test completo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_itinerary()) 