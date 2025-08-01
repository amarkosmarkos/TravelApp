#!/usr/bin/env python3
"""
Test para investigar por qué no se guarda el itinerario en la BBDD.
"""

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongodb, get_itineraries_collection
from app.agents.database_agent import DatabaseAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.routing_agent import RoutingAgent
from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow

async def test_itinerary_save_investigation():
    """Investiga por qué no se guarda el itinerario."""
    try:
        print("🔍 Investigando guardado de itinerarios...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("✅ Conexión a MongoDB establecida")
        
        # Test 1: Verificar que se puede guardar manualmente
        print("\n💾 Test 1: Guardado manual de itinerario")
        
        itineraries_collection = await get_itineraries_collection()
        
        # Crear un itinerario de prueba
        test_itinerary = {
            "travel_id": "test_travel_123",
            "user_id": "test_user_123",
            "country": "thailand",
            "cities": [
                {
                    "name": "Bangkok",
                    "latitude": 13.7563,
                    "longitude": 100.5018
                },
                {
                    "name": "Chiang Mai",
                    "latitude": 18.7883,
                    "longitude": 98.9853
                }
            ],
            "route": {
                "total_distance": 500.0,
                "estimated_time": 8.0,
                "algorithm": "tsp"
            },
            "itinerary": "Test itinerary content",
            "created_at": "2025-01-08T17:30:00Z",
            "updated_at": "2025-01-08T17:30:00Z"
        }
        
        # Intentar guardar
        result = await itineraries_collection.insert_one(test_itinerary)
        print(f"✅ Itinerario guardado con ID: {result.inserted_id}")
        
        # Verificar que se guardó
        saved_itinerary = await itineraries_collection.find_one({"_id": result.inserted_id})
        if saved_itinerary:
            print(f"✅ Itinerario encontrado en BBDD: {saved_itinerary['country']}")
        else:
            print("❌ Itinerario NO encontrado en BBDD")
        
        # Test 2: Verificar SmartItineraryWorkflow
        print("\n🤖 Test 2: SmartItineraryWorkflow")
        
        smart_workflow = SmartItineraryWorkflow()
        
        # Procesar solicitud
        response = await smart_workflow.process_smart_request(
            user_input="Quiero un itinerario para Tailandia",
            user_id="test_user_workflow",
            travel_id="test_travel_workflow",
            country="thailand"
        )
        
        print(f"✅ Workflow response: {response.get('intention', 'unknown')}")
        print(f"   - Mensaje: {len(response.get('message', ''))} caracteres")
        
        # Test 3: Verificar si se guardó el itinerario del workflow
        print("\n🔍 Test 3: Verificar itinerario del workflow")
        
        workflow_itinerary = await itineraries_collection.find_one({
            "travel_id": "test_travel_workflow"
        })
        
        if workflow_itinerary:
            print(f"✅ Itinerario del workflow guardado: {workflow_itinerary['country']}")
            print(f"   - Ciudades: {len(workflow_itinerary.get('cities', []))}")
            print(f"   - Tiene coordenadas: {bool(workflow_itinerary.get('cities', [{}])[0].get('latitude'))}")
        else:
            print("❌ Itinerario del workflow NO guardado")
        
        # Test 4: Verificar todos los itinerarios en la BBDD
        print("\n📊 Test 4: Todos los itinerarios en BBDD")
        
        all_itineraries = await itineraries_collection.find({}).to_list(length=None)
        print(f"✅ Total itinerarios en BBDD: {len(all_itineraries)}")
        
        for i, itinerary in enumerate(all_itineraries):
            print(f"   {i+1}. {itinerary.get('country', 'unknown')} - {itinerary.get('travel_id', 'no_id')}")
            if itinerary.get('cities'):
                print(f"      - Ciudades: {len(itinerary['cities'])}")
                print(f"      - Coordenadas: {bool(itinerary['cities'][0].get('latitude'))}")
        
        print("\n✅ Investigación de guardado completada!")
        
    except Exception as e:
        print(f"❌ Error en investigación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_itinerary_save_investigation()) 