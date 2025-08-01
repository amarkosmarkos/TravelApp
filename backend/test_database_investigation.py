#!/usr/bin/env python3
"""
Test para investigar la estructura de la base de datos.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import connect_to_mongodb, get_sites_collection, get_cities_collection

async def investigate_database():
    """Investiga la estructura de la base de datos."""
    try:
        print("🔍 Investigando la base de datos...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("✅ Conexión a MongoDB establecida")
        
        # Investigar colección de sitios
        print("\n📋 Investigando colección 'sites':")
        sites_collection = await get_sites_collection()
        
        # Ver algunos documentos de ejemplo
        sample_sites = await sites_collection.find().limit(5).to_list(length=None)
        print(f"Documentos de ejemplo en 'sites':")
        for site in sample_sites:
            print(f"  - {site}")
        
        # Buscar sitios de Tailandia con diferentes criterios
        print("\n🔍 Buscando sitios de Tailandia:")
        
        # Buscar por country_code
        thailand_sites_by_code = await sites_collection.find({"country_code": "TH"}).limit(5).to_list(length=None)
        print(f"Sitios con country_code='TH': {len(thailand_sites_by_code)}")
        
        # Buscar por nombre que contenga "thailand"
        thailand_sites_by_name = await sites_collection.find({"name": {"$regex": "thailand", "$options": "i"}}).limit(5).to_list(length=None)
        print(f"Sitios con nombre que contenga 'thailand': {len(thailand_sites_by_name)}")
        
        # Buscar por hierarchy que contenga "TH"
        thailand_sites_by_hierarchy = await sites_collection.find({"hierarchy": {"$regex": "TH", "$options": "i"}}).limit(5).to_list(length=None)
        print(f"Sitios con hierarchy que contenga 'TH': {len(thailand_sites_by_hierarchy)}")
        
        # Ver todos los campos únicos en la colección
        print("\n📊 Campos únicos en 'sites':")
        all_sites = await sites_collection.find().limit(10).to_list(length=None)
        if all_sites:
            fields = set()
            for site in all_sites:
                fields.update(site.keys())
            print(f"Campos encontrados: {sorted(fields)}")
        
        # Investigar colección de ciudades
        print("\n🏙️ Investigando colección 'cities':")
        cities_collection = await get_cities_collection()
        
        # Ver algunos documentos de ejemplo
        sample_cities = await cities_collection.find().limit(5).to_list(length=None)
        print(f"Documentos de ejemplo en 'cities':")
        for city in sample_cities:
            print(f"  - {city}")
        
        print("\n✅ Investigación completada!")
        
    except Exception as e:
        print(f"❌ Error en investigación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_database()) 