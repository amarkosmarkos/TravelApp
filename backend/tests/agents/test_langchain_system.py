#!/usr/bin/env python3
"""
Test del sistema LangChain completo.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import connect_to_mongodb
from app.agents.message_router import message_router
from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow

async def test_langchain_system():
    """Test del sistema LangChain completo."""
    try:
        print("Iniciando test del sistema LangChain...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("Conexión a MongoDB establecida")
        
        # Test 1: MessageRouter
        print("\nTest 1: MessageRouter")
        test_message = "Quiero crear un itinerario para Tailandia"
        classification = await message_router.classify_message(test_message)
        print(f"Clasificación: {classification}")
        
        # Test 2: SmartItineraryWorkflow
        print("\nTest 2: SmartItineraryWorkflow")
        smart_workflow = SmartItineraryWorkflow()
        print("SmartItineraryWorkflow creado")
        
        # Test 3: Procesamiento completo
        print("\nTest 3: Procesamiento completo")
        response = await message_router.route_message(
            message=test_message,
            user_id="test_user",
            travel_id="test_travel",
            context={"test": True}
        )
        print(f"Respuesta: {response}")
        
        print("\nTodos los tests del sistema LangChain pasaron!")
        
    except Exception as e:
        print(f"Error en test LangChain: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_langchain_system()) 