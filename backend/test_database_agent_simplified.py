#!/usr/bin/env python3
"""
Test del DatabaseAgent simplificado (solo cities).
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongodb
from app.agents.database_agent import DatabaseAgent

async def test_database_agent_simplified():
    """Test del DatabaseAgent simplificado."""
    try:
        print("🔧 Probando DatabaseAgent simplificado (solo cities)...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("✅ Conexión a MongoDB establecida")
        
        # Crear instancia del DatabaseAgent
        db_agent = DatabaseAgent()
        
        # Test 1: Buscar ciudades de Tailandia
        print("\n🇹🇭 Test 1: Buscar ciudades de Tailandia")
        thailand_cities = await db_agent.search_cities_by_country("thailand")
        print(f"✅ Encontradas {len(thailand_cities)} ciudades en Tailandia")
        
        # Mostrar algunas ciudades
        for i, city in enumerate(thailand_cities[:10]):
            print(f"  {i+1}. {city['name']} - {city.get('description', 'Sin descripción')[:60]}...")
        
        # Test 2: Buscar ciudades de Japón
        print("\n🇯🇵 Test 2: Buscar ciudades de Japón")
        japan_cities = await db_agent.search_cities_by_country("japan")
        print(f"✅ Encontradas {len(japan_cities)} ciudades en Japón")
        
        # Mostrar algunas ciudades
        for i, city in enumerate(japan_cities[:5]):
            print(f"  {i+1}. {city['name']} - {city.get('description', 'Sin descripción')[:60]}...")
        
        # Test 3: Buscar ciudades de España
        print("\n🇪🇸 Test 3: Buscar ciudades de España")
        spain_cities = await db_agent.search_cities_by_country("spain")
        print(f"✅ Encontradas {len(spain_cities)} ciudades en España")
        
        # Mostrar algunas ciudades
        for i, city in enumerate(spain_cities[:5]):
            print(f"  {i+1}. {city['name']} - {city.get('description', 'Sin descripción')[:60]}...")
        
        print("\n✅ DatabaseAgent simplificado funciona correctamente!")
        
    except Exception as e:
        print(f"❌ Error en test DatabaseAgent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_agent_simplified()) 