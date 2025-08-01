#!/usr/bin/env python3
"""
Test del DatabaseAgent arreglado.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongodb
from app.agents.database_agent import DatabaseAgent

async def test_database_agent_fixed():
    """Test del DatabaseAgent arreglado."""
    try:
        print("🔧 Probando DatabaseAgent arreglado...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("✅ Conexión a MongoDB establecida")
        
        # Crear instancia del DatabaseAgent
        db_agent = DatabaseAgent()
        
        # Test 1: Buscar ciudades de Tailandia
        print("\n🇹🇭 Test 1: Buscar ciudades de Tailandia")
        thailand_sites = await db_agent.search_cities_by_country("thailand")
        print(f"✅ Encontradas {len(thailand_sites)} entidades en Tailandia")
        
        # Mostrar algunos resultados
        for i, site in enumerate(thailand_sites[:5]):
            print(f"  {i+1}. {site['name']} ({site['type']}) - {site.get('description', 'Sin descripción')[:50]}...")
        
        # Test 2: Buscar ciudades de Japón
        print("\n🇯🇵 Test 2: Buscar ciudades de Japón")
        japan_sites = await db_agent.search_cities_by_country("japan")
        print(f"✅ Encontradas {len(japan_sites)} entidades en Japón")
        
        # Test 3: Buscar ciudades de España
        print("\n🇪🇸 Test 3: Buscar ciudades de España")
        spain_sites = await db_agent.search_cities_by_country("spain")
        print(f"✅ Encontradas {len(spain_sites)} entidades en España")
        
        print("\n✅ DatabaseAgent arreglado funciona correctamente!")
        
    except Exception as e:
        print(f"❌ Error en test DatabaseAgent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_agent_fixed()) 