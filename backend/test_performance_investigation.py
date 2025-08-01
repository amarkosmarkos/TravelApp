#!/usr/bin/env python3
"""
Test para investigar el rendimiento y uso de herramientas.
"""

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongodb
from app.agents.database_agent import DatabaseAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.routing_agent import RoutingAgent

async def test_performance_investigation():
    """Investiga el rendimiento y uso de herramientas."""
    try:
        print("🔍 Investigando rendimiento y herramientas...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("✅ Conexión a MongoDB establecida")
        
        # Test 1: DatabaseAgent performance
        print("\n📊 Test 1: DatabaseAgent performance")
        start_time = time.time()
        
        db_agent = DatabaseAgent()
        thailand_cities = await db_agent.search_cities_by_country("thailand")
        
        db_time = time.time() - start_time
        print(f"✅ DatabaseAgent: {len(thailand_cities)} ciudades en {db_time:.2f}s")
        
        # Test 2: RoutingAgent performance
        print("\n🗺️ Test 2: RoutingAgent performance")
        start_time = time.time()
        
        routing_agent = RoutingAgent()
        # Usar solo las primeras 5 ciudades para el test
        test_cities = thailand_cities[:5]
        route = routing_agent.calculate_route(test_cities)
        
        routing_time = time.time() - start_time
        print(f"✅ RoutingAgent: Ruta calculada en {routing_time:.2f}s")
        print(f"   - Total distancia: {route.get('total_distance', 0):.2f} km")
        print(f"   - Algoritmo usado: {route.get('algorithm', 'unknown')}")
        
        # Test 3: ItineraryAgent performance
        print("\n📝 Test 3: ItineraryAgent performance")
        start_time = time.time()
        
        itinerary_agent = ItineraryAgent()
        itinerary = itinerary_agent.create_itinerary(
            country="thailand",
            cities=test_cities,
            route=route
        )
        
        itinerary_time = time.time() - start_time
        print(f"✅ ItineraryAgent: Itinerario generado en {itinerary_time:.2f}s")
        print(f"   - Tiene itinerario: {'itinerary' in itinerary}")
        print(f"   - Tiene summary: {'summary' in itinerary}")
        
        # Test 4: Tiempo total estimado
        total_time = db_time + routing_time + itinerary_time
        print(f"\n⏱️ Tiempo total estimado: {total_time:.2f}s")
        
        # Test 5: Verificar que se usen todas las herramientas
        print("\n🔧 Test 5: Verificar uso de herramientas")
        
        # Verificar que DatabaseAgent devuelve datos correctos
        if len(thailand_cities) > 0:
            print(f"✅ DatabaseAgent: Funciona correctamente")
            print(f"   - Ejemplo: {thailand_cities[0]['name']}")
        else:
            print("❌ DatabaseAgent: No devuelve datos")
        
        # Verificar que RoutingAgent calcula rutas
        if route.get('route') and len(route['route']) > 0:
            print(f"✅ RoutingAgent: Calcula rutas correctamente")
            print(f"   - Ciudades en ruta: {len(route['route'])}")
        else:
            print("❌ RoutingAgent: No calcula rutas")
        
        # Verificar que ItineraryAgent genera itinerarios
        if itinerary.get('itinerary'):
            print(f"✅ ItineraryAgent: Genera itinerarios correctamente")
            itinerary_text = itinerary['itinerary']
            print(f"   - Longitud del itinerario: {len(itinerary_text)} caracteres")
        else:
            print("❌ ItineraryAgent: No genera itinerarios")
        
        print("\n✅ Investigación de rendimiento completada!")
        
    except Exception as e:
        print(f"❌ Error en investigación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_performance_investigation()) 